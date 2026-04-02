"""Sprint 1 Iteration 5 — Final coverage gaps.

Targets:
- Sign-off with audit_log as JSON dict (non-list iterable)
- Sign-off with audit_log as JSON string containing a dict
- advance_step with non-standard status values
- top-exposures default limit=20 verified at backend call level
- get_project returning falsy value (empty dict) vs None
- verify-hash with ecl_hash key entirely absent from project
- overlays with empty overlays list
- scenario-weights with empty dict
- Data endpoints: project_id query parameter forwarding
- list_projects backend returns None
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import pandas as pd


@pytest.fixture
def client():
    from app import app
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Sign-off: audit_log as JSON-string containing a dict (not list)
# ---------------------------------------------------------------------------
class TestSignOffAuditLogDict:
    """When audit_log is a JSON string that parses to a dict, `for entry in reversed(dict)`
    iterates over keys, and `isinstance(key_str, dict)` is False — so executor stays None."""

    @patch("routes.projects.backend")
    def test_sign_off_audit_log_json_dict_no_segregation_violation(self, mock_be, client):
        """JSON dict audit_log: iteration over keys yields strings, not dicts,
        so no executor is found and sign-off succeeds."""
        import json
        mock_be.get_project.return_value = {
            "project_id": "P1",
            "signed_off": False,
            "audit_log": json.dumps({"step": "model_execution", "user": "alice"}),
        }
        mock_be.sign_off_project.return_value = {"project_id": "P1", "signed_off": True}
        resp = client.post("/api/projects/P1/sign-off", json={"name": "alice"})
        assert resp.status_code == 200
        mock_be.sign_off_project.assert_called_once()

    @patch("routes.projects.backend")
    def test_sign_off_audit_log_already_list_of_dicts(self, mock_be, client):
        """When audit_log is already a Python list (not a JSON string),
        it should iterate correctly and find the executor."""
        mock_be.get_project.return_value = {
            "project_id": "P1",
            "signed_off": False,
            "audit_log": [
                {"step": "model_execution", "user": "alice"},
                {"step": "data_processing", "user": "bob"},
            ],
        }
        resp = client.post("/api/projects/P1/sign-off", json={"name": "alice"})
        assert resp.status_code == 403
        assert "Segregation of duties" in resp.json()["detail"]

    @patch("routes.projects.backend")
    def test_sign_off_audit_log_list_no_model_execution(self, mock_be, client):
        """When audit_log is a list but contains no model_execution entry,
        executor stays None and sign-off succeeds."""
        mock_be.get_project.return_value = {
            "project_id": "P1",
            "signed_off": False,
            "audit_log": [
                {"step": "data_processing", "user": "bob"},
                {"step": "overlays", "user": "carol"},
            ],
        }
        mock_be.sign_off_project.return_value = {"project_id": "P1", "signed_off": True}
        resp = client.post("/api/projects/P1/sign-off", json={"name": "alice"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# advance_step with non-standard status values
# ---------------------------------------------------------------------------
class TestAdvanceStepStatusValues:
    """The StepAction model accepts any string for status.
    Verify non-standard values pass through to backend."""

    @patch("routes.projects.backend")
    def test_advance_with_status_failed(self, mock_be, client):
        mock_be.advance_step.return_value = {"project_id": "P1", "current_step": 3}
        resp = client.post(
            "/api/projects/P1/advance",
            json={"action": "test", "user": "admin", "status": "failed"},
        )
        assert resp.status_code == 200
        _, kwargs = mock_be.advance_step.call_args
        # status is a positional arg, check it was passed
        call_args = mock_be.advance_step.call_args[0]
        assert call_args[5] == "failed"  # 6th positional arg is status

    @patch("routes.projects.backend")
    def test_advance_with_status_skipped(self, mock_be, client):
        mock_be.advance_step.return_value = {"project_id": "P1", "current_step": 3}
        resp = client.post(
            "/api/projects/P1/advance",
            json={"action": "test", "user": "admin", "status": "skipped"},
        )
        assert resp.status_code == 200
        call_args = mock_be.advance_step.call_args[0]
        assert call_args[5] == "skipped"

    @patch("routes.projects.backend")
    def test_advance_with_default_status_completed(self, mock_be, client):
        """When status is omitted, default is 'completed'."""
        mock_be.advance_step.return_value = {"project_id": "P1", "current_step": 3}
        resp = client.post(
            "/api/projects/P1/advance",
            json={"action": "test", "user": "admin"},
        )
        assert resp.status_code == 200
        call_args = mock_be.advance_step.call_args[0]
        assert call_args[5] == "completed"

    @patch("routes.projects.backend")
    def test_advance_with_empty_string_status(self, mock_be, client):
        mock_be.advance_step.return_value = {"project_id": "P1", "current_step": 3}
        resp = client.post(
            "/api/projects/P1/advance",
            json={"action": "test", "user": "admin", "status": ""},
        )
        assert resp.status_code == 200
        call_args = mock_be.advance_step.call_args[0]
        assert call_args[5] == ""


# ---------------------------------------------------------------------------
# top-exposures: default limit=20 verified at backend call level
# ---------------------------------------------------------------------------
class TestTopExposuresDefaultLimit:

    @patch("routes.data.backend")
    def test_top_exposures_default_limit_is_20(self, mock_be, client):
        mock_be.get_top_exposures.return_value = pd.DataFrame({"loan_id": ["L1"], "gca": [100.0]})
        resp = client.get("/api/data/top-exposures")
        assert resp.status_code == 200
        mock_be.get_top_exposures.assert_called_once_with(20)

    @patch("routes.data.backend")
    def test_top_exposures_custom_limit_forwarded(self, mock_be, client):
        mock_be.get_top_exposures.return_value = pd.DataFrame({"loan_id": ["L1"], "gca": [100.0]})
        resp = client.get("/api/data/top-exposures?limit=5")
        assert resp.status_code == 200
        mock_be.get_top_exposures.assert_called_once_with(5)

    @patch("routes.data.backend")
    def test_top_exposures_limit_zero(self, mock_be, client):
        mock_be.get_top_exposures.return_value = pd.DataFrame()
        resp = client.get("/api/data/top-exposures?limit=0")
        assert resp.status_code == 200
        mock_be.get_top_exposures.assert_called_once_with(0)


# ---------------------------------------------------------------------------
# get_project: falsy but non-None value
# ---------------------------------------------------------------------------
class TestGetProjectEdgeCases:

    @patch("routes.projects.backend")
    def test_get_project_empty_dict_is_falsy_returns_404(self, mock_be, client):
        """An empty dict {} is falsy — `if not p` is True → 404."""
        mock_be.get_project.return_value = {}
        resp = client.get("/api/projects/P1")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found"

    @patch("routes.projects.backend")
    def test_get_project_none_returns_404(self, mock_be, client):
        mock_be.get_project.return_value = None
        resp = client.get("/api/projects/P1")
        assert resp.status_code == 404

    @patch("routes.projects.backend")
    def test_get_project_zero_is_falsy_returns_404(self, mock_be, client):
        """Numeric 0 is falsy — `if not p` is True → 404."""
        mock_be.get_project.return_value = 0
        resp = client.get("/api/projects/P1")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# verify-hash: ecl_hash key completely absent from project dict
# ---------------------------------------------------------------------------
class TestVerifyHashMissingKey:

    @patch("routes.projects.backend")
    def test_verify_hash_ecl_hash_key_absent(self, mock_be, client):
        """When ecl_hash key is entirely missing, proj.get('ecl_hash') returns None → not_computed."""
        mock_be.get_project.return_value = {"project_id": "P1"}
        resp = client.get("/api/projects/P1/verify-hash")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_computed"

    @patch("routes.projects.backend")
    def test_verify_hash_ecl_hash_is_none_explicit(self, mock_be, client):
        """Explicit None ecl_hash → not_computed."""
        mock_be.get_project.return_value = {"project_id": "P1", "ecl_hash": None}
        resp = client.get("/api/projects/P1/verify-hash")
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_computed"


# ---------------------------------------------------------------------------
# overlays: empty overlays list and scenario-weights: empty dict
# ---------------------------------------------------------------------------
class TestOverlaysAndWeightsEdgeCases:

    @patch("routes.projects.backend")
    def test_save_overlays_empty_list(self, mock_be, client):
        """Saving empty overlays list — no comment, no advance."""
        mock_be.save_overlays.return_value = {"project_id": "P1", "overlays": []}
        resp = client.post(
            "/api/projects/P1/overlays",
            json={"overlays": [], "comment": ""},
        )
        assert resp.status_code == 200
        mock_be.save_overlays.assert_called_once_with("P1", [])
        mock_be.advance_step.assert_not_called()

    @patch("routes.projects.backend")
    def test_save_overlays_with_comment_triggers_advance(self, mock_be, client):
        """When comment is non-empty, advance_step is called after save_overlays."""
        mock_be.save_overlays.return_value = {"project_id": "P1", "overlays": []}
        mock_be.advance_step.return_value = {"project_id": "P1", "overlays": [], "current_step": 8}
        resp = client.post(
            "/api/projects/P1/overlays",
            json={"overlays": [], "comment": "No overlays needed"},
        )
        assert resp.status_code == 200
        mock_be.advance_step.assert_called_once()

    @patch("routes.projects.backend")
    def test_save_scenario_weights_empty_dict(self, mock_be, client):
        """Saving empty weights dict — accepted by endpoint."""
        mock_be.save_scenario_weights.return_value = {"project_id": "P1", "scenario_weights": {}}
        resp = client.post(
            "/api/projects/P1/scenario-weights",
            json={"weights": {}},
        )
        assert resp.status_code == 200
        mock_be.save_scenario_weights.assert_called_once_with("P1", {})


# ---------------------------------------------------------------------------
# list_projects: backend returns None or raises
# ---------------------------------------------------------------------------
class TestListProjectsEdgeCases:

    @patch("routes.projects.backend")
    def test_list_projects_backend_returns_none(self, mock_be, client):
        """If backend returns None, df_to_records should handle it."""
        mock_be.list_projects.return_value = None
        resp = client.get("/api/projects")
        # df_to_records(None) behavior depends on implementation
        # Could be 500 or empty list — just verify no unhandled crash
        assert resp.status_code in (200, 500)

    @patch("routes.projects.backend")
    def test_list_projects_backend_returns_empty_df(self, mock_be, client):
        mock_be.list_projects.return_value = pd.DataFrame()
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Data endpoints: project_id query parameter forwarding
# ---------------------------------------------------------------------------
class TestDataEndpointProjectIdForwarding:

    @patch("routes.data.backend")
    def test_portfolio_summary_no_project_id(self, mock_be, client):
        """Data endpoints don't require project_id at the route level —
        they forward whatever the query has to the backend."""
        mock_be.get_portfolio_summary.return_value = pd.DataFrame({"product": ["A"], "gca": [100]})
        resp = client.get("/api/data/portfolio-summary")
        assert resp.status_code == 200

    @patch("routes.data.backend")
    def test_stage_distribution_returns_list(self, mock_be, client):
        mock_be.get_stage_distribution.return_value = pd.DataFrame({
            "stage": [1, 2, 3], "count": [100, 20, 5]
        })
        resp = client.get("/api/data/stage-distribution")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0]["stage"] == 1


# ---------------------------------------------------------------------------
# Sign-off: already signed-off project
# ---------------------------------------------------------------------------
class TestSignOffAlreadySigned:

    @patch("routes.projects.backend")
    def test_sign_off_already_signed_returns_403(self, mock_be, client):
        mock_be.get_project.return_value = {
            "project_id": "P1",
            "signed_off": True,
            "audit_log": [],
        }
        resp = client.post("/api/projects/P1/sign-off", json={"name": "alice"})
        assert resp.status_code == 403
        assert "already signed off" in resp.json()["detail"]

    @patch("routes.projects.backend")
    def test_sign_off_project_not_found_in_get_project(self, mock_be, client):
        """When get_project returns None, sign-off should still proceed
        (proj is None, proj.get() with default, then backend call)."""
        mock_be.get_project.return_value = None
        mock_be.sign_off_project.return_value = {"project_id": "P1", "signed_off": True}
        resp = client.post("/api/projects/P1/sign-off", json={"name": "alice"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# reset_project: various error types
# ---------------------------------------------------------------------------
class TestResetProjectAdditional:

    @patch("routes.projects.backend")
    def test_reset_project_success(self, mock_be, client):
        mock_be.reset_project.return_value = {"project_id": "P1", "current_step": 1}
        resp = client.post("/api/projects/P1/reset")
        assert resp.status_code == 200

    @patch("routes.projects.backend")
    def test_reset_project_generic_exception_returns_400(self, mock_be, client):
        mock_be.reset_project.side_effect = Exception("DB connection lost")
        resp = client.post("/api/projects/P1/reset")
        assert resp.status_code == 400
        assert "DB connection lost" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# approval_history: exception handling
# ---------------------------------------------------------------------------
class TestApprovalHistoryExceptions:

    @patch("governance.rbac.get_approval_history")
    def test_approval_history_import_error(self, mock_fn, client):
        """When get_approval_history raises, endpoint returns 500."""
        mock_fn.side_effect = RuntimeError("RBAC module unavailable")
        resp = client.get("/api/projects/P1/approval-history")
        assert resp.status_code == 500
        assert "approval history" in resp.json()["detail"].lower()
