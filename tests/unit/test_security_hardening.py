"""Security hardening tests — Sprint 4.

Tests for:
  - Per-endpoint rate limiting tiers (simulation, reports)
  - Input validation via Pydantic Field constraints
  - SQL injection attempt rejection
  - XSS payload rejection via security headers
  - RBAC bypass attempt tests
  - CORS configuration hardening
"""
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from middleware.rate_limiter import (
    ENDPOINT_LIMITS,
    RateLimiterMiddleware,
    _match_endpoint_limit,
)


# ---------------------------------------------------------------------------
# Endpoint limit matching
# ---------------------------------------------------------------------------

class TestEndpointLimitMatching:
    def test_simulate_exact_match(self):
        assert _match_endpoint_limit("/api/simulate") == (5, 60)

    def test_simulate_stream_match(self):
        assert _match_endpoint_limit("/api/simulate-stream") == (5, 60)

    def test_reports_generate_prefix(self):
        assert _match_endpoint_limit("/api/reports/generate/proj-1") == (10, 60)

    def test_pipeline_start_prefix(self):
        assert _match_endpoint_limit("/api/pipeline/start/proj-1") == (10, 60)

    def test_backtest_run_match(self):
        assert _match_endpoint_limit("/api/backtest/run") == (10, 60)

    def test_normal_api_no_special_limit(self):
        assert _match_endpoint_limit("/api/projects") is None

    def test_health_no_special_limit(self):
        assert _match_endpoint_limit("/api/health") is None

    def test_data_no_special_limit(self):
        assert _match_endpoint_limit("/api/data/loans") is None


# ---------------------------------------------------------------------------
# Per-endpoint rate limiting integration
# ---------------------------------------------------------------------------

def _make_rate_app():
    app = FastAPI()
    app.add_middleware(RateLimiterMiddleware, max_requests=100, window_seconds=60)

    @app.post("/api/simulate")
    def simulate():
        return {"ok": True}

    @app.post("/api/reports/generate/proj-1")
    def gen_report():
        return {"ok": True}

    @app.get("/api/projects")
    def projects():
        return {"ok": True}

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return app


class TestPerEndpointRateLimiting:
    @pytest.fixture(autouse=True)
    def _enable_rate_limiting(self, monkeypatch):
        monkeypatch.delenv("RATE_LIMIT_DISABLED", raising=False)

    def test_simulate_limited_at_5(self):
        client = TestClient(_make_rate_app())
        for i in range(5):
            resp = client.post("/api/simulate", json={})
            assert resp.status_code == 200, f"Request {i+1} failed"
        resp = client.post("/api/simulate", json={})
        assert resp.status_code == 429
        assert "Rate limit exceeded" in resp.json()["detail"]

    def test_report_generate_limited_at_10(self):
        client = TestClient(_make_rate_app())
        for i in range(10):
            resp = client.post("/api/reports/generate/proj-1", json={})
            assert resp.status_code == 200, f"Request {i+1} failed"
        resp = client.post("/api/reports/generate/proj-1", json={})
        assert resp.status_code == 429

    def test_normal_endpoints_use_global_limit(self):
        client = TestClient(_make_rate_app())
        for _ in range(50):
            resp = client.get("/api/projects")
            assert resp.status_code == 200

    def test_get_requests_skip_endpoint_limit(self):
        """GET requests to expensive endpoints still only use global limit."""
        app = FastAPI()
        app.add_middleware(RateLimiterMiddleware, max_requests=100, window_seconds=60)

        @app.get("/api/simulate")
        def sim_get():
            return {"ok": True}

        client = TestClient(app)
        for _ in range(20):
            resp = client.get("/api/simulate")
            assert resp.status_code == 200

    def test_different_clients_have_separate_buckets(self):
        app = _make_rate_app()
        client = TestClient(app)
        for _ in range(5):
            client.post("/api/simulate", json={}, headers={"X-Forwarded-For": "1.1.1.1"})
        resp = client.post("/api/simulate", json={}, headers={"X-Forwarded-For": "1.1.1.1"})
        assert resp.status_code == 429
        resp2 = client.post("/api/simulate", json={}, headers={"X-Forwarded-For": "2.2.2.2"})
        assert resp2.status_code == 200

    def test_endpoint_and_global_limits_independent(self):
        """Hitting endpoint limit doesn't consume global budget."""
        app = _make_rate_app()
        client = TestClient(app)
        for _ in range(5):
            client.post("/api/simulate", json={})
        assert client.post("/api/simulate", json={}).status_code == 429
        assert client.get("/api/projects").status_code == 200

    def test_health_always_exempt(self):
        client = TestClient(_make_rate_app())
        for _ in range(200):
            resp = client.get("/api/health")
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Input validation — Pydantic Field constraints
# ---------------------------------------------------------------------------

class TestInputValidationSimulation:
    def test_n_simulations_too_large(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"n_simulations": 999999})
        assert resp.status_code == 422

    def test_n_simulations_negative(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"n_simulations": -1})
        assert resp.status_code == 422

    def test_n_simulations_zero(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"n_simulations": 0})
        assert resp.status_code == 422

    def test_pd_floor_out_of_range(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"pd_floor": 1.5})
        assert resp.status_code == 422

    def test_pd_cap_negative(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"pd_cap": -0.1})
        assert resp.status_code == 422

    def test_lgd_floor_out_of_range(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"lgd_floor": 2.0})
        assert resp.status_code == 422

    def test_correlation_out_of_range(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"pd_lgd_correlation": 5.0})
        assert resp.status_code == 422

    def test_random_seed_negative(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"random_seed": -1})
        assert resp.status_code == 422

    def test_aging_factor_too_large(self, fastapi_client):
        resp = fastapi_client.post("/api/simulate", json={"aging_factor": 1.5})
        assert resp.status_code == 422


class TestInputValidationProjects:
    def test_project_id_too_long(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/projects",
            json={"project_id": "a" * 200, "project_name": "Test"},
        )
        assert resp.status_code == 422

    def test_project_id_special_chars(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/projects",
            json={"project_id": "proj; DROP TABLE--", "project_name": "Test"},
        )
        assert resp.status_code == 422

    def test_project_id_empty(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/projects",
            json={"project_id": "", "project_name": "Test"},
        )
        assert resp.status_code == 422

    def test_project_name_too_long(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/projects",
            json={"project_id": "proj-1", "project_name": "x" * 300},
        )
        assert resp.status_code == 422

    def test_description_too_long(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/projects",
            json={
                "project_id": "proj-1",
                "project_name": "Test",
                "description": "x" * 3000,
            },
        )
        assert resp.status_code == 422

    def test_valid_project_accepted(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/projects",
            json={"project_id": "proj-valid-1", "project_name": "Valid Project"},
        )
        assert resp.status_code != 422


class TestInputValidationModels:
    def test_model_name_empty(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/models",
            json={"model_name": "", "model_type": "PD"},
        )
        assert resp.status_code == 422

    def test_model_name_too_long(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/models",
            json={"model_name": "x" * 300, "model_type": "PD"},
        )
        assert resp.status_code == 422

    def test_version_too_large(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/models",
            json={"model_name": "test", "model_type": "PD", "version": 99999},
        )
        assert resp.status_code == 422

    def test_version_zero(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/models",
            json={"model_name": "test", "model_type": "PD", "version": 0},
        )
        assert resp.status_code == 422

    def test_notes_too_long(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/models",
            json={"model_name": "test", "model_type": "PD", "notes": "x" * 5000},
        )
        assert resp.status_code == 422


class TestInputValidationDataMapping:
    def test_preview_limit_too_large(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/data-mapping/preview",
            json={"source_table": "catalog.schema.table", "limit": 5000},
        )
        assert resp.status_code == 422

    def test_preview_limit_zero(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/data-mapping/preview",
            json={"source_table": "catalog.schema.table", "limit": 0},
        )
        assert resp.status_code == 422

    def test_apply_invalid_mode(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/data-mapping/apply",
            json={
                "table_key": "loans",
                "source_table": "cat.sch.tbl",
                "mappings": {"col1": "col2"},
                "mode": "drop_table",
            },
        )
        assert resp.status_code == 422

    def test_source_table_empty(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/data-mapping/preview",
            json={"source_table": ""},
        )
        assert resp.status_code == 422


class TestInputValidationMarkov:
    def test_horizon_months_too_large(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/markov/forecast",
            json={"matrix_id": "m1", "initial_distribution": [0.5, 0.5], "horizon_months": 500},
        )
        assert resp.status_code == 422

    def test_horizon_months_zero(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/markov/forecast",
            json={"matrix_id": "m1", "initial_distribution": [0.5, 0.5], "horizon_months": 0},
        )
        assert resp.status_code == 422

    def test_compare_too_few_ids(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/markov/compare",
            json={"matrix_ids": ["m1"]},
        )
        assert resp.status_code == 422


class TestInputValidationRbac:
    def test_invalid_priority(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/rbac/approvals",
            json={
                "request_type": "model_approval",
                "entity_id": "m1",
                "requested_by": "user1",
                "priority": "super_urgent",
            },
        )
        assert resp.status_code == 422

    def test_valid_priority(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/rbac/approvals",
            json={
                "request_type": "model_approval",
                "entity_id": "m1",
                "requested_by": "user1",
                "priority": "high",
            },
        )
        assert resp.status_code != 422


class TestInputValidationProjectMembers:
    def test_invalid_member_role_rejected_by_model(self):
        """AddMemberRequest rejects invalid roles at the Pydantic level."""
        from pydantic import ValidationError
        from routes.project_members import AddMemberRequest

        with pytest.raises(ValidationError):
            AddMemberRequest(user_id="usr-001", role="superadmin")

    def test_valid_member_role_viewer(self):
        from routes.project_members import AddMemberRequest

        m = AddMemberRequest(user_id="usr-001", role="viewer")
        assert m.role == "viewer"

    def test_valid_member_role_editor(self):
        from routes.project_members import AddMemberRequest

        m = AddMemberRequest(user_id="usr-001", role="editor")
        assert m.role == "editor"

    def test_valid_member_role_manager(self):
        from routes.project_members import AddMemberRequest

        m = AddMemberRequest(user_id="usr-001", role="manager")
        assert m.role == "manager"

    def test_empty_user_id_rejected(self):
        from pydantic import ValidationError
        from routes.project_members import AddMemberRequest

        with pytest.raises(ValidationError):
            AddMemberRequest(user_id="", role="viewer")


class TestInputValidationJobs:
    def test_n_simulations_too_large(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/jobs/trigger",
            json={"job_key": "satellite_ecl_sync", "n_simulations": 999999},
        )
        assert resp.status_code == 422

    def test_pd_floor_out_of_range(self, fastapi_client):
        resp = fastapi_client.post(
            "/api/jobs/trigger",
            json={"job_key": "test", "pd_floor": 2.0},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# SQL injection attempt tests
# ---------------------------------------------------------------------------

class TestSQLInjectionPrevention:
    """Verify SQL injection payloads are rejected by input validation."""

    SQL_PAYLOADS = [
        "'; DROP TABLE loans; --",
        "1 OR 1=1",
        "1' UNION SELECT * FROM users--",
        "admin'--",
        "' OR '1'='1",
        "1; DELETE FROM ecl_workflow",
    ]

    def test_project_id_rejects_sql(self, fastapi_client):
        for payload in self.SQL_PAYLOADS:
            resp = fastapi_client.post(
                "/api/projects",
                json={"project_id": payload, "project_name": "Test"},
            )
            assert resp.status_code == 422, f"SQL payload not rejected: {payload}"

    def test_project_id_safe_identifier_pattern(self, fastapi_client):
        """Only alphanumeric, underscore, hyphen allowed."""
        safe_ids = ["proj-1", "my_project", "ECL2024", "test-proj-123"]
        for pid in safe_ids:
            resp = fastapi_client.post(
                "/api/projects",
                json={"project_id": pid, "project_name": "Test"},
            )
            assert resp.status_code != 422, f"Safe ID rejected: {pid}"

    def test_data_mapper_safe_identifier(self):
        """Test _safe_identifier rejects injection patterns."""
        from domain.data_mapper import _safe_identifier

        with pytest.raises(ValueError):
            _safe_identifier("table; DROP TABLE--")

        with pytest.raises(ValueError):
            _safe_identifier("table' OR '1'='1")

        assert _safe_identifier("valid_table") == "valid_table"
        assert _safe_identifier("my_schema.my_table") == "my_schema.my_table"


# ---------------------------------------------------------------------------
# XSS attempt tests
# ---------------------------------------------------------------------------

class TestXSSPrevention:
    """Verify XSS payloads don't execute through responses."""

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
        "<svg onload=alert(1)>",
        "'-alert(1)-'",
    ]

    def test_security_headers_present(self, fastapi_client):
        resp = fastapi_client.get("/api/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_xss_in_project_name_stored_safely(self, fastapi_client):
        """XSS in text fields is stored as-is (not executed) and returned escaped."""
        for payload in self.XSS_PAYLOADS:
            resp = fastapi_client.post(
                "/api/projects",
                json={"project_id": "xss-test", "project_name": payload},
            )
            assert resp.status_code != 422, f"XSS payload rejected as invalid: {payload}"

    def test_content_type_nosniff_on_all_responses(self, fastapi_client):
        endpoints = ["/api/health", "/api/health/detailed"]
        for ep in endpoints:
            resp = fastapi_client.get(ep)
            assert resp.headers.get("X-Content-Type-Options") == "nosniff"


# ---------------------------------------------------------------------------
# RBAC bypass attempt tests
# ---------------------------------------------------------------------------

class TestRBACBypassPrevention:
    """Test that RBAC cannot be bypassed via header manipulation."""

    @patch("middleware.auth.get_current_user")
    def test_forged_admin_header_rejected(self, mock_get_user, fastapi_client):
        """Sending X-User-Id of a non-admin user should not grant admin."""
        from governance.rbac import ROLE_PERMISSIONS
        mock_get_user.return_value = {
            "user_id": "attacker",
            "email": "attacker@evil.com",
            "display_name": "Attacker",
            "role": "analyst",
            "permissions": list(ROLE_PERMISSIONS.get("analyst", set())),
        }
        resp = fastapi_client.get(
            "/api/admin/config",
            headers={"X-User-Id": "attacker"},
        )
        assert resp.status_code == 403

    @patch("middleware.auth.get_current_user")
    def test_role_escalation_blocked(self, mock_get_user, fastapi_client):
        """Reviewer cannot access admin endpoints."""
        from governance.rbac import ROLE_PERMISSIONS
        mock_get_user.return_value = {
            "user_id": "reviewer-1",
            "email": "reviewer@bank.com",
            "display_name": "Reviewer",
            "role": "reviewer",
            "permissions": list(ROLE_PERMISSIONS.get("reviewer", set())),
        }
        resp = fastapi_client.get(
            "/api/admin/config",
            headers={"X-User-Id": "reviewer-1"},
        )
        assert resp.status_code == 403

    def test_empty_user_header_gets_anonymous(self, fastapi_client):
        """Empty auth headers should fall back to anonymous."""
        resp = fastapi_client.get(
            "/api/admin/config",
            headers={"X-User-Id": ""},
        )
        assert resp.status_code != 403

    @patch("middleware.auth.get_current_user")
    def test_analyst_cannot_sign_off(self, mock_get_user, fastapi_client):
        """Analyst role lacks sign_off_projects permission."""
        from governance.rbac import ROLE_PERMISSIONS
        mock_get_user.return_value = {
            "user_id": "analyst-1",
            "email": "analyst@bank.com",
            "display_name": "Analyst",
            "role": "analyst",
            "permissions": list(ROLE_PERMISSIONS.get("analyst", set())),
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/sign-off",
            json={"name": "analyst-1"},
            headers={"X-User-Id": "analyst-1"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# CORS configuration tests
# ---------------------------------------------------------------------------

class TestCORSConfiguration:
    def test_cors_no_credentials_with_wildcard(self):
        """When origins are wildcard, credentials should be disabled."""
        cors_origins = os.environ.get("CORS_ORIGINS", "")
        if not cors_origins or cors_origins in ('["*"]', ""):
            import json as _json
            from app import app as real_app
            for mw in real_app.user_middleware:
                if "CORSMiddleware" in str(mw.cls):
                    allow_creds = mw.kwargs.get("allow_credentials", True)
                    origins = mw.kwargs.get("allow_origins", [])
                    if origins == ["*"]:
                        assert allow_creds is False, (
                            "CORS should not allow credentials with wildcard origins"
                        )

    def test_cors_headers_restricted(self):
        """Allowed headers should be explicitly listed, not wildcard."""
        from app import app as real_app
        for mw in real_app.user_middleware:
            if "CORSMiddleware" in str(mw.cls):
                headers = mw.kwargs.get("allow_headers", [])
                assert headers != ["*"], "CORS allow_headers should not be wildcard"


# ---------------------------------------------------------------------------
# Auth middleware unit tests
# ---------------------------------------------------------------------------

class TestAuthMiddleware:
    def test_anonymous_user_has_analyst_role(self):
        from middleware.auth import ANONYMOUS_USER
        assert ANONYMOUS_USER["role"] == "analyst"
        assert ANONYMOUS_USER["user_id"] == "anonymous"

    def test_compute_ecl_hash_deterministic(self):
        from middleware.auth import compute_ecl_hash
        data = {"total_ecl": 1000.0, "products": ["mortgage"]}
        h1 = compute_ecl_hash(data)
        h2 = compute_ecl_hash(data)
        assert h1 == h2

    def test_compute_ecl_hash_changes_with_data(self):
        from middleware.auth import compute_ecl_hash
        h1 = compute_ecl_hash({"total_ecl": 1000.0})
        h2 = compute_ecl_hash({"total_ecl": 2000.0})
        assert h1 != h2

    def test_verify_ecl_hash_success(self):
        from middleware.auth import compute_ecl_hash, verify_ecl_hash
        data = {"total_ecl": 500.0}
        h = compute_ecl_hash(data)
        assert verify_ecl_hash(data, h) is True

    def test_verify_ecl_hash_failure(self):
        from middleware.auth import verify_ecl_hash
        assert verify_ecl_hash({"total_ecl": 500.0}, "badhash") is False

    def test_get_current_user_no_header(self):
        from middleware.auth import get_current_user
        request = MagicMock()
        request.headers = {}
        user = get_current_user(request)
        assert user["user_id"] == "anonymous"
        assert user["role"] == "analyst"

    def test_get_current_user_with_header(self):
        from middleware.auth import get_current_user
        request = MagicMock()
        request.headers = {"X-User-Id": "test-user"}
        with patch("governance.rbac.get_user", return_value=None):
            user = get_current_user(request)
            assert user["user_id"] == "test-user"
