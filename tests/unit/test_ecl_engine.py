"""
Unit tests for the Monte Carlo ECL simulation engine.

Tests convergence checks, simulation output structure, default parameters,
and edge cases like empty loan portfolios.
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from conftest import PRODUCT_TYPES, SCENARIOS


class TestConvergenceCheck:
    """Test _convergence_check with known inputs."""

    def test_basic_convergence(self):
        import ecl_engine
        n_loans, n_sims = 10, 100
        rng = np.random.default_rng(42)
        ecl_sims = rng.uniform(100, 200, (n_loans, n_sims))

        result = ecl_engine._convergence_check(ecl_sims, n_sims)

        assert "ecl_at_25pct_sims" in result
        assert "ecl_at_50pct_sims" in result
        assert "ecl_at_75pct_sims" in result
        assert "ecl_at_100pct_sims" in result
        assert "coefficient_of_variation" in result

    def test_convergence_cv_near_zero_for_stable_data(self):
        import ecl_engine
        n_loans, n_sims = 5, 1000
        ecl_sims = np.ones((n_loans, n_sims)) * 100.0

        result = ecl_engine._convergence_check(ecl_sims, n_sims)
        assert result["coefficient_of_variation"] == pytest.approx(0.0, abs=1e-4)

    def test_convergence_values_are_positive(self):
        import ecl_engine
        n_loans, n_sims = 5, 50
        ecl_sims = np.abs(np.random.default_rng(1).standard_normal((n_loans, n_sims))) * 1000

        result = ecl_engine._convergence_check(ecl_sims, n_sims)
        assert result["ecl_at_25pct_sims"] > 0
        assert result["ecl_at_100pct_sims"] > 0


class TestConvergenceCheckFromPaths:
    """Test _convergence_check_from_paths with portfolio-level path totals."""

    def test_basic_path_convergence(self):
        import ecl_engine
        n_sims = 200
        paths = np.random.default_rng(42).uniform(1000, 5000, n_sims)

        result = ecl_engine._convergence_check_from_paths(paths, n_sims)

        assert "ecl_at_25pct_sims" in result
        assert "ecl_at_100pct_sims" in result
        assert "coefficient_of_variation" in result
        assert result["coefficient_of_variation"] >= 0

    def test_constant_paths_zero_cv(self):
        import ecl_engine
        paths = np.full(100, 5000.0)
        result = ecl_engine._convergence_check_from_paths(paths, 100)
        assert result["coefficient_of_variation"] == pytest.approx(0.0, abs=1e-6)

    def test_single_path_no_division_error(self):
        import ecl_engine
        paths = np.array([5000.0])
        result = ecl_engine._convergence_check_from_paths(paths, 1)
        assert np.isfinite(result["coefficient_of_variation"])

    def test_nan_in_paths_handled(self):
        import ecl_engine
        paths = np.array([1000.0, np.nan, 2000.0, 3000.0])
        result = ecl_engine._convergence_check_from_paths(paths, 4)
        assert np.isfinite(result["coefficient_of_variation"])


class TestRunSimulation:
    """Test run_simulation with mocked data loaders."""

    @pytest.fixture
    def mock_loaders(self, sample_loans_df, sample_scenarios_df):
        """Patch _load_loans and _load_scenarios to return fixture data."""
        with patch("ecl_engine._load_loans", return_value=sample_loans_df), \
             patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df):
            yield

    def test_returns_correct_structure(self, mock_loaders):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=50)

        assert "portfolio_summary" in result
        assert "scenario_results" in result
        assert "product_scenario" in result
        assert "stage_summary" in result
        assert "run_metadata" in result

    def test_scenario_weights_sum_to_one(self, mock_loaders):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=50)

        total_weight = sum(s["weight"] for s in result["scenario_results"])
        assert total_weight == pytest.approx(1.0, abs=0.01)

    def test_ecl_values_non_negative(self, mock_loaders):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=50)

        for scenario in result["scenario_results"]:
            assert scenario["total_ecl"] >= 0, \
                f"Negative ECL for scenario {scenario['scenario']}"
            assert scenario["ecl_mean"] >= 0

    def test_portfolio_summary_has_products(self, mock_loaders, sample_loans_df):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=50)

        products_in_result = {r["product_type"] for r in result["portfolio_summary"]}
        products_in_input = set(sample_loans_df["product_type"].unique())
        assert products_in_result == products_in_input

    def test_run_metadata_fields(self, mock_loaders):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=50, pd_lgd_correlation=0.25)

        meta = result["run_metadata"]
        assert meta["n_sims"] == 50
        assert meta["pd_lgd_correlation"] == 0.25
        assert meta["loan_count"] == 20
        assert meta["duration_seconds"] >= 0
        assert "timestamp" in meta

    def test_progress_callback_called(self, mock_loaders):
        import ecl_engine
        events = []

        def callback(event):
            events.append(event)

        ecl_engine.run_simulation(n_sims=50, progress_callback=callback)

        phases = [e["phase"] for e in events]
        assert "loading" in phases
        assert "computing" in phases
        assert "aggregating" in phases
        assert "done" in phases

        done_events = [e for e in events if e["phase"] == "done"]
        assert len(done_events) == 1
        assert done_events[0]["progress"] == 100

    def test_custom_scenario_weights(self, mock_loaders):
        import ecl_engine
        subset = [SCENARIOS[0], SCENARIOS[-1]] if len(SCENARIOS) >= 2 else SCENARIOS[:1]
        remaining = round(1.0 / len(subset), 2)
        custom_weights = {s: remaining for s in subset}
        result = ecl_engine.run_simulation(n_sims=50, scenario_weights=custom_weights)

        result_scenarios = {s["scenario"] for s in result["scenario_results"]}
        assert result_scenarios == set(custom_weights.keys())

    def test_stage_summary_covers_all_stages(self, mock_loaders, sample_loans_df):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=50)

        stages_in_result = {r["stage"] for r in result["stage_summary"]}
        stages_in_input = set(sample_loans_df["assessed_stage"].unique())
        assert stages_in_result == stages_in_input

    def test_product_scenario_cross_product(self, mock_loaders, sample_loans_df):
        import ecl_engine
        result = ecl_engine.run_simulation(n_sims=50)

        n_products = sample_loans_df["product_type"].nunique()
        n_scenarios = len(ecl_engine.DEFAULT_SCENARIO_WEIGHTS)
        assert len(result["product_scenario"]) == n_products * n_scenarios


class TestRunSimulationEdgeCases:
    """Edge cases for the simulation engine."""

    def test_empty_loans_raises_value_error(self, sample_scenarios_df):
        import ecl_engine
        empty_df = pd.DataFrame(columns=[
            "loan_id", "product_type", "assessed_stage",
            "gross_carrying_amount", "effective_interest_rate",
            "current_lifetime_pd", "remaining_months",
        ])
        with patch("ecl_engine._load_loans", return_value=empty_df), \
             patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df):
            with pytest.raises(ValueError, match="No loans found"):
                ecl_engine.run_simulation(n_sims=10)

    def test_zero_eir_loans_produce_valid_ecl(self, sample_scenarios_df):
        """Loans with zero EIR should not produce NaN/Inf via division."""
        import ecl_engine
        rng = np.random.default_rng(42)
        loans = pd.DataFrame({
            "loan_id": [f"LN-{i}" for i in range(5)],
            "product_type": ["personal_loan"] * 5,
            "assessed_stage": [1, 1, 2, 2, 3],
            "gross_carrying_amount": [10000.0] * 5,
            "effective_interest_rate": [0.0, 0.0, 0.0, 0.0, 0.0],
            "current_lifetime_pd": [0.05, 0.10, 0.20, 0.30, 0.80],
            "remaining_months": [12, 24, 36, 48, 12],
        })
        with patch("ecl_engine._load_loans", return_value=loans), \
             patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df):
            result = ecl_engine.run_simulation(n_sims=50, random_seed=42)

        for s in result["scenario_results"]:
            assert np.isfinite(s["total_ecl"]), f"NaN/Inf ECL for scenario {s['scenario']}"
        for r in result["portfolio_summary"]:
            assert np.isfinite(r["total_ecl"]), "NaN/Inf in portfolio summary"

    def test_single_simulation_run(self, sample_loans_df, sample_scenarios_df):
        """n_sims=1 should produce valid results without division-by-zero in std."""
        import ecl_engine
        with patch("ecl_engine._load_loans", return_value=sample_loans_df), \
             patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df):
            result = ecl_engine.run_simulation(n_sims=1, random_seed=42)

        meta = result["run_metadata"]
        assert meta["n_sims"] == 1
        for prod_conv in meta["convergence_by_product"].values():
            assert np.isfinite(prod_conv["std_ecl"])
            assert np.isfinite(prod_conv["ci_95_width"])

    def test_empty_scenario_weights_falls_back_to_defaults(self, sample_loans_df, sample_scenarios_df):
        """Empty scenario weights dict falls back to DEFAULT_SCENARIO_WEIGHTS."""
        import ecl_engine
        with patch("ecl_engine._load_loans", return_value=sample_loans_df), \
             patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df):
            result = ecl_engine.run_simulation(n_sims=10, scenario_weights={})
        assert len(result["scenario_results"]) == len(ecl_engine.DEFAULT_SCENARIO_WEIGHTS)

    def test_extreme_pd_values_clipped(self, sample_scenarios_df):
        """PD values > 1.0 or < 0 should be clipped in prepare_loan_columns."""
        from ecl.monte_carlo import prepare_loan_columns
        loans = pd.DataFrame({
            "loan_id": ["L1", "L2", "L3"],
            "product_type": ["personal_loan"] * 3,
            "assessed_stage": [1, 2, 3],
            "gross_carrying_amount": [10000.0, 20000.0, 5000.0],
            "effective_interest_rate": [0.10, 0.15, 0.20],
            "current_lifetime_pd": [-0.05, 1.5, 0.50],
            "remaining_months": [12, 24, 36],
        })
        prepared = prepare_loan_columns(loans, {"personal_loan": 0.50})
        assert (prepared["base_pd"] >= 0.0).all()
        assert (prepared["base_pd"] <= 1.0).all()
        assert (prepared["eir"] >= 0.001).all()


class TestSprint1EdgeCaseFixes:
    """Regression tests for Sprint 1 Monte Carlo edge case fixes."""

    def test_n_sims_zero_raises(self, sample_loans_df, sample_scenarios_df):
        import ecl_engine
        with patch("ecl_engine._load_loans", return_value=sample_loans_df), \
             patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df):
            with pytest.raises(ValueError, match="n_sims must be >= 1"):
                ecl_engine.run_simulation(n_sims=0)

    def test_n_sims_negative_raises(self, sample_loans_df, sample_scenarios_df):
        import ecl_engine
        with patch("ecl_engine._load_loans", return_value=sample_loans_df), \
             patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df):
            with pytest.raises(ValueError, match="n_sims must be >= 1"):
                ecl_engine.run_simulation(n_sims=-5)

    def test_convergence_check_single_sim(self):
        from ecl.helpers import _convergence_check
        ecl_sims = np.array([[100.0], [200.0], [50.0]])
        result = _convergence_check(ecl_sims, 1)
        assert result["coefficient_of_variation"] == 0.0
        assert result["ecl_at_100pct_sims"] == 350.0

    def test_convergence_check_from_paths_single_sim(self):
        from ecl.helpers import _convergence_check_from_paths
        paths = np.array([5000.0])
        result = _convergence_check_from_paths(paths, 1)
        assert result["coefficient_of_variation"] == 0.0
        assert result["ecl_at_100pct_sims"] == 5000.0

    def test_eir_floor_assertion(self):
        from ecl.monte_carlo import prepare_loan_columns
        loans = pd.DataFrame({
            "loan_id": ["L1"], "product_type": ["personal_loan"],
            "assessed_stage": [1], "gross_carrying_amount": [10000.0],
            "effective_interest_rate": [0.0], "current_lifetime_pd": [0.05],
            "remaining_months": [12],
        })
        prepared = prepare_loan_columns(loans, {"personal_loan": 0.50})
        assert (prepared["eir"] >= 0.001).all()

    def test_nan_in_ecl_batch_cleaned(self):
        from ecl.monte_carlo import run_scenario_sims
        rng = np.random.default_rng(42)
        n_loans, n_sims = 3, 10
        result = run_scenario_sims(
            rng=rng, n_loans=n_loans, n_sims=n_sims, batch_size=10,
            rho_1d=np.full(n_loans, 0.3), base_pd=np.array([0.05, 0.10, 0.20]),
            base_lgd_arr=np.array([0.45, 0.50, 0.55]),
            pd_mult=1.0, lgd_mult=1.0, pd_vol=0.05, lgd_vol=0.03,
            pd_floor=0.001, pd_cap=0.95, lgd_floor=0.01, lgd_cap=0.95,
            aging_factor=0.08, is_stage_23_1d=np.array([False, True, True]),
            max_horizon=np.array([4, 8, 8]), global_max_q=8,
            quarterly_prepay=np.array([0.01, 0.01, 0.01]),
            rem_months_f=np.array([12.0, 24.0, 36.0]),
            is_bullet=np.array([False, False, False]),
            gca=np.array([10000.0, 20000.0, 5000.0]),
            eir=np.array([0.10, 0.15, 0.20]),
            products=np.array(["a", "a", "b"]),
            unique_products=np.array(["a", "b"]),
            product_sim_ecls={"a": np.zeros(n_sims), "b": np.zeros(n_sims)},
            w=0.5,
        )
        loan_ecl, path_ecls = result
        assert np.all(np.isfinite(loan_ecl))
        assert np.all(np.isfinite(path_ecls))


class TestGetDefaults:
    """Test get_defaults with mocked scenario data."""

    def test_returns_expected_keys(self, sample_scenarios_df):
        import ecl_engine
        with patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df), \
             patch("ecl_engine.backend.query_df", side_effect=Exception("no table")):
            result = ecl_engine.get_defaults()

        assert "scenarios" in result
        assert "default_weights" in result
        assert "products" in result
        assert "default_params" in result

    def test_default_params_values(self, sample_scenarios_df):
        import ecl_engine
        with patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df), \
             patch("ecl_engine.backend.query_df", side_effect=Exception("no table")):
            result = ecl_engine.get_defaults()

        params = result["default_params"]
        assert params["n_sims"] == 1000
        assert params["pd_lgd_correlation"] == 0.30
        assert params["pd_floor"] == 0.001
        assert params["pd_cap"] == 0.95

    def test_scenarios_match_input(self, sample_scenarios_df):
        import ecl_engine
        with patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df), \
             patch("ecl_engine.backend.query_df", side_effect=Exception("no table")):
            result = ecl_engine.get_defaults()

        scenario_names = [s["scenario"] for s in result["scenarios"]]
        assert len(scenario_names) == len(sample_scenarios_df)

    def test_products_include_all_configured(self, sample_scenarios_df):
        import ecl_engine
        with patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df), \
             patch("ecl_engine.backend.query_df", side_effect=Exception("no table")), \
             patch("admin_config.backend.query_df", side_effect=Exception("no table")):
            result = ecl_engine.get_defaults()

        product_names = [p["product_type"] for p in result["products"]]
        assert set(product_names) == set(ecl_engine.BASE_LGD.keys())

    def test_default_weights_sum_to_one(self, sample_scenarios_df):
        import ecl_engine
        with patch("ecl_engine._load_scenarios", return_value=sample_scenarios_df), \
             patch("ecl_engine.backend.query_df", side_effect=Exception("no table")):
            result = ecl_engine.get_defaults()

        total = sum(result["default_weights"].values())
        assert total == pytest.approx(1.0, abs=0.01)
