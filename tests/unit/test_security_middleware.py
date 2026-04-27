"""Tests for security headers and rate limiter middleware."""
import os
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.testclient import TestClient
from fastapi import FastAPI

from middleware.security_headers import SecurityHeadersMiddleware
from middleware.rate_limiter import RateLimiterMiddleware


def _make_app(rate_limit=5, window=60):
    """Create a minimal FastAPI app with security middleware for testing.

    Forces rate limiting ON regardless of RATE_LIMIT_DISABLED env var
    (which is set in conftest.py for the main app tests).
    """
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)
    test_app.add_middleware(RateLimiterMiddleware, max_requests=rate_limit, window_seconds=window)

    @test_app.get("/api/test")
    def api_test():
        return {"ok": True}

    @test_app.get("/api/health")
    def api_health():
        return {"status": "healthy"}

    @test_app.get("/static/file.js")
    def static_file():
        return {"file": "content"}

    return test_app


class TestSecurityHeaders:
    def test_nosniff_header(self):
        client = TestClient(_make_app())
        resp = client.get("/api/test")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"

    def test_frame_deny_header(self):
        client = TestClient(_make_app())
        resp = client.get("/api/test")
        assert resp.headers["X-Frame-Options"] == "DENY"

    def test_xss_protection_header(self):
        client = TestClient(_make_app())
        resp = client.get("/api/test")
        assert resp.headers["X-XSS-Protection"] == "1; mode=block"

    def test_referrer_policy_header(self):
        client = TestClient(_make_app())
        resp = client.get("/api/test")
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self):
        client = TestClient(_make_app())
        resp = client.get("/api/test")
        assert resp.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"

    def test_headers_on_static_too(self):
        client = TestClient(_make_app())
        resp = client.get("/static/file.js")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"


class TestRateLimiter:
    @pytest.fixture(autouse=True)
    def _enable_rate_limiting(self, monkeypatch):
        monkeypatch.delenv("RATE_LIMIT_DISABLED", raising=False)

    def test_allows_within_limit(self):
        client = TestClient(_make_app(rate_limit=5))
        for _ in range(5):
            resp = client.get("/api/test")
            assert resp.status_code == 200

    def test_blocks_over_limit(self):
        client = TestClient(_make_app(rate_limit=3))
        for _ in range(3):
            client.get("/api/test")
        resp = client.get("/api/test")
        assert resp.status_code == 429
        assert "Too many requests" in resp.json()["detail"]
        assert "Retry-After" in resp.headers

    def test_health_exempt(self):
        client = TestClient(_make_app(rate_limit=2))
        for _ in range(10):
            resp = client.get("/api/health")
            assert resp.status_code == 200

    def test_static_exempt(self):
        client = TestClient(_make_app(rate_limit=2))
        for _ in range(10):
            resp = client.get("/static/file.js")
            assert resp.status_code == 200

    def test_bucket_resets_after_window(self):
        app = _make_app(rate_limit=2, window=1)
        client = TestClient(app)
        client.get("/api/test")
        client.get("/api/test")
        assert client.get("/api/test").status_code == 429
        time.sleep(1.1)
        assert client.get("/api/test").status_code == 200
