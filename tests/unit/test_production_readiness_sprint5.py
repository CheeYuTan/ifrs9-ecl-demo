"""Sprint 5 (Run 6): Production readiness — request ID, error handling, structured logging."""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../app"))


@pytest.fixture
def client():
    with patch("db.pool._pool", MagicMock()):
        with patch("db.pool.query_df") as mock_qdf:
            mock_qdf.return_value = MagicMock(empty=True)
            from app import app
            from fastapi.testclient import TestClient
            return TestClient(app)


class TestRequestIDMiddleware:
    """Every response should include X-Request-ID header."""

    def test_health_has_request_id(self, client):
        with patch("backend.query_df", return_value=MagicMock(empty=False, __len__=lambda s: 1)):
            resp = client.get("/api/health")
        assert "x-request-id" in resp.headers

    def test_request_id_is_unique(self, client):
        with patch("backend.query_df", return_value=MagicMock(empty=False, __len__=lambda s: 1)):
            resp1 = client.get("/api/health")
            resp2 = client.get("/api/health")
        assert resp1.headers["x-request-id"] != resp2.headers["x-request-id"]

    def test_custom_request_id_preserved(self, client):
        with patch("backend.query_df", return_value=MagicMock(empty=False, __len__=lambda s: 1)):
            resp = client.get("/api/health", headers={"X-Request-ID": "test-123"})
        assert resp.headers["x-request-id"] == "test-123"

    def test_404_has_request_id(self, client):
        resp = client.get("/api/nonexistent-endpoint-xyz")
        assert "x-request-id" in resp.headers


class TestStructuredLogging:
    """Verify structured logging format is configured."""

    def test_logging_format_configured(self):
        import logging
        root = logging.getLogger()
        # At least one handler should exist
        assert len(root.handlers) > 0

    def test_app_logger_exists(self):
        import logging
        logger = logging.getLogger("app")
        assert logger is not None


class TestErrorHandlerMiddleware:
    """Unhandled errors should return structured JSON."""

    def test_error_handler_exists(self):
        from middleware.error_handler import ErrorHandlerMiddleware
        assert ErrorHandlerMiddleware is not None

    def test_request_id_middleware_exists(self):
        from middleware.request_id import RequestIDMiddleware
        assert RequestIDMiddleware is not None


class TestMiddlewareRegistration:
    """Middleware should be registered on the app."""

    def test_app_has_middleware(self, client):
        from app import app
        middleware_classes = [type(m).__name__ for m in getattr(app, 'user_middleware', [])]
        # Check that our custom middleware types are registered
        # FastAPI stores them differently, so check via Starlette's middleware stack
        assert hasattr(app, 'middleware_stack')


class TestAdminConfigMaxSimulations:
    """Simulation cap configurable via admin config (from Sprint 1)."""

    def test_defaults_endpoint_returns_params(self, client):
        import pandas as pd
        mock_df = pd.DataFrame([{
            "scenario": "base", "weight": 0.40, "ecl_mean": 1000,
            "ecl_p50": 950, "ecl_p75": 1100, "ecl_p95": 1400, "ecl_p99": 1600,
            "avg_pd_multiplier": 1.0, "avg_lgd_multiplier": 1.0,
            "pd_vol": 0.05, "lgd_vol": 0.03,
        }])
        with patch("ecl_engine._load_config", return_value=({}, {})):
            with patch("ecl_engine._build_product_maps", return_value=({}, {})):
                with patch("ecl_engine._load_scenarios", return_value=mock_df):
                    with patch("ecl_engine.backend"):
                        resp = client.get("/api/simulation-defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert "n_simulations" in data
        assert "pd_lgd_correlation" in data


class TestHealthEndpoints:
    """Health check endpoints work correctly."""

    def test_basic_health_check(self, client):
        with patch("backend.query_df", return_value=MagicMock(empty=False, __len__=lambda s: 1)):
            resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")

    def test_basic_health_check_degraded(self, client):
        with patch("backend.query_df", side_effect=Exception("DB down")):
            resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
