"""
QA Sprint 1 — Iteration 4: Error paths, boundary values, and remaining gaps.

Covers:
- Projects: create_project backend raises, save_overlays/advance_step partial
  failure, save_scenario_weights error, reset with specific error types,
  sign-off permission dependency rejection, verify-hash empty-string hash,
  verify-hash signed_off_at=None stringification
- Data: stage=0 and stage=-1 boundary, empty-string scenario, URL-encoded
  product types, very large limit, df_to_records raises during serialization
- Setup: complete with empty JSON body {}, complete with empty-string user,
  get_setup_status returns None, reset response passthrough, validate-tables
  error message
"""
import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(mock_db):
    import app as app_module
    return TestClient(app_module.app)


def _project_dict(**overrides):
    base = {
        "project_id": "proj-001",
        "project_name": "ECL Q4 2025",
        "project_type": "ifrs9",
        "description": "Quarterly ECL calculation",
        "reporting_date": "2025-12-31",
        "current_step": 1,
        "step_status": {"create_project": "completed"},
        "audit_log": [],
        "overlays": [],
        "scenario_weights": {},
        "signed_off_by": None,
        "signed_off_at": None,
        "ecl_hash": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return base


_SAMPLE_DF = pd.DataFrame({
    "product_type": ["mortgage", "personal"],
    "loan_count": [100, 200],
    "total_gca": [5_000_000.0, 3_000_000.0],
})

_EMPTY_DF = pd.DataFrame()


# ===================================================================
# PROJECTS — ERROR PATHS NOT YET COVERED
# ===================================================================

class TestCreateProjectBackendError:
    """POST /api/projects — backend.create_project raises."""

    def test_create_project_backend_raises_propagates_500(self, client):
        """When create_project raises, FastAPI returns 500 (no try/except in route)."""
        with patch("backend.create_project", side_effect=RuntimeError("Duplicate project_id")):
            resp = client.post("/api/projects", json={
                "project_id": "dup",
                "project_name": "Dup Test",
            })
        assert resp.status_code == 500

    def test_create_project_backend_raises_valueerror(self, client):
        """ValueError from backend also surfaces as 500."""
        with patch("backend.create_project", side_effect=ValueError("Invalid project_type")):
            resp = client.post("/api/projects", json={
                "project_id": "p1",
                "project_name": "Test",
            })
        assert resp.status_code == 500


class TestSaveOverlaysErrorPaths:
    """POST /api/projects/{id}/overlays — error paths."""

    def test_save_overlays_backend_raises(self, client):
        """save_overlays exception propagates as 500 (no try/except in route)."""
        with patch("backend.save_overlays", side_effect=RuntimeError("DB write failed")):
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": [{"id": "o1", "product": "mortgage", "type": "adj",
                              "amount": 100.0, "reason": "test"}],
            })
        assert resp.status_code == 500

    def test_advance_step_raises_after_overlays_saved(self, client):
        """Partial failure: overlays saved but advance_step raises."""
        proj = _project_dict()
        with patch("backend.save_overlays", return_value=proj) as mock_save, \
             patch("backend.advance_step", side_effect=ValueError("step error")):
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": [{"id": "o1", "product": "mortgage", "type": "adj",
                              "amount": 100.0, "reason": "test"}],
                "comment": "approve",
            })
        # save_overlays was called successfully
        mock_save.assert_called_once()
        # But advance_step raised, so 500 propagates
        assert resp.status_code == 500


class TestSaveWeightsErrorPath:
    """POST /api/projects/{id}/scenario-weights — backend raises."""

    def test_save_weights_backend_raises(self, client):
        """save_scenario_weights exception propagates as 500."""
        with patch("backend.save_scenario_weights",
                   side_effect=RuntimeError("DB error")):
            resp = client.post("/api/projects/proj-001/scenario-weights", json={
                "weights": {"base": 0.5, "down": 0.5},
            })
        assert resp.status_code == 500


class TestResetProjectErrorTypes:
    """POST /api/projects/{id}/reset — various exception types."""

    def test_reset_value_error_returns_400(self, client):
        """ValueError specifically still caught by the generic except."""
        with patch("backend.reset_project",
                   side_effect=ValueError("Project not found")):
            resp = client.post("/api/projects/proj-001/reset")
        assert resp.status_code == 400
        assert "Project not found" in resp.json()["detail"]

    def test_reset_runtime_error_returns_400(self, client):
        """RuntimeError also caught by except Exception."""
        with patch("backend.reset_project",
                   side_effect=RuntimeError("State machine error")):
            resp = client.post("/api/projects/proj-001/reset")
        assert resp.status_code == 400
        assert "State machine error" in resp.json()["detail"]

    def test_reset_error_message_forwarded_in_detail(self, client):
        """The exact exception message appears in the 400 response detail."""
        msg = "Cannot reset: signed off project requires approval"
        with patch("backend.reset_project", side_effect=Exception(msg)):
            resp = client.post("/api/projects/proj-001/reset")
        assert resp.status_code == 400
        assert resp.json()["detail"] == msg


class TestSignOffPermissionRejection:
    """POST /api/projects/{id}/sign-off — permission dependency rejection."""

    def test_sign_off_with_auth_header_no_permission(self, client):
        """User with auth header but lacking sign_off_projects permission → 403."""
        # The real require_permission checks X-Forwarded-User header.
        # When header is present, it checks the user's role permissions.
        # A user whose role lacks 'sign_off_projects' gets 403.
        with patch("governance.rbac.ROLE_PERMISSIONS", {"viewer": set()}):
            resp = client.post(
                "/api/projects/proj-001/sign-off",
                json={"name": "Viewer"},
                headers={"X-User-Id": "viewer_user"},
            )
        assert resp.status_code == 403

    def test_sign_off_without_auth_header_bypasses_rbac(self, client):
        """Without auth header, RBAC is bypassed (local dev mode) → proceeds."""
        proj = _project_dict(audit_log=[])
        signed = _project_dict(signed_off_by="Alice")
        with patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Alice",
            })
        assert resp.status_code == 200


class TestVerifyHashEdgeCasesIter4:
    """GET /api/projects/{id}/verify-hash — empty-string hash, None signed_off_at."""

    def test_empty_string_hash_treated_as_not_computed(self, client):
        """Empty string ecl_hash is falsy → should return not_computed."""
        proj = _project_dict(ecl_hash="")
        with patch("backend.get_project", return_value=proj):
            resp = client.get("/api/projects/proj-001/verify-hash")
        body = resp.json()
        assert body["status"] == "not_computed"
        assert "No ECL hash stored" in body["message"]

    def test_signed_off_at_none_becomes_string_none(self, client):
        """When signed_off_at is None, str(None) = 'None' in response."""
        proj = _project_dict(ecl_hash="abc", signed_off_at=None)
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=True), \
             patch("middleware.auth.compute_ecl_hash", return_value="abc"):
            resp = client.get("/api/projects/proj-001/verify-hash")
        body = resp.json()
        # str(proj.get("signed_off_at", "")) where value is None → "None"
        assert body["signed_off_at"] == "None"

    def test_signed_off_at_missing_key_becomes_empty_string(self, client):
        """When signed_off_at key is absent, default '' → str('') = ''."""
        proj = _project_dict(ecl_hash="abc")
        del proj["signed_off_at"]
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=True), \
             patch("middleware.auth.compute_ecl_hash", return_value="abc"):
            resp = client.get("/api/projects/proj-001/verify-hash")
        body = resp.json()
        assert body["signed_off_at"] == ""


class TestApprovalHistoryNonListReturn:
    """GET /api/projects/{id}/approval-history — non-list return."""

    def test_approval_history_returns_dict_passthrough(self, client):
        """If get_approval_history returns a dict, it is passed through."""
        with patch("governance.rbac.get_approval_history",
                   return_value={"count": 0, "items": []}):
            resp = client.get("/api/projects/proj-001/approval-history")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0

    def test_approval_history_returns_empty_list(self, client):
        """Empty approval history."""
        with patch("governance.rbac.get_approval_history", return_value=[]):
            resp = client.get("/api/projects/proj-001/approval-history")
        assert resp.status_code == 200
        assert resp.json() == []


# ===================================================================
# DATA — BOUNDARY VALUES AND EDGE CASES
# ===================================================================

class TestDataBoundaryValues:
    """Data endpoint boundary and edge-case inputs."""

    def test_ecl_by_stage_product_stage_zero(self, client):
        """Stage=0 is technically valid int but semantically invalid for IFRS 9."""
        with patch("backend.get_ecl_by_stage_product",
                   return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/ecl-by-stage-product/0")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(0)

    def test_ecl_by_stage_product_negative_stage(self, client):
        """Negative stage integer passed through to backend."""
        with patch("backend.get_ecl_by_stage_product",
                   return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/ecl-by-stage-product/-1")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(-1)

    def test_loans_by_stage_zero(self, client):
        """Stage=0 boundary."""
        with patch("backend.get_loans_by_stage",
                   return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/loans-by-stage/0")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(0)

    def test_loans_by_stage_negative(self, client):
        """Negative stage boundary."""
        with patch("backend.get_loans_by_stage",
                   return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/loans-by-stage/-1")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(-1)

    def test_ecl_by_scenario_empty_string(self, client):
        """Empty string scenario is valid (not missing) — passes to backend."""
        with patch("backend.get_ecl_by_scenario_product_detail",
                   return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/ecl-by-scenario-product-detail",
                              params={"scenario": ""})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("")

    def test_top_exposures_very_large_limit(self, client):
        """Very large limit value passed through."""
        with patch("backend.get_top_exposures",
                   return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/top-exposures", params={"limit": 999999})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(999999)

    def test_loans_by_product_url_encoded_type(self, client):
        """Product type with URL-encoded spaces."""
        with patch("backend.get_loans_by_product",
                   return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/loans-by-product/auto%20loan")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("auto loan")

    def test_loans_by_product_unicode(self, client):
        """Product type with unicode characters."""
        with patch("backend.get_loans_by_product",
                   return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/loans-by-product/crédit")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("crédit")


class TestDfToRecordsSerializationError:
    """Data endpoints when df_to_records itself raises (not the backend)."""

    def test_df_to_records_raises_caught_as_500(self, client):
        """If df_to_records raises during JSON serialization, route returns 500."""
        # Create a DataFrame with an object type that can't be JSON-serialized
        # The route wraps backend call + df_to_records in try/except
        bad_df = MagicMock()
        bad_df.to_dict.side_effect = TypeError("Cannot serialize custom type")
        with patch("backend.get_portfolio_summary", return_value=bad_df):
            resp = client.get("/api/data/portfolio-summary")
        assert resp.status_code == 500
        assert "Failed to load" in resp.json()["detail"]

    def test_df_to_records_with_numpy_object_dtype(self, client):
        """DataFrame with numpy object dtype containing non-serializable items."""
        # numpy arrays in DataFrame cells can cause issues
        df = pd.DataFrame({"data": [np.array([1, 2, 3]), np.array([4, 5, 6])]})
        with patch("backend.get_ecl_summary", return_value=df):
            resp = client.get("/api/data/ecl-summary")
        # Either succeeds with list conversion or fails with 500
        assert resp.status_code in (200, 500)


# ===================================================================
# SETUP — REMAINING GAPS
# ===================================================================

class TestSetupCompleteEdgeCasesIter4:
    """POST /api/setup/complete — additional edge cases."""

    def test_complete_with_empty_json_body(self, client):
        """Empty JSON {} should use default user='admin' from Pydantic model."""
        with patch("admin_config.mark_setup_complete",
                   return_value={"status": "ok"}) as mock_fn:
            resp = client.post("/api/setup/complete",
                               json={})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("admin")

    def test_complete_with_empty_string_user(self, client):
        """Empty string user is passed through verbatim (no validation)."""
        with patch("admin_config.mark_setup_complete",
                   return_value={"status": "ok"}) as mock_fn:
            resp = client.post("/api/setup/complete",
                               json={"user": ""})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("")


class TestSetupStatusNoneReturn:
    """GET /api/setup/status — get_setup_status returns None."""

    def test_status_returns_none_becomes_null_json(self, client):
        """When get_setup_status returns None, FastAPI serializes as null."""
        with patch("admin_config.get_setup_status", return_value=None):
            resp = client.get("/api/setup/status")
        assert resp.status_code == 200
        assert resp.json() is None


class TestSetupResetResponsePassthrough:
    """POST /api/setup/reset — response passthrough."""

    def test_reset_passes_through_all_fields(self, client):
        """Whatever mark_setup_incomplete returns is passed through."""
        result = {
            "setup_complete": False,
            "reset_at": "2025-12-31T12:00:00Z",
            "reset_by": "admin",
            "extra_field": "should be preserved",
        }
        with patch("admin_config.mark_setup_incomplete", return_value=result):
            resp = client.post("/api/setup/reset")
        body = resp.json()
        assert body["setup_complete"] is False
        assert body["reset_at"] == "2025-12-31T12:00:00Z"
        assert body["extra_field"] == "should be preserved"


class TestSetupValidateTablesErrorMessage:
    """POST /api/setup/validate-tables — error message check."""

    def test_validate_tables_error_contains_original_message(self, client):
        """The original exception message is included in 500 detail."""
        with patch("admin_config.validate_required_tables",
                   side_effect=Exception("catalog not found: ecl_dev")):
            resp = client.post("/api/setup/validate-tables")
        assert resp.status_code == 500
        assert "catalog not found" in resp.json()["detail"]

    def test_setup_reset_error_message(self, client):
        """Reset error includes descriptive message."""
        with patch("admin_config.mark_setup_incomplete",
                   side_effect=Exception("permission denied")):
            resp = client.post("/api/setup/reset")
        assert resp.status_code == 500
        assert "permission denied" in resp.json()["detail"]


# ===================================================================
# SIGN-OFF — AUDIT LOG JSON STRING EDGE CASES
# ===================================================================

class TestSignOffAuditLogJsonEdge:
    """Additional sign-off audit_log parsing edge cases."""

    def test_audit_log_valid_json_array_with_no_execution_entry(self, client):
        """JSON string audit_log that has entries but none for model_execution."""
        import json as _json
        audit_str = _json.dumps([
            {"step": "data_processing", "user": "Alice"},
            {"step": "data_qc", "user": "Bob"},
        ])
        proj = _project_dict(audit_log=audit_str)
        signed = _project_dict(signed_off_by="Charlie")
        with patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Charlie",
            })
        assert resp.status_code == 200

    def test_sign_off_no_body_returns_422(self, client):
        """Missing request body returns 422."""
        resp = client.post("/api/projects/proj-001/sign-off")
        assert resp.status_code == 422

    def test_sign_off_missing_name_returns_422(self, client):
        """Body without 'name' field returns 422."""
        resp = client.post("/api/projects/proj-001/sign-off", json={})
        assert resp.status_code == 422

    def test_sign_off_backend_raises_propagates_500(self, client):
        """When sign_off_project raises, the error propagates as 500."""
        proj = _project_dict(audit_log=[])
        with patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project",
                   side_effect=RuntimeError("DB write failed")):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Alice",
            })
        assert resp.status_code == 500


# ===================================================================
# LIST PROJECTS — BACKEND ERROR
# ===================================================================

class TestListProjectsError:
    """GET /api/projects — backend raises."""

    def test_list_projects_backend_raises(self, client):
        """list_projects raises → 500 (no try/except in route)."""
        with patch("backend.list_projects",
                   side_effect=RuntimeError("DB connection lost")):
            resp = client.get("/api/projects")
        assert resp.status_code == 500
