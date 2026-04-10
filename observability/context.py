"""Async-safe context propagation for observability labels."""

from __future__ import annotations

from contextvars import ContextVar
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
) -> Dict[str, str]:
    """Set all request context fields and return previous values.

    We intentionally do not return ContextVar tokens here. Streaming responses can
    cross execution contexts when advanced by Starlette/AnyIO, and resetting with
    a token created in a different context raises ValueError.
    """
    previous = {
        "chat_type": _CHAT_TYPE.get(),
        "user_hash": _USER_HASH.get(),
        "session_hash": _SESSION_HASH.get(),
        "project_hash": _PROJECT_HASH.get(),
        "agent_name": _AGENT_NAME.get(),
    }
    _CHAT_TYPE.set(chat_type or "unknown")
    _USER_HASH.set(stable_hash(user_id))
    _SESSION_HASH.set(stable_hash(session_id))
    _PROJECT_HASH.set(stable_hash(project_id))
    _AGENT_NAME.set((agent_name or "unknown").strip() or "unknown")
    return previous


def pop_context(previous: Dict[str, str]) -> None:
    """Restore request context from values returned by ``push_context``."""
    _CHAT_TYPE.set(previous.get("chat_type", "unknown") or "unknown")
    _USER_HASH.set(previous.get("user_hash", "unknown") or "unknown")
    _SESSION_HASH.set(previous.get("session_hash", "unknown") or "unknown")
    _PROJECT_HASH.set(previous.get("project_hash", "unknown") or "unknown")
    _AGENT_NAME.set(previous.get("agent_name", "unknown") or "unknown")


def set_agent_name(agent_name: str | None) -> str:
    """Update current agent context during routing/execution."""
    previous = _AGENT_NAME.get()
    _AGENT_NAME.set((agent_name or "unknown").strip() or "unknown")
    return previous


def reset_agent_name(previous: str) -> None:
    _AGENT_NAME.set(previous or "unknown")


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


def clear_context() -> None:
    """Force all observability context fields back to defaults."""
    _CHAT_TYPE.set("unknown")
    _USER_HASH.set("unknown")
    _SESSION_HASH.set("unknown")
    _PROJECT_HASH.set("unknown")
    _AGENT_NAME.set("unknown")
