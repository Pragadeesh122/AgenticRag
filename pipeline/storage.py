"""MinIO object storage helpers for document upload and retrieval."""

import logging
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit
import os

from clients import minio_client

logger = logging.getLogger("pipeline.storage")

BUCKET_NAME = "agenticrag-documents"


def ensure_bucket() -> None:
    """Create the bucket if it doesn't exist."""
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
        logger.info(f"created bucket '{BUCKET_NAME}'")


def get_presigned_put_url(object_key: str, expires: int = 3600) -> str:
    """Generate a presigned PUT URL for direct browser upload.

    Args:
        object_key: The object key (e.g. "project_id/document_id.pdf")
        expires: URL expiry in seconds (default 1 hour)

    Returns:
        Presigned URL string
    """
    ensure_bucket()
    url = minio_client.presigned_put_object(
        BUCKET_NAME,
        object_key,
        expires=timedelta(seconds=expires),
    )
    public_base = os.getenv("MINIO_PUBLIC_BASE_URL")
    if not public_base:
        return url

    signed = urlsplit(url)
    public = urlsplit(public_base)
    return urlunsplit(
        (
            public.scheme or signed.scheme,
            public.netloc or public.path,
            signed.path,
            signed.query,
            signed.fragment,
        )
    )


def download_to_bytes(object_key: str) -> bytes:
    """Download an object from MinIO and return its bytes."""
    response = minio_client.get_object(BUCKET_NAME, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def download_to_file(object_key: str, file_path: str) -> str:
    """Download an object from MinIO to a local file path.

    Returns the file_path for convenience.
    """
    minio_client.fget_object(BUCKET_NAME, object_key, file_path)
    logger.info(f"downloaded '{object_key}' → '{file_path}'")
    return file_path


def delete_object(object_key: str) -> None:
    """Delete a single object from MinIO."""
    minio_client.remove_object(BUCKET_NAME, object_key)
    logger.info(f"deleted object '{object_key}'")


def delete_project_objects(project_id: str) -> None:
    """Delete all objects under a project prefix."""
    objects = minio_client.list_objects(BUCKET_NAME, prefix=f"{project_id}/")
    for obj in objects:
        minio_client.remove_object(BUCKET_NAME, obj.object_name)
    logger.info(f"deleted all objects for project '{project_id}'")
