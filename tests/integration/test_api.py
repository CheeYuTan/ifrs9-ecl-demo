"""
Integration tests for the FastAPI IFRS 9 ECL API.

Uses FastAPI TestClient with a fully mocked backend to test all major
endpoint groups: health, projects, data, jobs, and simulation.
"""
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from conftest import PRODUCT_TYPES, MODEL_KEYS


@pytest.fixture
def client(mock_db):
    """FastAPI TestClient with backend mocked."""
    from fastapi.testclient import TestClient
    import app as app_module
    return TestClient(app_module.app)


@pytest.fixture
def _project_data():
    """Reusable project dict for workflow tests."""
    import backend
    step_status = {s: "pending" for s in backend.STEPS}
    step_status["create_project"] = "completed"
    return {
        "project_id": "test-001",
        "project_name": "Integration Test Project",
        "project_type": "ifrs9",
        "description": "For testing",
        "reporting_date": "2025-12-31",
        "current_step": 1,
        "step_status": step_status,
        "audit_log": [{"ts": datetime.now(timezone.utc).isoformat(),
                        "user": "Tester", "action": "Created", "detail": "init"}],
        "overlays": [],
        "scenario_weights": {},
        "signed_off_by": None,
        "signed_off_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


class TestHealthEndpoint:
    """GET /api/health"""

    def test_healthy_when_db_works(self, client, mock_db):
        mock_db["query_df"].return_value = pd.DataFrame({"ok": [1]})
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["lakebase"] == "connected"

    def test_degraded_when_db_fails(self, client, mock_db):
        mock_db["query_df"].side_effect = Exception("Connection refused")
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert "error" in data


class TestProjectEndpoints:
    """POST /api/projects, GET /api/projects, GET /api/projects/{id}"""

    def test_create_project(self, client, mock_db, _project_data):
        with patch("backend.create_project", return_value=_project_data):
            resp = client.post("/api/projects", json={
                "project_id": "test-001",
                "project_name": "Integration Test Project",
                "project_type": "ifrs9",
                "description": "For testing",
                "reporting_date": "2025-12-31",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "test-001"

    def test_list_projects(self, client, mock_db):
        mock_db["query_df"].return_value = pd.DataFrame({
            "project_id": ["p1", "p2"],
            "project_name": ["Project 1", "Project 2"],
            "project_type": ["ifrs9", "ifrs9"],
            "current_step": [1, 3],
            "created_at": ["2025-01-01", "2025-02-01"],
            "signed_off_by": [None, "Auditor"],
        })
        with patch("backend.list_projects", return_value=mock_db["query_df"].return_value):
            resp = client.get("/api/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_get_project_found(self, client, mock_db, _project_data):
        with patch("backend.get_project", return_value=_project_data):
            resp = client.get("/api/projects/test-001")
        assert resp.status_code == 200
        assert resp.json()["project_id"] == "test-001"

    def test_get_project_not_found(self, client, mock_db):
        with patch("backend.get_project", return_value=None):
            resp = client.get("/api/projects/nonexistent")
        assert resp.status_code == 404

    def test_advance_step(self, client, mock_db, _project_data):
        advanced = {**_project_data, "current_step": 2}
        with patch("backend.advance_step", return_value=advanced):
            resp = client.post("/api/projects/test-001/advance", json={
                "action": "data_processing",
                "user": "Analyst",
                "detail": "Data loaded",
            })
        assert resp.status_code == 200
        assert resp.json()["current_step"] == 2

    def test_advance_step_missing_project(self, client, mock_db):
        with patch("backend.advance_step", side_effect=ValueError("Project missing not found")):
            resp = client.post("/api/projects/missing/advance", json={
                "action": "data_processing",
                "user": "Analyst",
            })
        assert resp.status_code == 404

    def test_sign_off(self, client, mock_db, _project_data):
        signed = {**_project_data, "signed_off_by": "CFO"}
        with patch("backend.get_project", return_value=_project_data), \
             patch("backend.sign_off_project", return_value=signed):
            resp = client.post("/api/projects/test-001/sign-off", json={"name": "CFO"})
        assert resp.status_code == 200
        assert resp.json()["signed_off_by"] == "CFO"


class TestDataEndpoints:
    """Test data query endpoints return proper JSON arrays."""

    @pytest.mark.parametrize("endpoint,backend_fn", [
        ("/api/data/portfolio-summary", "get_portfolio_summary"),
        ("/api/data/stage-distribution", "get_stage_distribution"),
        ("/api/data/borrower-segments", "get_borrower_segment_stats"),
        ("/api/data/vintage-analysis", "get_vintage_analysis"),
        ("/api/data/dpd-distribution", "get_dpd_distribution"),
        ("/api/data/ecl-summary", "get_ecl_summary"),
        ("/api/data/scenario-summary", "get_scenario_summary"),
        ("/api/data/mc-distribution", "get_mc_distribution"),
        ("/api/data/stage-migration", "get_stage_migration"),
        ("/api/data/sensitivity", "get_sensitivity_data"),
    ])
    def test_data_endpoint_returns_list(self, client, mock_db, endpoint, backend_fn):
        fake_df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        with patch(f"backend.{backend_fn}", return_value=fake_df):
            resp = client.get(endpoint)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_portfolio_summary_500_on_error(self, client, mock_db):
        with patch("backend.get_portfolio_summary", side_effect=Exception("DB down")):
            resp = client.get("/api/data/portfolio-summary")
        assert resp.status_code == 500

    def test_top_exposures_with_limit(self, client, mock_db):
        fake_df = pd.DataFrame({
            "loan_id": [f"LN-{i}" for i in range(5)],
            "gca": [10000] * 5,
        })
        with patch("backend.get_top_exposures", return_value=fake_df) as mock_fn:
            resp = client.get("/api/data/top-exposures?limit=5")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(5)

    def test_loans_by_product(self, client, mock_db):
        product = PRODUCT_TYPES[0]
        fake_df = pd.DataFrame({"loan_id": ["LN-001"], "gca": [5000]})
        with patch("backend.get_loans_by_product", return_value=fake_df) as mock_fn:
            resp = client.get(f"/api/data/loans-by-product/{product}")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(product)

    def test_loans_by_stage(self, client, mock_db):
        fake_df = pd.DataFrame({"loan_id": ["LN-001"], "stage": [2]})
        with patch("backend.get_loans_by_stage", return_value=fake_df) as mock_fn:
            resp = client.get("/api/data/loans-by-stage/2")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(2)


class TestSatelliteModelEndpoints:
    """Test satellite model comparison and selection endpoints."""

    def test_satellite_model_comparison_no_run_id(self, client, mock_db):
        product = PRODUCT_TYPES[0]
        model = MODEL_KEYS[0]
        fake_df = pd.DataFrame({
            "product_type": [product],
            "model_type": [model],
            "r_squared": [0.85],
        })
        with patch("backend.get_satellite_model_comparison", return_value=fake_df) as mock_fn:
            resp = client.get("/api/data/satellite-model-comparison")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_satellite_model_comparison_with_run_id(self, client, mock_db):
        product = PRODUCT_TYPES[0]
        fake_df = pd.DataFrame({"product_type": [product]})
        with patch("backend.get_satellite_model_comparison", return_value=fake_df) as mock_fn:
            resp = client.get("/api/data/satellite-model-comparison?run_id=2025-06-15")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("2025-06-15")


class TestJobEndpoints:
    """Test Databricks Jobs trigger and status endpoints."""

    def test_trigger_satellite_job(self, client, mock_db):
        with patch("jobs.trigger_satellite_ecl_job", return_value={
            "run_id": 12345, "job_id": 999, "models": ["linear_regression"],
            "run_url": "https://example.com/run/12345",
        }):
            resp = client.post("/api/jobs/trigger", json={"job_key": "satellite_ecl_sync"})
        assert resp.status_code == 200
        assert resp.json()["run_id"] == 12345

    def test_trigger_full_pipeline(self, client, mock_db):
        with patch("jobs.trigger_full_pipeline", return_value={
            "run_id": 67890, "job_id": 888,
            "run_url": "https://example.com/run/67890",
        }):
            resp = client.post("/api/jobs/trigger", json={"job_key": "full_pipeline"})
        assert resp.status_code == 200
        assert resp.json()["run_id"] == 67890

    def test_trigger_unknown_job_key(self, client, mock_db):
        resp = client.post("/api/jobs/trigger", json={"job_key": "nonexistent"})
        assert resp.status_code == 400

    def test_get_run_status(self, client, mock_db):
        with patch("jobs.get_run_status", return_value={
            "run_id": 12345, "lifecycle_state": "TERMINATED",
            "result_state": "SUCCESS", "tasks": [],
        }):
            resp = client.get("/api/jobs/run/12345")
        assert resp.status_code == 200
        assert resp.json()["lifecycle_state"] == "TERMINATED"

    def test_get_jobs_config(self, client, mock_db):
        resp = client.get("/api/jobs/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "available_models" in data
        assert "job_ids" in data
        assert len(data["available_models"]) == len(MODEL_KEYS)

    def test_list_job_runs(self, client, mock_db):
        with patch("jobs.list_job_runs", return_value=[
            {"run_id": 1, "lifecycle_state": "TERMINATED"},
        ]):
            resp = client.get("/api/jobs/runs/satellite_ecl_sync?limit=5")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestSimulationEndpoints:
    """Test simulation validation and defaults endpoints."""

    def test_validate_simulation_valid(self, client, mock_db):
        resp = client.post("/api/simulate-validate", json={
            "n_simulations": 1000,
            "pd_lgd_correlation": 0.30,
            "pd_floor": 0.001,
            "pd_cap": 0.95,
            "lgd_floor": 0.01,
            "lgd_cap": 0.95,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0

    def test_validate_simulation_invalid_pd_range(self, client, mock_db):
        resp = client.post("/api/simulate-validate", json={
            "n_simulations": 1000,
            "pd_floor": 0.95,
            "pd_cap": 0.001,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert any("PD Floor" in e for e in data["errors"])

    def test_validate_simulation_too_few_sims(self, client, mock_db):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 50})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert any("100" in e for e in data["errors"])

    def test_validate_simulation_too_many_sims(self, client, mock_db):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 60000})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False

    def test_validate_scenario_weights_not_summing(self, client, mock_db):
        resp = client.post("/api/simulate-validate", json={
            "n_simulations": 1000,
            "scenario_weights": {"baseline": 0.50, "adverse": 0.20},
        })
        data = resp.json()
        assert data["valid"] is False
        assert any("weights" in e.lower() for e in data["errors"])

    def test_validate_warnings_for_high_sims(self, client, mock_db):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 3000})
        data = resp.json()
        assert len(data["warnings"]) > 0

    def test_validate_returns_estimates(self, client, mock_db):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 1000})
        data = resp.json()
        assert "estimated_seconds" in data
        assert "estimated_memory_mb" in data
        assert data["estimated_seconds"] > 0

    def test_simulation_defaults(self, client, mock_db):
        defaults = {
            "scenarios": [{"scenario": "baseline", "weight": 0.30}],
            "default_weights": {"baseline": 0.30},
            "products": [{"product_type": "credit_builder", "base_lgd": 0.35}],
            "default_params": {
                "n_sims": 1000, "pd_lgd_correlation": 0.30,
                "aging_factor": 0.08, "pd_floor": 0.001, "pd_cap": 0.95,
                "lgd_floor": 0.01, "lgd_cap": 0.95,
            },
        }
        with patch("ecl_engine.get_defaults", return_value=defaults):
            resp = client.get("/api/simulation-defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert data["n_simulations"] == 1000
        assert "scenario_weights" in data
