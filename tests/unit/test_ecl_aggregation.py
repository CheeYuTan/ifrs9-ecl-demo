"""Dedicated tests for ecl/aggregation.py — result aggregation and metadata."""
import time

import numpy as np
import pandas as pd
import pytest

from ecl.aggregation import aggregate_results


def _make_loans_df(n=10):
    """Create a minimal loans DataFrame for aggregation."""
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


def _make_aggregation_inputs(n_loans=10, n_sims=100, scenarios=None):
    """Create a full set of aggregation inputs."""
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


class TestAggregateResults:
    def test_basic_output_structure(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        assert "portfolio_summary" in result
        assert "scenario_results" in result
        assert "product_scenario" in result
        assert "stage_summary" in result
        assert "run_metadata" in result

    def test_portfolio_summary_has_data(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        assert len(result["portfolio_summary"]) > 0

    def test_portfolio_summary_fields(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        row = result["portfolio_summary"][0]
        assert "product_type" in row
        assert "stage" in row
        assert "loan_count" in row
        assert "total_gca" in row
        assert "total_ecl" in row
        assert "coverage_ratio" in row

    def test_scenario_results_count(self):
        scenarios = ["base", "upside", "downside"]
        inputs = _make_aggregation_inputs(scenarios=scenarios)
        result = aggregate_results(**inputs)
        assert len(result["scenario_results"]) == 3

    def test_scenario_results_fields(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        sc = result["scenario_results"][0]
        assert "scenario" in sc
        assert "weight" in sc
        assert "total_ecl" in sc
        assert "ecl_mean" in sc
        assert "ecl_p50" in sc
        assert "ecl_p95" in sc
        assert "ecl_p99" in sc

    def test_product_scenario_count(self):
        inputs = _make_aggregation_inputs(scenarios=["base", "upside"])
        result = aggregate_results(**inputs)
        n_products = len(inputs["loans_df"]["product_type"].unique())
        assert len(result["product_scenario"]) == n_products * 2

    def test_stage_summary_has_data(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        assert len(result["stage_summary"]) > 0

    def test_stage_summary_fields(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        row = result["stage_summary"][0]
        assert "stage" in row
        assert "loan_count" in row
        assert "total_gca" in row
        assert "total_ecl" in row

    def test_run_metadata(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        meta = result["run_metadata"]
        assert meta["n_sims"] == 100
        assert meta["random_seed"] == 42
        assert "timestamp" in meta
        assert "duration_seconds" in meta
        assert "loan_count" in meta
        assert "convergence_by_product" in meta

    def test_convergence_by_product(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        conv = result["run_metadata"]["convergence_by_product"]
        assert len(conv) > 0
        for prod, stats in conv.items():
            assert "mean_ecl" in stats
            assert "std_ecl" in stats
            assert "ci_95_width" in stats
            assert "ci_95_pct" in stats

    def test_single_scenario(self):
        inputs = _make_aggregation_inputs(scenarios=["base"])
        result = aggregate_results(**inputs)
        assert len(result["scenario_results"]) == 1

    def test_single_loan(self):
        inputs = _make_aggregation_inputs(n_loans=1, n_sims=10)
        result = aggregate_results(**inputs)
        assert len(result["portfolio_summary"]) >= 1

    def test_progress_callback_called(self):
        events = []
        inputs = _make_aggregation_inputs()
        inputs["progress_callback"] = events.append
        aggregate_results(**inputs)
        assert len(events) >= 2
        phases = [e["phase"] for e in events]
        assert "aggregating" in phases
        assert "done" in phases

    def test_ecl_values_nonnegative(self):
        inputs = _make_aggregation_inputs()
        inputs["loan_weighted_ecl"] = np.abs(inputs["loan_weighted_ecl"])
        result = aggregate_results(**inputs)
        for row in result["portfolio_summary"]:
            assert row["total_ecl"] >= 0

    def test_coverage_ratio_calculated(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        for row in result["portfolio_summary"]:
            assert isinstance(row["coverage_ratio"], (int, float))

    def test_weights_sum_in_scenario_results(self):
        inputs = _make_aggregation_inputs(scenarios=["base", "upside", "downside"])
        result = aggregate_results(**inputs)
        total_weight = sum(sc["weight"] for sc in result["scenario_results"])
        assert abs(total_weight - 1.0) < 0.001

    def test_large_simulation(self):
        inputs = _make_aggregation_inputs(n_loans=100, n_sims=500)
        result = aggregate_results(**inputs)
        assert len(result["portfolio_summary"]) > 0

    def test_metadata_duration_positive(self):
        inputs = _make_aggregation_inputs()
        result = aggregate_results(**inputs)
        assert result["run_metadata"]["duration_seconds"] >= 0
