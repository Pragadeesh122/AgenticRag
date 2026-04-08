import hashlib
import logging
import struct
from redis.commands.search.field import TagField, TextField, VectorField
from redis.commands.search.query import Query
from redis.commands.search.index_definition import IndexDefinition, IndexType
import os
import redis
from clients import llm_client
from llm.response_utils import extract_first_embedding

cache_redis = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=False,
)

logger = logging.getLogger("cache")

CACHE_PREFIX = "toolcache"
SMALL_EMBEDDING_MODEL = os.getenv("SMALL_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_PROFILE = SMALL_EMBEDDING_MODEL.lower().replace("/", "_").replace(":", "_")
INDEX_NAME = f"{CACHE_PREFIX}:{EMBEDDING_PROFILE}:idx"
DEFAULT_TTL = 60 * 60 * 24  # 24h
SIMILARITY_THRESHOLD = 0.87
DEFAULT_EMBEDDING_DIM = int(os.getenv("SMALL_EMBEDDING_DIMENSION", 1536))


def _embed(text: str) -> tuple[bytes, int]:
    """Get embedding and return raw bytes + vector dimension."""
    response = llm_client.embeddings.create(
        input=text, model=SMALL_EMBEDDING_MODEL
    )
    floats = extract_first_embedding(response)
    return struct.pack(f"{len(floats)}f", *floats), len(floats)


def _ensure_index(embedding_dim: int):
    """Create the RediSearch vector index if it doesn't exist."""
    try:
        cache_redis.ft(INDEX_NAME).info()
    except Exception:
        schema = (
            TagField("tool_name"),
            TextField("query"),
            TextField("result"),
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
        cache_redis.ft(INDEX_NAME).create_index(
            schema,
            definition=IndexDefinition(
                prefix=[f"{CACHE_PREFIX}:"], index_type=IndexType.HASH
            ),
        )
        logger.info("created RediSearch vector index")


def get_cached_result(tool_name: str, query: str) -> str | None:
    """Check if a similar query has been cached using Redis vector search."""
    query_embedding, embedding_dim = _embed(query)
    _ensure_index(embedding_dim)

    q = (
        Query(f"(@tool_name:{{{tool_name}}})=>[KNN 1 @embedding $vec AS score]")
        .sort_by("score")
        .return_fields("result", "score")
        .dialect(2)
    )

    try:
        results = cache_redis.ft(INDEX_NAME).search(
            q, query_params={"vec": query_embedding}
        )
    except Exception as e:
        logger.warning(f"redis search failed: {e}")
        return None

    logger.info(f"cache search returned {results.total} results for tool={tool_name}")
    if results.total == 0:
        return None

    doc = results.docs[0]
    # Redis COSINE distance = 1 - cosine_similarity, so similarity = 1 - distance
    similarity = 1 - float(doc.score)
    logger.info(f"Similarity Score {similarity}")
    if similarity >= SIMILARITY_THRESHOLD:
        logger.info(f"cache hit for {tool_name}: similarity={similarity:.3f}")
        return doc.result

    return None


def cache_result(tool_name: str, query: str, result: str, ttl: int = DEFAULT_TTL):
    """Cache a tool result with its embedding for Redis vector search."""
    query_embedding, embedding_dim = _embed(query)
    _ensure_index(embedding_dim)
    cache_key = f"{CACHE_PREFIX}:{tool_name}:{hashlib.md5(query.encode()).hexdigest()}"

    cache_redis.hset(
        cache_key,
        mapping={
            "tool_name": tool_name,
            "query": query,
            "result": result,
            "embedding": query_embedding,
        },
    )
    cache_redis.expire(cache_key, ttl)
    logger.info(f"cached result for {tool_name}: '{query[:50]}...' (ttl={ttl}s)")


def clear_cache(tool_name: str = None):
    """Clear cache entries. Pass tool_name to clear only that tool, or None for all."""
    pattern = f"{CACHE_PREFIX}:{tool_name}:*" if tool_name else f"{CACHE_PREFIX}:*"
    keys = list(cache_redis.scan_iter(pattern))
    if keys:
        cache_redis.delete(*keys)
        logger.info(f"cleared {len(keys)} cache entries")
