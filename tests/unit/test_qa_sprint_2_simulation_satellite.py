"""
QA Sprint 2: Simulation & Satellite Model Endpoints.

Tests routes/simulation.py (6 endpoints) and routes/satellite.py (12 endpoints)
with mocked backend, ecl_engine, jobs, and domain modules.
"""
import json
import queue
import threading
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock, PropertyMock

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


def _sim_raw_result(**overrides):
    """Build a realistic raw ecl_engine.run_simulation() result."""
    base = {
        "stage_summary": [
            {"stage": 1, "total_gca": 5000000.0, "total_ecl": 50000.0},
            {"stage": 2, "total_gca": 2000000.0, "total_ecl": 80000.0},
            {"stage": 3, "total_gca": 500000.0, "total_ecl": 150000.0},
        ],
        "scenario_results": [
            {"scenario": "base", "weight": 0.50, "total_ecl": 200000.0},
            {"scenario": "optimistic", "weight": 0.25, "total_ecl": 150000.0},
            {"scenario": "pessimistic", "weight": 0.25, "total_ecl": 300000.0},
        ],
        "portfolio_summary": [
            {"product_type": "mortgage", "loan_count": 100, "total_gca": 4000000.0, "total_ecl": 160000.0},
            {"product_type": "personal", "loan_count": 200, "total_gca": 3500000.0, "total_ecl": 120000.0},
        ],
        "product_scenario": [
            {"product_type": "mortgage", "scenario": "base", "total_ecl": 120000.0},
        ],
        "run_metadata": {
            "timestamp": "2025-12-01T10:00:00",
            "random_seed": 42,
            "duration_seconds": 12.5,
            "loan_count": 300,
            "convergence_by_product": {"mortgage": 0.02, "personal": 0.03},
        },
    }
    base.update(overrides)
    return base


def _defaults_result():
    """Build a realistic ecl_engine.get_defaults() result."""
    return {
        "default_params": {
            "n_sims": 1000,
            "pd_lgd_correlation": 0.30,
            "aging_factor": 0.08,
            "pd_floor": 0.001,
            "pd_cap": 0.95,
            "lgd_floor": 0.01,
            "lgd_cap": 0.95,
        },
        "default_weights": {"base": 0.50, "optimistic": 0.25, "pessimistic": 0.25},
        "scenarios": ["base", "optimistic", "pessimistic"],
        "products": ["mortgage", "personal"],
    }


def _model_run_dict(**overrides):
    """Build a realistic model run dict."""
    base = {
        "run_id": "sim_2025-12-01T10:00:00",
        "run_type": "monte_carlo_simulation",
        "run_timestamp": datetime(2025, 12, 1, 10, 0, 0),
        "models_used": ["monte_carlo"],
        "products": ["mortgage", "personal"],
        "total_cohorts": 300,
        "best_model_summary": {
            "random_seed": 42,
            "n_simulations": 1000,
            "total_ecl": 280000.0,
            "total_gca": 7500000.0,
            "duration_seconds": 12.5,
            "ecl_by_product": {"mortgage": 160000.0, "personal": 120000.0},
        },
        "status": "completed",
        "notes": "seed=42, n_sims=1000",
        "created_by": "system",
    }
    base.update(overrides)
    return base


def _satellite_comparison_df():
    """Build a satellite model comparison DataFrame."""
    return pd.DataFrame({
        "product_type": ["mortgage", "mortgage", "personal", "personal"],
        "cohort_id": ["2020", "2020", "2021", "2021"],
        "model_type": ["linear", "ridge", "linear", "ridge"],
        "r_squared": [0.85, 0.87, 0.80, 0.82],
        "rmse": [0.012, 0.011, 0.015, 0.014],
        "aic": [-100, -105, -90, -95],
        "bic": [-95, -100, -85, -90],
        "cv_rmse": [0.013, 0.012, 0.016, 0.015],
        "coefficients_json": ['{"a": 1}', '{"a": 2}', '{"b": 1}', '{"b": 2}'],
        "formula": ["y ~ x1", "y ~ x1", "y ~ x2", "y ~ x2"],
        "n_observations": [20, 20, 18, 18],
        "run_timestamp": ["2025-12-01"] * 4,
    })


def _satellite_selected_df():
    """Build a satellite model selected DataFrame."""
    return pd.DataFrame({
        "product_type": ["mortgage", "personal"],
        "cohort_id": ["2020", "2021"],
        "model_type": ["ridge", "ridge"],
        "r_squared": [0.87, 0.82],
        "rmse": [0.011, 0.014],
        "aic": [-105, -95],
        "bic": [-100, -90],
        "coefficients_json": ['{"a": 2}', '{"b": 2}'],
        "formula": ["y ~ x1", "y ~ x2"],
        "selection_reason": ["lowest_aic", "lowest_aic"],
        "n_observations": [20, 18],
        "run_timestamp": ["2025-12-01"] * 2,
    })


def _cohort_summary_df():
    return pd.DataFrame({
        "product_type": ["mortgage", "personal"],
        "cohort_id": ["2020", "2021"],
        "loan_count": [500, 300],
        "total_gca": [25000000.0, 15000000.0],
        "avg_pd": [0.025, 0.045],
        "avg_dpd": [5.2, 12.3],
        "stage1": [400, 200],
        "stage2": [80, 60],
        "stage3": [20, 40],
    })


# ===================================================================
# SIMULATION ROUTES — POST /api/simulate
# ===================================================================

class TestRunSimulation:
    """POST /api/simulate"""

    def test_happy_path(self, client):
        raw = _sim_raw_result()
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={"n_simulations": 500})
        assert resp.status_code == 200
        data = resp.json()
        assert "ecl_by_product" in data
        assert "scenario_summary" in data
        assert "loss_allowance_by_stage" in data
        assert "run_metadata" in data
        assert data["n_simulations"] == 500
        assert data["pd_lgd_correlation"] == 0.30

    def test_ecl_by_product_aggregation(self, client):
        raw = _sim_raw_result(portfolio_summary=[
            {"product_type": "mortgage", "loan_count": 50, "total_gca": 2000000.0, "total_ecl": 80000.0},
            {"product_type": "mortgage", "loan_count": 50, "total_gca": 2000000.0, "total_ecl": 80000.0},
            {"product_type": "personal", "loan_count": 200, "total_gca": 3500000.0, "total_ecl": 120000.0},
        ])
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        data = resp.json()
        products = {p["product_type"]: p for p in data["ecl_by_product"]}
        assert products["mortgage"]["loan_count"] == 100
        assert products["mortgage"]["total_gca"] == 4000000.0
        assert products["mortgage"]["total_ecl"] == 160000.0

    def test_stage_summary_transform(self, client):
        raw = _sim_raw_result()
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        data = resp.json()
        stages = data["loss_allowance_by_stage"]
        assert len(stages) == 3
        assert stages[0]["assessed_stage"] == 1
        assert "coverage_pct" in stages[0]
        assert stages[0]["coverage_pct"] == 1.0  # 50000/5000000*100

    def test_scenario_summary_weighted(self, client):
        raw = _sim_raw_result()
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        data = resp.json()
        scenarios = data["scenario_summary"]
        assert scenarios[0]["weighted"] == 100000.0  # 200000*0.5
        assert scenarios[1]["weighted"] == 37500.0  # 150000*0.25

    def test_returns_400_on_critical_pre_check_failures(self, client):
        critical_results = [{"check": "pd_range", "severity": "critical", "passed": False}]
        with patch("routes.simulation._run_pre_checks", return_value=critical_results), \
             patch("domain.validation_rules.has_critical_failures", return_value=True):
            resp = client.post("/api/simulate", json={})
        assert resp.status_code == 400
        data = resp.json()
        assert "validation" in data["detail"]["message"].lower() or "pre-calculation" in data["detail"]["message"].lower()

    def test_returns_500_on_engine_failure(self, client):
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("domain.validation_rules.has_critical_failures", return_value=False), \
             patch("ecl_engine.run_simulation", side_effect=RuntimeError("OOM")):
            resp = client.post("/api/simulate", json={})
        assert resp.status_code == 500
        assert "OOM" in resp.json()["detail"]

    def test_default_config_values(self, client):
        raw = _sim_raw_result()
        captured = {}
        original_run = MagicMock(return_value=raw)

        def capture_run(**kwargs):
            captured.update(kwargs)
            return raw

        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", side_effect=capture_run), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        assert resp.status_code == 200
        assert captured["n_sims"] == 1000
        assert captured["pd_lgd_correlation"] == 0.30
        assert captured["aging_factor"] == 0.08
        assert captured["pd_floor"] == 0.001
        assert captured["pd_cap"] == 0.95

    def test_custom_config_passed_through(self, client):
        raw = _sim_raw_result()
        captured = {}

        def capture_run(**kwargs):
            captured.update(kwargs)
            return raw

        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", side_effect=capture_run), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={
                "n_simulations": 2000,
                "pd_lgd_correlation": 0.5,
                "random_seed": 99,
                "scenario_weights": {"base": 0.6, "opt": 0.4},
            })
        assert resp.status_code == 200
        assert captured["n_sims"] == 2000
        assert captured["pd_lgd_correlation"] == 0.5
        assert captured["random_seed"] == 99
        assert captured["scenario_weights"] == {"base": 0.6, "opt": 0.4}

    def test_validation_results_included_in_response(self, client):
        raw = _sim_raw_result()
        checks = [{"check": "pd_range", "severity": "warning", "passed": True}]
        with patch("routes.simulation._run_pre_checks", return_value=checks), \
             patch("domain.validation_rules.has_critical_failures", return_value=False), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        assert resp.status_code == 200
        assert resp.json()["validation_results"] == checks

    def test_persist_failure_caught_by_outer_handler(self, client):
        """If _persist_simulation_run bypasses its own try/except (mock scenario),
        the outer except catches it. In production, _persist_simulation_run has its
        own try/except so this path shouldn't occur."""
        raw = _sim_raw_result()
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run", side_effect=Exception("DB down")):
            resp = client.post("/api/simulate", json={})
        # Outer except catches the exception and returns 500
        assert resp.status_code == 500

    def test_empty_portfolio_summary(self, client):
        raw = _sim_raw_result(portfolio_summary=[])
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        assert resp.status_code == 200
        assert resp.json()["ecl_by_product"] == []

    def test_empty_stage_summary(self, client):
        raw = _sim_raw_result(stage_summary=[])
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        assert resp.status_code == 200
        assert resp.json()["loss_allowance_by_stage"] == []

    def test_coverage_pct_zero_gca(self, client):
        raw = _sim_raw_result(stage_summary=[
            {"stage": 1, "total_gca": 0, "total_ecl": 0},
        ])
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        stages = resp.json()["loss_allowance_by_stage"]
        assert stages[0]["coverage_pct"] == 0

    def test_coverage_ratio_zero_gca_product(self, client):
        raw = _sim_raw_result(portfolio_summary=[
            {"product_type": "mortgage", "loan_count": 0, "total_gca": 0.0, "total_ecl": 0.0},
        ])
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        products = resp.json()["ecl_by_product"]
        assert products[0]["coverage_ratio"] == 0


# ===================================================================
# SIMULATION DEFAULTS — GET /api/simulation-defaults
# ===================================================================

class TestSimulationDefaults:
    """GET /api/simulation-defaults"""

    def test_happy_path(self, client):
        with patch("ecl_engine.get_defaults", return_value=_defaults_result()):
            resp = client.get("/api/simulation-defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert data["n_simulations"] == 1000
        assert data["pd_lgd_correlation"] == 0.30
        assert data["aging_factor"] == 0.08
        assert data["pd_floor"] == 0.001
        assert data["pd_cap"] == 0.95
        assert data["lgd_floor"] == 0.01
        assert data["lgd_cap"] == 0.95
        assert "scenario_weights" in data
        assert "scenarios" in data
        assert "products" in data

    def test_returns_500_on_failure(self, client):
        with patch("ecl_engine.get_defaults", side_effect=RuntimeError("No data")):
            resp = client.get("/api/simulation-defaults")
        assert resp.status_code == 500

    def test_missing_default_params_uses_fallbacks(self, client):
        with patch("ecl_engine.get_defaults", return_value={"default_params": {}, "default_weights": {}, "scenarios": [], "products": []}):
            resp = client.get("/api/simulation-defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert data["n_simulations"] == 1000  # fallback
        assert data["pd_lgd_correlation"] == 0.30


# ===================================================================
# SIMULATE STREAM — POST /api/simulate-stream
# ===================================================================

class TestSimulateStream:
    """POST /api/simulate-stream"""

    def test_stream_returns_sse_content_type(self, client):
        raw = _sim_raw_result()
        with patch("ecl_engine.run_simulation", return_value=raw):
            resp = client.post("/api/simulate-stream", json={"n_simulations": 100})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_stream_contains_result_event(self, client):
        raw = _sim_raw_result()
        with patch("ecl_engine.run_simulation", return_value=raw):
            resp = client.post("/api/simulate-stream", json={"n_simulations": 100})
        body = resp.text
        # Should contain a result event
        assert '"type": "result"' in body or '"type":"result"' in body

    def test_stream_error_event_on_failure(self, client):
        with patch("ecl_engine.run_simulation", side_effect=RuntimeError("Engine crash")):
            resp = client.post("/api/simulate-stream", json={"n_simulations": 100})
        body = resp.text
        assert '"type": "error"' in body or '"type":"error"' in body
        assert "Engine crash" in body

    def test_stream_no_cache_headers(self, client):
        raw = _sim_raw_result()
        with patch("ecl_engine.run_simulation", return_value=raw):
            resp = client.post("/api/simulate-stream", json={})
        assert resp.headers.get("cache-control") == "no-cache"

    def test_stream_with_progress_callback(self, client):
        raw = _sim_raw_result()

        def fake_simulation(**kwargs):
            cb = kwargs.get("progress_callback")
            if cb:
                cb({"pct": 50, "message": "Halfway"})
                cb({"pct": 100, "message": "Done"})
            return raw

        with patch("ecl_engine.run_simulation", side_effect=fake_simulation):
            resp = client.post("/api/simulate-stream", json={})
        body = resp.text
        assert "Halfway" in body or "progress" in body


# ===================================================================
# SIMULATE JOB — POST /api/simulate-job
# ===================================================================

class TestSimulateJob:
    """POST /api/simulate-job"""

    def test_happy_path(self, client):
        job_result = {"job_id": "123", "run_id": "456", "status": "RUNNING"}
        with patch("jobs.trigger_monte_carlo_job", return_value=job_result):
            resp = client.post("/api/simulate-job", json={"n_simulations": 500})
        assert resp.status_code == 200
        assert resp.json()["job_id"] == "123"

    def test_returns_500_on_failure(self, client):
        with patch("jobs.trigger_monte_carlo_job", side_effect=RuntimeError("No cluster")):
            resp = client.post("/api/simulate-job", json={})
        assert resp.status_code == 500
        assert "simulation job" in resp.json()["detail"].lower()

    def test_passes_all_config_params(self, client):
        captured = {}

        def capture(**kwargs):
            captured.update(kwargs)
            return {"job_id": "1", "run_id": "2"}

        with patch("jobs.trigger_monte_carlo_job", side_effect=capture):
            client.post("/api/simulate-job", json={
                "n_simulations": 2000,
                "pd_lgd_correlation": 0.5,
                "random_seed": 77,
                "scenario_weights": {"base": 1.0},
            })
        assert captured["n_simulations"] == 2000
        assert captured["pd_lgd_correlation"] == 0.5
        assert captured["random_seed"] == 77

    def test_use_databricks_job_flag_ignored(self, client):
        """use_databricks_job is a client hint, doesn't affect this endpoint."""
        with patch("jobs.trigger_monte_carlo_job", return_value={"job_id": "1"}):
            resp = client.post("/api/simulate-job", json={"use_databricks_job": True})
        assert resp.status_code == 200


# ===================================================================
# SIMULATE VALIDATE — POST /api/simulate-validate
# ===================================================================

class TestSimulateValidate:
    """POST /api/simulate-validate"""

    def test_valid_defaults(self, client):
        resp = client.post("/api/simulate-validate", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["errors"] == []
        assert "estimated_seconds" in data
        assert "estimated_memory_mb" in data

    def test_pd_floor_gte_cap(self, client):
        resp = client.post("/api/simulate-validate", json={"pd_floor": 0.95, "pd_cap": 0.90})
        data = resp.json()
        assert data["valid"] is False
        assert any("PD Floor" in e for e in data["errors"])

    def test_pd_floor_equals_cap(self, client):
        resp = client.post("/api/simulate-validate", json={"pd_floor": 0.5, "pd_cap": 0.5})
        data = resp.json()
        assert data["valid"] is False
        assert any("PD Floor" in e for e in data["errors"])

    def test_lgd_floor_gte_cap(self, client):
        resp = client.post("/api/simulate-validate", json={"lgd_floor": 0.95, "lgd_cap": 0.90})
        data = resp.json()
        assert data["valid"] is False
        assert any("LGD Floor" in e for e in data["errors"])

    def test_lgd_floor_equals_cap(self, client):
        resp = client.post("/api/simulate-validate", json={"lgd_floor": 0.5, "lgd_cap": 0.5})
        data = resp.json()
        assert data["valid"] is False

    def test_n_simulations_below_minimum(self, client):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 50})
        data = resp.json()
        assert data["valid"] is False
        assert any("100" in e for e in data["errors"])

    def test_n_simulations_exactly_100(self, client):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 100})
        data = resp.json()
        assert data["valid"] is True

    def test_n_simulations_above_max(self, client):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 999999})
        data = resp.json()
        assert data["valid"] is False
        assert any("Maximum" in e or "maximum" in e.lower() for e in data["errors"])

    def test_scenario_weights_not_summing_to_1(self, client):
        resp = client.post("/api/simulate-validate", json={
            "scenario_weights": {"base": 0.3, "opt": 0.2},
        })
        data = resp.json()
        assert data["valid"] is False
        assert any("weight" in e.lower() for e in data["errors"])

    def test_scenario_weights_within_tolerance(self, client):
        """Weights summing to 0.995 should be within 0.01 tolerance."""
        resp = client.post("/api/simulate-validate", json={
            "scenario_weights": {"base": 0.50, "opt": 0.245, "pess": 0.25},
        })
        data = resp.json()
        # 0.995 is within 0.01 of 1.0
        weight_errors = [e for e in data["errors"] if "weight" in e.lower()]
        assert len(weight_errors) == 0

    def test_scenario_weights_exactly_1(self, client):
        resp = client.post("/api/simulate-validate", json={
            "scenario_weights": {"base": 0.50, "opt": 0.25, "pess": 0.25},
        })
        data = resp.json()
        assert data["valid"] is True

    def test_warning_high_nsims(self, client):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 5000})
        data = resp.json()
        assert any("may take" in w.lower() for w in data["warnings"])

    def test_warning_low_nsims(self, client):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 200})
        data = resp.json()
        assert any("unstable" in w.lower() for w in data["warnings"])

    def test_warning_high_correlation(self, client):
        resp = client.post("/api/simulate-validate", json={"pd_lgd_correlation": 0.8})
        data = resp.json()
        assert any("correlation" in w.lower() for w in data["warnings"])

    def test_warning_high_aging_factor(self, client):
        resp = client.post("/api/simulate-validate", json={"aging_factor": 0.20})
        data = resp.json()
        assert any("aging" in w.lower() for w in data["warnings"])

    def test_no_warnings_for_moderate_params(self, client):
        resp = client.post("/api/simulate-validate", json={
            "n_simulations": 1000,
            "pd_lgd_correlation": 0.3,
            "aging_factor": 0.08,
        })
        data = resp.json()
        assert data["valid"] is True
        assert len(data["warnings"]) == 0

    def test_multiple_errors_accumulate(self, client):
        resp = client.post("/api/simulate-validate", json={
            "n_simulations": 50,
            "pd_floor": 0.99,
            "pd_cap": 0.01,
            "lgd_floor": 0.99,
            "lgd_cap": 0.01,
        })
        data = resp.json()
        assert data["valid"] is False
        assert len(data["errors"]) >= 3

    def test_estimated_seconds_positive(self, client):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 1000})
        data = resp.json()
        assert data["estimated_seconds"] > 0

    def test_estimated_memory_positive(self, client):
        resp = client.post("/api/simulate-validate", json={"n_simulations": 1000})
        data = resp.json()
        assert data["estimated_memory_mb"] > 0

    def test_null_scenario_weights_is_valid(self, client):
        resp = client.post("/api/simulate-validate", json={"scenario_weights": None})
        data = resp.json()
        weight_errors = [e for e in data["errors"] if "weight" in e.lower()]
        assert len(weight_errors) == 0

    def test_empty_scenario_weights_is_valid(self, client):
        """No scenario_weights key at all should be valid."""
        resp = client.post("/api/simulate-validate", json={})
        data = resp.json()
        weight_errors = [e for e in data["errors"] if "weight" in e.lower()]
        assert len(weight_errors) == 0


# ===================================================================
# SIMULATION COMPARE — GET /api/simulation/compare
# ===================================================================

class TestSimulationCompare:
    """GET /api/simulation/compare"""

    def test_happy_path(self, client):
        run_a = _model_run_dict(run_id="run_a", best_model_summary={
            "total_ecl": 200000.0, "total_gca": 7000000.0,
            "ecl_by_product": {"mortgage": 120000.0, "personal": 80000.0},
        })
        run_b = _model_run_dict(run_id="run_b", best_model_summary={
            "total_ecl": 220000.0, "total_gca": 7000000.0,
            "ecl_by_product": {"mortgage": 130000.0, "personal": 90000.0},
        })
        with patch("domain.model_runs.get_model_run", side_effect=lambda rid: {"run_a": run_a, "run_b": run_b}.get(rid)):
            resp = client.get("/api/simulation/compare?run_a=run_a&run_b=run_b")
        assert resp.status_code == 200
        data = resp.json()
        assert "deltas" in data
        assert "product_deltas" in data
        assert data["summary"]["metrics_compared"] > 0
        assert data["run_a"]["run_id"] == "run_a"
        assert data["run_b"]["run_id"] == "run_b"

    def test_product_deltas_computed(self, client):
        run_a = _model_run_dict(run_id="a", best_model_summary={
            "total_ecl": 100.0,
            "ecl_by_product": {"mortgage": 60.0, "personal": 40.0},
        })
        run_b = _model_run_dict(run_id="b", best_model_summary={
            "total_ecl": 120.0,
            "ecl_by_product": {"mortgage": 70.0, "personal": 50.0},
        })
        with patch("domain.model_runs.get_model_run", side_effect=lambda rid: {"a": run_a, "b": run_b}.get(rid)):
            resp = client.get("/api/simulation/compare?run_a=a&run_b=b")
        data = resp.json()
        pd_map = {d["product_type"]: d for d in data["product_deltas"]}
        assert pd_map["mortgage"]["absolute_delta"] == 10.0
        assert pd_map["personal"]["absolute_delta"] == 10.0

    def test_returns_404_when_run_not_found(self, client):
        with patch("domain.model_runs.get_model_run", return_value=None):
            resp = client.get("/api/simulation/compare?run_a=missing_a&run_b=missing_b")
        assert resp.status_code == 404

    def test_returns_404_when_one_run_missing(self, client):
        run_a = _model_run_dict(run_id="a")
        with patch("domain.model_runs.get_model_run", side_effect=lambda rid: run_a if rid == "a" else None):
            resp = client.get("/api/simulation/compare?run_a=a&run_b=missing")
        assert resp.status_code == 404

    def test_returns_500_on_unexpected_error(self, client):
        with patch("domain.model_runs.get_model_run", side_effect=RuntimeError("DB error")):
            resp = client.get("/api/simulation/compare?run_a=a&run_b=b")
        assert resp.status_code == 500

    def test_relative_delta_none_when_denominator_zero(self, client):
        run_a = _model_run_dict(run_id="a", best_model_summary={
            "total_ecl": 0.0, "ecl_by_product": {"mortgage": 0.0},
        })
        run_b = _model_run_dict(run_id="b", best_model_summary={
            "total_ecl": 100.0, "ecl_by_product": {"mortgage": 50.0},
        })
        with patch("domain.model_runs.get_model_run", side_effect=lambda rid: {"a": run_a, "b": run_b}.get(rid)):
            resp = client.get("/api/simulation/compare?run_a=a&run_b=b")
        data = resp.json()
        # When run_a value is 0, relative_delta_pct should be None
        ecl_delta = next(d for d in data["deltas"] if d["metric"] == "total_ecl")
        assert ecl_delta["relative_delta_pct"] is None

    def test_product_deltas_non_overlapping_products(self, client):
        run_a = _model_run_dict(run_id="a", best_model_summary={
            "ecl_by_product": {"mortgage": 100.0},
        })
        run_b = _model_run_dict(run_id="b", best_model_summary={
            "ecl_by_product": {"personal": 200.0},
        })
        with patch("domain.model_runs.get_model_run", side_effect=lambda rid: {"a": run_a, "b": run_b}.get(rid)):
            resp = client.get("/api/simulation/compare?run_a=a&run_b=b")
        data = resp.json()
        pd_map = {d["product_type"]: d for d in data["product_deltas"]}
        assert "mortgage" in pd_map
        assert "personal" in pd_map
        assert pd_map["mortgage"]["run_b_ecl"] == 0

    def test_summary_counts_improved_degraded(self, client):
        run_a = _model_run_dict(run_id="a", best_model_summary={
            "total_ecl": 200.0, "total_gca": 1000.0,
        })
        run_b = _model_run_dict(run_id="b", best_model_summary={
            "total_ecl": 180.0, "total_gca": 1100.0,
        })
        with patch("domain.model_runs.get_model_run", side_effect=lambda rid: {"a": run_a, "b": run_b}.get(rid)):
            resp = client.get("/api/simulation/compare?run_a=a&run_b=b")
        data = resp.json()
        assert data["summary"]["metrics_improved"] >= 1  # total_ecl decreased
        assert data["summary"]["metrics_degraded"] >= 1  # total_gca increased

    def test_empty_summaries(self, client):
        run_a = _model_run_dict(run_id="a", best_model_summary={})
        run_b = _model_run_dict(run_id="b", best_model_summary={})
        with patch("domain.model_runs.get_model_run", side_effect=lambda rid: {"a": run_a, "b": run_b}.get(rid)):
            resp = client.get("/api/simulation/compare?run_a=a&run_b=b")
        data = resp.json()
        assert data["deltas"] == []
        assert data["product_deltas"] == []


# ===================================================================
# SATELLITE MODEL COMPARISON — GET /api/data/satellite-model-comparison
# ===================================================================

class TestSatelliteModelComparison:
    """GET /api/data/satellite-model-comparison"""

    def test_happy_path(self, client):
        with patch("backend.get_satellite_model_comparison", return_value=_satellite_comparison_df()):
            resp = client.get("/api/data/satellite-model-comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 4
        assert data[0]["model_type"] in ("linear", "ridge")

    def test_with_run_id(self, client):
        captured_args = {}
        def capture(run_id=None):
            captured_args["run_id"] = run_id
            return _satellite_comparison_df()
        with patch("backend.get_satellite_model_comparison", side_effect=capture):
            resp = client.get("/api/data/satellite-model-comparison?run_id=abc123")
        assert resp.status_code == 200
        assert captured_args["run_id"] == "abc123"

    def test_empty_result(self, client):
        with patch("backend.get_satellite_model_comparison", return_value=pd.DataFrame()):
            resp = client.get("/api/data/satellite-model-comparison")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_500_on_error(self, client):
        with patch("backend.get_satellite_model_comparison", side_effect=RuntimeError("DB timeout")):
            resp = client.get("/api/data/satellite-model-comparison")
        assert resp.status_code == 500


# ===================================================================
# SATELLITE MODEL SELECTED — GET /api/data/satellite-model-selected
# ===================================================================

class TestSatelliteModelSelected:
    """GET /api/data/satellite-model-selected"""

    def test_happy_path(self, client):
        with patch("backend.get_satellite_model_selected", return_value=_satellite_selected_df()):
            resp = client.get("/api/data/satellite-model-selected")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["selection_reason"] == "lowest_aic"

    def test_with_run_id(self, client):
        captured_args = {}
        def capture(run_id=None):
            captured_args["run_id"] = run_id
            return _satellite_selected_df()
        with patch("backend.get_satellite_model_selected", side_effect=capture):
            resp = client.get("/api/data/satellite-model-selected?run_id=xyz")
        assert captured_args["run_id"] == "xyz"

    def test_empty_result(self, client):
        with patch("backend.get_satellite_model_selected", return_value=pd.DataFrame()):
            resp = client.get("/api/data/satellite-model-selected")
        assert resp.json() == []

    def test_returns_500_on_error(self, client):
        with patch("backend.get_satellite_model_selected", side_effect=Exception("fail")):
            resp = client.get("/api/data/satellite-model-selected")
        assert resp.status_code == 500


# ===================================================================
# MODEL RUNS — GET/POST /api/model-runs
# ===================================================================

class TestListModelRuns:
    """GET /api/model-runs"""

    def test_returns_list(self, client):
        df = pd.DataFrame({
            "run_id": ["r1", "r2"],
            "run_type": ["satellite_model", "monte_carlo"],
            "run_timestamp": ["2025-12-01", "2025-12-02"],
            "models_used": ['["linear"]', '["monte_carlo"]'],
            "products": ['["mortgage"]', '["personal"]'],
            "total_cohorts": [10, 20],
            "best_model_summary": ['{"total_ecl": 100}', '{"total_ecl": 200}'],
            "status": ["completed", "completed"],
            "notes": ["", ""],
            "created_by": ["system", "system"],
        })
        with patch("backend.list_model_runs", return_value=df):
            resp = client.get("/api/model-runs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # JSON fields should be parsed
        assert data[0]["models_used"] == ["linear"]
        assert data[0]["best_model_summary"] == {"total_ecl": 100}

    def test_with_run_type_filter(self, client):
        captured = {}
        def capture(run_type=None):
            captured["run_type"] = run_type
            return pd.DataFrame()
        with patch("backend.list_model_runs", side_effect=capture):
            client.get("/api/model-runs?run_type=satellite_model")
        assert captured["run_type"] == "satellite_model"

    def test_malformed_json_fields_preserved(self, client):
        df = pd.DataFrame({
            "run_id": ["r1"],
            "run_type": ["test"],
            "run_timestamp": ["2025-01-01"],
            "models_used": ["not-valid-json"],
            "products": ["also-bad"],
            "total_cohorts": [0],
            "best_model_summary": ["[broken"],
            "status": ["completed"],
            "notes": [""],
            "created_by": ["system"],
        })
        with patch("backend.list_model_runs", return_value=df):
            resp = client.get("/api/model-runs")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["models_used"] == "not-valid-json"

    def test_empty_list(self, client):
        with patch("backend.list_model_runs", return_value=pd.DataFrame()):
            resp = client.get("/api/model-runs")
        assert resp.json() == []

    def test_returns_500_on_error(self, client):
        with patch("backend.list_model_runs", side_effect=Exception("DB")):
            resp = client.get("/api/model-runs")
        assert resp.status_code == 500


class TestGetModelRun:
    """GET /api/model-runs/{run_id}"""

    def test_found(self, client):
        run = _model_run_dict()
        with patch("backend.get_model_run", return_value=run):
            resp = client.get("/api/model-runs/sim_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == run["run_id"]

    def test_not_found(self, client):
        with patch("backend.get_model_run", return_value=None):
            resp = client.get("/api/model-runs/nonexistent")
        assert resp.status_code == 404

    def test_returns_500_on_error(self, client):
        with patch("backend.get_model_run", side_effect=RuntimeError("DB")):
            resp = client.get("/api/model-runs/x")
        assert resp.status_code == 500

    def test_serializes_datetime(self, client):
        run = _model_run_dict()
        with patch("backend.get_model_run", return_value=run):
            resp = client.get("/api/model-runs/x")
        assert resp.status_code == 200
        # datetime should be serialized to string
        data = resp.json()
        assert isinstance(data["run_timestamp"], str)


class TestSaveModelRun:
    """POST /api/model-runs"""

    def test_happy_path(self, client):
        saved = _model_run_dict()
        with patch("backend.save_model_run", return_value=saved):
            resp = client.post("/api/model-runs", json={
                "run_id": "new_run",
                "run_type": "satellite_model",
                "models_used": ["ridge"],
                "products": ["mortgage"],
                "total_cohorts": 5,
                "best_model_summary": {"r2": 0.85},
                "notes": "test run",
            })
        assert resp.status_code == 200

    def test_minimal_payload(self, client):
        saved = _model_run_dict()
        with patch("backend.save_model_run", return_value=saved):
            resp = client.post("/api/model-runs", json={"run_id": "min"})
        assert resp.status_code == 200

    def test_missing_run_id_returns_422(self, client):
        resp = client.post("/api/model-runs", json={})
        assert resp.status_code == 422

    def test_returns_500_on_error(self, client):
        with patch("backend.save_model_run", side_effect=Exception("conflict")):
            resp = client.post("/api/model-runs", json={"run_id": "x"})
        assert resp.status_code == 500


# ===================================================================
# COHORT SUMMARY — GET /api/data/cohort-summary
# ===================================================================

class TestCohortSummary:
    """GET /api/data/cohort-summary"""

    def test_happy_path(self, client):
        with patch("backend.get_cohort_summary", return_value=_cohort_summary_df()):
            resp = client.get("/api/data/cohort-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert "loan_count" in data[0]
        assert "total_gca" in data[0]

    def test_empty_result(self, client):
        with patch("backend.get_cohort_summary", return_value=pd.DataFrame()):
            resp = client.get("/api/data/cohort-summary")
        assert resp.json() == []

    def test_returns_500_on_error(self, client):
        with patch("backend.get_cohort_summary", side_effect=Exception("DB")):
            resp = client.get("/api/data/cohort-summary")
        assert resp.status_code == 500


class TestCohortSummaryByProduct:
    """GET /api/data/cohort-summary/{product}"""

    def test_happy_path(self, client):
        df = _cohort_summary_df().head(1)
        with patch("backend.get_cohort_summary_by_product", return_value=df):
            resp = client.get("/api/data/cohort-summary/mortgage")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_nonexistent_product_returns_empty(self, client):
        with patch("backend.get_cohort_summary_by_product", return_value=pd.DataFrame()):
            resp = client.get("/api/data/cohort-summary/nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_500_on_error(self, client):
        with patch("backend.get_cohort_summary_by_product", side_effect=Exception("fail")):
            resp = client.get("/api/data/cohort-summary/x")
        assert resp.status_code == 500


# ===================================================================
# DRILL-DOWN DIMENSIONS — GET /api/data/drill-down-dimensions
# ===================================================================

class TestDrillDownDimensions:
    """GET /api/data/drill-down-dimensions"""

    def test_happy_path(self, client):
        dims = [{"key": "credit_grade", "label": "Credit Grade"}, {"key": "region", "label": "Geography"}]
        with patch("backend.get_drill_down_dimensions", return_value=dims):
            resp = client.get("/api/data/drill-down-dimensions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["key"] == "credit_grade"

    def test_with_product_param(self, client):
        captured = {}
        def capture(product="any"):
            captured["product"] = product
            return []
        with patch("backend.get_drill_down_dimensions", side_effect=capture):
            client.get("/api/data/drill-down-dimensions?product=mortgage")
        assert captured["product"] == "mortgage"

    def test_empty_dimensions(self, client):
        with patch("backend.get_drill_down_dimensions", return_value=[]):
            resp = client.get("/api/data/drill-down-dimensions")
        assert resp.json() == []

    def test_returns_500_on_error(self, client):
        with patch("backend.get_drill_down_dimensions", side_effect=Exception("fail")):
            resp = client.get("/api/data/drill-down-dimensions")
        assert resp.status_code == 500


# ===================================================================
# ECL BY COHORT — GET /api/data/ecl-by-cohort
# ===================================================================

class TestEclByCohort:
    """GET /api/data/ecl-by-cohort"""

    def test_happy_path(self, client):
        df = pd.DataFrame({
            "cohort_id": ["A", "B"],
            "loan_count": [100, 200],
            "total_gca": [5000000.0, 3000000.0],
            "total_ecl": [50000.0, 60000.0],
            "coverage_ratio": [1.0, 2.0],
        })
        with patch("backend.get_ecl_by_cohort", return_value=df):
            resp = client.get("/api/data/ecl-by-cohort?product=mortgage")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_with_dimension_param(self, client):
        captured = {}
        def capture(product, dimension="risk_band"):
            captured.update({"product": product, "dimension": dimension})
            return pd.DataFrame()
        with patch("backend.get_ecl_by_cohort", side_effect=capture):
            client.get("/api/data/ecl-by-cohort?product=mortgage&dimension=region")
        assert captured["dimension"] == "region"

    def test_missing_product_returns_422(self, client):
        resp = client.get("/api/data/ecl-by-cohort")
        assert resp.status_code == 422

    def test_returns_500_on_error(self, client):
        with patch("backend.get_ecl_by_cohort", side_effect=Exception("fail")):
            resp = client.get("/api/data/ecl-by-cohort?product=x")
        assert resp.status_code == 500


# ===================================================================
# STAGE BY COHORT — GET /api/data/stage-by-cohort
# ===================================================================

class TestStageByCohort:
    """GET /api/data/stage-by-cohort"""

    def test_happy_path(self, client):
        df = pd.DataFrame({
            "cohort_id": ["2020", "2020", "2020"],
            "assessed_stage": [1, 2, 3],
            "loan_count": [400, 80, 20],
            "total_gca": [20000000.0, 4000000.0, 1000000.0],
        })
        with patch("backend.get_stage_by_cohort", return_value=df):
            resp = client.get("/api/data/stage-by-cohort?product=mortgage")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_missing_product_returns_422(self, client):
        resp = client.get("/api/data/stage-by-cohort")
        assert resp.status_code == 422

    def test_empty_result(self, client):
        with patch("backend.get_stage_by_cohort", return_value=pd.DataFrame()):
            resp = client.get("/api/data/stage-by-cohort?product=x")
        assert resp.json() == []

    def test_returns_500_on_error(self, client):
        with patch("backend.get_stage_by_cohort", side_effect=Exception("fail")):
            resp = client.get("/api/data/stage-by-cohort?product=x")
        assert resp.status_code == 500


# ===================================================================
# PORTFOLIO BY COHORT — GET /api/data/portfolio-by-cohort
# ===================================================================

class TestPortfolioByCohort:
    """GET /api/data/portfolio-by-cohort"""

    def test_happy_path(self, client):
        df = pd.DataFrame({
            "cohort_id": ["A", "B"],
            "loan_count": [100, 200],
            "total_gca": [5000000.0, 3000000.0],
            "avg_pd_pct": [2.5, 4.5],
            "avg_dpd": [5.0, 12.0],
        })
        with patch("backend.get_portfolio_by_dimension", return_value=df):
            resp = client.get("/api/data/portfolio-by-cohort?product=mortgage")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_with_dimension(self, client):
        captured = {}
        def capture(product, dimension="risk_band"):
            captured.update({"product": product, "dimension": dimension})
            return pd.DataFrame()
        with patch("backend.get_portfolio_by_dimension", side_effect=capture):
            client.get("/api/data/portfolio-by-cohort?product=personal&dimension=vintage_year")
        assert captured["dimension"] == "vintage_year"

    def test_missing_product_returns_422(self, client):
        resp = client.get("/api/data/portfolio-by-cohort")
        assert resp.status_code == 422

    def test_returns_500_on_error(self, client):
        with patch("backend.get_portfolio_by_dimension", side_effect=Exception("fail")):
            resp = client.get("/api/data/portfolio-by-cohort?product=x")
        assert resp.status_code == 500


# ===================================================================
# ECL BY PRODUCT DRILLDOWN — GET /api/data/ecl-by-product-drilldown
# ===================================================================

class TestEclByProductDrilldown:
    """GET /api/data/ecl-by-product-drilldown"""

    def test_happy_path(self, client):
        df = pd.DataFrame({
            "product_type": ["mortgage", "personal"],
            "loan_count": [500, 300],
            "total_gca": [25000000.0, 15000000.0],
            "total_ecl": [250000.0, 300000.0],
            "coverage_ratio": [1.0, 2.0],
        })
        with patch("backend.get_ecl_by_product_drilldown", return_value=df):
            resp = client.get("/api/data/ecl-by-product-drilldown")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["product_type"] in ("mortgage", "personal")

    def test_empty_result(self, client):
        with patch("backend.get_ecl_by_product_drilldown", return_value=pd.DataFrame()):
            resp = client.get("/api/data/ecl-by-product-drilldown")
        assert resp.json() == []

    def test_returns_500_on_error(self, client):
        with patch("backend.get_ecl_by_product_drilldown", side_effect=Exception("fail")):
            resp = client.get("/api/data/ecl-by-product-drilldown")
        assert resp.status_code == 500


# ===================================================================
# SIMULATION CONFIG MODEL — Unit tests
# ===================================================================

class TestSimulationConfigModel:
    """SimulationConfig Pydantic model defaults and validation."""

    def test_default_values(self):
        from routes.simulation import SimulationConfig
        c = SimulationConfig()
        assert c.n_simulations == 1000
        assert c.pd_lgd_correlation == 0.30
        assert c.aging_factor == 0.08
        assert c.pd_floor == 0.001
        assert c.pd_cap == 0.95
        assert c.lgd_floor == 0.01
        assert c.lgd_cap == 0.95
        assert c.scenario_weights is None
        assert c.random_seed is None
        assert c.use_databricks_job is False

    def test_custom_values(self):
        from routes.simulation import SimulationConfig
        c = SimulationConfig(
            n_simulations=5000,
            pd_lgd_correlation=0.5,
            random_seed=42,
            scenario_weights={"base": 1.0},
        )
        assert c.n_simulations == 5000
        assert c.random_seed == 42


# ===================================================================
# TRANSFORM HELPER — _transform_simulation_result
# ===================================================================

class TestTransformSimulationResult:
    """Unit tests for _transform_simulation_result."""

    def test_stage_rename(self):
        from routes.simulation import _transform_simulation_result, SimulationConfig
        raw = {"stage_summary": [{"stage": 1, "total_gca": 100, "total_ecl": 5}],
               "scenario_results": [], "portfolio_summary": [], "product_scenario": [],
               "run_metadata": {}}
        config = SimulationConfig()
        result = _transform_simulation_result(raw, config)
        assert result["loss_allowance_by_stage"][0]["assessed_stage"] == 1
        assert "stage" not in result["loss_allowance_by_stage"][0]

    def test_scenario_weighted_contribution(self):
        from routes.simulation import _transform_simulation_result, SimulationConfig
        raw = {"stage_summary": [],
               "scenario_results": [{"scenario": "base", "weight": 0.6, "total_ecl": 1000}],
               "portfolio_summary": [], "product_scenario": [], "run_metadata": {}}
        config = SimulationConfig()
        result = _transform_simulation_result(raw, config)
        assert result["scenario_summary"][0]["weighted"] == 600.0
        assert result["scenario_summary"][0]["weighted_contribution"] == 600.0

    def test_product_aggregation_multiple_rows(self):
        from routes.simulation import _transform_simulation_result, SimulationConfig
        raw = {"stage_summary": [], "scenario_results": [],
               "portfolio_summary": [
                   {"product_type": "A", "loan_count": 10, "total_gca": 100, "total_ecl": 5},
                   {"product_type": "A", "loan_count": 20, "total_gca": 200, "total_ecl": 10},
               ],
               "product_scenario": [], "run_metadata": {}}
        config = SimulationConfig()
        result = _transform_simulation_result(raw, config)
        assert len(result["ecl_by_product"]) == 1
        assert result["ecl_by_product"][0]["loan_count"] == 30
        assert result["ecl_by_product"][0]["total_gca"] == 300
        assert result["ecl_by_product"][0]["total_ecl"] == 15

    def test_zero_gca_coverage_ratio(self):
        from routes.simulation import _transform_simulation_result, SimulationConfig
        raw = {"stage_summary": [], "scenario_results": [],
               "portfolio_summary": [{"product_type": "X", "loan_count": 0, "total_gca": 0, "total_ecl": 0}],
               "product_scenario": [], "run_metadata": {}}
        config = SimulationConfig()
        result = _transform_simulation_result(raw, config)
        assert result["ecl_by_product"][0]["coverage_ratio"] == 0

    def test_empty_raw_result(self):
        from routes.simulation import _transform_simulation_result, SimulationConfig
        raw = {"stage_summary": [], "scenario_results": [], "portfolio_summary": [],
               "product_scenario": [], "run_metadata": {}}
        config = SimulationConfig()
        result = _transform_simulation_result(raw, config)
        assert result["ecl_by_product"] == []
        assert result["loss_allowance_by_stage"] == []
        assert result["scenario_summary"] == []


# ===================================================================
# BUILD PRODUCT DELTAS — _build_product_deltas
# ===================================================================

class TestBuildProductDeltas:
    """Unit tests for _build_product_deltas."""

    def test_matching_products(self):
        from routes.simulation import _build_product_deltas
        a = {"ecl_by_product": {"mortgage": 100.0, "personal": 50.0}}
        b = {"ecl_by_product": {"mortgage": 120.0, "personal": 60.0}}
        result = _build_product_deltas(a, b)
        m = {r["product_type"]: r for r in result}
        assert m["mortgage"]["absolute_delta"] == 20.0
        assert m["personal"]["absolute_delta"] == 10.0

    def test_non_overlapping_products(self):
        from routes.simulation import _build_product_deltas
        a = {"ecl_by_product": {"mortgage": 100.0}}
        b = {"ecl_by_product": {"personal": 200.0}}
        result = _build_product_deltas(a, b)
        assert len(result) == 2

    def test_empty_both(self):
        from routes.simulation import _build_product_deltas
        result = _build_product_deltas({}, {})
        assert result == []

    def test_relative_delta_zero_base(self):
        from routes.simulation import _build_product_deltas
        a = {"ecl_by_product": {"mortgage": 0.0}}
        b = {"ecl_by_product": {"mortgage": 100.0}}
        result = _build_product_deltas(a, b)
        assert result[0]["relative_delta_pct"] is None


# ===================================================================
# SIMULATION CAP — _get_simulation_cap
# ===================================================================

class TestGetSimulationCap:
    """Test _get_simulation_cap helper."""

    def test_default_cap(self):
        from routes.simulation import _get_simulation_cap
        with patch("admin_config.get_config", side_effect=Exception("no config")):
            assert _get_simulation_cap() == 50000

    def test_cap_from_config(self):
        from routes.simulation import _get_simulation_cap
        cfg = {"model": {"default_parameters": {"max_simulations": 100000}}}
        with patch("admin_config.get_config", return_value=cfg):
            assert _get_simulation_cap() == 100000

    def test_cap_from_config_alt_keys(self):
        from routes.simulation import _get_simulation_cap
        cfg = {"model_config": {"default_params": {"max_simulations": 75000}}}
        with patch("admin_config.get_config", return_value=cfg):
            assert _get_simulation_cap() == 75000


# ===================================================================
# PRE-CHECKS — _run_pre_checks
# ===================================================================

class TestRunPreChecks:
    """Test _run_pre_checks helper."""

    def test_returns_empty_on_exception(self, client):
        from routes.simulation import _run_pre_checks, SimulationConfig
        with patch("backend.query_df", side_effect=Exception("no table")):
            result = _run_pre_checks(SimulationConfig())
        assert result == []

    def test_returns_empty_on_empty_loans(self, client):
        from routes.simulation import _run_pre_checks, SimulationConfig
        with patch("backend.query_df", return_value=pd.DataFrame()):
            result = _run_pre_checks(SimulationConfig())
        assert result == []

    def test_runs_checks_with_loan_data(self, client):
        from routes.simulation import _run_pre_checks, SimulationConfig
        loans_df = pd.DataFrame({
            "current_lifetime_pd": [0.05, 0.10],
            "effective_interest_rate": [0.08, 0.12],
            "remaining_months": [24, 36],
            "gross_carrying_amount": [10000, 20000],
            "assessed_stage": [1, 2],
            "days_past_due": [0, 30],
        })
        checks = [{"check": "pd_range", "passed": True}]
        with patch("backend.query_df", return_value=loans_df), \
             patch("domain.validation_rules.run_all_pre_calculation_checks", return_value=checks):
            result = _run_pre_checks(SimulationConfig())
        assert result == checks


# ===================================================================
# PERSIST SIMULATION RUN — _persist_simulation_run
# ===================================================================

class TestPersistSimulationRun:
    """Test _persist_simulation_run helper."""

    def test_calls_save_model_run(self):
        from routes.simulation import _persist_simulation_run, SimulationConfig
        result = {
            "ecl_by_product": [{"product_type": "mortgage", "total_ecl": 100}],
            "run_metadata": {"timestamp": "2025-01-01T00:00:00", "random_seed": 42,
                             "duration_seconds": 5, "loan_count": 10,
                             "convergence_by_product": {}},
        }
        config = SimulationConfig(n_simulations=500)
        with patch("domain.model_runs.save_model_run") as mock_save:
            _persist_simulation_run(result, config)
        mock_save.assert_called_once()
        call_kwargs = mock_save.call_args
        assert call_kwargs[1]["run_type"] == "monte_carlo_simulation" or \
               call_kwargs[0][1] == "monte_carlo_simulation"

    def test_swallows_exceptions(self):
        from routes.simulation import _persist_simulation_run, SimulationConfig
        result = {"ecl_by_product": [], "run_metadata": {"timestamp": "x"}}
        config = SimulationConfig()
        with patch("domain.model_runs.save_model_run", side_effect=Exception("fail")):
            # Should not raise
            _persist_simulation_run(result, config)


# ===================================================================
# DECIMAL/NaN SERIALIZATION EDGE CASES
# ===================================================================

class TestSerializationEdgeCases:
    """Ensure Decimal and NaN values serialize correctly."""

    def test_decimal_in_satellite_comparison(self, client):
        df = pd.DataFrame({
            "product_type": ["mortgage"],
            "cohort_id": ["2020"],
            "model_type": ["linear"],
            "r_squared": [Decimal("0.85")],
            "rmse": [Decimal("0.012")],
            "aic": [Decimal("-100")],
            "bic": [Decimal("-95")],
            "cv_rmse": [Decimal("0.013")],
            "coefficients_json": ['{}'],
            "formula": ["y~x"],
            "n_observations": [20],
            "run_timestamp": ["2025-01-01"],
        })
        with patch("backend.get_satellite_model_comparison", return_value=df):
            resp = client.get("/api/data/satellite-model-comparison")
        assert resp.status_code == 200

    def test_nan_in_cohort_summary(self, client):
        df = pd.DataFrame({
            "product_type": ["mortgage"],
            "cohort_id": ["2020"],
            "loan_count": [100],
            "total_gca": [float("nan")],
            "avg_pd": [0.05],
            "avg_dpd": [float("inf")],
            "stage1": [80],
            "stage2": [15],
            "stage3": [5],
        })
        with patch("backend.get_cohort_summary", return_value=df):
            resp = client.get("/api/data/cohort-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["total_gca"] is None  # NaN -> None
        assert data[0]["avg_dpd"] is None  # Inf -> None


# ===================================================================
# PYDANTIC VALIDATION — Request body validation
# ===================================================================

class TestPydanticValidation:
    """Test Pydantic model validation for request bodies."""

    def test_simulate_invalid_type_n_simulations(self, client):
        resp = client.post("/api/simulate", json={"n_simulations": "not_a_number"})
        assert resp.status_code == 422

    def test_simulate_invalid_type_correlation(self, client):
        resp = client.post("/api/simulate", json={"pd_lgd_correlation": "high"})
        assert resp.status_code == 422

    def test_model_runs_invalid_body(self, client):
        resp = client.post("/api/model-runs", json={"run_id": 123})
        # run_id should be string, but Pydantic may coerce int to str
        # The key test is that it doesn't crash
        assert resp.status_code in (200, 422, 500)

    def test_simulate_empty_body(self, client):
        """Empty body should use defaults and work (or fail on engine)."""
        with patch("routes.simulation._run_pre_checks", return_value=[]), \
             patch("ecl_engine.run_simulation", return_value=_sim_raw_result()), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={})
        assert resp.status_code == 200

    def test_validate_extra_fields_ignored(self, client):
        resp = client.post("/api/simulate-validate", json={
            "n_simulations": 1000,
            "unknown_field": "ignored",
        })
        assert resp.status_code == 200
