"""Tests for api/rate_limit.py — sliding window, JWT subject extraction, fallback."""

import re
import time
import uuid
from collections import deque
from unittest.mock import MagicMock, patch

import jwt
import pytest

from api import rate_limit as rl_module
from api.rate_limit import (
    RATE_LIMIT_RULES,
    _RATE_LIMIT_FALLBACK,
    _consume_sliding_window_fallback,
    _extract_user_id_from_token,
    _client_ip,
    consume_rate_limit,
    get_rate_limit_subject,
    match_rate_limit_rule,
    COOKIE_NAME,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
)
from api.auth.config import SECRET


def _make_request(
    path="/chat/stream",
    method="POST",
    cookies=None,
    headers=None,
    client_host="127.0.0.1",
):
    """Build a minimal fake Request object."""
    req = MagicMock()
    req.url.path = path
    req.method = method
    req.cookies = cookies or {}
    req.headers = headers or {}
    req.client = MagicMock()
    req.client.host = client_host
    return req


def _make_jwt(user_id: str, secret: str = SECRET) -> str:
    """Create a valid JWT token matching the fastapi-users format."""
    return jwt.encode(
        {"sub": user_id, "aud": JWT_AUDIENCE},
        secret,
        algorithm=JWT_ALGORITHM,
    )


# ---------------------------------------------------------------------------
# JWT subject extraction
# ---------------------------------------------------------------------------


class TestExtractUserIdFromToken:
    def test_valid_cookie_extracts_user_id(self):
        user_id = str(uuid.uuid4())
        token = _make_jwt(user_id)
        req = _make_request(cookies={COOKIE_NAME: token})
        assert _extract_user_id_from_token(req) == f"user:{user_id}"

    def test_valid_bearer_header_extracts_user_id(self):
        user_id = str(uuid.uuid4())
        token = _make_jwt(user_id)
        req = _make_request(headers={"Authorization": f"Bearer {token}"})
        assert _extract_user_id_from_token(req) == f"user:{user_id}"

    def test_cookie_takes_precedence_over_header(self):
        user_cookie = str(uuid.uuid4())
        user_header = str(uuid.uuid4())
        req = _make_request(
            cookies={COOKIE_NAME: _make_jwt(user_cookie)},
            headers={"Authorization": f"Bearer {_make_jwt(user_header)}"},
        )
        assert _extract_user_id_from_token(req) == f"user:{user_cookie}"

    def test_no_token_returns_none(self):
        req = _make_request()
        assert _extract_user_id_from_token(req) is None

    def test_expired_token_returns_none(self):
        token = jwt.encode(
            {"sub": "user-1", "aud": JWT_AUDIENCE, "exp": 0},
            SECRET,
            algorithm=JWT_ALGORITHM,
        )
        req = _make_request(cookies={COOKIE_NAME: token})
        assert _extract_user_id_from_token(req) is None

    def test_wrong_secret_returns_none(self):
        token = _make_jwt("user-1", secret="wrong-secret")
        req = _make_request(cookies={COOKIE_NAME: token})
        assert _extract_user_id_from_token(req) is None

    def test_malformed_token_returns_none(self):
        req = _make_request(cookies={COOKIE_NAME: "not.a.jwt"})
        assert _extract_user_id_from_token(req) is None


class TestGetRateLimitSubject:
    def test_authenticated_user_keyed_by_user_id(self):
        user_id = str(uuid.uuid4())
        token = _make_jwt(user_id)
        req = _make_request(cookies={COOKIE_NAME: token})
        assert get_rate_limit_subject(req) == f"user:{user_id}"

    def test_unauthenticated_keyed_by_ip(self):
        req = _make_request(client_host="10.0.0.1")
        assert get_rate_limit_subject(req) == "ip:10.0.0.1"

    def test_forwarded_for_used_for_ip(self):
        req = _make_request(headers={"x-forwarded-for": "203.0.113.5, 10.0.0.1"})
        assert get_rate_limit_subject(req) == "ip:203.0.113.5"

    def test_two_users_same_ip_get_different_subjects(self):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        req_a = _make_request(
            cookies={COOKIE_NAME: _make_jwt(user_a)}, client_host="10.0.0.1"
        )
        req_b = _make_request(
            cookies={COOKIE_NAME: _make_jwt(user_b)}, client_host="10.0.0.1"
        )
        assert get_rate_limit_subject(req_a) != get_rate_limit_subject(req_b)


# ---------------------------------------------------------------------------
# Rule matching
# ---------------------------------------------------------------------------


class TestMatchRule:
    def test_matches_chat_stream(self):
        req = _make_request(path="/chat/stream", method="POST")
        rule = match_rate_limit_rule(req)
        assert rule is not None
        assert rule["name"] == "chat_stream"

    def test_matches_project_chat(self):
        req = _make_request(path="/projects/abc-123/chat", method="POST")
        rule = match_rate_limit_rule(req)
        assert rule is not None
        assert rule["name"] == "project_chat"

    def test_no_match_returns_none(self):
        req = _make_request(path="/metrics", method="GET")
        assert match_rate_limit_rule(req) is None

    def test_wrong_method_no_match(self):
        req = _make_request(path="/chat/stream", method="GET")
        assert match_rate_limit_rule(req) is None


# ---------------------------------------------------------------------------
# In-memory fallback (deque-based sliding window)
# ---------------------------------------------------------------------------


class TestFallbackSlidingWindow:
    def setup_method(self):
        _RATE_LIMIT_FALLBACK.clear()

    def test_allows_up_to_limit(self):
        for i in range(5):
            allowed, remaining, _ = _consume_sliding_window_fallback("k", 5, 60)
            assert allowed is True
            assert remaining == 5 - (i + 1)

    def test_blocks_at_limit_plus_one(self):
        for _ in range(5):
            _consume_sliding_window_fallback("k", 5, 60)
        allowed, remaining, retry_after = _consume_sliding_window_fallback("k", 5, 60)
        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    def test_recovers_after_window(self):
        for _ in range(5):
            _consume_sliding_window_fallback("k", 5, 0.01)
        time.sleep(0.02)
        allowed, _, _ = _consume_sliding_window_fallback("k", 5, 0.01)
        assert allowed is True

    def test_independent_keys(self):
        for _ in range(5):
            _consume_sliding_window_fallback("key-a", 5, 60)
        # key-b should still be allowed
        allowed, _, _ = _consume_sliding_window_fallback("key-b", 5, 60)
        assert allowed is True


# ---------------------------------------------------------------------------
# consume_rate_limit with mocked Redis
# ---------------------------------------------------------------------------


class TestConsumeRateLimit:
    def setup_method(self):
        _RATE_LIMIT_FALLBACK.clear()

    def _rule(self, limit=5, window=60):
        return {"name": "test_rule", "limit": limit, "window": window}

    @patch.object(rl_module, "_get_lua_script")
    def test_sliding_window_allows_up_to_limit(self, mock_get_script):
        call_count = {"n": 0}

        def fake_script(keys, args):
            call_count["n"] += 1
            n = call_count["n"]
            if n <= 5:
                return [1, n, 0]  # allowed, count, retry_after_ms
            return [0, 5, 30000]

        mock_get_script.return_value = fake_script
        rule = self._rule(limit=5)

        for i in range(5):
            allowed, remaining, _ = consume_rate_limit(rule, "user:1")
            assert allowed is True

    @patch.object(rl_module, "_get_lua_script")
    def test_sliding_window_blocks_at_limit_plus_one(self, mock_get_script):
        call_count = {"n": 0}

        def fake_script(keys, args):
            call_count["n"] += 1
            if call_count["n"] <= 5:
                return [1, call_count["n"], 0]
            return [0, 5, 30000]

        mock_get_script.return_value = fake_script
        rule = self._rule(limit=5)

        for _ in range(5):
            consume_rate_limit(rule, "user:1")
        allowed, remaining, retry_after = consume_rate_limit(rule, "user:1")
        assert allowed is False
        assert remaining == 0
        assert retry_after >= 1

    @patch.object(rl_module, "_get_lua_script")
    def test_fallback_on_redis_failure(self, mock_get_script):
        mock_get_script.side_effect = Exception("connection refused")
        rule = self._rule(limit=3)

        for i in range(3):
            allowed, _, _ = consume_rate_limit(rule, "user:1")
            assert allowed is True

        allowed, _, retry_after = consume_rate_limit(rule, "user:1")
        assert allowed is False
        assert retry_after > 0

    @patch.object(rl_module, "_get_lua_script")
    def test_user_keying_separates_budgets(self, mock_get_script):
        counts = {}

        def fake_script(keys, args):
            key = keys[0]
            counts[key] = counts.get(key, 0) + 1
            n = counts[key]
            limit = int(args[2])
            if n <= limit:
                return [1, n, 0]
            return [0, limit, 30000]

        mock_get_script.return_value = fake_script
        rule = self._rule(limit=2)

        # User A uses 2 requests
        for _ in range(2):
            allowed, _, _ = consume_rate_limit(rule, "user:a")
            assert allowed is True

        # User A is now blocked
        allowed, _, _ = consume_rate_limit(rule, "user:a")
        assert allowed is False

        # User B still has budget
        allowed, _, _ = consume_rate_limit(rule, "user:b")
        assert allowed is True


# ---------------------------------------------------------------------------
# Sliding window vs fixed window behavior
# ---------------------------------------------------------------------------


class TestSlidingWindowSmoothing:
    """Verify that the sliding window prevents the 2x burst that fixed windows allow."""

    def setup_method(self):
        _RATE_LIMIT_FALLBACK.clear()

    def test_sliding_window_smooths_bursts(self):
        """20 requests at t=0, then 20 more at t=window-5s.

        Fixed window would allow all 40 (two separate windows).
        Sliding window should block the second burst because the first
        burst's timestamps are still inside the trailing window.
        """
        limit = 20
        window = 60.0
        key = "burst-test"

        # First burst: fill to the limit
        now = time.time()
        dq = deque()
        for _ in range(limit):
            dq.append(now)
        _RATE_LIMIT_FALLBACK[key] = dq

        # Second burst at t=window-5 — first burst is still in window
        future = now + window - 5
        allowed_in_second_burst = 0
        blocked_in_second_burst = 0

        for _ in range(20):
            # Manually set the time context: don't popleft old entries
            # since they're still within `window` of `future`
            cutoff = future - window
            while dq and dq[0] <= cutoff:
                dq.popleft()

            if len(dq) >= limit:
                blocked_in_second_burst += 1
            else:
                dq.append(future)
                allowed_in_second_burst += 1

        # All 20 of the first burst are within window, so second burst is blocked
        assert blocked_in_second_burst == 20
        assert allowed_in_second_burst == 0


# ---------------------------------------------------------------------------
# Integration: middleware with async_client
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_middleware_429_includes_headers(async_client, monkeypatch):
    from api import server as server_module

    monkeypatch.setattr(server_module, "session_owned_by_user", lambda *_: True)
    monkeypatch.setattr(
        server_module,
        "chat_stream",
        lambda *_: iter(["event: done\ndata: {}\n\n"]),
    )

    # Use unique rule name to avoid Redis state from other tests
    test_id = uuid.uuid4().hex[:8]
    monkeypatch.setattr(
        rl_module,
        "RATE_LIMIT_RULES",
        (
            {
                "name": f"test_{test_id}",
                "method": "POST",
                "pattern": re.compile(r"^/chat/stream$"),
                "limit": 1,
                "window": 60,
            },
        ),
    )
    _RATE_LIMIT_FALLBACK.clear()

    first = await async_client.post(
        "/chat/stream", json={"sessionId": "s", "message": "m"}
    )
    second = await async_client.post(
        "/chat/stream", json={"sessionId": "s", "message": "m"}
    )

    assert first.status_code == 200
    assert "x-ratelimit-limit" in first.headers
    assert "x-ratelimit-remaining" in first.headers

    assert second.status_code == 429
    assert "retry-after" in second.headers
    assert second.json()["detail"] == "Rate limit exceeded"


@pytest.mark.asyncio
async def test_unmatched_route_passes_through(async_client):
    """Routes without a matching rule are not rate-limited."""
    response = await async_client.get("/metrics")
    assert response.status_code == 200
    assert "x-ratelimit-limit" not in response.headers
