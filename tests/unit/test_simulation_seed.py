"""Tests for simulation reproducibility, convergence, and comparison."""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


def _make_loans_df(n=50):
    rng = np.random.default_rng(99)
    return pd.DataFrame({
        "loan_id": [f"L{i}" for i in range(n)],
        "product_type": rng.choice(["mortgage", "personal_loan"], n).tolist(),
        "assessed_stage": rng.choice([1, 1, 1, 2, 3], n).tolist(),
        "gross_carrying_amount": np.round(rng.uniform(5000, 100000, n), 2).tolist(),
        "effective_interest_rate": np.round(rng.uniform(0.03, 0.12, n), 4).tolist(),
        "current_lifetime_pd": np.round(rng.uniform(0.01, 0.3, n), 4).tolist(),
        "remaining_months": rng.integers(6, 60, n).tolist(),
    })


def _make_scenarios_df():
    scenarios = ["baseline", "adverse"]
    return pd.DataFrame({
        "scenario": scenarios,
        "weight": [0.6, 0.4],
        "ecl_mean": [1e6, 1.5e6],
        "ecl_p50": [9e5, 1.4e6],
        "ecl_p75": [1.1e6, 1.6e6],
        "ecl_p95": [1.3e6, 1.8e6],
        "ecl_p99": [1.5e6, 2.0e6],
        "avg_pd_multiplier": [1.0, 1.5],
        "avg_lgd_multiplier": [1.0, 1.2],
        "pd_vol": [0.05, 0.08],
        "lgd_vol": [0.03, 0.05],
    })


@pytest.fixture
def _patch_engine():
    loans = _make_loans_df()
    scenarios = _make_scenarios_df()
    with patch("ecl_engine._load_loans", return_value=loans), \
         patch("ecl_engine._load_scenarios", return_value=scenarios):
        yield loans, scenarios


class TestRandomSeedReproducibility:
    def test_same_seed_same_result(self, _patch_engine):
        import ecl_engine
        result_a = ecl_engine.run_simulation(n_sims=100, random_seed=42)
        result_b = ecl_engine.run_simulation(n_sims=100, random_seed=42)
        ecl_a = sum(r["total_ecl"] for r in result_a["portfolio_summary"])
        ecl_b = sum(r["total_ecl"] for r in result_b["portfolio_summary"])
        assert ecl_a == ecl_b

    def test_different_seed_different_result(self, _patch_engine):
        import ecl_engine
        result_a = ecl_engine.run_simulation(n_sims=200, random_seed=42)
        result_b = ecl_engine.run_simulation(n_sims=200, random_seed=99)
        ecl_a = sum(r["total_ecl"] for r in result_a["portfolio_summary"])
        ecl_b = sum(r["total_ecl"] for r in result_b["portfolio_summary"])
        assert ecl_a != ecl_b

    def test_seed_stored_in_metadata(self, _patch_engine):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=100, random_seed=42)
        assert result["run_metadata"]["random_seed"] == 42

    def test_auto_generated_seed_when_none(self, _patch_engine):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=100, random_seed=None)
        assert result["run_metadata"]["random_seed"] is not None
        assert isinstance(result["run_metadata"]["random_seed"], int)


class TestConvergenceDiagnostics:
    def test_convergence_by_product_present(self, _patch_engine):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=100, random_seed=42)
        conv = result["run_metadata"]["convergence_by_product"]
        assert len(conv) > 0
        for prod, metrics in conv.items():
            assert "mean_ecl" in metrics
            assert "std_ecl" in metrics
            assert "ci_95_width" in metrics
            assert "ci_95_pct" in metrics

    def test_ci_width_decreases_with_more_sims(self, _patch_engine):
        import ecl_engine
        r100 = ecl_engine.run_simulation(n_sims=100, random_seed=42)
        r500 = ecl_engine.run_simulation(n_sims=500, random_seed=42)
        conv_100 = r100["run_metadata"]["convergence_by_product"]
        conv_500 = r500["run_metadata"]["convergence_by_product"]
        for prod in conv_100:
            if prod in conv_500 and conv_100[prod]["ci_95_pct"] > 0:
                assert conv_500[prod]["ci_95_pct"] <= conv_100[prod]["ci_95_pct"] * 1.5

    def test_convergence_values_non_negative(self, _patch_engine):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=100, random_seed=42)
        for prod, metrics in result["run_metadata"]["convergence_by_product"].items():
            assert metrics["std_ecl"] >= 0
            assert metrics["ci_95_width"] >= 0
            assert metrics["ci_95_pct"] >= 0

    def test_ci_width_is_positive_for_stochastic_simulation(self, _patch_engine):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=200, random_seed=42)
        conv = result["run_metadata"]["convergence_by_product"]
        has_positive_ci = any(m["ci_95_width"] > 0 for m in conv.values())
        assert has_positive_ci, "At least one product should have non-zero CI width in a stochastic simulation"


class TestSimulationConfig:
    def test_random_seed_in_config(self):
        from routes.simulation import SimulationConfig
        config = SimulationConfig(random_seed=42)
        assert config.random_seed == 42

    def test_random_seed_optional(self):
        from routes.simulation import SimulationConfig
        config = SimulationConfig()
        assert config.random_seed is None

    def test_cap_raised_to_50000(self):
        from routes.simulation import SimulationConfig
        config = SimulationConfig(n_simulations=50000)
        assert config.n_simulations == 50000


class TestCompareEndpoint:
    def test_compare_returns_deltas(self):
        with patch("domain.model_runs.query_df") as mock_q, \
             patch("domain.model_runs.execute"):
            from domain.model_runs import ensure_model_runs_table
            mock_q.return_value = pd.DataFrame()
            ensure_model_runs_table()

            run_a_data = pd.DataFrame([{
                "run_id": "A", "run_type": "ecl_simulation",
                "models_used": '["linear"]', "products": '["mortgage"]',
                "best_model_summary": '{"total_ecl": 1000000, "avg_pd": 0.05}',
                "total_cohorts": 5, "run_timestamp": "2025-01-01",
                "status": "completed", "notes": "", "created_by": "system",
            }])
            run_b_data = pd.DataFrame([{
                "run_id": "B", "run_type": "ecl_simulation",
                "models_used": '["linear"]', "products": '["mortgage"]',
                "best_model_summary": '{"total_ecl": 1100000, "avg_pd": 0.06}',
                "total_cohorts": 5, "run_timestamp": "2025-01-02",
                "status": "completed", "notes": "", "created_by": "system",
            }])
            mock_q.side_effect = [run_a_data, run_b_data]

            from routes.simulation import compare_simulation_runs
            result = compare_simulation_runs("A", "B")
            assert "deltas" in result
            assert len(result["deltas"]) == 2
            ecl_delta = next(d for d in result["deltas"] if d["metric"] == "total_ecl")
            assert ecl_delta["absolute_delta"] == 100000
            assert ecl_delta["relative_delta_pct"] == 10.0

    def test_compare_missing_run(self):
        with patch("domain.model_runs.query_df") as mock_q, \
             patch("domain.model_runs.execute"):
            mock_q.return_value = pd.DataFrame()
            from routes.simulation import compare_simulation_runs
            with pytest.raises(HTTPException) as exc_info:
                compare_simulation_runs("missing_a", "missing_b")
            assert exc_info.value.status_code == 404

    def test_compare_same_run(self):
        with patch("domain.model_runs.query_df") as mock_q, \
             patch("domain.model_runs.execute"):
            run_data = pd.DataFrame([{
                "run_id": "A", "run_type": "ecl_simulation",
                "models_used": '["linear"]', "products": '["mortgage"]',
                "best_model_summary": '{"total_ecl": 1000000}',
                "total_cohorts": 5, "run_timestamp": "2025-01-01",
                "status": "completed", "notes": "", "created_by": "system",
            }])
            mock_q.side_effect = [run_data.copy(), run_data.copy()]
            from routes.simulation import compare_simulation_runs
            result = compare_simulation_runs("A", "A")
            for delta in result["deltas"]:
                assert delta["absolute_delta"] == 0
