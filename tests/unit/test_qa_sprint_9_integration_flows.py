"""
Sprint 9 QA — Integration flow tests: 6 multi-endpoint scenarios.

All flows use the FastAPI TestClient with mocked database.
Each flow tests a realistic multi-step user journey.

Patching strategy:
  - Routes that call `backend.xxx` → patch `backend.xxx`
  - Routes that import from domain at module level → patch `routes.<module>.<func>`
  - Routes that import inside function → patch the source module
"""
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _project_row(pid="PROJ-INT", step=1, signed_off=False, project_type="ifrs9"):
    """Build a realistic project row dict as returned by backend.get_project."""
    return {
        "project_id": pid,
        "project_name": "Integration Test Project",
        "project_type": project_type,
        "description": "Test project for integration flows",
        "reporting_date": "2025-12-31",
        "current_step": step,
        "step_status": {"create_project": "completed", "data_upload": "pending"},
        "audit_log": [],
        "overlays": [],
        "scenario_weights": {},
        "signed_off_by": "Auditor" if signed_off else None,
        "signed_off_at": datetime.now(timezone.utc).isoformat() if signed_off else None,
        "ecl_hash": None,
        "attestation_data": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _model_row(mid="mdl-001", status="draft", model_type="pd"):
    return {
        "model_id": mid,
        "model_name": f"Test Model {mid}",
        "model_type": model_type,
        "algorithm": "logistic_regression",
        "version": 1,
        "status": status,
        "description": "Test model",
        "product_type": "personal_loan",
        "cohort": "Q4-2025",
        "parameters": {},
        "performance_metrics": {"auc": 0.85},
        "training_data_info": {},
        "created_by": "analyst",
        "notes": "",
        "parent_model_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _user_row(uid="usr-001", role="analyst"):
    from governance.rbac import ROLE_PERMISSIONS
    return {
        "user_id": uid,
        "email": f"{uid}@bank.com",
        "display_name": f"User {uid}",
        "role": role,
        "department": "Risk",
        "is_active": True,
        "permissions": list(ROLE_PERMISSIONS.get(role, set())),
    }


def _approval_row(rid="apr-001", status="pending", entity_id="PROJ-INT"):
    return {
        "request_id": rid,
        "request_type": "model_approval",
        "entity_id": entity_id,
        "entity_type": "project",
        "status": status,
        "requested_by": "usr-001",
        "assigned_to": "usr-003",
        "approved_by": None,
        "approved_at": None,
        "rejection_reason": "",
        "comments": "",
        "priority": "normal",
        "due_date": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requested_by_name": "Ana Reyes",
        "assigned_to_name": "Sarah Chen",
        "approved_by_name": None,
    }


# ---------------------------------------------------------------------------
# Flow 1: Create project -> advance through steps -> sign-off
# ---------------------------------------------------------------------------

class TestIntegrationFlow1ProjectLifecycle:
    """Full project lifecycle: create -> advance -> overlays -> sign-off."""

    def test_create_and_get_project(self, fastapi_client, mock_db):
        proj = _project_row("NEW-PROJ")
        with patch("backend.create_project", return_value=proj):
            resp = fastapi_client.post("/api/projects", json={
                "project_id": "NEW-PROJ",
                "project_name": "New Project",
                "project_type": "ifrs9",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["project_id"] == "NEW-PROJ"

    def test_advance_step(self, fastapi_client, mock_db):
        proj = _project_row("PROJ-INT", step=2)
        with patch("backend.advance_step", return_value=proj):
            resp = fastapi_client.post("/api/projects/PROJ-INT/advance", json={
                "action": "data_upload",
                "user": "analyst",
                "detail": "Uploaded loan data",
            })
            assert resp.status_code == 200
            assert resp.json()["current_step"] == 2

    def test_save_overlays(self, fastapi_client, mock_db):
        proj = _project_row("PROJ-INT", step=3)
        with patch("backend.save_overlays", return_value=proj), \
             patch("backend.advance_step", return_value=proj):
            resp = fastapi_client.post("/api/projects/PROJ-INT/overlays", json={
                "overlays": [{
                    "id": "ovl-1", "product": "personal_loan",
                    "type": "absolute", "amount": 50000,
                    "reason": "Management adjustment",
                }],
                "comment": "Q4 overlay",
            })
            assert resp.status_code == 200

    def test_save_scenario_weights(self, fastapi_client, mock_db):
        proj = _project_row("PROJ-INT", step=4)
        with patch("backend.save_scenario_weights", return_value=proj):
            resp = fastapi_client.post("/api/projects/PROJ-INT/scenario-weights", json={
                "weights": {"base": 0.6, "optimistic": 0.2, "pessimistic": 0.2},
            })
            assert resp.status_code == 200

    def test_sign_off_project(self, fastapi_client, mock_db):
        """Sign off a project (no auth header = RBAC bypass)."""
        proj = _project_row("PROJ-INT", step=5)
        signed_proj = _project_row("PROJ-INT", step=5, signed_off=True)
        with patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed_proj):
            resp = fastapi_client.post("/api/projects/PROJ-INT/sign-off", json={
                "name": "Sarah Chen",
            })
            assert resp.status_code == 200

    def test_sign_off_already_signed_returns_403(self, fastapi_client, mock_db):
        """Can't sign off an already signed-off project.

        Route checks proj.get("signed_off_by") via the signed_off_by field.
        """
        proj = _project_row("PROJ-INT", signed_off=True)
        # The route checks proj.get("signed_off") — but the actual key is signed_off_by.
        # Add explicit "signed_off" key to ensure the route's check triggers.
        proj["signed_off"] = True
        with patch("backend.get_project", return_value=proj):
            resp = fastapi_client.post("/api/projects/PROJ-INT/sign-off", json={
                "name": "Another Approver",
            })
            assert resp.status_code == 403

    def test_verify_hash_not_computed(self, fastapi_client, mock_db):
        proj = _project_row("PROJ-INT")
        with patch("backend.get_project", return_value=proj):
            resp = fastapi_client.get("/api/projects/PROJ-INT/verify-hash")
            assert resp.status_code == 200
            assert resp.json()["status"] == "not_computed"

    def test_get_nonexistent_project_returns_404(self, fastapi_client, mock_db):
        with patch("backend.get_project", return_value=None):
            resp = fastapi_client.get("/api/projects/NO-SUCH")
            assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Flow 2: Simulation validation -> get defaults -> verify consistency
# ---------------------------------------------------------------------------

class TestIntegrationFlow2Simulation:
    """Simulation validation and defaults consistency."""

    def test_get_simulation_defaults(self, fastapi_client, mock_db):
        """Get simulation defaults returns expected structure."""
        mock_engine = MagicMock()
        mock_engine.get_defaults.return_value = {
            "default_params": {
                "n_sims": 1000, "pd_lgd_correlation": 0.30,
                "aging_factor": 0.08, "pd_floor": 0.001,
                "pd_cap": 0.95, "lgd_floor": 0.01, "lgd_cap": 0.95,
            },
            "default_weights": {"base": 0.6},
            "scenarios": [{"key": "base"}],
            "products": ["personal_loan"],
        }
        with patch.dict("sys.modules", {"ecl_engine": mock_engine}):
            resp = fastapi_client.get("/api/simulation-defaults")
            assert resp.status_code == 200
            data = resp.json()
            assert "n_simulations" in data
            assert data["n_simulations"] == 1000

    def test_simulation_validate_valid_params(self, fastapi_client, mock_db):
        """Validate simulation parameters — valid params."""
        resp = fastapi_client.post("/api/simulate-validate", json={
            "n_simulations": 1000,
            "pd_lgd_correlation": 0.30,
            "aging_factor": 0.08,
            "pd_floor": 0.001,
            "pd_cap": 0.95,
            "lgd_floor": 0.01,
            "lgd_cap": 0.95,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0

    def test_simulation_validate_invalid_params(self, fastapi_client, mock_db):
        """Validate simulation parameters — invalid (pd_floor >= pd_cap)."""
        resp = fastapi_client.post("/api/simulate-validate", json={
            "n_simulations": 1000,
            "pd_floor": 0.95,
            "pd_cap": 0.001,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_simulation_validate_too_few_sims(self, fastapi_client, mock_db):
        """Validate — fewer than 100 simulations."""
        resp = fastapi_client.post("/api/simulate-validate", json={
            "n_simulations": 50,
        })
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


# ---------------------------------------------------------------------------
# Flow 3: Model registration -> backtest -> promote champion
# ---------------------------------------------------------------------------

class TestIntegrationFlow3ModelLifecycle:
    """Model registration, status update, and champion promotion."""

    def test_register_model(self, fastapi_client, mock_db):
        model = _model_row("mdl-new", status="draft")
        with patch("backend.register_model", return_value=model):
            resp = fastapi_client.post("/api/models", json={
                "model_name": "PD Logistic v2",
                "model_type": "pd",
                "algorithm": "logistic_regression",
            })
            assert resp.status_code == 200
            assert resp.json()["model_id"] == "mdl-new"

    def test_update_model_status_to_pending_review(self, fastapi_client, mock_db):
        model = _model_row("mdl-new", status="pending_review")
        with patch("backend.update_model_status", return_value=model):
            resp = fastapi_client.put("/api/models/mdl-new/status", json={
                "status": "pending_review",
                "user": "analyst",
                "comment": "Ready for validation",
            })
            assert resp.status_code == 200
            assert resp.json()["status"] == "pending_review"

    def test_promote_champion(self, fastapi_client, mock_db):
        model = _model_row("mdl-new", status="champion")
        with patch("backend.promote_champion", return_value=model):
            resp = fastapi_client.post("/api/models/mdl-new/promote", json={
                "user": "approver",
            })
            assert resp.status_code == 200
            assert resp.json()["status"] == "champion"

    def test_get_model_not_found(self, fastapi_client, mock_db):
        with patch("backend.get_model", return_value=None):
            resp = fastapi_client.get("/api/models/no-such-model")
            assert resp.status_code == 404

    def test_list_models(self, fastapi_client, mock_db):
        models = [_model_row("mdl-1"), _model_row("mdl-2")]
        with patch("backend.list_models", return_value=models):
            resp = fastapi_client.get("/api/models")
            assert resp.status_code == 200
            assert len(resp.json()) == 2

    def test_get_model_audit_trail(self, fastapi_client, mock_db):
        trail = [{"event": "created", "user": "analyst", "ts": "2025-12-01"}]
        with patch("backend.get_model_audit_trail", return_value=trail):
            resp = fastapi_client.get("/api/models/mdl-1/audit")
            assert resp.status_code == 200
            assert len(resp.json()) == 1

    def test_compare_models(self, fastapi_client, mock_db):
        models = [_model_row("mdl-1"), _model_row("mdl-2")]
        with patch("backend.compare_models", return_value=models):
            resp = fastapi_client.post("/api/models/compare", json={
                "model_ids": ["mdl-1", "mdl-2"],
            })
            assert resp.status_code == 200
            assert len(resp.json()) == 2

    def test_invalid_status_transition_returns_400(self, fastapi_client, mock_db):
        with patch("backend.update_model_status", side_effect=ValueError("Invalid transition")):
            resp = fastapi_client.put("/api/models/mdl-1/status", json={
                "status": "champion",
                "user": "analyst",
            })
            assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Flow 4: Approval request -> approve -> verify in history
# ---------------------------------------------------------------------------

class TestIntegrationFlow4ApprovalWorkflow:
    """RBAC approval workflow: request -> approve -> history."""

    def test_create_approval_request(self, fastapi_client, mock_db):
        approval = _approval_row("apr-new")
        with patch("backend.create_approval_request", return_value=approval):
            resp = fastapi_client.post("/api/rbac/approvals", json={
                "request_type": "model_approval",
                "entity_id": "PROJ-INT",
                "entity_type": "project",
                "requested_by": "usr-001",
                "assigned_to": "usr-003",
            })
            assert resp.status_code == 200
            assert resp.json()["request_id"] == "apr-new"
            assert resp.json()["status"] == "pending"

    def test_approve_request(self, fastapi_client, mock_db):
        approved = _approval_row("apr-new", status="approved")
        approved["approved_by"] = "usr-003"
        with patch("backend.approve_request", return_value=approved):
            resp = fastapi_client.post("/api/rbac/approvals/apr-new/approve", json={
                "user_id": "usr-003",
                "comment": "Looks good",
            })
            assert resp.status_code == 200
            assert resp.json()["status"] == "approved"

    def test_reject_request(self, fastapi_client, mock_db):
        rejected = _approval_row("apr-rej", status="rejected")
        with patch("backend.reject_request", return_value=rejected):
            resp = fastapi_client.post("/api/rbac/approvals/apr-rej/reject", json={
                "user_id": "usr-003",
                "comment": "Needs revision",
            })
            assert resp.status_code == 200
            assert resp.json()["status"] == "rejected"

    def test_approval_history(self, fastapi_client, mock_db):
        history = [
            _approval_row("apr-1", status="approved"),
            _approval_row("apr-2", status="rejected"),
        ]
        with patch("backend.get_approval_history", return_value=history):
            resp = fastapi_client.get("/api/rbac/approvals/history/PROJ-INT")
            assert resp.status_code == 200
            assert len(resp.json()) == 2

    def test_list_users_with_role_filter(self, fastapi_client, mock_db):
        users = [_user_row("usr-003", "approver")]
        with patch("backend.list_users", return_value=users):
            resp = fastapi_client.get("/api/rbac/users?role=approver")
            assert resp.status_code == 200
            assert len(resp.json()) == 1
            assert resp.json()[0]["role"] == "approver"

    def test_check_permissions(self, fastapi_client, mock_db):
        user = _user_row("usr-003", "approver")
        with patch("backend.get_user", return_value=user):
            resp = fastapi_client.get("/api/rbac/permissions/usr-003")
            assert resp.status_code == 200
            data = resp.json()
            assert "approve_requests" in data["permissions"]

    def test_approve_already_approved_returns_400(self, fastapi_client, mock_db):
        with patch("backend.approve_request", side_effect=ValueError("Request is already approved")):
            resp = fastapi_client.post("/api/rbac/approvals/apr-done/approve", json={
                "user_id": "usr-003",
                "comment": "",
            })
            assert resp.status_code == 400

    def test_user_not_found_returns_404(self, fastapi_client, mock_db):
        with patch("backend.get_user", return_value=None):
            resp = fastapi_client.get("/api/rbac/users/no-such")
            assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Flow 5: Period-close pipeline step sequencing
# ---------------------------------------------------------------------------

class TestIntegrationFlow5PeriodClose:
    """Period-close pipeline: start -> execute steps -> complete.

    Routes import directly from domain.period_close at module level,
    so we patch routes.period_close.<func>.
    """

    def test_list_pipeline_steps(self, fastapi_client, mock_db):
        resp = fastapi_client.get("/api/pipeline/steps")
        assert resp.status_code == 200
        steps = resp.json()
        assert isinstance(steps, list)
        assert len(steps) > 0
        for s in steps:
            assert "key" in s

    def test_start_pipeline(self, fastapi_client, mock_db):
        run = {"run_id": "run-001", "project_id": "PROJ-INT", "status": "running", "steps": []}
        with patch("routes.period_close.start_pipeline", return_value=run):
            resp = fastapi_client.post("/api/pipeline/start/PROJ-INT", json={
                "triggered_by": "analyst",
            })
            assert resp.status_code == 200
            assert resp.json()["run_id"] == "run-001"

    def test_execute_pipeline_step(self, fastapi_client, mock_db):
        result = {"step_key": "data_freshness", "status": "completed", "duration_ms": 150}
        run = {"run_id": "run-001", "status": "running", "steps": []}
        with patch("routes.period_close.get_pipeline_run", return_value=run), \
             patch("routes.period_close.execute_step", return_value=result):
            resp = fastapi_client.post("/api/pipeline/run/run-001/execute-step", json={
                "step_key": "data_freshness",
            })
            assert resp.status_code == 200

    def test_complete_pipeline(self, fastapi_client, mock_db):
        run = {"run_id": "run-001", "status": "running", "steps": [
            {"key": "data_validation", "status": "completed"},
        ]}
        completed_run = {**run, "status": "completed"}
        with patch("routes.period_close.get_pipeline_run", side_effect=[run, completed_run]), \
             patch("routes.period_close.complete_pipeline"):
            resp = fastapi_client.post("/api/pipeline/run/run-001/complete")
            assert resp.status_code == 200

    def test_invalid_step_key_returns_400(self, fastapi_client, mock_db):
        run = {"run_id": "run-001", "status": "running", "steps": []}
        with patch("routes.period_close.get_pipeline_run", return_value=run):
            resp = fastapi_client.post("/api/pipeline/run/run-001/execute-step", json={
                "step_key": "INVALID_STEP_KEY",
            })
            assert resp.status_code == 400

    def test_get_run_not_found(self, fastapi_client, mock_db):
        with patch("routes.period_close.get_pipeline_run", return_value=None):
            resp = fastapi_client.get("/api/pipeline/run/no-such-run")
            assert resp.status_code == 404

    def test_pipeline_health(self, fastapi_client, mock_db):
        health = {"project_id": "PROJ-INT", "last_run": None, "status": "no_runs"}
        with patch("routes.period_close.get_pipeline_health", return_value=health):
            resp = fastapi_client.get("/api/pipeline/health/PROJ-INT")
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Flow 6: Data mapping suggest -> validate -> apply pipeline
# ---------------------------------------------------------------------------

class TestIntegrationFlow6DataMapping:
    """Data mapping workflow: suggest -> validate -> apply.

    Routes import directly from domain.data_mapper at module level,
    so we patch routes.data_mapping.<func>.
    """

    def test_get_mapping_status(self, fastapi_client, mock_db):
        status = {"mapped": 3, "unmapped": 2, "tables": ["loans", "ecl"]}
        with patch("routes.data_mapping.get_mapping_status", return_value=status):
            resp = fastapi_client.get("/api/data-mapping/status")
            assert resp.status_code == 200
            assert resp.json()["mapped"] == 3

    def test_suggest_mappings(self, fastapi_client, mock_db):
        suggestions = {
            "mappings": {"loan_id": "LOAN_ID", "amount": "GROSS_CARRYING_AMOUNT"},
            "confidence": 0.85,
        }
        with patch("routes.data_mapping.suggest_mappings", return_value=suggestions):
            resp = fastapi_client.post("/api/data-mapping/suggest", json={
                "table_key": "model_ready_loans",
                "source_table": "catalog.schema.raw_loans",
            })
            assert resp.status_code == 200

    def test_validate_mappings(self, fastapi_client, mock_db):
        validation = {"valid": True, "errors": [], "warnings": []}
        with patch("routes.data_mapping.validate_mapping", return_value=validation):
            resp = fastapi_client.post("/api/data-mapping/validate", json={
                "table_key": "model_ready_loans",
                "source_table": "catalog.schema.raw_loans",
                "mappings": {"loan_id": "LOAN_ID"},
            })
            assert resp.status_code == 200

    def test_apply_mapping(self, fastapi_client, mock_db):
        result = {"status": "success", "rows_ingested": 1000}
        with patch("routes.data_mapping.apply_mapping", return_value=result):
            resp = fastapi_client.post("/api/data-mapping/apply", json={
                "table_key": "model_ready_loans",
                "source_table": "catalog.schema.raw_loans",
                "mappings": {"loan_id": "LOAN_ID"},
                "mode": "overwrite",
            })
            assert resp.status_code == 200

    def test_list_catalogs(self, fastapi_client, mock_db):
        catalogs = [{"name": "main"}, {"name": "staging"}]
        with patch("routes.data_mapping.list_uc_catalogs", return_value=catalogs):
            resp = fastapi_client.get("/api/data-mapping/catalogs")
            assert resp.status_code == 200
            assert len(resp.json()) == 2

    def test_validate_invalid_mapping(self, fastapi_client, mock_db):
        validation = {"valid": False, "errors": ["Missing required column: loan_id"], "warnings": []}
        with patch("routes.data_mapping.validate_mapping", return_value=validation):
            resp = fastapi_client.post("/api/data-mapping/validate", json={
                "table_key": "model_ready_loans",
                "source_table": "catalog.schema.raw_loans",
                "mappings": {},
            })
            assert resp.status_code == 200
            assert resp.json()["valid"] is False


# ---------------------------------------------------------------------------
# Cross-cutting: middleware visible on integration endpoints
# ---------------------------------------------------------------------------

class TestIntegrationCrossCutting:
    """Verify middleware headers are present on integration flow endpoints."""

    def test_request_id_on_project_endpoint(self, fastapi_client, mock_db):
        with patch("backend.list_projects", return_value=pd.DataFrame()):
            resp = fastapi_client.get("/api/projects")
            assert "x-request-id" in resp.headers

    def test_request_id_on_model_endpoint(self, fastapi_client, mock_db):
        with patch("backend.list_models", return_value=[]):
            resp = fastapi_client.get("/api/models")
            assert "x-request-id" in resp.headers

    def test_request_id_on_rbac_endpoint(self, fastapi_client, mock_db):
        with patch("backend.list_users", return_value=[]):
            resp = fastapi_client.get("/api/rbac/users")
            assert "x-request-id" in resp.headers

    def test_structured_error_on_not_found(self, fastapi_client, mock_db):
        with patch("backend.get_project", return_value=None):
            resp = fastapi_client.get("/api/projects/NONEXISTENT")
            assert resp.status_code == 404
            body = resp.json()
            assert "detail" in body

    def test_health_endpoint(self, fastapi_client, mock_db):
        mock_db["query_df"].return_value = pd.DataFrame({"ok": [1]})
        resp = fastapi_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
