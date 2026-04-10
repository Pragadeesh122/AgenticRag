"""Async-safe context propagation for observability labels."""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Dict

from observability.hash import stable_hash

_CHAT_TYPE: ContextVar[str] = ContextVar("obs_chat_type", default="unknown")
_USER_HASH: ContextVar[str] = ContextVar("obs_user_hash", default="unknown")
_SESSION_HASH: ContextVar[str] = ContextVar("obs_session_hash", default="unknown")
_PROJECT_HASH: ContextVar[str] = ContextVar("obs_project_hash", default="unknown")
_AGENT_NAME: ContextVar[str] = ContextVar("obs_agent_name", default="unknown")


def push_context(
    *,
    chat_type: str = "unknown",
    user_id: str | None = None,
    session_id: str | None = None,
    project_id: str | None = None,
    agent_name: str | None = None,
) -> Dict[str, Token]:
    """Set all request context fields and return reset tokens."""
    return {
        "chat_type": _CHAT_TYPE.set(chat_type or "unknown"),
        "user_hash": _USER_HASH.set(stable_hash(user_id)),
        "session_hash": _SESSION_HASH.set(stable_hash(session_id)),
        "project_hash": _PROJECT_HASH.set(stable_hash(project_id)),
        "agent_name": _AGENT_NAME.set((agent_name or "unknown").strip() or "unknown"),
    }


def pop_context(tokens: Dict[str, Token]) -> None:
    """Reset request context using tokens returned by ``push_context``."""
    if "chat_type" in tokens:
        _CHAT_TYPE.reset(tokens["chat_type"])
    if "user_hash" in tokens:
        _USER_HASH.reset(tokens["user_hash"])
    if "session_hash" in tokens:
        _SESSION_HASH.reset(tokens["session_hash"])
    if "project_hash" in tokens:
        _PROJECT_HASH.reset(tokens["project_hash"])
    if "agent_name" in tokens:
        _AGENT_NAME.reset(tokens["agent_name"])


def set_agent_name(agent_name: str | None) -> Token:
    """Update current agent context during routing/execution."""
    return _AGENT_NAME.set((agent_name or "unknown").strip() or "unknown")


def reset_agent_name(token: Token) -> None:
    _AGENT_NAME.reset(token)


def get_chat_type() -> str:
    return _CHAT_TYPE.get()


def get_user_hash() -> str:
    return _USER_HASH.get()


def get_session_hash() -> str:
    return _SESSION_HASH.get()


def get_project_hash() -> str:
    return _PROJECT_HASH.get()


def get_agent_name() -> str:
    return _AGENT_NAME.get()

