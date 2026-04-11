import asyncio
import logging
import os

from arq import create_pool
from arq.connections import RedisSettings

logger = logging.getLogger("services.chat_postprocess")

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))


def _normalize_memory_messages(messages: list[dict]) -> list[dict]:
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
        if isinstance(msg, dict)
        and msg.get("role") in ("user", "assistant")
        and msg.get("content")
    ]


async def _enqueue_memory_persistence(messages: list[dict], user_id: str) -> None:
    pool = await create_pool(RedisSettings(host=redis_host, port=redis_port))
    await pool.enqueue_job("persist_memories_task", user_id, messages)


def schedule_memory_persistence(messages: list[dict], user_id: str) -> None:
    normalized_messages = _normalize_memory_messages(messages)
    if not user_id or not normalized_messages:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(_enqueue_memory_persistence(normalized_messages, user_id))
        except Exception as exc:
            logger.error(f"failed to enqueue memory persistence: {exc}")
        return

    loop.create_task(_enqueue_memory_persistence(normalized_messages, user_id))
