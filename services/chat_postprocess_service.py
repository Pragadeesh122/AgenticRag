import asyncio
import logging
import os
from typing import Optional

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


async def _enqueue_memory_persistence(
    messages: list[dict],
    user_id: str,
    session_id: Optional[str],
) -> None:
    pool = await create_pool(RedisSettings(host=redis_host, port=redis_port))
    await pool.enqueue_job(
        "persist_memories_task", user_id, messages, session_id
    )


async def _enqueue_memory_summary_refresh(
    messages: list[dict],
    session_id: str,
) -> None:
    pool = await create_pool(RedisSettings(host=redis_host, port=redis_port))
    await pool.enqueue_job(
        "refresh_rolling_summary_task", messages, session_id
    )


def schedule_memory_persistence(
    messages: list[dict],
    user_id: str,
    session_id: Optional[str] = None,
) -> None:
    normalized_messages = _normalize_memory_messages(messages)
    if not user_id or not normalized_messages:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(
                _enqueue_memory_persistence(normalized_messages, user_id, session_id)
            )
        except Exception as exc:
            logger.error(f"failed to enqueue memory persistence: {exc}")
        return

    loop.create_task(
        _enqueue_memory_persistence(normalized_messages, user_id, session_id)
    )


def schedule_memory_summary_refresh(
    messages: list[dict],
    session_id: Optional[str],
) -> None:
    normalized_messages = _normalize_memory_messages(messages)
    if not session_id or not normalized_messages:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(
                _enqueue_memory_summary_refresh(normalized_messages, session_id)
            )
        except Exception as exc:
            logger.error(f"failed to enqueue rolling summary refresh: {exc}")
        return

    loop.create_task(
        _enqueue_memory_summary_refresh(normalized_messages, session_id)
    )
