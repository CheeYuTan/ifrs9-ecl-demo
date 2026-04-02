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
