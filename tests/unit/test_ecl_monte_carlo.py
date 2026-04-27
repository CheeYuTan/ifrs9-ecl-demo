"""Dedicated tests for ecl/monte_carlo.py — loan column prep and simulation loop."""
import numpy as np
import pandas as pd
import pytest

from ecl.monte_carlo import prepare_loan_columns, run_scenario_sims


def _make_raw_loans(n=20):
    """Create a minimal raw loans DataFrame."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "loan_id": [f"L{i}" for i in range(n)],
        "product_type": ["mortgage"] * (n // 2) + ["personal"] * (n - n // 2),
        "assessed_stage": [1] * (n // 3) + [2] * (n // 3) + [3] * (n - 2 * (n // 3)),
        "current_lifetime_pd": rng.random(n) * 0.1,
        "remaining_months": rng.integers(3, 120, n),
        "gross_carrying_amount": rng.random(n) * 500000 + 10000,
        "effective_interest_rate": rng.random(n) * 0.1 + 0.01,
        "days_past_due": [0] * (n // 2) + [30] * (n - n // 2),
    })


class TestPrepareColumns:
    def test_adds_expected_columns(self):
        df = _make_raw_loans()
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        for col in ("stage", "gca", "eir", "base_pd", "rem_q", "rem_months_f", "base_lgd"):
            assert col in result.columns

    def test_stage_from_assessed_stage(self):
        df = _make_raw_loans()
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert set(result["stage"].unique()).issubset({1, 2, 3})

    def test_eir_floor(self):
        df = _make_raw_loans()
        df.loc[0, "effective_interest_rate"] = 0.0
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["eir"] >= 0.001).all()

    def test_base_pd_clipped(self):
        df = _make_raw_loans()
        df.loc[0, "current_lifetime_pd"] = -0.5
        df.loc[1, "current_lifetime_pd"] = 1.5
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["base_pd"] >= 0.0).all()
        assert (result["base_pd"] <= 1.0).all()

    def test_rem_q_at_least_one(self):
        df = _make_raw_loans()
        df.loc[0, "remaining_months"] = 0
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["rem_q"] >= 1).all()

    def test_base_lgd_from_product_map(self):
        df = _make_raw_loans()
        result = prepare_loan_columns(df, {"mortgage": 0.20, "personal": 0.55})
        mortgage_lgd = result.loc[result["product_type"] == "mortgage", "base_lgd"]
        personal_lgd = result.loc[result["product_type"] == "personal", "base_lgd"]
        assert (mortgage_lgd == 0.20).all()
        assert (personal_lgd == 0.55).all()

    def test_base_lgd_fallback_for_unknown_product(self):
        df = _make_raw_loans()
        df.loc[0, "product_type"] = "exotic"
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        exotic_lgd = result.loc[result["product_type"] == "exotic", "base_lgd"]
        assert (exotic_lgd == 0.50).all()

    def test_drops_na_assessed_stage(self):
        df = _make_raw_loans()
        df.loc[0, "assessed_stage"] = None
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert len(result) == len(df) - 1

    def test_drops_na_remaining_months(self):
        df = _make_raw_loans()
        df.loc[0, "remaining_months"] = None
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert len(result) == len(df) - 1

    def test_drops_na_gca(self):
        df = _make_raw_loans()
        df.loc[0, "gross_carrying_amount"] = None
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert len(result) == len(df) - 1

    def test_rem_months_f_at_least_one(self):
        df = _make_raw_loans()
        df.loc[0, "remaining_months"] = 0
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["rem_months_f"] >= 1).all()

    def test_eir_assertion_holds(self):
        df = _make_raw_loans()
        df["effective_interest_rate"] = 0.0
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["eir"] >= 0.001).all()

    def test_nan_pd_replaced(self):
        df = _make_raw_loans()
        df.loc[0, "current_lifetime_pd"] = None
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert not result["base_pd"].isna().any()

    def test_nan_eir_replaced(self):
        df = _make_raw_loans()
        df.loc[0, "effective_interest_rate"] = None
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert not result["eir"].isna().any()


class TestRunScenarioSims:
    def _make_sim_inputs(self, n_loans=5, n_sims=10):
        rng = np.random.default_rng(42)
        products = np.array(["mortgage"] * 3 + ["personal"] * 2)
        unique_products = np.array(["mortgage", "personal"])
        return {
            "rng": rng,
            "n_loans": n_loans,
            "n_sims": n_sims,
            "batch_size": min(n_sims, 5),
            "rho_1d": np.full(n_loans, 0.3),
            "base_pd": np.full(n_loans, 0.05),
            "base_lgd_arr": np.full(n_loans, 0.45),
            "pd_mult": 1.0,
            "lgd_mult": 1.0,
            "pd_vol": 0.05,
            "lgd_vol": 0.03,
            "pd_floor": 0.001,
            "pd_cap": 0.95,
            "lgd_floor": 0.01,
            "lgd_cap": 0.95,
            "aging_factor": 0.08,
            "is_stage_23_1d": np.array([False, False, False, True, True]),
            "max_horizon": np.array([4, 4, 4, 10, 10]),
            "global_max_q": 10,
            "quarterly_prepay": np.full(n_loans, 0.01),
            "rem_months_f": np.array([36.0, 24.0, 48.0, 60.0, 12.0]),
            "is_bullet": np.array([False, False, False, False, True]),
            "gca": np.array([100000.0, 200000.0, 150000.0, 80000.0, 50000.0]),
            "eir": np.full(n_loans, 0.05),
            "products": products,
            "unique_products": unique_products,
            "product_sim_ecls": {p: np.zeros(n_sims) for p in unique_products},
            "w": 0.5,
        }

    def test_returns_two_arrays(self):
        inputs = self._make_sim_inputs()
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert isinstance(loan_ecl, np.ndarray)
        assert isinstance(path_ecls, np.ndarray)

    def test_loan_ecl_shape(self):
        inputs = self._make_sim_inputs(n_loans=5, n_sims=10)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert loan_ecl.shape == (5,)

    def test_path_ecls_shape(self):
        inputs = self._make_sim_inputs(n_loans=5, n_sims=10)
        _, path_ecls = run_scenario_sims(**inputs)
        assert path_ecls.shape == (10,)

    def test_ecl_nonnegative(self):
        inputs = self._make_sim_inputs()
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert (loan_ecl >= 0).all()
        assert (path_ecls >= 0).all()

    def test_ecl_finite(self):
        inputs = self._make_sim_inputs()
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))
        assert np.all(np.isfinite(path_ecls))

    def test_stressed_scenario(self):
        inputs = self._make_sim_inputs()
        loan_ecl_base, _ = run_scenario_sims(**inputs)

        stressed_inputs = self._make_sim_inputs()
        stressed_inputs["rng"] = np.random.default_rng(42)
        stressed_inputs["pd_mult"] = 2.0
        stressed_inputs["lgd_mult"] = 1.5
        loan_ecl_stressed, _ = run_scenario_sims(**stressed_inputs)

        assert loan_ecl_stressed.sum() > loan_ecl_base.sum()

    def test_product_sim_ecls_populated(self):
        inputs = self._make_sim_inputs()
        run_scenario_sims(**inputs)
        for prod, arr in inputs["product_sim_ecls"].items():
            assert arr.sum() > 0

    def test_batching_produces_similar_results(self):
        inputs_small = self._make_sim_inputs(n_sims=200)
        inputs_small["batch_size"] = 50
        inputs_small["rng"] = np.random.default_rng(42)
        loan_ecl_batched, _ = run_scenario_sims(**inputs_small)

        inputs_full = self._make_sim_inputs(n_sims=200)
        inputs_full["batch_size"] = 200
        inputs_full["rng"] = np.random.default_rng(99)
        loan_ecl_full, _ = run_scenario_sims(**inputs_full)

        np.testing.assert_allclose(loan_ecl_batched, loan_ecl_full, rtol=0.5)

    def test_reproducibility(self):
        inputs1 = self._make_sim_inputs()
        inputs1["rng"] = np.random.default_rng(42)
        ecl1, paths1 = run_scenario_sims(**inputs1)

        inputs2 = self._make_sim_inputs()
        inputs2["rng"] = np.random.default_rng(42)
        ecl2, paths2 = run_scenario_sims(**inputs2)

        np.testing.assert_array_equal(ecl1, ecl2)
        np.testing.assert_array_equal(paths1, paths2)

    def test_bullet_loans(self):
        inputs = self._make_sim_inputs()
        inputs["is_bullet"] = np.ones(5, dtype=bool)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_low_pd_produces_low_ecl(self):
        inputs_low = self._make_sim_inputs(n_sims=50)
        inputs_low["base_pd"] = np.full(5, 0.001)
        inputs_low["rng"] = np.random.default_rng(42)
        loan_ecl_low, _ = run_scenario_sims(**inputs_low)

        inputs_high = self._make_sim_inputs(n_sims=50)
        inputs_high["base_pd"] = np.full(5, 0.20)
        inputs_high["rng"] = np.random.default_rng(42)
        loan_ecl_high, _ = run_scenario_sims(**inputs_high)

        assert loan_ecl_low.sum() < loan_ecl_high.sum()

    def test_single_sim(self):
        inputs = self._make_sim_inputs(n_sims=1)
        inputs["batch_size"] = 1
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert loan_ecl.shape == (5,)
        assert path_ecls.shape == (1,)
