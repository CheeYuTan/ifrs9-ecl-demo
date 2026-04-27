"""Dedicated tests for middleware/rate_limiter.py — token bucket rate limiting."""
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from middleware.rate_limiter import RateLimiterMiddleware


class TestRateLimiterInit:
    def test_default_max_requests(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=100, window_seconds=60)
        assert rl.max_requests == 100

    def test_default_window_seconds(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=100, window_seconds=60)
        assert rl.window_seconds == 60

    def test_custom_params(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=50, window_seconds=30)
        assert rl.max_requests == 50
        assert rl.window_seconds == 30

    def test_empty_buckets(self):
        rl = RateLimiterMiddleware(app=MagicMock())
        assert len(rl._buckets) == 0

    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": "1"})
    def test_disabled_by_env_var_1(self):
        rl = RateLimiterMiddleware(app=MagicMock())
        assert rl._disabled is True

    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": "true"})
    def test_disabled_by_env_var_true(self):
        rl = RateLimiterMiddleware(app=MagicMock())
        assert rl._disabled is True

    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": "0"})
    def test_not_disabled_by_zero(self):
        rl = RateLimiterMiddleware(app=MagicMock())
        assert rl._disabled is False

    @patch.dict(os.environ, {}, clear=True)
    def test_not_disabled_by_default(self):
        # Remove RATE_LIMIT_DISABLED if present
        env = os.environ.copy()
        env.pop("RATE_LIMIT_DISABLED", None)
        with patch.dict(os.environ, env, clear=True):
            rl = RateLimiterMiddleware(app=MagicMock())
            assert rl._disabled is False


class TestClientKey:
    def _make_rl(self):
        return RateLimiterMiddleware(app=MagicMock())

    def test_uses_forwarded_for(self):
        rl = self._make_rl()
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        assert rl._client_key(request) == "1.2.3.4"

    def test_uses_client_host_when_no_forwarded(self):
        rl = self._make_rl()
        request = MagicMock()
        request.headers = {}
        request.client.host = "10.0.0.1"
        assert rl._client_key(request) == "10.0.0.1"

    def test_returns_unknown_when_no_client(self):
        rl = self._make_rl()
        request = MagicMock()
        request.headers = {}
        request.client = None
        assert rl._client_key(request) == "unknown"

    def test_strips_forwarded_for_spaces(self):
        rl = self._make_rl()
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "  1.2.3.4 , 5.6.7.8"}
        assert rl._client_key(request) == "1.2.3.4"


class TestIsRateLimited:
    def test_not_limited_below_threshold(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=5, window_seconds=60)
        for _ in range(4):
            assert rl._is_rate_limited("test_client", 5, 60) is False

    def test_limited_at_threshold(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=3, window_seconds=60)
        rl._is_rate_limited("key1", 3, 60)
        rl._is_rate_limited("key1", 3, 60)
        rl._is_rate_limited("key1", 3, 60)
        assert rl._is_rate_limited("key1", 3, 60) is True

    def test_different_keys_independent(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=2, window_seconds=60)
        rl._is_rate_limited("client_a", 2, 60)
        rl._is_rate_limited("client_a", 2, 60)
        assert rl._is_rate_limited("client_a", 2, 60) is True
        assert rl._is_rate_limited("client_b", 2, 60) is False

    def test_single_request_not_limited(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=100, window_seconds=60)
        assert rl._is_rate_limited("one_shot", 100, 60) is False

    def test_max_requests_one(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=1, window_seconds=60)
        assert rl._is_rate_limited("strict", 1, 60) is False
        assert rl._is_rate_limited("strict", 1, 60) is True

    def test_old_entries_expire(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=2, window_seconds=1)
        rl._is_rate_limited("key", 2, 1)
        rl._is_rate_limited("key", 2, 1)
        assert rl._is_rate_limited("key", 2, 1) is True
        time.sleep(1.1)
        assert rl._is_rate_limited("key", 2, 1) is False

    def test_bucket_cleanup(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=10, window_seconds=1)
        for _ in range(5):
            rl._is_rate_limited("cleaner", 10, 1)
        assert len(rl._buckets["cleaner"]) == 5
        time.sleep(1.1)
        rl._is_rate_limited("cleaner", 10, 1)
        assert len(rl._buckets["cleaner"]) == 1


class TestDispatch:
    def _mock_request(self, path="/api/data", client_host="1.2.3.4", method="GET"):
        request = MagicMock()
        request.url.path = path
        request.method = method
        request.headers = {}
        request.client.host = client_host
        return request

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": ""})
    async def test_non_api_paths_bypass(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=100, window_seconds=60)
        request = self._mock_request(path="/assets/main.js")
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        await rl.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": ""})
    async def test_health_endpoint_bypass(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=100, window_seconds=60)
        request = self._mock_request(path="/api/health")
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        await rl.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": ""})
    async def test_health_detailed_bypass(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=100, window_seconds=60)
        request = self._mock_request(path="/api/health/detailed")
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        await rl.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": ""})
    async def test_api_path_gets_rate_checked(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=1, window_seconds=60)
        request = self._mock_request(path="/api/data")
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        await rl.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": ""})
    async def test_returns_429_when_limited(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=1, window_seconds=60)
        request = self._mock_request(path="/api/data", client_host="10.0.0.1")
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        await rl.dispatch(request, call_next)
        request2 = self._mock_request(path="/api/data", client_host="10.0.0.1")
        response = await rl.dispatch(request2, call_next)
        assert response.status_code == 429

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": ""})
    async def test_429_includes_retry_after(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=1, window_seconds=30)
        request = self._mock_request(path="/api/data", client_host="10.0.0.2")
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        await rl.dispatch(request, call_next)
        request2 = self._mock_request(path="/api/data", client_host="10.0.0.2")
        response = await rl.dispatch(request2, call_next)
        assert response.headers.get("Retry-After") == "30"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"RATE_LIMIT_DISABLED": "1"})
    async def test_disabled_bypasses_all(self):
        rl = RateLimiterMiddleware(app=MagicMock(), max_requests=1, window_seconds=60)
        request = self._mock_request(path="/api/data")
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        await rl.dispatch(request, call_next)
        await rl.dispatch(request, call_next)
        assert call_next.call_count == 2
