"""Sprint 1 (Run 6): Fix simulation debt — seed persistence, per-product compare, configurable cap, jobs config."""
import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../app"))


class TestJobsConfigEndpoint:
    """Fix pre-existing test_get_jobs_config failure — job_ids in response."""

    @pytest.fixture
    def client(self):
        with patch("db.pool._pool", MagicMock()):
            with patch("db.pool.query_df") as mock_qdf:
                mock_qdf.return_value = MagicMock(empty=True)
                from app import app
                from fastapi.testclient import TestClient
                return TestClient(app)

    @pytest.fixture
    def mock_jobs(self):
        with patch("jobs._get_workspace_client") as mock_ws:
            mock_ws.return_value = MagicMock()
            with patch("jobs._get_job_ids", return_value={"satellite_ecl_sync": 123}):
                with patch("jobs.get_jobs_status", return_value={"scripts_base": "/test", "jobs": {}}):
                    yield

    def test_jobs_config_has_job_ids(self, client, mock_jobs):
        resp = client.get("/api/jobs/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "job_ids" in data
        assert "available_models" in data
        assert data["job_ids"] == {"satellite_ecl_sync": 123}

    def test_jobs_config_has_available_models(self, client, mock_jobs):
        resp = client.get("/api/jobs/config")
        data = resp.json()
        assert len(data["available_models"]) == 8


class TestSimulationCapConfigurable:
    """Simulation cap should come from admin config, not hardcoded."""

    def test_get_simulation_cap_default(self):
        from routes.simulation import _get_simulation_cap
        with patch("admin_config.get_config", side_effect=Exception("no db")):
            assert _get_simulation_cap() == 50000

    def test_get_simulation_cap_from_config(self):
        from routes.simulation import _get_simulation_cap
        mock_cfg = {"model": {"default_parameters": {"max_simulations": 100000}}}
        with patch("admin_config.get_config", return_value=mock_cfg):
            assert _get_simulation_cap() == 100000

    def test_validate_respects_configurable_cap(self):
        from routes.simulation import validate_simulation, SimulationConfig
        with patch("routes.simulation._get_simulation_cap", return_value=10000):
            config = SimulationConfig(n_simulations=15000)
            result = validate_simulation(config)
            assert not result["valid"]
            assert any("10,000" in e for e in result["errors"])

    def test_validate_passes_within_cap(self):
        from routes.simulation import validate_simulation, SimulationConfig
        with patch("routes.simulation._get_simulation_cap", return_value=100000):
            config = SimulationConfig(n_simulations=75000)
            result = validate_simulation(config)
            # Should not have a cap error
            cap_errors = [e for e in result["errors"] if "Maximum" in e]
            assert len(cap_errors) == 0


class TestSeedPersistence:
    """Simulation seed should be persisted to model_runs DB."""

    def test_persist_simulation_run_called(self):
        from routes.simulation import _persist_simulation_run, SimulationConfig
        config = SimulationConfig(n_simulations=100)
        result = {
            "run_metadata": {"random_seed": 42, "timestamp": "2026-01-01T00:00:00", "duration_seconds": 5.0, "loan_count": 100},
            "ecl_by_product": [{"product_type": "mortgage", "total_ecl": 1000.0, "total_gca": 50000.0}],
        }
        with patch("domain.model_runs.save_model_run") as mock_save:
            mock_save.return_value = {"run_id": "sim_2026-01-01T00:00:00"}
            _persist_simulation_run(result, config)
            mock_save.assert_called_once()
            call_kwargs = mock_save.call_args
            assert call_kwargs[1]["run_type"] == "monte_carlo_simulation" or call_kwargs[0][1] == "monte_carlo_simulation"

    def test_persist_simulation_run_includes_seed(self):
        from routes.simulation import _persist_simulation_run, SimulationConfig
        config = SimulationConfig(n_simulations=500, random_seed=12345)
        result = {
            "run_metadata": {"random_seed": 12345, "timestamp": "2026-01-01T00:00:00", "duration_seconds": 2.0, "loan_count": 50},
            "ecl_by_product": [{"product_type": "personal_loan", "total_ecl": 500.0, "total_gca": 10000.0}],
        }
        with patch("domain.model_runs.save_model_run") as mock_save:
            mock_save.return_value = {}
            _persist_simulation_run(result, config)
            call_args = mock_save.call_args
            summary = call_args[1].get("best_model_summary") or call_args[0][5]
            assert summary["random_seed"] == 12345
            assert summary["n_simulations"] == 500

    def test_persist_failure_does_not_raise(self):
        from routes.simulation import _persist_simulation_run, SimulationConfig
        config = SimulationConfig(n_simulations=100)
        result = {"run_metadata": {}, "ecl_by_product": []}
        with patch("domain.model_runs.save_model_run", side_effect=Exception("DB down")):
            # Should not raise
            _persist_simulation_run(result, config)


class TestPerProductComparison:
    """Simulation compare should include per-product ECL deltas."""

    def test_build_product_deltas_basic(self):
        from routes.simulation import _build_product_deltas
        summary_a = {"ecl_by_product": {"mortgage": 1000, "personal_loan": 500}}
        summary_b = {"ecl_by_product": {"mortgage": 1200, "personal_loan": 450}}
        deltas = _build_product_deltas(summary_a, summary_b)
        assert len(deltas) == 2
        mortgage = next(d for d in deltas if d["product_type"] == "mortgage")
        assert mortgage["absolute_delta"] == 200.0
        assert mortgage["relative_delta_pct"] == 20.0

    def test_build_product_deltas_missing_product(self):
        from routes.simulation import _build_product_deltas
        summary_a = {"ecl_by_product": {"mortgage": 1000}}
        summary_b = {"ecl_by_product": {"mortgage": 1100, "auto_loan": 300}}
        deltas = _build_product_deltas(summary_a, summary_b)
        assert len(deltas) == 2
        auto = next(d for d in deltas if d["product_type"] == "auto_loan")
        assert auto["run_a_ecl"] == 0
        assert auto["run_b_ecl"] == 300

    def test_build_product_deltas_empty(self):
        from routes.simulation import _build_product_deltas
        deltas = _build_product_deltas({}, {})
        assert deltas == []

    def test_compare_endpoint_includes_product_deltas(self):
        from routes.simulation import compare_simulation_runs
        mock_run_a = {
            "run_timestamp": "2026-01-01", "run_type": "monte_carlo_simulation",
            "products": ["mortgage"], "best_model_summary": {
                "total_ecl": 1000, "random_seed": 42,
                "ecl_by_product": {"mortgage": 800, "personal_loan": 200},
            },
        }
        mock_run_b = {
            "run_timestamp": "2026-01-02", "run_type": "monte_carlo_simulation",
            "products": ["mortgage"], "best_model_summary": {
                "total_ecl": 1100, "random_seed": 99,
                "ecl_by_product": {"mortgage": 900, "personal_loan": 200},
            },
        }
        with patch("domain.model_runs.get_model_run", side_effect=[mock_run_a, mock_run_b]):
            result = compare_simulation_runs("run_a", "run_b")
            assert "product_deltas" in result
            assert len(result["product_deltas"]) == 2
            assert result["run_a"]["seed"] == 42
            assert result["run_b"]["seed"] == 99
            assert result["summary"]["products_compared"] == 2

    def test_compare_endpoint_404_missing_run(self):
        with patch("domain.model_runs.get_model_run", side_effect=[None, None]):
            with pytest.raises(Exception):
                from routes.simulation import compare_simulation_runs
                compare_simulation_runs("missing_a", "missing_b")


class TestAdminConfigMaxSimulations:
    """max_simulations should be in admin config defaults."""

    def test_max_simulations_in_model_config(self):
        from admin_config import MODEL_CONFIG
        assert "max_simulations" in MODEL_CONFIG["default_parameters"]
        assert MODEL_CONFIG["default_parameters"]["max_simulations"] == 50000
