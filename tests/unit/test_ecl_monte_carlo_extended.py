"""Extended tests for ecl/monte_carlo.py — additional edge cases and property checks."""
import numpy as np
import pandas as pd
import pytest

from ecl.monte_carlo import prepare_loan_columns, run_scenario_sims


def _make_raw_loans(n=20):
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


class TestPrepareColumnsExtended:
    def test_output_length_matches_input(self):
        df = _make_raw_loans(50)
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert len(result) == 50

    def test_no_na_in_stage(self):
        df = _make_raw_loans()
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert not result["stage"].isna().any()

    def test_no_na_in_gca(self):
        df = _make_raw_loans()
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert not result["gca"].isna().any()

    def test_gca_positive(self):
        df = _make_raw_loans()
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["gca"] > 0).all()

    def test_base_pd_range(self):
        df = _make_raw_loans()
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["base_pd"] >= 0).all()
        assert (result["base_pd"] <= 1).all()

    def test_lgd_range(self):
        df = _make_raw_loans()
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["base_lgd"] > 0).all()
        assert (result["base_lgd"] < 1).all()

    def test_single_loan(self):
        df = _make_raw_loans(1)
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert len(result) == 1

    def test_large_loan_set(self):
        df = _make_raw_loans(200)
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert len(result) == 200

    def test_all_stage_1(self):
        df = _make_raw_loans()
        df["assessed_stage"] = 1
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["stage"] == 1).all()

    def test_all_stage_3(self):
        df = _make_raw_loans()
        df["assessed_stage"] = 3
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["stage"] == 3).all()

    def test_mixed_products(self):
        df = _make_raw_loans(30)
        df.loc[:9, "product_type"] = "mortgage"
        df.loc[10:19, "product_type"] = "personal"
        df.loc[20:, "product_type"] = "auto"
        result = prepare_loan_columns(df, {"mortgage": 0.15, "personal": 0.50, "auto": 0.35})
        auto_lgd = result.loc[result["product_type"] == "auto", "base_lgd"]
        assert (auto_lgd == 0.35).all()

    def test_very_high_eir(self):
        df = _make_raw_loans()
        df["effective_interest_rate"] = 0.50
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["eir"] == 0.50).all()

    def test_very_short_remaining_months(self):
        df = _make_raw_loans()
        df["remaining_months"] = 1
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["rem_q"] >= 1).all()

    def test_very_long_remaining_months(self):
        df = _make_raw_loans()
        df["remaining_months"] = 600
        result = prepare_loan_columns(df, {"mortgage": 0.25, "personal": 0.50})
        assert (result["rem_q"] > 1).all()


class TestRunScenarioSimsExtended:
    def _make_inputs(self, n_loans=5, n_sims=10):
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

    def test_zero_lgd_produces_zero_ecl(self):
        inputs = self._make_inputs(n_sims=50)
        inputs["base_lgd_arr"] = np.zeros(5)
        inputs["lgd_mult"] = 0.0
        inputs["lgd_floor"] = 0.0
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert loan_ecl.sum() == pytest.approx(0.0, abs=1e-6)

    def test_high_pd_high_lgd_produces_large_ecl(self):
        inputs = self._make_inputs(n_sims=50)
        inputs["base_pd"] = np.full(5, 0.80)
        inputs["base_lgd_arr"] = np.full(5, 0.90)
        inputs["pd_mult"] = 2.0
        inputs["lgd_mult"] = 2.0
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert loan_ecl.sum() > 0

    def test_all_stage_1_shorter_horizon(self):
        inputs = self._make_inputs(n_sims=20)
        inputs["is_stage_23_1d"] = np.array([False] * 5)
        inputs["max_horizon"] = np.array([4] * 5)
        inputs["rng"] = np.random.default_rng(42)
        ecl_s1, _ = run_scenario_sims(**inputs)

        inputs2 = self._make_inputs(n_sims=20)
        inputs2["is_stage_23_1d"] = np.array([True] * 5)
        inputs2["max_horizon"] = np.array([40] * 5)
        inputs2["global_max_q"] = 40
        inputs2["rng"] = np.random.default_rng(42)
        ecl_s23, _ = run_scenario_sims(**inputs2)

        assert ecl_s23.sum() > ecl_s1.sum()

    def test_higher_gca_higher_ecl(self):
        inputs_low = self._make_inputs(n_sims=50)
        inputs_low["gca"] = np.full(5, 10000.0)
        inputs_low["rng"] = np.random.default_rng(42)
        ecl_low, _ = run_scenario_sims(**inputs_low)

        inputs_high = self._make_inputs(n_sims=50)
        inputs_high["gca"] = np.full(5, 1000000.0)
        inputs_high["rng"] = np.random.default_rng(42)
        ecl_high, _ = run_scenario_sims(**inputs_high)

        assert ecl_high.sum() > ecl_low.sum()

    def test_zero_correlation(self):
        inputs = self._make_inputs()
        inputs["rho_1d"] = np.zeros(5)
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_high_correlation(self):
        inputs = self._make_inputs()
        inputs["rho_1d"] = np.full(5, 0.9)
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_no_prepay(self):
        inputs = self._make_inputs()
        inputs["quarterly_prepay"] = np.zeros(5)
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_high_prepay(self):
        inputs = self._make_inputs()
        inputs["quarterly_prepay"] = np.full(5, 0.20)
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl_high, _ = run_scenario_sims(**inputs)

        inputs2 = self._make_inputs()
        inputs2["quarterly_prepay"] = np.zeros(5)
        inputs2["rng"] = np.random.default_rng(42)
        loan_ecl_no, _ = run_scenario_sims(**inputs2)

        assert loan_ecl_high.sum() < loan_ecl_no.sum()

    def test_single_loan(self):
        inputs = self._make_inputs(n_loans=1, n_sims=10)
        inputs["rho_1d"] = np.array([0.3])
        inputs["base_pd"] = np.array([0.05])
        inputs["base_lgd_arr"] = np.array([0.45])
        inputs["is_stage_23_1d"] = np.array([False])
        inputs["max_horizon"] = np.array([4])
        inputs["quarterly_prepay"] = np.array([0.01])
        inputs["rem_months_f"] = np.array([36.0])
        inputs["is_bullet"] = np.array([False])
        inputs["gca"] = np.array([100000.0])
        inputs["eir"] = np.array([0.05])
        inputs["products"] = np.array(["mortgage"])
        inputs["unique_products"] = np.array(["mortgage"])
        inputs["product_sim_ecls"] = {"mortgage": np.zeros(10)}
        inputs["batch_size"] = 10
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert loan_ecl.shape == (1,)
        assert path_ecls.shape == (10,)

    def test_path_ecls_sum_to_loan_ecl_total(self):
        inputs = self._make_inputs(n_sims=100)
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        total_from_paths = path_ecls.mean()
        total_from_loans = loan_ecl.sum() / inputs["n_sims"]
        np.testing.assert_allclose(total_from_paths, total_from_loans, rtol=0.01)

    def test_large_number_of_sims(self):
        inputs = self._make_inputs(n_sims=500)
        inputs["batch_size"] = 100
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert loan_ecl.shape == (5,)
        assert path_ecls.shape == (500,)

    def test_very_short_horizon(self):
        inputs = self._make_inputs()
        inputs["max_horizon"] = np.ones(5, dtype=int)
        inputs["global_max_q"] = 1
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_pd_cap_enforced(self):
        inputs = self._make_inputs(n_sims=50)
        inputs["base_pd"] = np.full(5, 0.99)
        inputs["pd_mult"] = 3.0
        inputs["pd_cap"] = 0.95
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_lgd_cap_enforced(self):
        inputs = self._make_inputs(n_sims=50)
        inputs["base_lgd_arr"] = np.full(5, 0.90)
        inputs["lgd_mult"] = 3.0
        inputs["lgd_cap"] = 0.95
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_weight_does_not_affect_loan_ecl_shape(self):
        inputs = self._make_inputs()
        inputs["w"] = 0.1
        inputs["rng"] = np.random.default_rng(42)
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert loan_ecl.shape == (5,)

    def test_aging_factor_effect(self):
        inputs_low = self._make_inputs(n_sims=100)
        inputs_low["aging_factor"] = 0.0
        inputs_low["rng"] = np.random.default_rng(42)
        ecl_low, _ = run_scenario_sims(**inputs_low)

        inputs_high = self._make_inputs(n_sims=100)
        inputs_high["aging_factor"] = 0.50
        inputs_high["rng"] = np.random.default_rng(42)
        ecl_high, _ = run_scenario_sims(**inputs_high)

        assert ecl_high.sum() >= ecl_low.sum()
