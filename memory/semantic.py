import json
import logging
import uuid
from memory.redis_client import redis_client
from clients import llm_client
from prompts.memory import MEMORY, MEMORY_COMPARISON
from database.core import sync_session_maker
from database.models import UserMemory
from sqlalchemy import select
from llm.response_utils import extract_first_text

logger = logging.getLogger("memory")

MEMORY_KEY_PREFIX = "memory:"

MEMORY_CATEGORIES = [
    "work_context",
    "personal_context",
    "top_of_mind",
    "preferences",
]


def _memory_key(user_id: str) -> str:
    return f"{MEMORY_KEY_PREFIX}{user_id}"


def get_user_memory(user_id: str) -> str:
    """Load all stored user memory from Redis hash, organized by category."""
    facts = redis_client.hgetall(_memory_key(user_id))
    if not facts:
        return ""
    sections = []
    for category in MEMORY_CATEGORIES:
        if category in facts:
            label = category.replace("_", " ").title()
            sections.append(f"{label}\n{facts[category]}")
    return "\n\n".join(sections)


def extract_and_save_memories(messages: list, user_id: str):
    """Extract NEW facts from conversation and merge with existing memory in Redis."""
    key = _memory_key(user_id)
    existing = redis_client.hgetall(key)

    conversation = json.dumps(
        [
            m
            for m in messages
            if isinstance(m, dict)
            and m.get("role") in ("user", "assistant")
            and m.get("content")
        ],
        indent=1,
    )

    # Phase 1: Extract only NEW facts from this conversation
    response = llm_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": MEMORY,
            },
            {"role": "user", "content": f"Conversation:\n{conversation}"},
        ],
    )

    try:
        new_facts = json.loads(extract_first_text(response, "{}"))
        new_facts = {k: v for k, v in new_facts.items() if k in MEMORY_CATEGORIES and v}

        if not new_facts:
            logger.info("no new memories to save")
            return

        # Phase 2: For categories that already have memory, merge old + new via LLM
        for category, new_value in new_facts.items():
            old_value = existing.get(category)
            if old_value:
                merge_response = llm_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": MEMORY_COMPARISON,
                        },
                        {
                            "role": "user",
                            "content": f"Existing memory:\n{old_value}\n\nNew facts:\n{new_value}",
                        },
                    ],
                )
                merged = extract_first_text(merge_response, "").strip()
                redis_client.hset(key, category, merged)
                logger.info(f"merged memory for '{category}'")
            else:
                redis_client.hset(key, category, str(new_value))
                logger.info(f"created new memory for '{category}'")

        logger.info(f"saved {len(new_facts)} memory categories to Redis")
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"failed to extract memories: {e}")


def _sync_redis_memory_to_db(user_id: str) -> None:
    key = _memory_key(user_id)
    existing = redis_client.hgetall(key)

    with sync_session_maker() as session:
        stmt = select(UserMemory).where(UserMemory.user_id == uuid.UUID(user_id))
        memory = session.execute(stmt).scalar_one_or_none()
        if not memory:
            memory = UserMemory(user_id=uuid.UUID(user_id))
            session.add(memory)

        for category in MEMORY_CATEGORIES:
            setattr(memory, category, existing.get(category, ""))

        session.commit()


def sync_redis_memory_to_db(user_id: str) -> None:
    try:
        _sync_redis_memory_to_db(user_id)
        logger.info("synced memory from Redis to Postgres")
    except Exception as e:
        logger.error(f"failed to sync memory to Postgres: {e}")


def extract_and_persist_memories(messages: list, user_id: str) -> None:
    extract_and_save_memories(messages, user_id)
    sync_redis_memory_to_db(user_id)
