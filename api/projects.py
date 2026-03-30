"""Project and document management API endpoints."""

import logging
from threading import Thread

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pipeline.ingestion import ingest_document
from pipeline.pinecone_helpers import delete_namespace, delete_document_vectors
from pipeline.retrieval_cache import invalidate_project_cache
from pipeline.storage import (
    ensure_bucket,
    get_presigned_put_url,
    delete_object,
    delete_project_objects,
)
from api.session import create_project_session, delete_session
from api.project_chat import project_chat_stream
from agents import AGENTS

logger = logging.getLogger("api.projects")

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectChatRequest(BaseModel):
    session_id: str
    message: str
    chunk_count: int = 0
    agent: str | None = None


class PresignedUrlRequest(BaseModel):
    document_id: str
    filename: str


class IngestRequest(BaseModel):
    document_id: str
    filename: str


# ─── Document processing status (in-memory, keyed by document_id) ───
_processing_status: dict[str, dict] = {}


def _process_document(
    object_key: str,
    project_id: str,
    document_id: str,
    filename: str,
):
    """Background task: run the ingestion pipeline and update status."""
    _processing_status[document_id] = {"status": "processing", "error": None}

    try:
        result = ingest_document(
            object_key=object_key,
            project_id=project_id,
            document_id=document_id,
            filename=filename,
        )
        _processing_status[document_id] = {
            "status": "ready",
            "chunk_count": result["chunk_count"],
            "chunk_strategy": result["chunk_strategy"],
            "error": None,
        }
        logger.info(f"document '{document_id}' processed: {result['chunk_count']} chunks")
        invalidate_project_cache(project_id)

    except Exception as e:
        logger.error(f"document '{document_id}' processing failed: {e}")
        _processing_status[document_id] = {
            "status": "failed",
            "error": str(e),
        }


# ─── Presigned URL endpoint ───

@router.post("/{project_id}/presign")
def get_upload_url(project_id: str, req: PresignedUrlRequest):
    """Generate a presigned PUT URL for direct browser-to-MinIO upload."""
    ext = req.filename.rsplit(".", 1)[-1].lower() if "." in req.filename else ""
    if ext not in {"pdf", "txt", "md", "csv", "docx"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: pdf, txt, md, csv, docx",
        )

    object_key = f"{project_id}/{req.document_id}.{ext}"

    try:
        ensure_bucket()
        url = get_presigned_put_url(object_key)
    except Exception as e:
        logger.error(f"failed to generate presigned URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")

    return {"url": url, "object_key": object_key}


# ─── Ingest trigger endpoint ───

@router.post("/{project_id}/ingest")
def trigger_ingest(project_id: str, req: IngestRequest):
    """Trigger background ingestion after the file has been uploaded to MinIO."""
    ext = req.filename.rsplit(".", 1)[-1].lower() if "." in req.filename else ""
    object_key = f"{project_id}/{req.document_id}.{ext}"

    _processing_status[req.document_id] = {"status": "processing", "error": None}

    thread = Thread(
        target=_process_document,
        args=(object_key, project_id, req.document_id, req.filename),
        daemon=True,
    )
    thread.start()

    return {"document_id": req.document_id, "status": "processing"}


# ─── Status endpoint ───

@router.get("/{project_id}/documents/{document_id}/status")
def get_document_status(project_id: str, document_id: str):
    """Check processing status of a document."""
    status = _processing_status.get(document_id)
    if not status:
        raise HTTPException(status_code=404, detail="Document not found in processing queue")
    return {"document_id": document_id, **status}


# ─── Delete endpoints ───

@router.delete("/{project_id}")
def delete_project(project_id: str):
    """Delete a project's vectors and uploaded files."""
    try:
        delete_namespace(project_id)
    except Exception as e:
        logger.warning(f"failed to delete Pinecone namespace: {e}")

    try:
        delete_project_objects(project_id)
    except Exception as e:
        logger.warning(f"failed to delete MinIO objects: {e}")

    invalidate_project_cache(project_id)
    return {"status": "deleted"}


@router.delete("/{project_id}/documents/{document_id}")
def delete_document(project_id: str, document_id: str):
    """Delete a document's vectors from Pinecone and file from MinIO."""
    try:
        delete_document_vectors(project_id, document_id)
    except Exception as e:
        logger.warning(f"failed to delete document vectors: {e}")

    # Try to clean up the MinIO object (we don't know the extension, so list by prefix)
    try:
        from clients import minio_client
        from pipeline.storage import BUCKET_NAME
        objects = minio_client.list_objects(BUCKET_NAME, prefix=f"{project_id}/{document_id}")
        for obj in objects:
            minio_client.remove_object(BUCKET_NAME, obj.object_name)
    except Exception as e:
        logger.warning(f"failed to delete MinIO object: {e}")

    _processing_status.pop(document_id, None)
    invalidate_project_cache(project_id)
    return {"status": "deleted"}


# ─── Agents ───

@router.get("/agents")
def list_agents():
    """List all available project agents."""
    return [
        {"name": a.name, "description": a.description, "structured_output": a.structured_output}
        for a in AGENTS.values()
    ]


# ─── Project chat endpoints ───

@router.post("/{project_id}/session")
def new_project_session(project_id: str, project_name: str = "", user_id: str = ""):
    """Create a new Redis session scoped to a project."""
    session_id = create_project_session(project_name, user_id=user_id)
    return {"session_id": session_id}


@router.delete("/{project_id}/session/{session_id}")
def remove_project_session(project_id: str, session_id: str):
    """Delete a project chat session from Redis."""
    delete_session(session_id)
    return {"status": "deleted"}


@router.post("/{project_id}/chat")
def project_chat(project_id: str, req: ProjectChatRequest):
    """Send a message and receive an SSE stream with RAG-augmented response."""
    try:
        return StreamingResponse(
            project_chat_stream(
                session_id=req.session_id,
                user_message=req.message,
                project_id=project_id,
                chunk_count=req.chunk_count,
                agent_name=req.agent,
            ),
            media_type="text/event-stream",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
