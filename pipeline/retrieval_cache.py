"""Redis-backed semantic cache for project retrieval results."""

import hashlib
import json
import logging
import struct

from memory.redis_client import redis_client
from clients import openai_client

logger = logging.getLogger("pipeline.retrieval_cache")

CACHE_PREFIX = "retrieval_cache"
INDEX_NAME = f"{CACHE_PREFIX}:idx"
DEFAULT_TTL = 60 * 60  # 1 hour
SIMILARITY_THRESHOLD = 0.90
EMBEDDING_DIM = 1536  # text-embedding-3-small


def _embed(text: str) -> bytes:
    """Get embedding for cache lookup (small model, fast + cheap)."""
    response = openai_client.embeddings.create(
        input=text, model="text-embedding-3-small"
    )
    floats = response.data[0].embedding
    return struct.pack(f"{len(floats)}f", *floats)


def _ensure_index():
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
                {"TYPE": "FLOAT32", "DIM": EMBEDDING_DIM, "DISTANCE_METRIC": "COSINE"},
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
    _ensure_index()
    query_embedding = _embed(query)

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
    _ensure_index()
    query_embedding = _embed(query)
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
