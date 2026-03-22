"""In-memory session store for conversation histories."""

import uuid
import logging
from memory import get_user_memory
from prompts import ORCHESTRATOR

logger = logging.getLogger("session")

_sessions: dict[str, list[dict]] = {}


def _build_system_prompt() -> str:
    system_prompt = ORCHESTRATOR
    user_memory = get_user_memory()
    if user_memory:
        system_prompt += f"\n\nKnown facts about the user:\n{user_memory}"
        logger.info("loaded user memory from Redis")
    return system_prompt


def create_session() -> str:
    session_id = uuid.uuid4().hex[:12]
    _sessions[session_id] = [
        {"role": "system", "content": _build_system_prompt()}
    ]
    logger.info(f"created session {session_id}")
    return session_id


def get_messages(session_id: str) -> list[dict]:
    if session_id not in _sessions:
        raise KeyError(f"session '{session_id}' not found")
    return _sessions[session_id]


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
    logger.info(f"deleted session {session_id}")
