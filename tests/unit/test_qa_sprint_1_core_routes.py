"""
QA Sprint 1: Core Workflow & Data Endpoints.

Tests routes/projects.py (10 endpoints), routes/data.py (32 endpoints),
and routes/setup.py (5 endpoints) with mocked backend.
"""
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pandas as pd
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
    """Build a realistic project dict for mock returns."""
    base = {
        "project_id": "proj-001",
        "project_name": "ECL Q4 2025",
        "project_type": "ifrs9",
        "description": "Quarterly ECL calculation",
        "reporting_date": "2025-12-31",
        "current_step": 1,
        "step_status": {"create_project": "completed", "data_processing": "pending"},
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
# PROJECTS ROUTES — /api/projects/*
# ===================================================================

class TestListProjects:
    """GET /api/projects"""

    def test_returns_list_with_projects(self, client):
        df = pd.DataFrame({
            "project_id": ["p1", "p2"],
            "project_name": ["A", "B"],
            "project_type": ["ifrs9", "ifrs9"],
            "current_step": [1, 3],
            "created_at": ["2025-01-01", "2025-06-01"],
            "signed_off_by": [None, "Auditor"],
        })
        with patch("backend.list_projects", return_value=df):
            resp = client.get("/api/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["project_id"] == "p1"

    def test_returns_empty_list_when_no_projects(self, client):
        with patch("backend.list_projects", return_value=_EMPTY_DF):
            resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetProject:
    """GET /api/projects/{project_id}"""

    def test_returns_project_when_found(self, client):
        proj = _project_dict()
        with patch("backend.get_project", return_value=proj):
            resp = client.get("/api/projects/proj-001")
        assert resp.status_code == 200
        body = resp.json()
        assert body["project_id"] == "proj-001"
        assert body["project_type"] == "ifrs9"

    def test_404_when_project_missing(self, client):
        with patch("backend.get_project", return_value=None):
            resp = client.get("/api/projects/nonexistent")
        assert resp.status_code == 404

    def test_response_contains_required_fields(self, client):
        proj = _project_dict()
        with patch("backend.get_project", return_value=proj):
            resp = client.get("/api/projects/proj-001")
        body = resp.json()
        for field in ("project_id", "project_name", "current_step", "step_status"):
            assert field in body


class TestCreateProject:
    """POST /api/projects"""

    def test_create_project_success(self, client):
        proj = _project_dict()
        with patch("backend.create_project", return_value=proj):
            resp = client.post("/api/projects", json={
                "project_id": "proj-001",
                "project_name": "ECL Q4 2025",
            })
        assert resp.status_code == 200
        assert resp.json()["project_id"] == "proj-001"

    def test_create_project_with_all_fields(self, client):
        proj = _project_dict(description="Full", reporting_date="2025-12-31")
        with patch("backend.create_project", return_value=proj) as mock_fn:
            resp = client.post("/api/projects", json={
                "project_id": "proj-001",
                "project_name": "ECL Q4",
                "project_type": "ifrs9",
                "description": "Full",
                "reporting_date": "2025-12-31",
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(
            "proj-001", "ECL Q4", "ifrs9", "Full", "2025-12-31"
        )

    def test_create_project_defaults(self, client):
        """project_type defaults to ifrs9, description/reporting_date default to ''."""
        proj = _project_dict()
        with patch("backend.create_project", return_value=proj) as mock_fn:
            resp = client.post("/api/projects", json={
                "project_id": "p1",
                "project_name": "Test",
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("p1", "Test", "ifrs9", "", "")

    def test_create_project_missing_required_field(self, client):
        resp = client.post("/api/projects", json={"project_name": "NoId"})
        assert resp.status_code == 422


class TestAdvanceStep:
    """POST /api/projects/{project_id}/advance"""

    def test_advance_step_success(self, client):
        proj = _project_dict(current_step=2)
        with patch("backend.advance_step", return_value=proj):
            resp = client.post("/api/projects/proj-001/advance", json={
                "action": "data_processing",
                "user": "analyst",
            })
        assert resp.status_code == 200
        assert resp.json()["current_step"] == 2

    def test_advance_step_with_detail(self, client):
        proj = _project_dict()
        with patch("backend.advance_step", return_value=proj) as mock_fn:
            resp = client.post("/api/projects/proj-001/advance", json={
                "action": "data_processing",
                "user": "analyst",
                "detail": "Completed data load",
                "status": "completed",
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once()

    def test_advance_step_404_missing_project(self, client):
        with patch("backend.advance_step", side_effect=ValueError("Project not found")):
            resp = client.post("/api/projects/missing/advance", json={
                "action": "data_processing",
                "user": "analyst",
            })
        assert resp.status_code == 404

    def test_advance_step_missing_action_field(self, client):
        resp = client.post("/api/projects/p1/advance", json={"user": "a"})
        assert resp.status_code == 422


class TestSaveOverlays:
    """POST /api/projects/{project_id}/overlays"""

    def test_save_overlays_without_comment(self, client):
        proj = _project_dict(overlays=[{"id": "o1", "product": "mortgage",
                                         "type": "add", "amount": 1000,
                                         "reason": "test", "ifrs9": ""}])
        with patch("backend.save_overlays", return_value=proj):
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": [{
                    "id": "o1", "product": "mortgage",
                    "type": "add", "amount": 1000,
                    "reason": "test",
                }],
            })
        assert resp.status_code == 200

    def test_save_overlays_with_comment_advances_step(self, client):
        proj = _project_dict()
        with patch("backend.save_overlays", return_value=proj), \
             patch("backend.advance_step", return_value=proj) as adv:
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": [{
                    "id": "o1", "product": "personal",
                    "type": "add", "amount": 500,
                    "reason": "adjustment",
                }],
                "comment": "Approved by manager",
            })
        assert resp.status_code == 200
        adv.assert_called_once()

    def test_save_empty_overlays(self, client):
        proj = _project_dict(overlays=[])
        with patch("backend.save_overlays", return_value=proj):
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": [],
            })
        assert resp.status_code == 200


class TestSaveScenarioWeights:
    """POST /api/projects/{project_id}/scenario-weights"""

    def test_save_weights_success(self, client):
        proj = _project_dict(scenario_weights={"base": 0.5, "down": 0.3, "up": 0.2})
        with patch("backend.save_scenario_weights", return_value=proj) as mock_fn:
            resp = client.post("/api/projects/proj-001/scenario-weights", json={
                "weights": {"base": 0.5, "downside": 0.3, "upside": 0.2},
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("proj-001", {"base": 0.5, "downside": 0.3, "upside": 0.2})

    def test_save_empty_weights(self, client):
        proj = _project_dict(scenario_weights={})
        with patch("backend.save_scenario_weights", return_value=proj):
            resp = client.post("/api/projects/proj-001/scenario-weights", json={
                "weights": {},
            })
        assert resp.status_code == 200


class TestSignOff:
    """POST /api/projects/{project_id}/sign-off"""

    def test_sign_off_success(self, client):
        proj = _project_dict(signed_off_by=None, audit_log=[])
        signed = _project_dict(signed_off_by="CFO")
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "CFO",
            })
        assert resp.status_code == 200

    def test_sign_off_already_signed_returns_403(self, client):
        proj = _project_dict(signed_off_by="Auditor")
        proj["signed_off"] = True
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "CFO",
            })
        assert resp.status_code == 403
        assert "already signed off" in resp.json()["detail"]

    def test_sign_off_segregation_of_duties_violation(self, client):
        audit_log = [
            {"ts": "2025-01-01T00:00:00Z", "user": "Alice",
             "action": "model_execution", "detail": "", "step": "model_execution"},
        ]
        proj = _project_dict(audit_log=audit_log)
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Alice",
            })
        assert resp.status_code == 403
        assert "Segregation of duties" in resp.json()["detail"]

    def test_sign_off_with_attestation_data(self, client):
        proj = _project_dict(audit_log=[])
        signed = _project_dict(signed_off_by="CFO")
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed) as mock_fn:
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "CFO",
                "attestation_data": {"method": "digital_signature", "cert_id": "X123"},
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(
            "proj-001", "CFO",
            attestation_data={"method": "digital_signature", "cert_id": "X123"},
        )


class TestVerifyHash:
    """GET /api/projects/{project_id}/verify-hash"""

    def test_verify_hash_valid(self, client):
        proj = _project_dict(ecl_hash="abc123")
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=True), \
             patch("middleware.auth.compute_ecl_hash", return_value="abc123"):
            resp = client.get("/api/projects/proj-001/verify-hash")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "valid"
        assert body["match"] is True

    def test_verify_hash_invalid(self, client):
        proj = _project_dict(ecl_hash="abc123")
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=False), \
             patch("middleware.auth.compute_ecl_hash", return_value="xyz789"):
            resp = client.get("/api/projects/proj-001/verify-hash")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "invalid"
        assert body["match"] is False

    def test_verify_hash_no_hash_stored(self, client):
        proj = _project_dict(ecl_hash=None)
        with patch("backend.get_project", return_value=proj):
            resp = client.get("/api/projects/proj-001/verify-hash")
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_computed"

    def test_verify_hash_missing_project(self, client):
        with patch("backend.get_project", return_value=None):
            resp = client.get("/api/projects/missing/verify-hash")
        assert resp.status_code == 404


class TestApprovalHistory:
    """GET /api/projects/{project_id}/approval-history"""

    def test_approval_history_success(self, client):
        history = [{"id": 1, "action": "approve", "user": "CFO"}]
        with patch("governance.rbac.get_approval_history", return_value=history):
            resp = client.get("/api/projects/proj-001/approval-history")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert resp.json()[0]["action"] == "approve"

    def test_approval_history_empty(self, client):
        with patch("governance.rbac.get_approval_history", return_value=[]):
            resp = client.get("/api/projects/proj-001/approval-history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_approval_history_error_returns_500(self, client):
        with patch("governance.rbac.get_approval_history",
                   side_effect=Exception("RBAC service down")):
            resp = client.get("/api/projects/proj-001/approval-history")
        assert resp.status_code == 500


class TestResetProject:
    """POST /api/projects/{project_id}/reset"""

    def test_reset_success(self, client):
        proj = _project_dict(current_step=1)
        with patch("backend.reset_project", return_value=proj):
            resp = client.post("/api/projects/proj-001/reset")
        assert resp.status_code == 200
        assert resp.json()["current_step"] == 1

    def test_reset_error_returns_400(self, client):
        with patch("backend.reset_project", side_effect=Exception("Cannot reset")):
            resp = client.post("/api/projects/proj-001/reset")
        assert resp.status_code == 400


# ===================================================================
# DATA ROUTES — /api/data/*
# ===================================================================

# All simple GET endpoints that return df_to_records(backend.get_X())
_SIMPLE_DATA_ENDPOINTS = [
    ("/api/data/portfolio-summary", "get_portfolio_summary"),
    ("/api/data/stage-distribution", "get_stage_distribution"),
    ("/api/data/borrower-segments", "get_borrower_segment_stats"),
    ("/api/data/vintage-analysis", "get_vintage_analysis"),
    ("/api/data/dpd-distribution", "get_dpd_distribution"),
    ("/api/data/stage-by-product", "get_stage_by_product"),
    ("/api/data/pd-distribution", "get_pd_distribution"),
    ("/api/data/dq-results", "get_dq_results"),
    ("/api/data/dq-summary", "get_dq_summary"),
    ("/api/data/gl-reconciliation", "get_gl_reconciliation"),
    ("/api/data/ecl-summary", "get_ecl_summary"),
    ("/api/data/ecl-by-product", "get_ecl_by_product"),
    ("/api/data/scenario-summary", "get_scenario_summary"),
    ("/api/data/mc-distribution", "get_mc_distribution"),
    ("/api/data/ecl-by-scenario-product", "get_ecl_by_scenario_product"),
    ("/api/data/ecl-concentration", "get_ecl_concentration"),
    ("/api/data/stage-migration", "get_stage_migration"),
    ("/api/data/credit-risk-exposure", "get_credit_risk_exposure"),
    ("/api/data/loss-allowance-by-stage", "get_loss_allowance_by_stage"),
    ("/api/data/sensitivity", "get_sensitivity_data"),
    ("/api/data/scenario-comparison", "get_scenario_comparison"),
    ("/api/data/stress-by-stage", "get_stress_by_stage"),
    ("/api/data/vintage-performance", "get_vintage_performance"),
    ("/api/data/vintage-by-product", "get_vintage_by_product"),
    ("/api/data/concentration-by-segment", "get_concentration_by_segment"),
    ("/api/data/concentration-by-product-stage", "get_concentration_by_product_stage"),
    ("/api/data/top-concentration-risk", "get_top_concentration_risk"),
]


class TestDataEndpointsHappyPath:
    """Happy-path tests for all simple data GET endpoints."""

    @pytest.mark.parametrize("endpoint,backend_fn", _SIMPLE_DATA_ENDPOINTS)
    def test_returns_list_with_data(self, client, endpoint, backend_fn):
        with patch(f"backend.{backend_fn}", return_value=_SAMPLE_DF):
            resp = client.get(endpoint)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert "product_type" in data[0]

    @pytest.mark.parametrize("endpoint,backend_fn", _SIMPLE_DATA_ENDPOINTS)
    def test_returns_empty_list_for_empty_df(self, client, endpoint, backend_fn):
        with patch(f"backend.{backend_fn}", return_value=_EMPTY_DF):
            resp = client.get(endpoint)
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.parametrize("endpoint,backend_fn", _SIMPLE_DATA_ENDPOINTS)
    def test_returns_500_on_error(self, client, endpoint, backend_fn):
        with patch(f"backend.{backend_fn}", side_effect=Exception("db error")):
            resp = client.get(endpoint)
        assert resp.status_code == 500
        assert "Failed to load" in resp.json()["detail"]


class TestDataEndpointsParameterized:
    """Parameterized data endpoints with path/query params."""

    def test_ecl_by_stage_product_with_stage(self, client):
        df = pd.DataFrame({"product": ["mortgage"], "ecl": [100000.0]})
        with patch("backend.get_ecl_by_stage_product", return_value=df) as mock_fn:
            resp = client.get("/api/data/ecl-by-stage-product/2")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(2)

    def test_ecl_by_stage_product_stage_1(self, client):
        with patch("backend.get_ecl_by_stage_product", return_value=_SAMPLE_DF):
            resp = client.get("/api/data/ecl-by-stage-product/1")
        assert resp.status_code == 200

    def test_ecl_by_stage_product_stage_3(self, client):
        with patch("backend.get_ecl_by_stage_product", return_value=_SAMPLE_DF):
            resp = client.get("/api/data/ecl-by-stage-product/3")
        assert resp.status_code == 200

    def test_ecl_by_stage_product_error(self, client):
        with patch("backend.get_ecl_by_stage_product",
                   side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-by-stage-product/1")
        assert resp.status_code == 500

    def test_ecl_by_scenario_product_detail(self, client):
        df = pd.DataFrame({"product": ["mortgage"], "ecl": [50000.0]})
        with patch("backend.get_ecl_by_scenario_product_detail",
                   return_value=df) as mock_fn:
            resp = client.get("/api/data/ecl-by-scenario-product-detail",
                              params={"scenario": "base"})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("base")

    def test_ecl_by_scenario_product_detail_error(self, client):
        with patch("backend.get_ecl_by_scenario_product_detail",
                   side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-by-scenario-product-detail",
                              params={"scenario": "downside"})
        assert resp.status_code == 500

    def test_top_exposures_default_limit(self, client):
        df = pd.DataFrame({"loan_id": ["L1"], "exposure": [1_000_000.0]})
        with patch("backend.get_top_exposures", return_value=df) as mock_fn:
            resp = client.get("/api/data/top-exposures")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(20)

    def test_top_exposures_custom_limit(self, client):
        with patch("backend.get_top_exposures", return_value=_SAMPLE_DF) as mock_fn:
            resp = client.get("/api/data/top-exposures", params={"limit": 5})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(5)

    def test_top_exposures_error(self, client):
        with patch("backend.get_top_exposures", side_effect=Exception("db error")):
            resp = client.get("/api/data/top-exposures")
        assert resp.status_code == 500

    def test_loans_by_product(self, client):
        df = pd.DataFrame({"loan_id": ["L1"], "product_type": ["mortgage"]})
        with patch("backend.get_loans_by_product", return_value=df) as mock_fn:
            resp = client.get("/api/data/loans-by-product/mortgage")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("mortgage")

    def test_loans_by_product_error(self, client):
        with patch("backend.get_loans_by_product", side_effect=Exception("err")):
            resp = client.get("/api/data/loans-by-product/personal")
        assert resp.status_code == 500

    def test_loans_by_stage(self, client):
        df = pd.DataFrame({"loan_id": ["L1"], "stage": [1]})
        with patch("backend.get_loans_by_stage", return_value=df) as mock_fn:
            resp = client.get("/api/data/loans-by-stage/1")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(1)

    def test_loans_by_stage_error(self, client):
        with patch("backend.get_loans_by_stage", side_effect=Exception("err")):
            resp = client.get("/api/data/loans-by-stage/3")
        assert resp.status_code == 500


class TestDataEndpointsNaNHandling:
    """Verify NaN/Inf values in DataFrames are sanitized to null."""

    def test_nan_values_become_null(self, client):
        df = pd.DataFrame({"value": [1.0, float("nan"), 3.0]})
        with patch("backend.get_portfolio_summary", return_value=df):
            resp = client.get("/api/data/portfolio-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data[1]["value"] is None

    def test_inf_values_become_null(self, client):
        df = pd.DataFrame({"value": [float("inf"), float("-inf"), 5.0]})
        with patch("backend.get_ecl_summary", return_value=df):
            resp = client.get("/api/data/ecl-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["value"] is None
        assert data[1]["value"] is None
        assert data[2]["value"] == 5.0


# ===================================================================
# SETUP ROUTES — /api/setup/*
# ===================================================================

class TestSetupStatus:
    """GET /api/setup/status"""

    def test_status_success(self, client):
        status = {"setup_complete": True, "completed_by": "admin"}
        with patch("admin_config.get_setup_status", return_value=status):
            resp = client.get("/api/setup/status")
        assert resp.status_code == 200
        assert resp.json()["setup_complete"] is True

    def test_status_not_complete(self, client):
        status = {"setup_complete": False, "completed_by": None}
        with patch("admin_config.get_setup_status", return_value=status):
            resp = client.get("/api/setup/status")
        assert resp.status_code == 200
        assert resp.json()["setup_complete"] is False

    def test_status_error_returns_500(self, client):
        with patch("admin_config.get_setup_status",
                   side_effect=Exception("db unreachable")):
            resp = client.get("/api/setup/status")
        assert resp.status_code == 500


class TestSetupValidateTables:
    """POST /api/setup/validate-tables"""

    def test_validate_tables_success(self, client):
        result = {"valid": True, "missing": [], "found": ["loans", "scenarios"]}
        with patch("admin_config.validate_required_tables", return_value=result):
            resp = client.post("/api/setup/validate-tables")
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_validate_tables_with_missing(self, client):
        result = {"valid": False, "missing": ["ecl_results"], "found": ["loans"]}
        with patch("admin_config.validate_required_tables", return_value=result):
            resp = client.post("/api/setup/validate-tables")
        assert resp.status_code == 200
        assert resp.json()["valid"] is False
        assert "ecl_results" in resp.json()["missing"]

    def test_validate_tables_error_returns_500(self, client):
        with patch("admin_config.validate_required_tables",
                   side_effect=Exception("connection failed")):
            resp = client.post("/api/setup/validate-tables")
        assert resp.status_code == 500


class TestSetupSeedData:
    """POST /api/setup/seed-sample-data"""

    def test_seed_data_success(self, client):
        with patch("backend.ensure_tables"):
            resp = client.post("/api/setup/seed-sample-data")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_seed_data_error_returns_500(self, client):
        with patch("backend.ensure_tables",
                   side_effect=Exception("seed failed")):
            resp = client.post("/api/setup/seed-sample-data")
        assert resp.status_code == 500


class TestSetupComplete:
    """POST /api/setup/complete"""

    def test_complete_with_default_user(self, client):
        result = {"setup_complete": True, "completed_by": "admin"}
        with patch("admin_config.mark_setup_complete",
                   return_value=result) as mock_fn:
            resp = client.post("/api/setup/complete")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("admin")

    def test_complete_with_custom_user(self, client):
        result = {"setup_complete": True, "completed_by": "john"}
        with patch("admin_config.mark_setup_complete",
                   return_value=result) as mock_fn:
            resp = client.post("/api/setup/complete", json={"user": "john"})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("john")

    def test_complete_error_returns_500(self, client):
        with patch("admin_config.mark_setup_complete",
                   side_effect=Exception("db error")):
            resp = client.post("/api/setup/complete")
        assert resp.status_code == 500


class TestSetupReset:
    """POST /api/setup/reset"""

    def test_reset_success(self, client):
        result = {"setup_complete": False}
        with patch("admin_config.mark_setup_incomplete", return_value=result):
            resp = client.post("/api/setup/reset")
        assert resp.status_code == 200
        assert resp.json()["setup_complete"] is False

    def test_reset_error_returns_500(self, client):
        with patch("admin_config.mark_setup_incomplete",
                   side_effect=Exception("db error")):
            resp = client.post("/api/setup/reset")
        assert resp.status_code == 500


# ===================================================================
# ITERATION 2 — EDGE CASES & DEEPER COVERAGE
# ===================================================================

class TestSignOffEdgeCases:
    """Additional edge cases for sign-off endpoint discovered in iteration 2."""

    def test_sign_off_audit_log_as_json_string(self, client):
        """Bug path: audit_log stored as JSON string instead of list."""
        import json as _json
        audit_log_str = _json.dumps([
            {"ts": "2025-01-01T00:00:00Z", "user": "Bob",
             "action": "model_execution", "detail": "", "step": "model_execution"},
        ])
        proj = _project_dict(audit_log=audit_log_str)
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Bob",
            })
        assert resp.status_code == 403
        assert "Segregation of duties" in resp.json()["detail"]

    def test_sign_off_audit_log_as_invalid_json_string(self, client):
        """Edge case: audit_log is a string but not valid JSON — should not crash."""
        proj = _project_dict(audit_log="not-valid-json")
        signed = _project_dict(signed_off_by="Alice")
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Alice",
            })
        # Invalid JSON string for audit_log should be treated as empty list,
        # so no segregation check fires → sign-off succeeds
        assert resp.status_code == 200

    def test_sign_off_audit_log_empty_list(self, client):
        """Edge: empty audit_log with no model_execution entry → sign-off succeeds."""
        proj = _project_dict(audit_log=[])
        signed = _project_dict(signed_off_by="Alice")
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Alice",
            })
        assert resp.status_code == 200

    def test_sign_off_different_executor_and_signer(self, client):
        """Segregation passes when executor != signer."""
        audit_log = [
            {"ts": "2025-01-01T00:00:00Z", "user": "Bob",
             "action": "model_execution", "detail": "", "step": "model_execution"},
        ]
        proj = _project_dict(audit_log=audit_log)
        signed = _project_dict(signed_off_by="Alice")
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Alice",
            })
        assert resp.status_code == 200

    def test_sign_off_multiple_audit_entries_uses_last_executor(self, client):
        """The LAST model_execution entry determines the executor."""
        audit_log = [
            {"ts": "2025-01-01T00:00:00Z", "user": "Alice",
             "action": "model_execution", "detail": "", "step": "model_execution"},
            {"ts": "2025-02-01T00:00:00Z", "user": "Bob",
             "action": "model_execution", "detail": "Re-run", "step": "model_execution"},
        ]
        proj = _project_dict(audit_log=audit_log)
        # Bob is the LAST executor → signing as Bob should fail
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Bob",
            })
        assert resp.status_code == 403

        # Alice is NOT the last executor → signing as Alice should succeed
        signed = _project_dict(signed_off_by="Alice")
        with patch("routes.projects.require_permission", return_value=lambda: {"user": "admin"}), \
             patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=signed):
            resp = client.post("/api/projects/proj-001/sign-off", json={
                "name": "Alice",
            })
        assert resp.status_code == 200


class TestProjectCreateEdgeCases:
    """Iteration 2: more edge cases for project creation."""

    def test_create_project_with_empty_strings(self, client):
        """Explicitly pass empty strings for optional fields."""
        proj = _project_dict()
        with patch("backend.create_project", return_value=proj) as mock_fn:
            resp = client.post("/api/projects", json={
                "project_id": "p1",
                "project_name": "Test",
                "description": "",
                "reporting_date": "",
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("p1", "Test", "ifrs9", "", "")

    def test_create_project_with_different_type(self, client):
        """Non-default project_type."""
        proj = _project_dict(project_type="cecl")
        with patch("backend.create_project", return_value=proj) as mock_fn:
            resp = client.post("/api/projects", json={
                "project_id": "p1",
                "project_name": "CECL Proj",
                "project_type": "cecl",
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("p1", "CECL Proj", "cecl", "", "")


class TestAdvanceStepEdgeCases:
    """Iteration 2: edge cases for step advancement."""

    def test_advance_step_with_custom_status(self, client):
        proj = _project_dict()
        with patch("backend.advance_step", return_value=proj) as mock_fn:
            resp = client.post("/api/projects/proj-001/advance", json={
                "action": "data_processing",
                "user": "analyst",
                "status": "in_progress",
            })
        assert resp.status_code == 200
        call_args = mock_fn.call_args
        # Verify the status parameter is passed through
        assert call_args[0][5] == "in_progress"

    def test_advance_step_value_error_detail_in_response(self, client):
        """ValueError message should appear in 404 detail."""
        with patch("backend.advance_step",
                   side_effect=ValueError("No project with ID 'ghost'")):
            resp = client.post("/api/projects/ghost/advance", json={
                "action": "data_processing",
                "user": "analyst",
            })
        assert resp.status_code == 404
        assert "ghost" in resp.json()["detail"]


class TestVerifyHashEdgeCases:
    """Iteration 2: additional hash verification tests."""

    def test_verify_hash_response_shape(self, client):
        """Verify all expected fields in a valid hash response."""
        proj = _project_dict(ecl_hash="abc123", signed_off_by="CFO",
                             signed_off_at="2025-12-31T12:00:00Z")
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=True), \
             patch("middleware.auth.compute_ecl_hash", return_value="abc123"):
            resp = client.get("/api/projects/proj-001/verify-hash")
        body = resp.json()
        assert "status" in body
        assert "stored_hash" in body
        assert "computed_hash" in body
        assert "match" in body
        assert "signed_off_by" in body
        assert "signed_off_at" in body
        assert body["stored_hash"] == "abc123"
        assert body["signed_off_by"] == "CFO"

    def test_verify_hash_not_computed_shape(self, client):
        """Verify response shape when no hash is stored."""
        proj = _project_dict(ecl_hash=None)
        with patch("backend.get_project", return_value=proj):
            resp = client.get("/api/projects/proj-001/verify-hash")
        body = resp.json()
        assert body["status"] == "not_computed"
        assert "message" in body


class TestOverlayEdgeCases:
    """Iteration 2: edge cases for overlay saving."""

    def test_save_overlays_multiple_items(self, client):
        """Save multiple overlay items at once."""
        overlays = [
            {"id": "o1", "product": "mortgage", "type": "add", "amount": 1000, "reason": "adj1"},
            {"id": "o2", "product": "personal", "type": "subtract", "amount": 500, "reason": "adj2"},
            {"id": "o3", "product": "auto", "type": "add", "amount": 750, "reason": "adj3"},
        ]
        proj = _project_dict(overlays=overlays)
        with patch("backend.save_overlays", return_value=proj) as mock_fn:
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": overlays,
            })
        assert resp.status_code == 200
        # Verify all 3 overlays were passed through
        saved = mock_fn.call_args[0][1]
        assert len(saved) == 3

    def test_save_overlays_with_ifrs9_field(self, client):
        """The optional ifrs9 field should be preserved."""
        overlays = [{"id": "o1", "product": "mortgage", "type": "add",
                     "amount": 1000, "reason": "test", "ifrs9": "Stage 2 overlay"}]
        proj = _project_dict(overlays=overlays)
        with patch("backend.save_overlays", return_value=proj) as mock_fn:
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": overlays,
            })
        assert resp.status_code == 200
        saved_overlay = mock_fn.call_args[0][1][0]
        assert saved_overlay["ifrs9"] == "Stage 2 overlay"


class TestScenarioWeightsEdgeCases:
    """Iteration 2: edge cases for scenario weights."""

    def test_save_weights_with_three_scenarios(self, client):
        """Standard 3-scenario IFRS 9 setup."""
        weights = {"base": 0.50, "downside": 0.30, "upside": 0.20}
        proj = _project_dict(scenario_weights=weights)
        with patch("backend.save_scenario_weights", return_value=proj) as mock_fn:
            resp = client.post("/api/projects/proj-001/scenario-weights", json={
                "weights": weights,
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("proj-001", weights)

    def test_save_weights_single_scenario(self, client):
        """Edge: single scenario with weight 1.0."""
        weights = {"base": 1.0}
        proj = _project_dict(scenario_weights=weights)
        with patch("backend.save_scenario_weights", return_value=proj):
            resp = client.post("/api/projects/proj-001/scenario-weights", json={
                "weights": weights,
            })
        assert resp.status_code == 200


class TestDataEndpointsMissingParams:
    """Iteration 2: test parameterized endpoints with missing/invalid params."""

    def test_ecl_by_scenario_product_detail_missing_scenario(self, client):
        """Missing required query param 'scenario' → 422."""
        resp = client.get("/api/data/ecl-by-scenario-product-detail")
        assert resp.status_code == 422

    def test_ecl_by_stage_product_invalid_stage(self, client):
        """Non-integer stage value → 422."""
        resp = client.get("/api/data/ecl-by-stage-product/abc")
        assert resp.status_code == 422

    def test_loans_by_stage_invalid_stage(self, client):
        """Non-integer stage value → 422."""
        resp = client.get("/api/data/loans-by-stage/xyz")
        assert resp.status_code == 422

    def test_top_exposures_negative_limit(self, client):
        """Negative limit — should still call backend (no validation in route)."""
        with patch("backend.get_top_exposures", return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/top-exposures", params={"limit": -1})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(-1)

    def test_top_exposures_zero_limit(self, client):
        """Zero limit."""
        with patch("backend.get_top_exposures", return_value=_EMPTY_DF) as mock_fn:
            resp = client.get("/api/data/top-exposures", params={"limit": 0})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(0)


class TestDataEndpointsDecimalHandling:
    """Iteration 2: verify Decimal values in DataFrames are serialized to float."""

    def test_decimal_values_become_float(self, client):
        from decimal import Decimal as D
        df = pd.DataFrame({"amount": [D("1234.56"), D("7890.12")]})
        with patch("backend.get_portfolio_summary", return_value=df):
            resp = client.get("/api/data/portfolio-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["amount"] == 1234.56
        assert isinstance(data[0]["amount"], float)

    def test_datetime_values_serialized(self, client):
        df = pd.DataFrame({
            "date": [datetime(2025, 12, 31, 12, 0, 0)],
            "value": [42.0],
        })
        with patch("backend.get_ecl_summary", return_value=df):
            resp = client.get("/api/data/ecl-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "2025-12-31" in data[0]["date"]


class TestDataEndpointsErrorMessages:
    """Iteration 2: verify error detail messages are descriptive."""

    def test_portfolio_summary_error_has_descriptive_message(self, client):
        with patch("backend.get_portfolio_summary",
                   side_effect=Exception("connection timeout")):
            resp = client.get("/api/data/portfolio-summary")
        detail = resp.json()["detail"]
        assert "Failed to load" in detail
        assert "portfolio summary" in detail

    def test_ecl_by_stage_product_error_message(self, client):
        with patch("backend.get_ecl_by_stage_product",
                   side_effect=Exception("query failed")):
            resp = client.get("/api/data/ecl-by-stage-product/1")
        detail = resp.json()["detail"]
        assert "Failed to load" in detail
        assert "stage-product" in detail

    def test_top_exposures_error_message(self, client):
        with patch("backend.get_top_exposures",
                   side_effect=Exception("timeout")):
            resp = client.get("/api/data/top-exposures")
        detail = resp.json()["detail"]
        assert "Failed to load" in detail
        assert "top exposures" in detail


class TestDataEndpointsLargeDataFrame:
    """Iteration 2: test with larger DataFrames to verify no truncation."""

    def test_large_dataframe_all_rows_returned(self, client):
        """100-row DataFrame should return all 100 records."""
        df = pd.DataFrame({
            "loan_id": [f"L{i}" for i in range(100)],
            "amount": [float(i * 1000) for i in range(100)],
        })
        with patch("backend.get_portfolio_summary", return_value=df):
            resp = client.get("/api/data/portfolio-summary")
        assert resp.status_code == 200
        assert len(resp.json()) == 100

    def test_single_row_dataframe(self, client):
        """Single-row DataFrame."""
        df = pd.DataFrame({"metric": ["total_ecl"], "value": [123456.78]})
        with patch("backend.get_ecl_summary", return_value=df):
            resp = client.get("/api/data/ecl-summary")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestSetupEdgeCases:
    """Iteration 2: additional setup route edge cases."""

    def test_seed_data_returns_expected_shape(self, client):
        """Verify both 'status' and 'message' keys in response."""
        with patch("backend.ensure_tables"):
            resp = client.post("/api/setup/seed-sample-data")
        body = resp.json()
        assert "status" in body
        assert "message" in body
        assert body["status"] == "ok"

    def test_validate_tables_response_shape(self, client):
        """Verify response contains expected keys."""
        result = {"valid": True, "missing": [], "found": ["loans", "scenarios", "ecl_results"]}
        with patch("admin_config.validate_required_tables", return_value=result):
            resp = client.post("/api/setup/validate-tables")
        body = resp.json()
        assert "valid" in body
        assert "missing" in body
        assert "found" in body
        assert len(body["found"]) == 3

    def test_status_error_message_is_descriptive(self, client):
        """Error response should mention 'setup status'."""
        with patch("admin_config.get_setup_status",
                   side_effect=Exception("db unreachable")):
            resp = client.get("/api/setup/status")
        assert resp.status_code == 500
        assert "setup status" in resp.json()["detail"].lower()


class TestProjectListEdgeCases:
    """Iteration 2: additional project listing edge cases."""

    def test_list_projects_large_result(self, client):
        """50-project DataFrame returns all 50."""
        df = pd.DataFrame({
            "project_id": [f"p{i}" for i in range(50)],
            "project_name": [f"Project {i}" for i in range(50)],
            "project_type": ["ifrs9"] * 50,
            "current_step": [1] * 50,
            "created_at": ["2025-01-01"] * 50,
            "signed_off_by": [None] * 50,
        })
        with patch("backend.list_projects", return_value=df):
            resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 50

    def test_list_projects_with_signed_off_entries(self, client):
        """Projects with non-null signed_off_by values."""
        df = pd.DataFrame({
            "project_id": ["p1", "p2"],
            "project_name": ["Signed", "Open"],
            "project_type": ["ifrs9", "ifrs9"],
            "current_step": [8, 3],
            "created_at": ["2025-01-01", "2025-06-01"],
            "signed_off_by": ["CFO", None],
        })
        with patch("backend.list_projects", return_value=df):
            resp = client.get("/api/projects")
        data = resp.json()
        assert data[0]["signed_off_by"] == "CFO"
        assert data[1]["signed_off_by"] is None


class TestResetProjectEdgeCases:
    """Iteration 2: additional reset endpoint tests."""

    def test_reset_returns_project_at_step_1(self, client):
        """After reset, project should be at step 1 with clean state."""
        proj = _project_dict(current_step=1, overlays=[], scenario_weights={},
                             signed_off_by=None)
        with patch("backend.reset_project", return_value=proj):
            resp = client.post("/api/projects/proj-001/reset")
        body = resp.json()
        assert body["current_step"] == 1
        assert body["signed_off_by"] is None

    def test_reset_error_message_preserved(self, client):
        """Error message from backend is passed through in 400 response."""
        with patch("backend.reset_project",
                   side_effect=Exception("Cannot reset: project is locked")):
            resp = client.post("/api/projects/proj-001/reset")
        assert resp.status_code == 400
        assert "locked" in resp.json()["detail"]
