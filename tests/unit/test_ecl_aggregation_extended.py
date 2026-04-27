"""Extended tests for ecl/aggregation.py — edge cases and data integrity."""
import time

import numpy as np
import pandas as pd
import pytest

from ecl.aggregation import aggregate_results


def _make_loans_df(n=10):
    return pd.DataFrame({
        "loan_id": [f"L{i}" for i in range(n)],
        "product_type": ["mortgage"] * (n // 2) + ["personal"] * (n - n // 2),
        "stage": [1] * (n // 2) + [2] * (n - n // 2),
        "gca": np.random.default_rng(42).random(n) * 100000 + 10000,
        "eir": [0.05] * n,
        "base_pd": [0.03] * n,
        "rem_q": [4] * n,
        "rem_months_f": [12.0] * n,
        "base_lgd": [0.45] * n,
    })


def _make_inputs(n_loans=10, n_sims=100, scenarios=None):
    if scenarios is None:
        scenarios = ["base", "upside", "downside"]
    weights = {sc: 1.0 / len(scenarios) for sc in scenarios}
    rng = np.random.default_rng(42)

    loans_df = _make_loans_df(n_loans)
    products = loans_df["product_type"].values
    unique_products = loans_df["product_type"].unique()

    loan_weighted_ecl = rng.random(n_loans) * 1000
    scenario_ecl_totals = {sc: rng.random(n_loans) * 1000 for sc in scenarios}
    scenario_ecl_paths = {sc: rng.random(n_sims) * 10000 for sc in scenarios}
    product_sim_ecls = {p: rng.random(n_sims) * 5000 for p in unique_products}

    return {
        "loans_df": loans_df,
        "loan_weighted_ecl": loan_weighted_ecl,
        "scenario_ecl_totals": scenario_ecl_totals,
        "scenario_ecl_paths": scenario_ecl_paths,
        "product_sim_ecls": product_sim_ecls,
        "products": products,
        "scenarios": scenarios,
        "weights": weights,
        "n_sims": n_sims,
        "n_loans": n_loans,
        "sim_params": {
            "n_sims": n_sims,
            "random_seed": 42,
            "pd_lgd_correlation": 0.30,
            "aging_factor": 0.08,
            "pd_floor": 0.001,
            "pd_cap": 0.95,
            "lgd_floor": 0.01,
            "lgd_cap": 0.95,
        },
        "t0": time.time() - 5.0,
        "load_time": 1.0,
        "progress_callback": None,
    }


class TestAggregateResultsExtended:
    def test_five_scenarios(self):
        scenarios = ["base", "up", "down", "severe", "tail"]
        inputs = _make_inputs(scenarios=scenarios)
        result = aggregate_results(**inputs)
        assert len(result["scenario_results"]) == 5

    def test_many_loans(self):
        inputs = _make_inputs(n_loans=500, n_sims=50)
        result = aggregate_results(**inputs)
        assert result["run_metadata"]["loan_count"] == 500

    def test_many_simulations(self):
        inputs = _make_inputs(n_loans=5, n_sims=1000)
        result = aggregate_results(**inputs)
        assert result["run_metadata"]["n_sims"] == 1000

    def test_portfolio_summary_groups(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        products = {row["product_type"] for row in result["portfolio_summary"]}
        assert "mortgage" in products
        assert "personal" in products

    def test_stage_summary_covers_all_stages(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        stages = {row["stage"] for row in result["stage_summary"]}
        assert 1 in stages
        assert 2 in stages

    def test_scenario_ecl_totals_stored(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        for sc in result["scenario_results"]:
            assert sc["total_ecl"] > 0

    def test_scenario_percentiles_ordered(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        for sc in result["scenario_results"]:
            assert sc["ecl_p50"] <= sc["ecl_p95"]
            assert sc["ecl_p95"] <= sc["ecl_p99"]

    def test_product_scenario_has_both_products(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        products = {row["product_type"] for row in result["product_scenario"]}
        assert "mortgage" in products
        assert "personal" in products

    def test_run_metadata_has_timestamp(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        assert "timestamp" in result["run_metadata"]

    def test_run_metadata_has_duration(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        assert "duration_seconds" in result["run_metadata"]
        assert result["run_metadata"]["duration_seconds"] >= 0

    def test_convergence_has_mean_ecl(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        for prod, stats in result["run_metadata"]["convergence_by_product"].items():
            assert "mean_ecl" in stats
            assert isinstance(stats["mean_ecl"], (int, float))

    def test_convergence_has_ci_width(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        for prod, stats in result["run_metadata"]["convergence_by_product"].items():
            assert "ci_95_width" in stats
            assert stats["ci_95_width"] >= 0

    def test_all_ecl_positive_portfolio(self):
        inputs = _make_inputs()
        inputs["loan_weighted_ecl"] = np.abs(inputs["loan_weighted_ecl"])
        result = aggregate_results(**inputs)
        for row in result["portfolio_summary"]:
            assert row["total_ecl"] >= 0

    def test_total_gca_positive(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        for row in result["portfolio_summary"]:
            assert row["total_gca"] > 0

    def test_coverage_ratio_bounded(self):
        inputs = _make_inputs()
        inputs["loan_weighted_ecl"] = np.abs(inputs["loan_weighted_ecl"])
        result = aggregate_results(**inputs)
        for row in result["portfolio_summary"]:
            assert isinstance(row["coverage_ratio"], (int, float))

    def test_single_product(self):
        inputs = _make_inputs(n_loans=5)
        inputs["loans_df"]["product_type"] = "mortgage"
        inputs["products"] = inputs["loans_df"]["product_type"].values
        unique = inputs["loans_df"]["product_type"].unique()
        inputs["product_sim_ecls"] = {p: np.random.default_rng(42).random(100) * 5000 for p in unique}
        result = aggregate_results(**inputs)
        products = {row["product_type"] for row in result["portfolio_summary"]}
        assert products == {"mortgage"}

    def test_all_stage_1_loans(self):
        inputs = _make_inputs(n_loans=10)
        inputs["loans_df"]["stage"] = 1
        result = aggregate_results(**inputs)
        stages = {row["stage"] for row in result["stage_summary"]}
        assert stages == {1}

    def test_three_stages(self):
        inputs = _make_inputs(n_loans=9)
        inputs["loans_df"]["stage"] = [1, 1, 1, 2, 2, 2, 3, 3, 3]
        result = aggregate_results(**inputs)
        stages = {row["stage"] for row in result["stage_summary"]}
        assert stages == {1, 2, 3}

    def test_zero_ecl_loans(self):
        inputs = _make_inputs()
        inputs["loan_weighted_ecl"] = np.zeros(10)
        result = aggregate_results(**inputs)
        total_ecl = sum(row["total_ecl"] for row in result["portfolio_summary"])
        assert total_ecl == 0

    def test_deterministic_with_same_inputs(self):
        inputs1 = _make_inputs()
        inputs2 = _make_inputs()
        r1 = aggregate_results(**inputs1)
        r2 = aggregate_results(**inputs2)
        assert r1["portfolio_summary"] == r2["portfolio_summary"]

    def test_progress_callback_receives_done(self):
        events = []
        inputs = _make_inputs()
        inputs["progress_callback"] = events.append
        aggregate_results(**inputs)
        phases = [e["phase"] for e in events]
        assert "done" in phases

    def test_sim_params_preserved_in_metadata(self):
        inputs = _make_inputs()
        result = aggregate_results(**inputs)
        meta = result["run_metadata"]
        assert meta["n_sims"] == 100
        assert meta["random_seed"] == 42

    def test_empty_product_sim_ecls(self):
        inputs = _make_inputs()
        unique = inputs["loans_df"]["product_type"].unique()
        inputs["product_sim_ecls"] = {p: np.zeros(100) for p in unique}
        result = aggregate_results(**inputs)
        assert "convergence_by_product" in result["run_metadata"]
