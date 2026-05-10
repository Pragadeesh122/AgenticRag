"""Resolve general-chat attachments into LLM content blocks.

Images become {"type": "image_url", ...} blocks pointing at a presigned MinIO URL.
Documents (pdf/docx/csv/md/txt) are downloaded, text-extracted, and inlined as
text blocks so the LLM can read their content directly.
"""

import logging
import os
import tempfile
from typing import Iterable

from pipeline.extractor import extract_text, SUPPORTED_TYPES as DOC_TYPES
from pipeline.storage import (
    download_to_file,
    get_presigned_get_url,
)

logger = logging.getLogger("pipeline.chat_attachments")

IMAGE_MIME_PREFIX = "image/"
IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "gif"}

# Cap inlined extracted text per file so a 200-page PDF can't blow the prompt.
MAX_EXTRACTED_CHARS = 200_000

# Presigned GET URL TTL for image links handed to the LLM. 1h is enough for the
# turn; the URL is regenerated every time we rebuild context.
IMAGE_URL_TTL = 3600


def _ext_from(att: dict) -> str:
    filename = att.get("filename") or ""
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


def _is_image(att: dict) -> bool:
    mime = (att.get("mimeType") or "").lower()
    if mime.startswith(IMAGE_MIME_PREFIX):
        return True
    return _ext_from(att) in IMAGE_EXTS


def _resolve_image(att: dict) -> dict | None:
    storage_key = att.get("storageKey")
    if not storage_key:
        return None
    try:
        url = get_presigned_get_url(storage_key, expires=IMAGE_URL_TTL)
    except Exception as exc:
        logger.warning("failed to presign image '%s': %s", storage_key, exc)
        return None
    return {"type": "image_url", "image_url": {"url": url}}


def _resolve_document(att: dict) -> dict | None:
    storage_key = att.get("storageKey")
    filename = att.get("filename") or "attachment"
    ext = _ext_from(att)
    if ext not in DOC_TYPES:
        logger.warning("skipping unsupported attachment type '%s' for %s", ext, filename)
        return None
    if not storage_key:
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp_path = tmp.name
        download_to_file(storage_key, tmp_path)
        sections = extract_text(tmp_path)
    except Exception as exc:
        logger.warning("failed to extract '%s' (%s): %s", filename, storage_key, exc)
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    if not sections:
        return None

    parts = []
    for section in sections:
        text = (section.get("text") or "").strip()
        if not text:
            continue
        page = section.get("page_number")
        if page is not None:
            parts.append(f"[page {page}]\n{text}")
        else:
            parts.append(text)
    body = "\n\n".join(parts)
    if not body:
        return None

    truncated = False
    if len(body) > MAX_EXTRACTED_CHARS:
        body = body[:MAX_EXTRACTED_CHARS]
        truncated = True
        logger.info(
            "truncated extracted text for '%s' to %d chars", filename, MAX_EXTRACTED_CHARS
        )

    suffix = "\n\n[content truncated]" if truncated else ""
    return {
        "type": "text",
        "text": f"[Attached file: {filename}]\n{body}{suffix}",
    }


def resolve_to_content_block(att: dict) -> dict | None:
    """Convert one attachment ref into an OpenAI-style content block.

    Returns None if the attachment can't be resolved (the caller should drop it).
    """
    if _is_image(att):
        return _resolve_image(att)
    return _resolve_document(att)


def build_user_content(text: str, attachments: Iterable[dict] | None) -> str | list[dict]:
    """Build a user-message ``content`` value.

    With no attachments we keep the existing plain-string shape so downstream
    paths (Redis history, summarizer, memory extraction) are unchanged. With
    attachments we return the OpenAI list-form content array — the user's text
    first, then one block per attachment.
    """
    refs = list(attachments or [])
    if not refs:
        return text

    blocks: list[dict] = []
    if text:
        blocks.append({"type": "text", "text": text})

    for att in refs:
        block = resolve_to_content_block(att)
        if block is not None:
            blocks.append(block)

    if not blocks:
        return text
    if len(blocks) == 1 and blocks[0].get("type") == "text":
        return blocks[0]["text"]
    return blocks
