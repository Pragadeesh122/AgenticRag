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


def session_exists(session_id: str) -> bool:
    """Check if a session exists in Redis."""
    return redis_client.exists(_session_key(session_id)) > 0


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


def restore_session(session_id: str, messages: list[dict]) -> None:
    """Recreate a Redis session from persisted messages (e.g. from DB)."""
    # Build system prompt + filter to user/assistant messages only
    system_prompt = _build_system_prompt()
    restored = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            restored.append({"role": msg["role"], "content": msg["content"]})
    redis_client.set(
        _session_key(session_id),
        json.dumps(restored),
        ex=SESSION_TTL,
    )
    logger.info(f"restored session {session_id} with {len(restored)} messages")


def get_session_agent(session_id: str) -> str | None:
    """Get the active agent name for a session."""
    return redis_client.get(f"{_session_key(session_id)}:agent")


def set_session_agent(session_id: str, agent_name: str) -> None:
    """Store the active agent name for a session."""
    redis_client.set(f"{_session_key(session_id)}:agent", agent_name, ex=SESSION_TTL)


def delete_session(session_id: str) -> None:
    redis_client.delete(_session_key(session_id))
    redis_client.delete(f"{_session_key(session_id)}:agent")
    logger.info(f"deleted session {session_id}")
