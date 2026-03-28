"""Ingestion orchestrator: extract -> chunk -> embed -> upsert to Pinecone."""

import logging
import os
import tempfile

from pipeline.extractor import extract_text
from pipeline.chunker import chunk_pages
from pipeline.embedder import embed_dense, embed_sparse
from pipeline.pinecone_helpers import ensure_index, upsert_vectors
from pipeline.storage import download_to_file

logger = logging.getLogger("pipeline.ingestion")


def ingest_document(
    object_key: str,
    project_id: str,
    document_id: str,
    filename: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 300,
) -> dict:
    """Full ingestion pipeline for a single document.

    Downloads the file from MinIO, then runs extract -> chunk -> embed -> upsert.

    Args:
        object_key: MinIO object key (e.g. "project_id/document_id.pdf")
        project_id: Project ID for Pinecone namespace
        document_id: Document ID for vector metadata
        filename: Original filename (used for extension detection)
        chunk_size: Target chunk size in characters (~400-500 tokens)
        chunk_overlap: Overlap between chunks in characters

    Returns:
        {"chunk_count": int, "chunk_strategy": str}
    """
    ensure_index()

    # Download from MinIO to a temp file
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    tmp_dir = tempfile.mkdtemp(prefix="agenticrag_")
    file_path = os.path.join(tmp_dir, f"{document_id}.{ext}")

    try:
        logger.info(f"downloading '{object_key}' from MinIO")
        download_to_file(object_key, file_path)

        # 1. Extract text
        logger.info(f"extracting text from '{file_path}'")
        pages = extract_text(file_path)
        if not pages:
            raise ValueError(f"No text extracted from '{filename}'")

        logger.info(f"extracted {len(pages)} pages/sections")

        # 2. Chunk
        chunks, strategy = chunk_pages(pages, chunk_size, chunk_overlap)
        if not chunks:
            raise ValueError(f"No chunks produced from '{filename}'")

        logger.info(f"produced {len(chunks)} chunks using '{strategy}'")

        # 3. Embed (dense + sparse)
        texts = [c["text"] for c in chunks]
        dense_embeddings = embed_dense(texts)
        sparse_embeddings = embed_sparse(texts)

        # 4. Build vectors with metadata (Pinecone rejects null values)
        vectors = []
        running_offset = 0
        for i, chunk in enumerate(chunks):
            vector_id = f"{document_id}_{i}"
            metadata = {
                "text": chunk["text"][:8000],  # Pinecone allows 40KB per field
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"],
                "start_index": running_offset,
                "document_id": document_id,
                "project_id": project_id,
            }
            # Only include page if it's a real value (PDFs)
            if chunk.get("page_number") is not None:
                metadata["page"] = chunk["page_number"]

            vectors.append({
                "id": vector_id,
                "values": dense_embeddings[i],
                "sparse_values": sparse_embeddings[i],
                "metadata": metadata,
            })
            running_offset += len(chunk["text"])

        # 5. Upsert to Pinecone
        upsert_vectors(project_id, vectors)

        logger.info(
            f"ingested document '{document_id}': "
            f"{len(chunks)} chunks, strategy='{strategy}'"
        )

        return {"chunk_count": len(chunks), "chunk_strategy": strategy}

    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(tmp_dir):
            os.rmdir(tmp_dir)
