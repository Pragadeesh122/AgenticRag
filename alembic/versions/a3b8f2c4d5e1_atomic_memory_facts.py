"""Atomic memory facts with pgvector

Replaces the coarse 4-column user_memory table with user_memory_fact:
one row per atomic fact, vector-indexed for semantic lookup, with
supersession timestamps for cross-session consolidation.

The old user_memory table is kept intact for the backfill read path
and will be dropped in a follow-up migration.

Revision ID: a3b8f2c4d5e1
Revises: 7c4f9e2f8b2b
Create Date: 2026-04-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a3b8f2c4d5e1"
down_revision: Union[str, Sequence[str], None] = "7c4f9e2f8b2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector extension — idempotent
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # user_memory_fact table with vector(1536) for text-embedding-3-small
    op.execute(
        """
        CREATE TABLE user_memory_fact (
            id                 TEXT PRIMARY KEY,
            user_id            UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            text               TEXT NOT NULL,
            embedding          vector(1536) NOT NULL,
            observed_at        TIMESTAMP NOT NULL DEFAULT NOW(),
            superseded_at      TIMESTAMP,
            superseded_by      TEXT,
            source_session_id  TEXT
        )
        """
    )

    # Composite index for the common retrieval query (active facts per user)
    op.execute(
        """
        CREATE INDEX ix_user_memory_fact_user_active
        ON user_memory_fact (user_id, superseded_at)
        """
    )

    # HNSW cosine index for vector similarity search.
    # HNSW is chosen over IVFFlat because it has no minimum row-count requirement
    # and delivers better recall on sparse per-user data.
    op.execute(
        """
        CREATE INDEX ix_user_memory_fact_embedding_hnsw
        ON user_memory_fact
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_memory_fact_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_user_memory_fact_user_active")
    op.execute("DROP TABLE IF EXISTS user_memory_fact")
    # Do not drop the vector extension — other tables may use it.
