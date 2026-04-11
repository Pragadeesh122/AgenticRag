import asyncio
import hashlib
import json
import logging

from memory import extract_and_persist_memories
from memory.redis_client import redis_client

logger = logging.getLogger("worker.memory")

MEMORY_TASK_TTL = 60 * 60 * 24 * 7
MEMORY_TASK_LOCK_TTL = 60 * 5


def _memory_task_fingerprint(messages: list[dict]) -> str:
    normalized = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
        if isinstance(msg, dict)
        and msg.get("role") in ("user", "assistant")
        and msg.get("content")
    ]
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def persist_memories_task(ctx, user_id: str, messages: list[dict]):
    fingerprint = _memory_task_fingerprint(messages)
    processed_key = f"memory-task:{user_id}:{fingerprint}:done"
    lock_key = f"memory-task:{user_id}:{fingerprint}:lock"

    if redis_client.get(processed_key):
        logger.info("memory task skipped: already processed")
        return {"status": "skipped", "fingerprint": fingerprint}

    lock_acquired = redis_client.set(lock_key, "1", ex=MEMORY_TASK_LOCK_TTL, nx=True)
    if not lock_acquired:
        logger.info("memory task skipped: already in progress")
        return {"status": "in_progress", "fingerprint": fingerprint}

    try:
        if redis_client.get(processed_key):
            logger.info("memory task skipped after lock: already processed")
            return {"status": "skipped", "fingerprint": fingerprint}

        await asyncio.to_thread(extract_and_persist_memories, messages, user_id)
        redis_client.set(processed_key, "1", ex=MEMORY_TASK_TTL)
        logger.info("memory task persisted successfully")
        return {"status": "ok", "fingerprint": fingerprint}
    finally:
        redis_client.delete(lock_key)
