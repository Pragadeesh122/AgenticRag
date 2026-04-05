import os
import uuid
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from arq import create_pool
from arq.connections import RedisSettings
from typing import Optional, List

from api.auth.manager import current_active_user
from database.core import get_db
from database.models import User, Project, Document, ChatSession, ChatMessage
from services.project_service import ProjectService
from services.document_service import DocumentService
from pipeline.storage import ensure_bucket, get_presigned_put_url
from api.project_chat import project_chat_stream
from tasks.document_tasks import process_document_task

from agents.registry import AGENTS

logger = logging.getLogger("api.projects")

router = APIRouter(prefix="/projects", tags=["projects"])

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
document_ingest_mode = os.getenv("DOCUMENT_INGEST_MODE", "worker").lower()


async def get_arq_pool():
    return await create_pool(RedisSettings(host=redis_host, port=redis_port))

# --- Schemas ---
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class UploadInitRequest(BaseModel):
    filename: str
    fileSize: int = 0

class UploadConfirmRequest(BaseModel):
    documentId: str
    filename: str

class ProjectChatRequest(BaseModel):
    sessionId: str
    message: str
    agent: Optional[str] = None

# --- Project CRUD ---
def _serialize_document(d):
    return {
        "id": d.id,
        "projectId": d.project_id,
        "filename": d.filename,
        "fileType": d.file_type,
        "fileSize": d.file_size,
        "chunkCount": d.chunk_count,
        "chunkStrategy": d.chunk_strategy,
        "status": d.status,
        "errorMessage": d.error_message,
        "createdAt": d.created_at.isoformat() if hasattr(d, 'created_at') and d.created_at else None
    }

def _serialize_project(p):
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "status": p.status,
        "documents": [_serialize_document(d) for d in getattr(p, "documents", [])],
        "createdAt": p.created_at.isoformat() if hasattr(p, "created_at") and p.created_at else None,
        "updatedAt": p.updated_at.isoformat() if hasattr(p, "updated_at") and p.updated_at else None,
    }

@router.get("")
async def list_projects(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    projects = await ProjectService(db).get_user_projects(user.id)
    return [_serialize_project(p) for p in projects]

@router.post("")
async def create_project(
    data: ProjectCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    project = await ProjectService(db).create_project(user.id, data.name, data.description)
    return _serialize_project(project)

# Ensure /agents is declared BEFORE /{project_id}
@router.get("/agents")
def list_agents():
    return [
        {
            "name": agent.name,
            "description": agent.description,
            "capabilities": getattr(agent, "capabilities", []),
        }
        for agent in AGENTS.values()
    ]

@router.get("/{project_id}")
async def fetch_project(
    project_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    project = await ProjectService(db).get_project(project_id, user.id)
    if not project:
        raise HTTPException(404, "Project not found")
    return _serialize_project(project)

@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    project = await ProjectService(db).get_project(project_id, user.id)
    if not project:
        raise HTTPException(404, "Project not found")
    
    stmt = select(Project).where(Project.id == project_id)
    p = (await db.execute(stmt)).scalar_one()
    if data.name is not None:
        p.name = data.name
    if data.description is not None:
        p.description = data.description
    if data.status is not None:
        p.status = data.status
    await db.commit()
    return {"status": "ok"}

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await ProjectService(db).delete_project(project_id, user.id)
    return {"status": "deleted"}


# --- Documents CRUD & Upload flow ---
@router.post("/{project_id}/upload")
async def start_upload(
    project_id: str,
    req: UploadInitRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate DB record and presigned PUT URL."""
    project = await ProjectService(db).get_project(project_id, user.id)
    if not project:
        raise HTTPException(404, "Project not found")
    
    ext = req.filename.rsplit(".", 1)[-1].lower() if "." in req.filename else ""
    supported = {"pdf", "txt", "md", "csv", "docx"}
    if ext not in supported:
        raise HTTPException(400, f"Unsupported file type. Supported: {', '.join(supported)}")

    doc_service = DocumentService(db)
    # create_document_record acts as initialization
    doc = await doc_service.create_document_record(
        project_id=project_id,
        user_id=user.id,
        filename=req.filename,
        file_type=ext,
        file_size=req.fileSize
    )
    
    object_key = f"{project_id}/{doc.id}.{ext}"
    try:
        ensure_bucket()
        url = get_presigned_put_url(object_key)
    except Exception as e:
        logger.error(f"failed to generate presigned URL: {e}")
        # rollback document creation conceptually
        await db.execute(delete(Document).where(Document.id == doc.id))
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")

    serialized = _serialize_document(doc)
    return {
        **serialized,
        "uploadUrl": url
    }

@router.put("/{project_id}/upload")
async def confirm_upload(
    project_id: str,
    req: UploadConfirmRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger background ingestion after MinIO upload completes."""
    project = await ProjectService(db).get_project(project_id, user.id)
    if not project:
        raise HTTPException(404, "Project not found")

    ext = req.filename.rsplit(".", 1)[-1].lower() if "." in req.filename else ""
    object_key = f"{project_id}/{req.documentId}.{ext}"

    stmt = select(Document).where(Document.id == req.documentId, Document.project_id == project_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
        
    doc.status = "processing"
    await db.commit()

    if document_ingest_mode == "background":
        background_tasks.add_task(
            process_document_task,
            {},
            object_key,
            project_id,
            req.documentId,
            req.filename,
        )
    else:
        arq_pool = await get_arq_pool()
        await arq_pool.enqueue_job(
            "process_document_task",
            object_key,
            project_id,
            req.documentId,
            req.filename,
        )

    return {"document_id": req.documentId, "status": "processing"}

@router.get("/{project_id}/documents")
async def list_documents(
    project_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    docs = await DocumentService(db).get_project_documents(project_id, user.id)
    return [_serialize_document(d) for d in docs]

@router.delete("/{project_id}/documents/{doc_id}")
async def remove_document(
    project_id: str,
    doc_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    doc_service = DocumentService(db)
    await doc_service.delete_document(project_id, doc_id, user.id)
    return {"status": "deleted"}

@router.get("/{project_id}/documents/{doc_id}/status")
async def get_document_status(
    project_id: str,
    doc_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    project = await ProjectService(db).get_project(project_id, user.id)
    if not project:
        raise HTTPException(404, "Project not found")

    stmt = select(Document).where(Document.id == doc_id, Document.project_id == project_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
        
    return {
        "status": doc.status,
        "chunkCount": doc.chunk_count,
        "chunkStrategy": doc.chunk_strategy,
        "errorMessage": doc.error_message
    }

# --- Project Chat Sessions ---
@router.get("/{project_id}/sessions")
async def get_project_sessions(
    project_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatSession).where(
        ChatSession.project_id == project_id,
        ChatSession.user_id == user.id
    ).order_by(ChatSession.updated_at.desc())
    sessions = (await db.execute(stmt)).scalars().all()
    
    return [{
        "id": s.id,
        "projectId": s.project_id,
        "backendSessionId": s.backend_session_id,
        "title": s.title,
        "createdAt": s.created_at.isoformat(),
        "updatedAt": s.updated_at.isoformat()
    } for s in sessions]

@router.post("/{project_id}/session")
async def create_project_session(
    project_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    from api.session import create_session
    sid = create_session(str(user.id))
    
    new_id = str(uuid.uuid4())
    session = ChatSession(
        id=new_id,
        user_id=user.id,
        project_id=project_id,
        title="New chat",
        backend_session_id=sid
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "id": session.id,
        "projectId": session.project_id,
        "backendSessionId": session.backend_session_id,
        "title": session.title,
        "createdAt": session.created_at.isoformat(),
        "updatedAt": session.updated_at.isoformat()
    }

@router.delete("/{project_id}/session/{session_id}")
async def remove_project_session(
    project_id: str,
    session_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.project_id == project_id,
        ChatSession.user_id == user.id
    )
    s = (await db.execute(stmt)).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Session not found")
        
    from api.session import delete_session
    if s.backend_session_id:
        delete_session(s.backend_session_id)
        
    await db.delete(s)
    await db.commit()
    return {"status": "ok"}

@router.post("/{project_id}/chat")
def project_chat_endpoint(
    project_id: str,
    req: ProjectChatRequest,
    user: User = Depends(current_active_user)
):
    try:
        return StreamingResponse(
            project_chat_stream(
                session_id=req.sessionId,
                user_message=req.message,
                project_id=project_id,
                chunk_count=0,
                agent_name=req.agent
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"stream failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
