import asyncio
import logging
import re
import threading

from sqlalchemy import select

from clients import openai_client
from database.core import async_session_maker
from database.models import ChatSession
from memory import extract_and_persist_memories

logger = logging.getLogger("services.chat_postprocess")


TITLE_SYSTEM_PROMPT = (
    "Generate a concise chat title from the conversation. "
    "Return only the title, no quotes or punctuation. "
    "Keep it under 5 words and specific."
)


def _clean_title(title: str, fallback: str) -> str:
    cleaned = re.sub(r"\s+", " ", title.strip().strip("\"'`")).strip(" .:-")
    if not cleaned:
        return fallback
    words = cleaned.split()
    return " ".join(words[:5])[:60]


def _fallback_title(user_message: str) -> str:
    cleaned = re.sub(r"\s+", " ", user_message).strip()
    words = cleaned.split()
    return " ".join(words[:5])[:60] or "New chat"


def generate_title(user_message: str, assistant_message: str) -> str:
    fallback = _fallback_title(user_message)
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": TITLE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"User message:\n{user_message}\n\n"
                        f"Assistant response:\n{assistant_message[:1200]}"
                    ),
                },
            ],
        )
        content = response.choices[0].message.content or ""
        return _clean_title(content, fallback)
    except Exception as e:
        logger.warning(f"title generation failed, using fallback: {e}")
        return fallback


async def _persist_title(backend_session_id: str, title: str) -> None:
    async with async_session_maker() as session:
        stmt = select(ChatSession).where(
            ChatSession.backend_session_id == backend_session_id
        )
        chat_session = (await session.execute(stmt)).scalar_one_or_none()
        if not chat_session or chat_session.title != "New chat":
            return

        chat_session.title = title
        await session.commit()


def schedule_session_title(
    backend_session_id: str,
    user_message: str,
    assistant_message: str,
) -> None:
    def _worker() -> None:
        title = generate_title(user_message, assistant_message)
        try:
            asyncio.run(_persist_title(backend_session_id, title))
            logger.info(f"stored auto-title '{title}'")
        except Exception as e:
            logger.error(f"failed to persist auto-title: {e}")

    threading.Thread(target=_worker, daemon=True).start()


def schedule_memory_persistence(messages: list[dict], user_id: str) -> None:
    def _worker() -> None:
        extract_and_persist_memories(messages, user_id)

    threading.Thread(target=_worker, daemon=True).start()
