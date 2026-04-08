import logging
import re
import threading

from sqlalchemy import select

from database.core import sync_session_maker
from database.models import ChatSession
from memory import extract_and_persist_memories

logger = logging.getLogger("services.chat_postprocess")

MAX_TITLE_WORDS = 12
MAX_TITLE_CHARS = 80


def _clean_title(title: str, fallback: str) -> str:
    cleaned = re.sub(r"\s+", " ", title.strip().strip("\"'`")).strip(" .:-")
    if not cleaned:
        return fallback
    words = cleaned.split()
    cleaned = " ".join(words[:MAX_TITLE_WORDS])[:MAX_TITLE_CHARS].strip()
    return cleaned or fallback


def _fallback_title(user_message: str) -> str:
    cleaned = re.sub(r"\s+", " ", user_message).strip()
    words = cleaned.split()
    return " ".join(words[:MAX_TITLE_WORDS])[:MAX_TITLE_CHARS] or "New chat"


def generate_title(user_message: str) -> str:
    fallback = _fallback_title(user_message)
    return _clean_title(user_message, fallback)


def _persist_title(backend_session_id: str, title: str) -> None:
    with sync_session_maker() as session:
        stmt = select(ChatSession).where(
            ChatSession.backend_session_id == backend_session_id
        )
        chat_session = session.execute(stmt).scalar_one_or_none()
        if not chat_session or chat_session.title != "New chat":
            return

        chat_session.title = title
        session.commit()


def schedule_session_title(
    backend_session_id: str,
    user_message: str,
) -> None:
    def _worker() -> None:
        title = generate_title(user_message)
        try:
            _persist_title(backend_session_id, title)
            logger.info(f"stored session title '{title}'")
        except Exception as e:
            logger.error(f"failed to persist session title: {e}")

    threading.Thread(target=_worker, daemon=True).start()


def schedule_memory_persistence(messages: list[dict], user_id: str) -> None:
    def _worker() -> None:
        extract_and_persist_memories(messages, user_id)

    threading.Thread(target=_worker, daemon=True).start()
