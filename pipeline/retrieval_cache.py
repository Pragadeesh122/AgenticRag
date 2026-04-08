"""Redis-backed semantic cache for project retrieval results."""

import hashlib
import json
import logging
import os
import struct

from memory.redis_client import redis_client
from clients import llm_client
from llm.response_utils import extract_first_embedding

logger = logging.getLogger("pipeline.retrieval_cache")

CACHE_PREFIX = "retrieval_cache"
SMALL_EMBEDDING_MODEL = os.getenv("SMALL_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_PROFILE = SMALL_EMBEDDING_MODEL.lower().replace("/", "_").replace(":", "_")
INDEX_NAME = f"{CACHE_PREFIX}:{EMBEDDING_PROFILE}:idx"
DEFAULT_TTL = 60 * 60  # 1 hour
SIMILARITY_THRESHOLD = 0.90
DEFAULT_EMBEDDING_DIM = int(os.getenv("SMALL_EMBEDDING_DIMENSION", 1536))


def _embed(text: str) -> tuple[bytes, int]:
    """Get embedding for cache lookup (small model, fast + cheap)."""
    response = llm_client.embeddings.create(
        input=text, model=SMALL_EMBEDDING_MODEL
    )
    floats = extract_first_embedding(response)
    return struct.pack(f"{len(floats)}f", *floats), len(floats)


def _ensure_index(embedding_dim: int):
    """Create the RediSearch vector index if it doesn't exist."""
    try:
        redis_client.ft(INDEX_NAME).info()
    except Exception:
        from redis.commands.search.field import TagField, TextField, VectorField
        from redis.commands.search.index_definition import IndexDefinition, IndexType

        schema = (
            TagField("project_id"),
            TextField("query"),
            TextField("results"),
            VectorField(
                "embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": embedding_dim or DEFAULT_EMBEDDING_DIM,
                    "DISTANCE_METRIC": "COSINE",
                },
            ),
        )
        redis_client.ft(INDEX_NAME).create_index(
            schema,
            definition=IndexDefinition(
                prefix=[f"{CACHE_PREFIX}:"], index_type=IndexType.HASH
            ),
        )
        logger.info("created retrieval cache RediSearch index")


def get_cached_retrieval(project_id: str, query: str) -> list[dict] | None:
    """Check if a similar query for this project has cached retrieval results."""
    query_embedding, embedding_dim = _embed(query)
    _ensure_index(embedding_dim)

    from redis.commands.search.query import Query

    q = (
        Query(f"(@project_id:{{{project_id}}})=>[KNN 1 @embedding $vec AS score]")
        .sort_by("score")
        .return_fields("results", "score")
        .dialect(2)
    )

    try:
        search_results = redis_client.ft(INDEX_NAME).search(
            q, query_params={"vec": query_embedding}
        )
    except Exception as e:
        logger.warning(f"retrieval cache search failed: {e}")
        return None

    if search_results.total == 0:
        return None

    doc = search_results.docs[0]
    similarity = 1 - float(doc.score)

    if similarity >= SIMILARITY_THRESHOLD:
        logger.info(f"retrieval cache hit: project={project_id}, similarity={similarity:.3f}")
        return json.loads(doc.results)

    return None


def cache_retrieval(project_id: str, query: str, results: list[dict], ttl: int = DEFAULT_TTL):
    """Cache retrieval results for a project query."""
    query_embedding, embedding_dim = _embed(query)
    _ensure_index(embedding_dim)
    cache_key = f"{CACHE_PREFIX}:{project_id}:{hashlib.md5(query.encode()).hexdigest()}"

    redis_client.hset(
        cache_key,
        mapping={
            "project_id": project_id,
            "query": query,
            "results": json.dumps(results),
            "embedding": query_embedding,
        },
    )
    redis_client.expire(cache_key, ttl)
    logger.info(f"cached retrieval: project={project_id}, query='{query[:50]}...' ({len(results)} results, ttl={ttl}s)")


def invalidate_project_cache(project_id: str):
    """Clear all cached retrievals for a project (e.g. after new document upload)."""
    pattern = f"{CACHE_PREFIX}:{project_id}:*"
    keys = list(redis_client.scan_iter(pattern))
    if keys:
        redis_client.delete(*keys)
        logger.info(f"invalidated {len(keys)} retrieval cache entries for project '{project_id}'")
