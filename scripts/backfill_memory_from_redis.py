"""One-off migration: split legacy Redis category blobs into atomic facts.

Reads the old ``memory:{user_id}`` Redis hash (four category keys) and feeds each
user's combined text through the new extraction prompt to produce atomic facts.
The resulting facts are embedded and inserted into ``user_memory_fact`` with
``source_session_id = "backfill-from-redis"``.

Idempotent: re-running it for a user who already has a backfill row is a no-op.

Usage::

    uv run python -m scripts.backfill_memory_from_redis

The legacy Redis hashes are left in place. After the new pipeline has been
running stably for a few weeks, flush them manually:

    redis-cli --scan --pattern 'memory:*' | xargs -n 100 redis-cli del
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text as sa_text

from database.core import sync_session_maker
from database.models import UserMemory, UserMemoryFact
from memory.redis_client import redis_client
from memory.semantic import _embed, _extract_candidate_facts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("backfill.memory")

LEGACY_CATEGORIES = [
    "work_context",
    "personal_context",
    "top_of_mind",
    "preferences",
]
BACKFILL_SESSION_ID = "backfill-from-redis"


def _already_backfilled(db, user_id: uuid.UUID) -> bool:
    row = db.execute(
        sa_text(
            "SELECT 1 FROM user_memory_fact "
            "WHERE user_id = :uid AND source_session_id = :sid LIMIT 1"
        ),
        {"uid": str(user_id), "sid": BACKFILL_SESSION_ID},
    ).first()
    return row is not None


def _read_redis_hash(user_id: str) -> dict:
    return redis_client.hgetall(f"memory:{user_id}") or {}


def _read_postgres_legacy(db, user_id: uuid.UUID) -> dict:
    row = db.execute(
        select(UserMemory).where(UserMemory.user_id == user_id)
    ).scalar_one_or_none()
    if not row:
        return {}
    return {
        "work_context": row.work_context or "",
        "personal_context": row.personal_context or "",
        "top_of_mind": row.top_of_mind or "",
        "preferences": row.preferences or "",
    }


def _blob_to_pseudo_conversation(blob: dict) -> list[dict]:
    """Turn category→text into a fake user-message transcript.

    The extraction prompt reads user messages; wrap each non-empty category
    as a single user utterance so the extractor will mine it for atomic facts.
    """
    messages: list[dict] = []
    for cat in LEGACY_CATEGORIES:
        value = (blob.get(cat) or "").strip()
        if value:
            messages.append(
                {"role": "user", "content": f"({cat.replace('_', ' ')}) {value}"}
            )
    return messages


def backfill_user(user_id: str) -> int:
    uid = uuid.UUID(user_id)
    with sync_session_maker() as db:
        if _already_backfilled(db, uid):
            logger.info("user %s already backfilled, skipping", user_id)
            return 0

        # Prefer Redis (freshest) and fall back to the legacy Postgres mirror.
        blob = _read_redis_hash(user_id) or _read_postgres_legacy(db, uid)
        if not blob or not any((blob.get(c) or "").strip() for c in LEGACY_CATEGORIES):
            logger.info("user %s has no legacy memory, skipping", user_id)
            return 0

        pseudo_messages = _blob_to_pseudo_conversation(blob)
        observation_date = (
            datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
        )
        facts = _extract_candidate_facts(
            pseudo_messages,
            rolling_summary=None,
            observation_date=observation_date,
        )
        if not facts:
            logger.info("user %s produced no extractable facts", user_id)
            return 0

        for fact in facts:
            embedding = _embed(fact)
            db.add(
                UserMemoryFact(
                    user_id=uid,
                    text=fact,
                    embedding=embedding,
                    observed_at=observation_date,
                    source_session_id=BACKFILL_SESSION_ID,
                )
            )
        db.commit()
        logger.info("user %s backfilled %d facts", user_id, len(facts))
        return len(facts)


def _all_user_ids() -> list[str]:
    """Union of users that have a legacy memory row or a Redis hash."""
    ids: set[str] = set()
    with sync_session_maker() as db:
        rows = db.execute(select(UserMemory.user_id)).fetchall()
        for (uid,) in rows:
            ids.add(str(uid))
    for key in redis_client.scan_iter("memory:*"):
        parts = key.split(":", 1)
        if len(parts) == 2:
            ids.add(parts[1])
    return sorted(ids)


def main() -> None:
    user_ids = _all_user_ids()
    logger.info("backfilling %d users", len(user_ids))
    total_facts = 0
    for uid in user_ids:
        try:
            total_facts += backfill_user(uid)
        except Exception as exc:
            logger.error("backfill failed for %s: %s", uid, exc)
    logger.info(
        "backfill complete: %d facts written across %d users",
        total_facts,
        len(user_ids),
    )


if __name__ == "__main__":
    main()
