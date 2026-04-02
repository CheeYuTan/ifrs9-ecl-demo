"""
QA Sprint 4 — Advanced Features & Period Close Pipeline Endpoints.

Tests routes/advanced.py (9 endpoints) and routes/period_close.py (7 endpoints)
with mocked backend/domain modules.
"""
import json
from decimal import Decimal
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


def _cure_result(**overrides):
    base = {
        "analysis_id": "CURE-001",
        "product_type": "mortgage",
        "segment": "retail",
        "observation_period": "2024Q1-2025Q4",
        "cure_rates": {
            "by_dpd": [
                {"dpd_bucket": "1-30 DPD", "cure_rate": 0.72, "sample_size": 500},
                {"dpd_bucket": "31-60 DPD", "cure_rate": 0.45, "sample_size": 300},
            ],
        },
        "methodology": "observed",
        "created_at": "2025-12-31T00:00:00",
    }
    base.update(overrides)
    return base


def _ccf_result(**overrides):
    base = {
        "analysis_id": "CCF-001",
        "product_type": "credit_card",
        "ccf_by_stage": {"stage_1": 0.85, "stage_2": 0.65, "stage_3": 0.95},
        "ccf_by_utilization": [
            {"utilization_band": "0-25%", "ccf": 0.20},
            {"utilization_band": "25-50%", "ccf": 0.45},
        ],
        "methodology": "observed",
        "created_at": "2025-12-31T00:00:00",
    }
    base.update(overrides)
    return base


def _collateral_result(**overrides):
    base = {
        "analysis_id": "COL-001",
        "collateral_type": "residential_property",
        "haircut_pct": 20.0,
        "recovery_rate": 0.65,
        "time_to_recovery_months": 18.0,
        "methodology": "observed",
        "created_at": "2025-12-31T00:00:00",
    }
    base.update(overrides)
    return base


def _pipeline_run(**overrides):
    steps = [
        {"key": "data_freshness", "label": "Data Freshness Check", "order": 1,
         "status": "pending", "started_at": None, "completed_at": None,
         "duration_seconds": None, "error": None},
        {"key": "data_quality", "label": "Data Quality Validation", "order": 2,
         "status": "pending", "started_at": None, "completed_at": None,
         "duration_seconds": None, "error": None},
        {"key": "model_execution", "label": "Model Execution", "order": 3,
         "status": "pending", "started_at": None, "completed_at": None,
         "duration_seconds": None, "error": None},
        {"key": "ecl_calculation", "label": "ECL Calculation", "order": 4,
         "status": "pending", "started_at": None, "completed_at": None,
         "duration_seconds": None, "error": None},
        {"key": "report_generation", "label": "Report Generation", "order": 5,
         "status": "pending", "started_at": None, "completed_at": None,
         "duration_seconds": None, "error": None},
        {"key": "attribution", "label": "Attribution Computation", "order": 6,
         "status": "pending", "started_at": None, "completed_at": None,
         "duration_seconds": None, "error": None},
    ]
    base = {
        "run_id": "PIPE-proj-001-20251231120000",
        "project_id": "proj-001",
        "status": "running",
        "started_at": "2025-12-31T12:00:00",
        "completed_at": None,
        "duration_seconds": None,
        "steps": steps,
        "error_message": None,
        "triggered_by": "system",
    }
    base.update(overrides)
    return base


# ===================================================================
# ADVANCED ROUTES — /api/advanced/*
# ===================================================================

# --- Cure Rates ---

class TestComputeCureRates:
    """POST /api/advanced/cure-rates/compute"""

    def test_compute(self, client):
        with patch("backend.compute_cure_rates", return_value=_cure_result()):
            resp = client.post("/api/advanced/cure-rates/compute", json={})
        assert resp.status_code == 200
        assert resp.json()["analysis_id"] == "CURE-001"

    def test_compute_with_product(self, client):
        with patch("backend.compute_cure_rates", return_value=_cure_result()) as mock:
            resp = client.post("/api/advanced/cure-rates/compute",
                               json={"product_type": "mortgage"})
        assert resp.status_code == 200
        mock.assert_called_once_with("mortgage")

    def test_compute_no_product(self, client):
        with patch("backend.compute_cure_rates", return_value=_cure_result()) as mock:
            resp = client.post("/api/advanced/cure-rates/compute", json={})
        mock.assert_called_once_with(None)

    def test_compute_exception(self, client):
        with patch("backend.compute_cure_rates", side_effect=RuntimeError("fail")):
            resp = client.post("/api/advanced/cure-rates/compute", json={})
        assert resp.status_code == 500


class TestListCureAnalyses:
    """GET /api/advanced/cure-rates"""

    def test_list(self, client):
        with patch("backend.list_cure_analyses", return_value=[_cure_result()]):
            resp = client.get("/api/advanced/cure-rates")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_empty(self, client):
        with patch("backend.list_cure_analyses", return_value=[]):
            resp = client.get("/api/advanced/cure-rates")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_exception(self, client):
        with patch("backend.list_cure_analyses", side_effect=RuntimeError("fail")):
            resp = client.get("/api/advanced/cure-rates")
        assert resp.status_code == 500


class TestGetCureAnalysis:
    """GET /api/advanced/cure-rates/{analysis_id}"""

    def test_get(self, client):
        with patch("backend.get_cure_analysis", return_value=_cure_result()):
            resp = client.get("/api/advanced/cure-rates/CURE-001")
        assert resp.status_code == 200
        assert resp.json()["analysis_id"] == "CURE-001"

    def test_not_found(self, client):
        with patch("backend.get_cure_analysis", return_value=None):
            resp = client.get("/api/advanced/cure-rates/MISSING")
        assert resp.status_code == 404

    def test_exception(self, client):
        with patch("backend.get_cure_analysis", side_effect=RuntimeError("fail")):
            resp = client.get("/api/advanced/cure-rates/CURE-001")
        assert resp.status_code == 500


# --- CCF ---

class TestComputeCCF:
    """POST /api/advanced/ccf/compute"""

    def test_compute(self, client):
        with patch("backend.compute_ccf", return_value=_ccf_result()):
            resp = client.post("/api/advanced/ccf/compute", json={})
        assert resp.status_code == 200
        assert resp.json()["analysis_id"] == "CCF-001"

    def test_compute_with_product(self, client):
        with patch("backend.compute_ccf", return_value=_ccf_result()) as mock:
            resp = client.post("/api/advanced/ccf/compute",
                               json={"product_type": "credit_card"})
        mock.assert_called_once_with("credit_card")

    def test_compute_exception(self, client):
        with patch("backend.compute_ccf", side_effect=RuntimeError("fail")):
            resp = client.post("/api/advanced/ccf/compute", json={})
        assert resp.status_code == 500


class TestListCCFAnalyses:
    """GET /api/advanced/ccf"""

    def test_list(self, client):
        with patch("backend.list_ccf_analyses", return_value=[_ccf_result()]):
            resp = client.get("/api/advanced/ccf")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_exception(self, client):
        with patch("backend.list_ccf_analyses", side_effect=RuntimeError("fail")):
            resp = client.get("/api/advanced/ccf")
        assert resp.status_code == 500


class TestGetCCFAnalysis:
    """GET /api/advanced/ccf/{analysis_id}"""

    def test_get(self, client):
        with patch("backend.get_ccf_analysis", return_value=_ccf_result()):
            resp = client.get("/api/advanced/ccf/CCF-001")
        assert resp.status_code == 200

    def test_not_found(self, client):
        with patch("backend.get_ccf_analysis", return_value=None):
            resp = client.get("/api/advanced/ccf/MISSING")
        assert resp.status_code == 404

    def test_exception(self, client):
        with patch("backend.get_ccf_analysis", side_effect=RuntimeError("fail")):
            resp = client.get("/api/advanced/ccf/CCF-001")
        assert resp.status_code == 500


# --- Collateral ---

class TestComputeCollateral:
    """POST /api/advanced/collateral/compute"""

    def test_compute(self, client):
        with patch("backend.compute_collateral_haircuts", return_value=_collateral_result()):
            resp = client.post("/api/advanced/collateral/compute", json={})
        assert resp.status_code == 200
        assert resp.json()["analysis_id"] == "COL-001"

    def test_compute_with_product(self, client):
        with patch("backend.compute_collateral_haircuts", return_value=_collateral_result()) as mock:
            resp = client.post("/api/advanced/collateral/compute",
                               json={"product_type": "mortgage"})
        mock.assert_called_once_with("mortgage")

    def test_compute_exception(self, client):
        with patch("backend.compute_collateral_haircuts", side_effect=RuntimeError("fail")):
            resp = client.post("/api/advanced/collateral/compute", json={})
        assert resp.status_code == 500


class TestListCollateralAnalyses:
    """GET /api/advanced/collateral"""

    def test_list(self, client):
        with patch("backend.list_collateral_analyses", return_value=[_collateral_result()]):
            resp = client.get("/api/advanced/collateral")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_exception(self, client):
        with patch("backend.list_collateral_analyses", side_effect=RuntimeError("fail")):
            resp = client.get("/api/advanced/collateral")
        assert resp.status_code == 500


class TestGetCollateralAnalysis:
    """GET /api/advanced/collateral/{analysis_id}"""

    def test_get(self, client):
        with patch("backend.get_collateral_analysis", return_value=_collateral_result()):
            resp = client.get("/api/advanced/collateral/COL-001")
        assert resp.status_code == 200

    def test_not_found(self, client):
        with patch("backend.get_collateral_analysis", return_value=None):
            resp = client.get("/api/advanced/collateral/MISSING")
        assert resp.status_code == 404

    def test_exception(self, client):
        with patch("backend.get_collateral_analysis", side_effect=RuntimeError("fail")):
            resp = client.get("/api/advanced/collateral/COL-001")
        assert resp.status_code == 500


# ===================================================================
# PERIOD CLOSE PIPELINE ROUTES — /api/pipeline/*
# ===================================================================

class TestStartPipeline:
    """POST /api/pipeline/start/{project_id}"""

    def test_start(self, client):
        run = _pipeline_run()
        with patch("routes.period_close.start_pipeline", return_value=run):
            resp = client.post("/api/pipeline/start/proj-001", json={"triggered_by": "admin"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert len(data["steps"]) == 6

    def test_start_default_user(self, client):
        with patch("routes.period_close.start_pipeline", return_value=_pipeline_run()) as mock:
            resp = client.post("/api/pipeline/start/proj-001", json={})
        mock.assert_called_once_with("proj-001", "system")

    def test_start_exception(self, client):
        with patch("routes.period_close.start_pipeline", side_effect=RuntimeError("fail")):
            resp = client.post("/api/pipeline/start/proj-001", json={})
        assert resp.status_code == 500


class TestListPipelineSteps:
    """GET /api/pipeline/steps"""

    def test_list_steps(self, client):
        resp = client.get("/api/pipeline/steps")
        assert resp.status_code == 200
        steps = resp.json()
        assert len(steps) == 6
        keys = [s["key"] for s in steps]
        assert "data_freshness" in keys
        assert "ecl_calculation" in keys
        assert "attribution" in keys

    def test_steps_ordered(self, client):
        resp = client.get("/api/pipeline/steps")
        steps = resp.json()
        orders = [s["order"] for s in steps]
        assert orders == sorted(orders)


class TestGetPipelineRun:
    """GET /api/pipeline/run/{run_id}"""

    def test_get_run(self, client):
        with patch("routes.period_close.get_pipeline_run", return_value=_pipeline_run()):
            resp = client.get("/api/pipeline/run/PIPE-001")
        assert resp.status_code == 200
        assert resp.json()["run_id"] == "PIPE-proj-001-20251231120000"

    def test_run_not_found(self, client):
        with patch("routes.period_close.get_pipeline_run", return_value=None):
            resp = client.get("/api/pipeline/run/MISSING")
        assert resp.status_code == 404


class TestExecuteStep:
    """POST /api/pipeline/run/{run_id}/execute-step"""

    def test_execute_step(self, client):
        step_result = {"key": "data_freshness", "status": "completed", "duration_seconds": 1.5}
        with patch("routes.period_close.get_pipeline_run", return_value=_pipeline_run()), \
             patch("routes.period_close.execute_step", return_value=step_result):
            resp = client.post("/api/pipeline/run/PIPE-001/execute-step",
                               json={"step_key": "data_freshness"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_invalid_step_key_returns_400(self, client):
        resp = client.post("/api/pipeline/run/PIPE-001/execute-step",
                           json={"step_key": "nonexistent_step"})
        assert resp.status_code == 400
        assert "Invalid step key" in resp.json()["detail"]

    def test_run_not_found_returns_404(self, client):
        with patch("routes.period_close.get_pipeline_run", return_value=None):
            resp = client.post("/api/pipeline/run/MISSING/execute-step",
                               json={"step_key": "data_freshness"})
        assert resp.status_code == 404

    def test_step_failure(self, client):
        step_result = {"key": "data_quality", "status": "failed",
                       "error": "DQ checks failed", "duration_seconds": 0.5}
        with patch("routes.period_close.get_pipeline_run", return_value=_pipeline_run()), \
             patch("routes.period_close.execute_step", return_value=step_result):
            resp = client.post("/api/pipeline/run/PIPE-001/execute-step",
                               json={"step_key": "data_quality"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "failed"

    def test_step_exception(self, client):
        with patch("routes.period_close.get_pipeline_run", return_value=_pipeline_run()), \
             patch("routes.period_close.execute_step", side_effect=RuntimeError("crash")):
            resp = client.post("/api/pipeline/run/PIPE-001/execute-step",
                               json={"step_key": "data_freshness"})
        assert resp.status_code == 500


class TestCompletePipeline:
    """POST /api/pipeline/run/{run_id}/complete"""

    def test_complete_success(self, client):
        run = _pipeline_run()
        for s in run["steps"]:
            s["status"] = "completed"
        completed_run = {**run, "status": "completed"}
        with patch("routes.period_close.get_pipeline_run", side_effect=[run, completed_run]), \
             patch("routes.period_close.complete_pipeline"):
            resp = client.post("/api/pipeline/run/PIPE-001/complete")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_complete_with_failed_steps(self, client):
        run = _pipeline_run()
        run["steps"][1]["status"] = "failed"  # data_quality failed
        failed_run = {**run, "status": "failed"}
        with patch("routes.period_close.get_pipeline_run", side_effect=[run, failed_run]), \
             patch("routes.period_close.complete_pipeline") as mock_complete:
            resp = client.post("/api/pipeline/run/PIPE-001/complete")
        assert resp.status_code == 200
        call_args = mock_complete.call_args
        assert call_args[1].get("status") or call_args[0][1] == "failed"

    def test_complete_not_found(self, client):
        with patch("routes.period_close.get_pipeline_run", return_value=None):
            resp = client.post("/api/pipeline/run/MISSING/complete")
        assert resp.status_code == 404

    def test_complete_exception(self, client):
        run = _pipeline_run()
        with patch("routes.period_close.get_pipeline_run", return_value=run), \
             patch("routes.period_close.complete_pipeline", side_effect=RuntimeError("fail")):
            resp = client.post("/api/pipeline/run/PIPE-001/complete")
        assert resp.status_code == 500


class TestPipelineHealth:
    """GET /api/pipeline/health/{project_id}"""

    def test_health(self, client):
        health = {
            "last_run": _pipeline_run(status="completed"),
            "total_runs": 3,
            "last_status": "completed",
            "last_duration": 45.2,
            "recent_runs": [_pipeline_run(status="completed")],
        }
        with patch("routes.period_close.get_pipeline_health", return_value=health):
            resp = client.get("/api/pipeline/health/proj-001")
        assert resp.status_code == 200
        assert resp.json()["total_runs"] == 3

    def test_health_no_runs(self, client):
        with patch("routes.period_close.get_pipeline_health",
                   return_value={"last_run": None, "total_runs": 0, "status": "no_runs"}):
            resp = client.get("/api/pipeline/health/proj-001")
        assert resp.status_code == 200
        assert resp.json()["total_runs"] == 0


class TestRunFullPipeline:
    """POST /api/pipeline/run-all/{project_id}"""

    def test_run_all_success(self, client):
        run = _pipeline_run()
        completed_run = {**run, "status": "completed"}
        step_ok = {"status": "completed", "duration_seconds": 1.0, "message": "ok"}
        with patch("routes.period_close.start_pipeline", return_value=run), \
             patch("routes.period_close.execute_step", return_value=step_ok), \
             patch("routes.period_close.complete_pipeline"), \
             patch("routes.period_close.get_pipeline_run", return_value=completed_run):
            resp = client.post("/api/pipeline/run-all/proj-001", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert "step_results" in data

    def test_run_all_stops_on_failure(self, client):
        run = _pipeline_run()
        failed_run = {**run, "status": "failed"}
        call_count = [0]

        def mock_execute(run_id, step_key):
            call_count[0] += 1
            if step_key == "data_quality":
                return {"status": "failed", "error": "DQ checks failed"}
            return {"status": "completed", "message": "ok"}

        with patch("routes.period_close.start_pipeline", return_value=run), \
             patch("routes.period_close.execute_step", side_effect=mock_execute), \
             patch("routes.period_close.complete_pipeline"), \
             patch("routes.period_close.get_pipeline_run", return_value=failed_run):
            resp = client.post("/api/pipeline/run-all/proj-001", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        # Should have stopped at step 2 (data_quality)
        assert call_count[0] == 2

    def test_run_all_exception(self, client):
        with patch("routes.period_close.start_pipeline", side_effect=RuntimeError("fail")):
            resp = client.post("/api/pipeline/run-all/proj-001", json={})
        assert resp.status_code == 500


# ===================================================================
# PIPELINE — Step ordering & all-steps validation
# ===================================================================

class TestPipelineStepOrdering:
    """Verify pipeline steps follow correct execution order."""

    def test_all_six_steps_present(self, client):
        resp = client.get("/api/pipeline/steps")
        steps = resp.json()
        expected_keys = [
            "data_freshness", "data_quality", "model_execution",
            "ecl_calculation", "report_generation", "attribution",
        ]
        actual_keys = [s["key"] for s in steps]
        assert actual_keys == expected_keys

    @pytest.mark.parametrize("step_key", [
        "data_freshness", "data_quality", "model_execution",
        "ecl_calculation", "report_generation", "attribution",
    ])
    def test_each_valid_step_accepted(self, client, step_key):
        step_result = {"key": step_key, "status": "completed", "duration_seconds": 1.0}
        with patch("routes.period_close.get_pipeline_run", return_value=_pipeline_run()), \
             patch("routes.period_close.execute_step", return_value=step_result):
            resp = client.post("/api/pipeline/run/PIPE-001/execute-step",
                               json={"step_key": step_key})
        assert resp.status_code == 200


# ===================================================================
# ADVANCED — Domain-level cure rate validations
# ===================================================================

class TestCureRateDomainValidation:
    """Cure rates should be between 0 and 1 and decrease with DPD severity."""

    def test_cure_rates_bounded(self, client):
        result = _cure_result()
        with patch("backend.compute_cure_rates", return_value=result):
            resp = client.post("/api/advanced/cure-rates/compute", json={})
        data = resp.json()
        for entry in data["cure_rates"]["by_dpd"]:
            assert 0 <= entry["cure_rate"] <= 1, \
                f"Cure rate {entry['cure_rate']} out of [0,1] for {entry['dpd_bucket']}"

    def test_cure_rates_decrease_with_dpd(self, client):
        result = _cure_result()
        with patch("backend.compute_cure_rates", return_value=result):
            resp = client.post("/api/advanced/cure-rates/compute", json={})
        rates = resp.json()["cure_rates"]["by_dpd"]
        if len(rates) >= 2:
            assert rates[0]["cure_rate"] >= rates[-1]["cure_rate"], \
                "Cure rates should generally decrease with DPD severity"


class TestCCFDomainValidation:
    """CCF values should be between 0 and 1."""

    def test_ccf_by_stage_bounded(self, client):
        result = _ccf_result()
        with patch("backend.compute_ccf", return_value=result):
            resp = client.post("/api/advanced/ccf/compute", json={})
        for stage, ccf in resp.json()["ccf_by_stage"].items():
            assert 0 <= ccf <= 1, f"CCF {ccf} out of [0,1] for {stage}"


class TestCollateralDomainValidation:
    """Collateral haircuts and recovery rates should be bounded."""

    def test_haircut_bounded(self, client):
        result = _collateral_result()
        with patch("backend.compute_collateral_haircuts", return_value=result):
            resp = client.post("/api/advanced/collateral/compute", json={})
        data = resp.json()
        assert 0 <= data["haircut_pct"] <= 100
        assert 0 <= data["recovery_rate"] <= 1
        assert data["time_to_recovery_months"] >= 0
