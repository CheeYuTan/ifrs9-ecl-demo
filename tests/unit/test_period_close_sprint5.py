"""Tests for Sprint 5: Period-End Close Orchestration.

Covers:
  - Pipeline CRUD (start, get, complete)
  - Step execution with mocked DB responses
  - Pipeline health endpoint
  - Full pipeline run-all endpoint
  - Step validation (invalid step key)
  - Pipeline step listing
"""
import json
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

DOMAIN_MOD = "domain.period_close"


# ── Pipeline Steps ─────────────────────────────────────────────────────────

class TestPipelineSteps:
    """Tests for pipeline step definitions."""

    def test_pipeline_steps_has_six_steps(self):
        from domain.period_close import PIPELINE_STEPS
        assert len(PIPELINE_STEPS) == 6

    def test_pipeline_steps_ordered(self):
        from domain.period_close import PIPELINE_STEPS
        orders = [s["order"] for s in PIPELINE_STEPS]
        assert orders == [1, 2, 3, 4, 5, 6]

    def test_pipeline_steps_have_required_keys(self):
        from domain.period_close import PIPELINE_STEPS
        for step in PIPELINE_STEPS:
            assert "key" in step
            assert "label" in step
            assert "order" in step

    def test_list_steps_endpoint(self, fastapi_client, mock_db):
        resp = fastapi_client.get("/api/pipeline/steps")
        assert resp.status_code == 200
        steps = resp.json()
        assert len(steps) == 6
        assert steps[0]["key"] == "data_freshness"


# ── Start Pipeline ─────────────────────────────────────────────────────────

class TestStartPipeline:
    """Tests for POST /api/pipeline/start/{project_id}"""

    def test_start_pipeline_success(self, fastapi_client, mock_db):
        with patch(f"{DOMAIN_MOD}.execute"):
            resp = fastapi_client.post(
                "/api/pipeline/start/proj-001",
                json={"triggered_by": "test-user"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "proj-001"
        assert data["status"] == "running"
        assert data["triggered_by"] == "test-user"
        assert len(data["steps"]) == 6
        assert all(s["status"] == "pending" for s in data["steps"])

    def test_start_pipeline_default_trigger(self, fastapi_client, mock_db):
        with patch(f"{DOMAIN_MOD}.execute"):
            resp = fastapi_client.post(
                "/api/pipeline/start/proj-002",
                json={},
            )
        assert resp.status_code == 200
        assert resp.json()["triggered_by"] == "system"

    def test_start_pipeline_run_id_format(self, fastapi_client, mock_db):
        with patch(f"{DOMAIN_MOD}.execute"):
            resp = fastapi_client.post(
                "/api/pipeline/start/proj-003",
                json={},
            )
        assert resp.json()["run_id"].startswith("PIPE-proj-003-")


# ── Get Pipeline Run ───────────────────────────────────────────────────────

class TestGetPipelineRun:
    """Tests for GET /api/pipeline/run/{run_id}"""

    def test_get_run_not_found(self, fastapi_client, mock_db):
        with patch(f"{DOMAIN_MOD}.query_df", return_value=pd.DataFrame()):
            resp = fastapi_client.get("/api/pipeline/run/PIPE-nonexistent")
        assert resp.status_code == 404

    def test_get_run_found(self, fastapi_client, mock_db):
        steps = [{"key": "data_freshness", "status": "completed"}]
        run_df = pd.DataFrame([{
            "run_id": "PIPE-001", "project_id": "proj-001",
            "status": "running", "started_at": "2025-12-31T10:00:00",
            "completed_at": None, "duration_seconds": None,
            "steps": json.dumps(steps),
            "error_message": None, "triggered_by": "admin",
        }])
        with patch(f"{DOMAIN_MOD}.query_df", return_value=run_df):
            resp = fastapi_client.get("/api/pipeline/run/PIPE-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == "PIPE-001"
        assert data["status"] == "running"


# ── Execute Step ───────────────────────────────────────────────────────────

class TestExecuteStep:
    """Tests for POST /api/pipeline/run/{run_id}/execute-step"""

    def test_invalid_step_key(self, fastapi_client, mock_db):
        resp = fastapi_client.post(
            "/api/pipeline/run/PIPE-001/execute-step",
            json={"step_key": "invalid_step"},
        )
        assert resp.status_code == 400

    def test_run_not_found_for_step(self, fastapi_client, mock_db):
        with patch(f"{DOMAIN_MOD}.query_df", return_value=pd.DataFrame()):
            resp = fastapi_client.post(
                "/api/pipeline/run/PIPE-nonexistent/execute-step",
                json={"step_key": "data_freshness"},
            )
        assert resp.status_code == 404

    def test_execute_step_data_freshness(self, fastapi_client, mock_db):
        steps = [{"key": "data_freshness", "status": "pending",
                  "started_at": None, "completed_at": None,
                  "duration_seconds": None, "error": None}]
        run_df = pd.DataFrame([{
            "run_id": "PIPE-001", "project_id": "proj-001",
            "status": "running", "started_at": "2025-12-31T10:00:00",
            "completed_at": None, "duration_seconds": None,
            "steps": json.dumps(steps),
            "error_message": None, "triggered_by": "system",
        }])
        freshness_df = pd.DataFrame([{
            "last_updated": "2025-12-31 08:00:00", "record_count": 10000,
        }])
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            query = args[0] if args else ""
            if "pipeline_runs" in str(query):
                return run_df
            return freshness_df

        with patch(f"{DOMAIN_MOD}.query_df", side_effect=side_effect), \
             patch(f"{DOMAIN_MOD}.execute"):
            resp = fastapi_client.post(
                "/api/pipeline/run/PIPE-001/execute-step",
                json={"step_key": "data_freshness"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"] == "data_freshness"
        assert data["status"] == "completed"
        assert "record_count" in data


# ── Complete Pipeline ──────────────────────────────────────────────────────

class TestCompletePipeline:
    """Tests for POST /api/pipeline/run/{run_id}/complete"""

    def _make_run_df(self, run_id, steps, status="running"):
        return pd.DataFrame([{
            "run_id": run_id, "project_id": "proj-001",
            "status": status, "started_at": "2025-12-31T10:00:00",
            "completed_at": None, "duration_seconds": None,
            "steps": json.dumps(steps),
            "error_message": None, "triggered_by": "system",
        }])

    def test_complete_pipeline_not_found(self, fastapi_client, mock_db):
        with patch(f"{DOMAIN_MOD}.query_df", return_value=pd.DataFrame()):
            resp = fastapi_client.post("/api/pipeline/run/PIPE-nonexistent/complete")
        assert resp.status_code == 404

    def test_complete_pipeline_success(self, fastapi_client, mock_db):
        steps = [
            {"key": "data_freshness", "status": "completed"},
            {"key": "data_quality", "status": "completed"},
        ]
        run_df = self._make_run_df("PIPE-001", steps)
        completed_df = self._make_run_df("PIPE-001", steps, "completed")
        calls = [0]
        def side_effect(*args, **kwargs):
            calls[0] += 1
            if calls[0] <= 1:
                return run_df
            return completed_df

        with patch(f"{DOMAIN_MOD}.query_df", side_effect=side_effect), \
             patch(f"{DOMAIN_MOD}.execute"):
            resp = fastapi_client.post("/api/pipeline/run/PIPE-001/complete")
        assert resp.status_code == 200

    def test_complete_pipeline_with_failures(self, fastapi_client, mock_db):
        steps = [
            {"key": "data_freshness", "status": "completed"},
            {"key": "data_quality", "status": "failed"},
        ]
        run_df = self._make_run_df("PIPE-002", steps)
        failed_df = self._make_run_df("PIPE-002", steps, "failed")
        calls = [0]
        def side_effect(*args, **kwargs):
            calls[0] += 1
            if calls[0] <= 1:
                return run_df
            return failed_df

        with patch(f"{DOMAIN_MOD}.query_df", side_effect=side_effect), \
             patch(f"{DOMAIN_MOD}.execute"):
            resp = fastapi_client.post("/api/pipeline/run/PIPE-002/complete")
        assert resp.status_code == 200


# ── Pipeline Health ────────────────────────────────────────────────────────

class TestPipelineHealth:
    """Tests for GET /api/pipeline/health/{project_id}"""

    def test_health_no_runs(self, fastapi_client, mock_db):
        with patch(f"{DOMAIN_MOD}.query_df", return_value=pd.DataFrame()):
            resp = fastapi_client.get("/api/pipeline/health/proj-new")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_runs"] == 0

    def test_health_with_runs(self, fastapi_client, mock_db):
        health_df = pd.DataFrame([{
            "run_id": "PIPE-001", "status": "completed",
            "started_at": "2025-12-31T10:00:00",
            "completed_at": "2025-12-31T10:05:00",
            "duration_seconds": 300.0,
            "steps": json.dumps([{"key": "data_freshness", "status": "completed"}]),
        }])
        with patch(f"{DOMAIN_MOD}.query_df", return_value=health_df):
            resp = fastapi_client.get("/api/pipeline/health/proj-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_runs"] >= 1
        assert data["last_status"] == "completed"


# ── Domain Logic Unit Tests ────────────────────────────────────────────────

class TestPeriodCloseDomain:
    """Unit tests for domain/period_close.py functions."""

    def test_data_freshness_no_data_raises(self):
        with patch(f"{DOMAIN_MOD}.query_df", return_value=pd.DataFrame()):
            from domain.period_close import _check_data_freshness
            with pytest.raises(ValueError, match="Data freshness check failed"):
                _check_data_freshness()

    def test_data_freshness_zero_records_raises(self):
        df = pd.DataFrame([{"last_updated": None, "record_count": 0}])
        with patch(f"{DOMAIN_MOD}.query_df", return_value=df):
            from domain.period_close import _check_data_freshness
            with pytest.raises(ValueError, match="No loan data found"):
                _check_data_freshness()

    def test_data_quality_no_data_raises(self):
        with patch(f"{DOMAIN_MOD}.query_df", return_value=pd.DataFrame()):
            from domain.period_close import _check_data_quality
            with pytest.raises(ValueError, match="Data quality validation failed"):
                _check_data_quality()

    def test_model_execution_zero_results_raises(self):
        df = pd.DataFrame([{"cnt": 0}])
        with patch(f"{DOMAIN_MOD}.query_df", return_value=df):
            from domain.period_close import _check_model_execution
            with pytest.raises(ValueError, match="No model execution results"):
                _check_model_execution()

    def test_ecl_calculation_empty_raises(self):
        with patch(f"{DOMAIN_MOD}.query_df", return_value=pd.DataFrame()):
            from domain.period_close import _check_ecl_calculation
            with pytest.raises(ValueError, match="ECL calculation check failed"):
                _check_ecl_calculation()

    def test_run_step_logic_unknown_step(self):
        from domain.period_close import _run_step_logic
        result = _run_step_logic("unknown_step")
        assert "message" in result

    def test_data_freshness_success(self):
        df = pd.DataFrame([{"last_updated": "2025-12-31", "record_count": 5000}])
        with patch(f"{DOMAIN_MOD}.query_df", return_value=df):
            from domain.period_close import _check_data_freshness
            result = _check_data_freshness()
        assert result["record_count"] == 5000
        assert "threshold_days" in result
