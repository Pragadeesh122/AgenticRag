import json
import logging
from memory.redis_client import redis_client
from clients import openai_client
from prompts.memory import MEMORY, MEMORY_COMPARISON

logger = logging.getLogger("memory")

MEMORY_KEY = "memory:user"


MEMORY_CATEGORIES = [
    "work_context",
    "personal_context",
    "top_of_mind",
    "preferences",
]


def get_user_memory() -> str:
    """Load all stored user memory from Redis hash, organized by category."""
    facts = redis_client.hgetall(MEMORY_KEY)
    if not facts:
        return ""
    sections = []
    for category in MEMORY_CATEGORIES:
        if category in facts:
            label = category.replace("_", " ").title()
            sections.append(f"{label}\n{facts[category]}")
    return "\n\n".join(sections)


def extract_and_save_memories(messages: list):
    """Extract NEW facts from conversation and merge with existing memory in Redis."""
    existing = redis_client.hgetall(MEMORY_KEY)

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
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": MEMORY,
            },
            {"role": "user", "content": f"Conversation:\n{conversation}"},
        ],
    )

    try:
        new_facts = json.loads(response.choices[0].message.content)
        new_facts = {k: v for k, v in new_facts.items() if k in MEMORY_CATEGORIES and v}

        if not new_facts:
            logger.info("no new memories to save")
            return

        # Phase 2: For categories that already have memory, merge old + new via LLM
        for category, new_value in new_facts.items():
            old_value = existing.get(category)
            if old_value:
                merge_response = openai_client.chat.completions.create(
                    model="gpt-4o",
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
                merged = merge_response.choices[0].message.content.strip()
                redis_client.hset(MEMORY_KEY, category, merged)
                logger.info(f"merged memory for '{category}'")
            else:
                redis_client.hset(MEMORY_KEY, category, str(new_value))
                logger.info(f"created new memory for '{category}'")

        logger.info(f"saved {len(new_facts)} memory categories to Redis")
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"failed to extract memories: {e}")
