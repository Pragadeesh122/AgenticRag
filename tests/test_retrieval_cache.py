"""Tests for pipeline/retrieval_cache.py — tag escaping + full cache behavior."""

import hashlib
import json
import struct
import unittest
from unittest.mock import MagicMock, patch, call
from types import SimpleNamespace

from pipeline.retrieval_cache import (
    _escape_tag_value,
    get_cached_retrieval,
    cache_retrieval,
    invalidate_project_cache,
    CACHE_PREFIX,
    DEFAULT_TTL,
    SIMILARITY_THRESHOLD,
)


class RetrievalCacheTagEscapingTests(unittest.TestCase):
    def test_uuid_dash_is_escaped_for_redisearch_tag_filter(self):
        project_id = "90ca197b-126a-43f4-a9a1-6b61a1a32716"
        escaped = _escape_tag_value(project_id)
        self.assertEqual(escaped, "90ca197b\\-126a\\-43f4\\-a9a1\\-6b61a1a32716")

    def test_alphanumeric_and_underscore_stay_unchanged(self):
        value = "project_123ABC"
        self.assertEqual(_escape_tag_value(value), value)


# --- Mocked cache behavior tests ---

FAKE_EMBEDDING = [0.1] * 16
FAKE_EMBEDDING_BYTES = struct.pack(f"{len(FAKE_EMBEDDING)}f", *FAKE_EMBEDDING)
FAKE_DIM = len(FAKE_EMBEDDING)

SAMPLE_RESULTS = [
    {"id": "v1", "score": 0.95, "text": "chunk text", "source": "doc.pdf"}
]


def _mock_embed(text):
    """Patch target for _embed — returns deterministic bytes + dim."""
    return FAKE_EMBEDDING_BYTES, FAKE_DIM


def _make_search_result(total, docs=None):
    """Build a fake RediSearch search result."""
    result = MagicMock()
    result.total = total
    result.docs = docs or []
    return result


class CacheMissTests(unittest.TestCase):
    @patch("pipeline.retrieval_cache._ensure_index")
    @patch("pipeline.retrieval_cache._embed", side_effect=_mock_embed)
    @patch("pipeline.retrieval_cache.redis_client")
    def test_cache_miss_returns_none(self, mock_redis, mock_embed, mock_ensure):
        mock_redis.ft.return_value.search.return_value = _make_search_result(total=0)
        result = get_cached_retrieval("proj-1", "what is the warranty?")
        self.assertIsNone(result)

    @patch("pipeline.retrieval_cache._ensure_index")
    @patch("pipeline.retrieval_cache._embed", side_effect=_mock_embed)
    @patch("pipeline.retrieval_cache.redis_client")
    def test_cache_hit_below_threshold_returns_none(self, mock_redis, mock_embed, mock_ensure):
        # similarity = 1 - score; score=0.15 means similarity=0.85 < 0.90
        doc = MagicMock()
        doc.score = 0.15
        doc.results = json.dumps(SAMPLE_RESULTS)
        mock_redis.ft.return_value.search.return_value = _make_search_result(total=1, docs=[doc])

        result = get_cached_retrieval("proj-1", "some query")
        self.assertIsNone(result)

    @patch("pipeline.retrieval_cache._ensure_index")
    @patch("pipeline.retrieval_cache._embed", side_effect=_mock_embed)
    @patch("pipeline.retrieval_cache.redis_client")
    def test_cache_hit_above_threshold_returns_results(self, mock_redis, mock_embed, mock_ensure):
        # similarity = 1 - 0.05 = 0.95 >= 0.90
        doc = MagicMock()
        doc.score = 0.05
        doc.results = json.dumps(SAMPLE_RESULTS)
        mock_redis.ft.return_value.search.return_value = _make_search_result(total=1, docs=[doc])

        result = get_cached_retrieval("proj-1", "matching query")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "v1")

    @patch("pipeline.retrieval_cache._ensure_index")
    @patch("pipeline.retrieval_cache._embed", side_effect=_mock_embed)
    @patch("pipeline.retrieval_cache.redis_client")
    def test_cache_search_exception_returns_none(self, mock_redis, mock_embed, mock_ensure):
        mock_redis.ft.return_value.search.side_effect = Exception("connection refused")
        result = get_cached_retrieval("proj-1", "query")
        self.assertIsNone(result)


class CacheWriteTests(unittest.TestCase):
    @patch("pipeline.retrieval_cache._ensure_index")
    @patch("pipeline.retrieval_cache._embed", side_effect=_mock_embed)
    @patch("pipeline.retrieval_cache.redis_client")
    def test_cache_key_format_includes_md5(self, mock_redis, mock_embed, mock_ensure):
        query = "test query"
        cache_retrieval("proj-1", query, SAMPLE_RESULTS)

        expected_md5 = hashlib.md5(query.encode()).hexdigest()
        expected_key = f"{CACHE_PREFIX}:proj-1:{expected_md5}"

        mock_redis.hset.assert_called_once()
        actual_key = mock_redis.hset.call_args[0][0]
        self.assertEqual(actual_key, expected_key)

    @patch("pipeline.retrieval_cache._ensure_index")
    @patch("pipeline.retrieval_cache._embed", side_effect=_mock_embed)
    @patch("pipeline.retrieval_cache.redis_client")
    def test_cache_retrieval_sets_ttl(self, mock_redis, mock_embed, mock_ensure):
        cache_retrieval("proj-1", "query", SAMPLE_RESULTS)

        mock_redis.expire.assert_called_once()
        args = mock_redis.expire.call_args[0]
        self.assertEqual(args[1], DEFAULT_TTL)

    @patch("pipeline.retrieval_cache._ensure_index")
    @patch("pipeline.retrieval_cache._embed", side_effect=_mock_embed)
    @patch("pipeline.retrieval_cache.redis_client")
    def test_cache_retrieval_custom_ttl(self, mock_redis, mock_embed, mock_ensure):
        cache_retrieval("proj-1", "query", SAMPLE_RESULTS, ttl=120)

        args = mock_redis.expire.call_args[0]
        self.assertEqual(args[1], 120)

    @patch("pipeline.retrieval_cache._ensure_index")
    @patch("pipeline.retrieval_cache._embed", side_effect=_mock_embed)
    @patch("pipeline.retrieval_cache.redis_client")
    def test_cache_stores_serialized_results(self, mock_redis, mock_embed, mock_ensure):
        cache_retrieval("proj-1", "query", SAMPLE_RESULTS)

        mapping = mock_redis.hset.call_args[1]["mapping"]
        self.assertEqual(mapping["project_id"], "proj-1")
        self.assertEqual(mapping["query"], "query")
        self.assertEqual(json.loads(mapping["results"]), SAMPLE_RESULTS)
        self.assertEqual(mapping["embedding"], FAKE_EMBEDDING_BYTES)


class CacheInvalidationTests(unittest.TestCase):
    @patch("pipeline.retrieval_cache.redis_client")
    def test_invalidate_project_cache_deletes_matching_keys(self, mock_redis):
        mock_redis.scan_iter.return_value = [
            f"{CACHE_PREFIX}:proj-1:abc",
            f"{CACHE_PREFIX}:proj-1:def",
            f"{CACHE_PREFIX}:proj-1:ghi",
        ]

        invalidate_project_cache("proj-1")

        mock_redis.scan_iter.assert_called_once_with(f"{CACHE_PREFIX}:proj-1:*")
        mock_redis.delete.assert_called_once_with(
            f"{CACHE_PREFIX}:proj-1:abc",
            f"{CACHE_PREFIX}:proj-1:def",
            f"{CACHE_PREFIX}:proj-1:ghi",
        )

    @patch("pipeline.retrieval_cache.redis_client")
    def test_invalidate_no_keys_skips_delete(self, mock_redis):
        mock_redis.scan_iter.return_value = []
        invalidate_project_cache("proj-1")
        mock_redis.delete.assert_not_called()
