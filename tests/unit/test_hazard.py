"""Tests for domain/hazard.py — Hazard models and survival curves."""
import json
import math
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch


@pytest.fixture
def hazard_portfolio_df():
    rng = np.random.default_rng(42)
    n = 200
    return pd.DataFrame({
        "loan_id": [f"L{i}" for i in range(n)],
        "product_type": rng.choice(["mortgage", "personal_loan", "credit_card"], n).tolist(),
        "segment": rng.choice(["retail", "sme", "corporate"], n).tolist(),
        "assessed_stage": rng.choice([1, 1, 1, 2, 3], n).tolist(),
        "days_past_due": rng.integers(0, 120, n).tolist(),
        "current_lifetime_pd": np.round(rng.uniform(0.01, 0.4, n), 4).tolist(),
        "gross_carrying_amount": np.round(rng.uniform(1000, 50000, n), 2).tolist(),
        "remaining_term": rng.integers(6, 60, n).tolist(),
        "vintage_cohort": rng.choice(["2022", "2023", "2024"], n).tolist(),
    })


@pytest.fixture
def _patch_db():
    with patch("domain.hazard_tables.query_df") as mock_q_tables, \
         patch("domain.hazard_tables.execute") as mock_e_tables, \
         patch("domain.hazard_retrieval.query_df") as mock_q_retrieval, \
         patch("domain.hazard_estimation.execute") as mock_e_estimation:
        mock_q = mock_q_retrieval
        mock_e = mock_e_estimation
        mock_q_tables.return_value = pd.DataFrame()
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e,
               "query_df_tables": mock_q_tables, "execute_tables": mock_e_tables}


class TestEstimateCoxPh:
    def test_produces_valid_coefficients(self, hazard_portfolio_df):
        from domain.hazard import _estimate_cox_ph
        n_obs = len(hazard_portfolio_df)
        n_events = int((hazard_portfolio_df["assessed_stage"] >= 3).sum())
        result = _estimate_cox_ph(hazard_portfolio_df, n_obs, n_events)
        covariates = result["coefficients"]["covariates"]
        assert len(covariates) == 4
        for cov in covariates:
            assert "coefficient" in cov
            assert "hazard_ratio" in cov
            assert "std_error" in cov
            assert cov["hazard_ratio"] > 0

    def test_survival_decreases_over_time(self, hazard_portfolio_df):
        from domain.hazard import _estimate_cox_ph
        n_obs = len(hazard_portfolio_df)
        n_events = max(1, int((hazard_portfolio_df["assessed_stage"] >= 3).sum()))
        result = _estimate_cox_ph(hazard_portfolio_df, n_obs, n_events)
        curves = result["curves"]
        assert len(curves) >= 1
        overall = curves[0]
        probs = overall["survival_probs"]
        for i in range(1, len(probs)):
            assert probs[i] <= probs[i - 1] + 1e-6

    def test_concordance_in_range(self, hazard_portfolio_df):
        from domain.hazard import _estimate_cox_ph
        result = _estimate_cox_ph(hazard_portfolio_df, 200, 20)
        assert 0 < result["concordance_index"] <= 1.0

    def test_aic_bic_computed(self, hazard_portfolio_df):
        from domain.hazard import _estimate_cox_ph
        result = _estimate_cox_ph(hazard_portfolio_df, 200, 20)
        assert isinstance(result["aic"], float)
        assert isinstance(result["bic"], float)


class TestEstimateDiscreteTime:
    def test_produces_valid_coefficients(self, hazard_portfolio_df):
        from domain.hazard import _estimate_discrete_time
        result = _estimate_discrete_time(hazard_portfolio_df, 200, 20)
        assert "intercept" in result["coefficients"]
        assert "time_coefficient" in result["coefficients"]
        assert len(result["coefficients"]["covariates"]) == 3

    def test_survival_decreases(self, hazard_portfolio_df):
        from domain.hazard import _estimate_discrete_time
        result = _estimate_discrete_time(hazard_portfolio_df, 200, 20)
        overall = result["curves"][0]
        probs = overall["survival_probs"]
        for i in range(1, len(probs)):
            assert probs[i] <= probs[i - 1] + 1e-6

    def test_handles_vintage_rates(self, hazard_portfolio_df):
        from domain.hazard import _estimate_discrete_time
        result = _estimate_discrete_time(hazard_portfolio_df, 200, 20)
        vintage_rates = result["coefficients"].get("vintage_rates", {})
        assert len(vintage_rates) > 0
        for rate in vintage_rates.values():
            assert 0 <= rate <= 1


class TestEstimateKaplanMeier:
    def test_non_parametric(self, hazard_portfolio_df):
        from domain.hazard import _estimate_kaplan_meier
        result = _estimate_kaplan_meier(hazard_portfolio_df, 200, 20)
        assert result["coefficients"]["method"] == "kaplan_meier"
        assert result["coefficients"]["non_parametric"] is True

    def test_survival_decreases(self, hazard_portfolio_df):
        from domain.hazard import _estimate_kaplan_meier
        result = _estimate_kaplan_meier(hazard_portfolio_df, 200, 20)
        probs = result["curves"][0]["survival_probs"]
        for i in range(1, len(probs)):
            assert probs[i] <= probs[i - 1] + 1e-6

    def test_product_curves_generated(self, hazard_portfolio_df):
        from domain.hazard import _estimate_kaplan_meier
        result = _estimate_kaplan_meier(hazard_portfolio_df, 200, 20)
        assert len(result["curves"]) > 1


class TestBuildSegmentCurves:
    def test_produces_curves_per_segment(self, hazard_portfolio_df):
        from domain.hazard import _build_segment_curves
        baseline = {str(t): 0.005 for t in range(1, 61)}
        coefficients = {"covariates": [
            {"name": "days_past_due", "coefficient": 0.01},
            {"name": "current_lifetime_pd", "coefficient": 2.0},
        ]}
        curves = _build_segment_curves(hazard_portfolio_df, baseline, coefficients, 60)
        assert len(curves) >= 1
        assert curves[0]["segment"] == "all"

    def test_survival_in_range(self, hazard_portfolio_df):
        from domain.hazard import _build_segment_curves
        baseline = {str(t): 0.003 for t in range(1, 61)}
        coefficients = {"covariates": [
            {"name": "days_past_due", "coefficient": 0.005},
        ]}
        curves = _build_segment_curves(hazard_portfolio_df, baseline, coefficients, 60)
        for curve in curves:
            for p in curve["survival_probs"]:
                assert 0 <= p <= 1.0


class TestEstimateHazardModel:
    def test_raises_for_unknown_type(self, _patch_db, hazard_portfolio_df):
        from domain.hazard import estimate_hazard_model
        _patch_db["query_df_tables"].return_value = hazard_portfolio_df
        with pytest.raises(ValueError, match="Unknown model type"):
            estimate_hazard_model("invalid_type")

    def test_raises_for_empty_data(self, _patch_db):
        from domain.hazard import estimate_hazard_model
        _patch_db["query_df_tables"].return_value = pd.DataFrame()
        with pytest.raises(ValueError, match="No portfolio data"):
            estimate_hazard_model("cox_ph")


class TestComputeSurvivalCurve:
    def test_no_covariates(self, _patch_db):
        from domain.hazard import compute_survival_curve
        model_row = pd.DataFrame([{
            "model_id": "h1",
            "model_type": "cox_ph",
            "coefficients": json.dumps({"covariates": [
                {"name": "days_past_due", "coefficient": 0.01},
            ]}),
            "baseline_hazard": json.dumps({str(t): 0.004 for t in range(1, 61)}),
            "concordance_index": 0.75,
        }])
        curves_df = pd.DataFrame()
        _patch_db["query_df"].side_effect = [model_row, curves_df]
        result = compute_survival_curve("h1")
        assert result["risk_multiplier"] == 1.0
        assert len(result["survival_probs"]) == 60
        assert all(0 <= p <= 1 for p in result["survival_probs"])

    def test_covariates_increase_risk(self, _patch_db):
        from domain.hazard import compute_survival_curve
        model_row = pd.DataFrame([{
            "model_id": "h1",
            "model_type": "cox_ph",
            "coefficients": json.dumps({"covariates": [
                {"name": "days_past_due", "coefficient": 0.02},
            ]}),
            "baseline_hazard": json.dumps({str(t): 0.004 for t in range(1, 61)}),
            "concordance_index": 0.75,
        }])
        curves_df = pd.DataFrame()
        _patch_db["query_df"].side_effect = [model_row, curves_df, model_row, curves_df]
        base = compute_survival_curve("h1")
        risky = compute_survival_curve("h1", {"days_past_due": 90})
        assert risky["risk_multiplier"] > 1.0
        assert risky["survival_probs"][-1] < base["survival_probs"][-1]

    def test_raises_for_missing_model(self, _patch_db):
        from domain.hazard import compute_survival_curve
        with pytest.raises(ValueError, match="not found"):
            compute_survival_curve("bad-id")


class TestComputeTermStructurePd:
    def test_cumulative_increases(self, _patch_db):
        from domain.hazard import compute_term_structure_pd
        model_row = pd.DataFrame([{
            "model_id": "h1",
            "model_type": "cox_ph",
            "coefficients": json.dumps({}),
            "baseline_hazard": json.dumps({str(t): 0.005 for t in range(1, 61)}),
        }])
        curves_df = pd.DataFrame()
        _patch_db["query_df"].side_effect = [model_row, curves_df]
        result = compute_term_structure_pd("h1", max_months=24)
        cum = result["cumulative_pd"]
        for i in range(1, len(cum)):
            assert cum[i] >= cum[i - 1] - 1e-10

    def test_pd_12m_and_lifetime(self, _patch_db):
        from domain.hazard import compute_term_structure_pd
        model_row = pd.DataFrame([{
            "model_id": "h1",
            "model_type": "cox_ph",
            "coefficients": json.dumps({}),
            "baseline_hazard": json.dumps({str(t): 0.008 for t in range(1, 61)}),
        }])
        curves_df = pd.DataFrame()
        _patch_db["query_df"].side_effect = [model_row, curves_df]
        result = compute_term_structure_pd("h1", max_months=60)
        assert 0 < result["pd_12_month"] < result["pd_lifetime"]


class TestCompareHazardModels:
    def test_empty_list(self, _patch_db):
        from domain.hazard import compare_hazard_models
        result = compare_hazard_models([])
        assert result == {"models": [], "curves": []}

    def test_returns_model_summaries(self, _patch_db):
        from domain.hazard import compare_hazard_models
        model_row = pd.DataFrame([{
            "model_id": "h1",
            "model_type": "cox_ph",
            "coefficients": json.dumps({}),
            "baseline_hazard": json.dumps({}),
            "concordance_index": 0.78,
            "log_likelihood": -500.0,
            "aic": 1008.0,
            "bic": 1020.0,
            "n_observations": 1000,
            "n_events": 50,
            "product_type": None,
            "segment": None,
            "estimation_date": "2025-12-31",
        }])
        curves_df = pd.DataFrame([{
            "curve_id": "c1",
            "segment": "all",
            "time_points": json.dumps([1, 2, 3]),
            "survival_probs": json.dumps([0.99, 0.98, 0.97]),
            "hazard_rates": json.dumps([0.01, 0.01, 0.01]),
        }])
        _patch_db["query_df"].side_effect = [model_row, curves_df]
        result = compare_hazard_models(["h1"])
        assert len(result["models"]) == 1
        assert result["models"][0]["concordance_index"] == 0.78


class TestListHazardModels:
    def test_empty(self, _patch_db):
        from domain.hazard import list_hazard_models
        assert list_hazard_models() == []

    def test_with_filter(self, _patch_db):
        from domain.hazard import list_hazard_models
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "model_id": "h1", "model_type": "cox_ph",
        }])
        result = list_hazard_models(model_type="cox_ph")
        assert len(result) == 1
