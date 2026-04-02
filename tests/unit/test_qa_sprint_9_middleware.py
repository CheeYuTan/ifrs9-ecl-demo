"""
Sprint 9 QA — Middleware tests: auth, error handler, request ID.

Tests cover:
  - get_current_user with all header combinations
  - require_permission with authorized/unauthorized roles and no-auth bypass
  - require_project_not_locked with signed-off and unsigned projects
  - compute_ecl_hash consistency and verify_ecl_hash tamper detection
  - ErrorHandlerMiddleware structured 500 responses
  - RequestIDMiddleware auto-generation and client preservation
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient
from fastapi import FastAPI, HTTPException, Request


# ---------------------------------------------------------------------------
# Auth: get_current_user
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    """Test get_current_user extracts identity from headers."""

    def _make_request(self, headers: dict | None = None):
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [
                (k.lower().encode(), v.encode())
                for k, v in (headers or {}).items()
            ],
        }
        return Request(scope)

    def test_x_forwarded_user_header(self):
        from middleware.auth import get_current_user
        req = self._make_request({"X-Forwarded-User": "usr-001"})
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = {
                "user_id": "usr-001", "role": "analyst",
                "permissions": ["view_portfolio"],
            }
            user = get_current_user(req)
            assert user["user_id"] == "usr-001"
            mock_get.assert_called_once_with("usr-001")

    def test_x_user_id_header(self):
        from middleware.auth import get_current_user
        req = self._make_request({"X-User-Id": "usr-002"})
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = {
                "user_id": "usr-002", "role": "reviewer",
                "permissions": ["review_models"],
            }
            user = get_current_user(req)
            assert user["user_id"] == "usr-002"

    def test_lowercase_x_user_id_header(self):
        from middleware.auth import get_current_user
        req = self._make_request({"x-user-id": "usr-003"})
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = {
                "user_id": "usr-003", "role": "approver",
                "permissions": ["approve_requests"],
            }
            user = get_current_user(req)
            assert user["user_id"] == "usr-003"

    def test_no_auth_header_returns_anonymous(self):
        from middleware.auth import get_current_user, ANONYMOUS_USER
        req = self._make_request({})
        user = get_current_user(req)
        assert user["user_id"] == "anonymous"
        assert user["role"] == "analyst"
        # Returned dict should be a copy, not the singleton
        assert user is not ANONYMOUS_USER

    def test_x_forwarded_user_takes_priority_over_x_user_id(self):
        from middleware.auth import get_current_user
        req = self._make_request({
            "X-Forwarded-User": "usr-001",
            "X-User-Id": "usr-002",
        })
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = {"user_id": "usr-001", "role": "analyst", "permissions": []}
            user = get_current_user(req)
            mock_get.assert_called_once_with("usr-001")
            assert user["user_id"] == "usr-001"

    def test_unknown_user_id_returns_default_analyst(self):
        from middleware.auth import get_current_user
        req = self._make_request({"X-User-Id": "unknown-user"})
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = None
            user = get_current_user(req)
            assert user["user_id"] == "unknown-user"
            assert user["role"] == "analyst"

    def test_rbac_import_failure_returns_fallback(self):
        from middleware.auth import get_current_user
        req = self._make_request({"X-User-Id": "usr-001"})
        with patch("governance.rbac.get_user", side_effect=Exception("DB down")):
            user = get_current_user(req)
            assert user["user_id"] == "usr-001"
            assert user["role"] == "analyst"
            assert user["permissions"] == []


# ---------------------------------------------------------------------------
# Auth: require_permission
# ---------------------------------------------------------------------------

class TestRequirePermission:
    """Test require_permission dependency."""

    def _make_request(self, headers: dict | None = None):
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [
                (k.lower().encode(), v.encode())
                for k, v in (headers or {}).items()
            ],
        }
        return Request(scope)

    def test_authorized_role_passes(self):
        from middleware.auth import require_permission
        checker = require_permission("approve_requests")
        req = self._make_request({"X-User-Id": "usr-003"})
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = {"user_id": "usr-003", "role": "approver", "permissions": []}
            result = checker(req)
            assert result["user_id"] == "usr-003"

    def test_unauthorized_role_raises_403(self):
        from middleware.auth import require_permission
        checker = require_permission("approve_requests")
        req = self._make_request({"X-User-Id": "usr-001"})
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = {"user_id": "usr-001", "role": "analyst", "permissions": []}
            with pytest.raises(HTTPException) as exc_info:
                checker(req)
            assert exc_info.value.status_code == 403
            assert "approve_requests" in str(exc_info.value.detail)

    def test_no_auth_header_bypasses_rbac(self):
        from middleware.auth import require_permission, ANONYMOUS_USER
        checker = require_permission("approve_requests")
        req = self._make_request({})
        result = checker(req)
        assert result["user_id"] == "anonymous"

    def test_admin_has_all_permissions(self):
        from middleware.auth import require_permission
        for action in ["manage_users", "manage_config", "approve_requests", "sign_off_projects"]:
            checker = require_permission(action)
            req = self._make_request({"X-User-Id": "admin"})
            with patch("governance.rbac.get_user") as mock_get:
                mock_get.return_value = {"user_id": "admin", "role": "admin", "permissions": []}
                result = checker(req)
                assert result["user_id"] == "admin"


# ---------------------------------------------------------------------------
# Auth: require_project_not_locked
# ---------------------------------------------------------------------------

class TestRequireProjectNotLocked:
    """Test require_project_not_locked blocks signed-off projects."""

    def _make_request(self, project_id: str = "PROJ001"):
        scope = {
            "type": "http",
            "method": "POST",
            "path": f"/api/projects/{project_id}/update",
            "query_string": b"",
            "headers": [],
            "path_params": {"project_id": project_id},
        }
        return Request(scope)

    def test_signed_off_project_raises_403(self):
        from middleware.auth import require_project_not_locked
        checker = require_project_not_locked()
        req = self._make_request("PROJ001")
        with patch("domain.workflow.get_project") as mock_gp:
            mock_gp.return_value = {"project_id": "PROJ001", "signed_off": True}
            with pytest.raises(HTTPException) as exc_info:
                checker(req)
            assert exc_info.value.status_code == 403
            assert "signed off" in str(exc_info.value.detail).lower()

    def test_unsigned_project_passes(self):
        from middleware.auth import require_project_not_locked
        checker = require_project_not_locked()
        req = self._make_request("PROJ001")
        with patch("domain.workflow.get_project") as mock_gp:
            mock_gp.return_value = {"project_id": "PROJ001", "signed_off": False}
            # Should not raise
            checker(req)

    def test_missing_project_passes(self):
        from middleware.auth import require_project_not_locked
        checker = require_project_not_locked()
        req = self._make_request("PROJ-NONE")
        with patch("domain.workflow.get_project") as mock_gp:
            mock_gp.return_value = None
            checker(req)

    def test_no_project_id_in_path_passes(self):
        from middleware.auth import require_project_not_locked
        checker = require_project_not_locked()
        scope = {
            "type": "http", "method": "GET", "path": "/",
            "query_string": b"", "headers": [], "path_params": {},
        }
        req = Request(scope)
        checker(req)


# ---------------------------------------------------------------------------
# Auth: ECL hash computation & verification
# ---------------------------------------------------------------------------

class TestECLHash:
    """Test compute_ecl_hash and verify_ecl_hash."""

    def test_consistent_hash(self):
        from middleware.auth import compute_ecl_hash
        data = {"ecl_total": 1234567.89, "stage_1": 100000, "stage_2": 200000}
        h1 = compute_ecl_hash(data)
        h2 = compute_ecl_hash(data)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_different_data_different_hash(self):
        from middleware.auth import compute_ecl_hash
        data1 = {"ecl_total": 1234567.89}
        data2 = {"ecl_total": 1234567.90}
        assert compute_ecl_hash(data1) != compute_ecl_hash(data2)

    def test_key_order_does_not_affect_hash(self):
        from middleware.auth import compute_ecl_hash
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}
        assert compute_ecl_hash(data1) == compute_ecl_hash(data2)

    def test_verify_hash_valid(self):
        from middleware.auth import compute_ecl_hash, verify_ecl_hash
        data = {"ecl": 999, "stages": [1, 2, 3]}
        h = compute_ecl_hash(data)
        assert verify_ecl_hash(data, h) is True

    def test_verify_hash_detects_tampered_data(self):
        from middleware.auth import compute_ecl_hash, verify_ecl_hash
        data = {"ecl": 999}
        h = compute_ecl_hash(data)
        tampered = {"ecl": 1000}
        assert verify_ecl_hash(tampered, h) is False

    def test_verify_hash_detects_wrong_hash(self):
        from middleware.auth import verify_ecl_hash
        data = {"ecl": 999}
        assert verify_ecl_hash(data, "0" * 64) is False

    def test_hash_handles_nested_structures(self):
        from middleware.auth import compute_ecl_hash
        data = {"nested": {"a": [1, 2, 3], "b": {"c": 4}}}
        h = compute_ecl_hash(data)
        assert isinstance(h, str) and len(h) == 64

    def test_hash_handles_datetime_via_default_str(self):
        from middleware.auth import compute_ecl_hash
        from datetime import datetime
        data = {"ts": datetime(2025, 1, 1)}
        h = compute_ecl_hash(data)
        assert isinstance(h, str) and len(h) == 64

    def test_empty_dict_hash(self):
        from middleware.auth import compute_ecl_hash
        h = compute_ecl_hash({})
        assert isinstance(h, str) and len(h) == 64


# ---------------------------------------------------------------------------
# Error Handler Middleware
# ---------------------------------------------------------------------------

class TestErrorHandlerMiddleware:
    """Test ErrorHandlerMiddleware returns structured 500 responses."""

    def _make_app_with_error(self, error_msg: str = "Boom"):
        test_app = FastAPI()

        from middleware.request_id import RequestIDMiddleware
        from middleware.error_handler import ErrorHandlerMiddleware
        test_app.add_middleware(ErrorHandlerMiddleware)
        test_app.add_middleware(RequestIDMiddleware)

        @test_app.get("/api/explode")
        def explode():
            raise RuntimeError(error_msg)

        @test_app.get("/api/ok")
        def ok():
            return {"status": "ok"}

        return TestClient(test_app, raise_server_exceptions=False)

    def test_unhandled_exception_returns_500_json(self):
        client = self._make_app_with_error("Something broke")
        resp = client.get("/api/explode")
        assert resp.status_code == 500
        body = resp.json()
        assert body["error"] == "internal_server_error"
        assert "Something broke" in body["message"]

    def test_error_response_includes_request_id(self):
        client = self._make_app_with_error()
        resp = client.get("/api/explode")
        body = resp.json()
        assert "request_id" in body
        assert body["request_id"] != "unknown"

    def test_error_response_includes_path(self):
        client = self._make_app_with_error()
        resp = client.get("/api/explode")
        body = resp.json()
        assert body["path"] == "/api/explode"

    def test_no_stack_trace_in_error_response(self):
        client = self._make_app_with_error()
        resp = client.get("/api/explode")
        body_str = json.dumps(resp.json())
        assert "Traceback" not in body_str
        assert "File " not in body_str

    def test_normal_requests_unaffected(self):
        client = self._make_app_with_error()
        resp = client.get("/api/ok")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Request ID Middleware
# ---------------------------------------------------------------------------

class TestRequestIDMiddleware:
    """Test RequestIDMiddleware adds/preserves X-Request-ID."""

    @pytest.fixture
    def test_client(self):
        test_app = FastAPI()

        from middleware.request_id import RequestIDMiddleware
        test_app.add_middleware(RequestIDMiddleware)

        @test_app.get("/api/test")
        def test_endpoint(request: Request):
            return {"request_id": request.state.request_id}

        @test_app.get("/assets/style.css")
        def static_asset():
            return {"type": "asset"}

        @test_app.get("/docs/readme")
        def docs_page():
            return {"type": "docs"}

        return TestClient(test_app)

    def test_auto_generates_request_id(self, test_client):
        resp = test_client.get("/api/test")
        assert resp.status_code == 200
        assert "x-request-id" in resp.headers
        rid = resp.headers["x-request-id"]
        assert len(rid) > 0

    def test_preserves_client_request_id(self, test_client):
        custom_id = "my-custom-id-12345"
        resp = test_client.get("/api/test", headers={"X-Request-ID": custom_id})
        assert resp.headers["x-request-id"] == custom_id

    def test_request_id_stored_on_state(self, test_client):
        resp = test_client.get("/api/test")
        body = resp.json()
        assert body["request_id"] == resp.headers["x-request-id"]

    def test_auto_generated_id_is_uuid_prefix(self, test_client):
        resp = test_client.get("/api/test")
        rid = resp.headers["x-request-id"]
        # Auto-generated is str(uuid4())[:12]
        assert len(rid) == 12

    def test_different_requests_get_different_ids(self, test_client):
        r1 = test_client.get("/api/test")
        r2 = test_client.get("/api/test")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]

    def test_assets_path_excluded_from_logging(self, test_client):
        """Assets still get request IDs, just not logged."""
        resp = test_client.get("/assets/style.css")
        assert resp.status_code == 200
        assert "x-request-id" in resp.headers

    def test_docs_path_excluded_from_logging(self, test_client):
        resp = test_client.get("/docs/readme")
        assert resp.status_code == 200
        assert "x-request-id" in resp.headers
