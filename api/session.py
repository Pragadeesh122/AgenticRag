"""Redis-backed session store for conversation histories."""

import uuid
import json
import logging
from memory import get_user_memory
from memory.redis_client import redis_client
from prompts import ORCHESTRATOR
from prompts.project_chat import PROJECT_CHAT

logger = logging.getLogger("session")

SESSION_PREFIX = "session:"
SESSION_TTL = 60 * 60 * 24  # 24 hours


def _session_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}{session_id}"


def _build_system_prompt() -> str:
    system_prompt = ORCHESTRATOR
    user_memory = get_user_memory()
    if user_memory:
        system_prompt += f"\n\nKnown facts about the user:\n{user_memory}"
        logger.info("loaded user memory from Redis")
    return system_prompt


def create_session() -> str:
    session_id = uuid.uuid4().hex[:12]
    messages = [{"role": "system", "content": _build_system_prompt()}]
    redis_client.set(
        _session_key(session_id),
        json.dumps(messages),
        ex=SESSION_TTL,
    )
    logger.info(f"created session {session_id}")
    return session_id


def create_project_session(project_name: str = "") -> str:
    """Create a session scoped to a project (RAG context, no tools)."""
    session_id = uuid.uuid4().hex[:12]
    system_prompt = PROJECT_CHAT
    if project_name:
        system_prompt += f"\n\nYou are answering questions about the project: **{project_name}**\n"
    user_memory = get_user_memory()
    if user_memory:
        system_prompt += f"\nKnown facts about the user:\n{user_memory}"
    messages = [{"role": "system", "content": system_prompt}]
    redis_client.set(
        _session_key(session_id),
        json.dumps(messages),
        ex=SESSION_TTL,
    )
    logger.info(f"created project session {session_id}")
    return session_id


def get_messages(session_id: str) -> list[dict]:
    data = redis_client.get(_session_key(session_id))
    if data is None:
        raise KeyError(f"session '{session_id}' not found")
    return json.loads(data)


def save_messages(session_id: str, messages: list[dict]) -> None:
    """Persist the current message list back to Redis."""
    redis_client.set(
        _session_key(session_id),
        json.dumps(messages),
        ex=SESSION_TTL,
    )


def delete_session(session_id: str) -> None:
    redis_client.delete(_session_key(session_id))
    logger.info(f"deleted session {session_id}")
