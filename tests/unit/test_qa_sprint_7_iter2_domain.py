"""
Sprint 7 Iteration 2: Additional domain analytical tests.

Covers gaps identified in iteration 1 review:
  - Model registry: generate_model_card, _extract_assumptions/limitations, sensitivity edge cases
  - Markov: _mat_mult, _mat_power, forecast_stage_distribution, list/compare, estimate edge cases
  - Hazard: estimate_hazard_model orchestrator, compare_hazard_models, survival curve with covariates,
            list_hazard_models, get_hazard_model
  - Advanced: compute_cure_rates structure, compute_ccf revolving vs non-revolving, list functions
  - Backtesting: get_backtest_trend multi-result, list_backtests filtering
  - Period close: step ordering, PIPELINE_STEPS completeness, _run_step_logic unknown key
"""
import json
import math
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


# ===========================================================================
# MODEL REGISTRY — generate_model_card, assumptions, limitations, sensitivity
# ===========================================================================


@pytest.fixture
def _patch_registry_db():
    with patch("domain.model_registry.query_df") as mock_q, \
         patch("domain.model_registry.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


def _make_model_row(overrides=None):
    """Build a model registry DataFrame row with defaults."""
    base = {
        "model_id": "m1",
        "model_name": "PD Model v1",
        "model_type": "PD",
        "algorithm": "logistic",
        "version": 1,
        "description": "Default PD model",
        "status": "approved",
        "product_type": "mortgage",
        "cohort": "2024",
        "parameters": json.dumps({"intercept": -2.5, "unemployment_coeff": 0.3, "gdp_coeff": -0.15}),
        "performance_metrics": json.dumps({"r_squared": 0.65, "auc": 0.82, "validation_type": "out_of_sample"}),
        "training_data_info": json.dumps({"sample_size": 50000, "date_range": "2020-2023", "data_hash": "abc123"}),
        "is_champion": True,
        "created_by": "analyst",
        "created_at": datetime(2025, 1, 15, tzinfo=timezone.utc),
        "approved_by": "manager",
        "approved_at": datetime(2025, 2, 1, tzinfo=timezone.utc),
        "promoted_by": None,
        "promoted_at": None,
        "retired_by": None,
        "retired_at": None,
        "notes": "",
        "parent_model_id": None,
    }
    if overrides:
        base.update(overrides)
    return pd.DataFrame([base])


class TestGenerateModelCard:
    def test_card_has_required_sections(self, _patch_registry_db):
        from domain.model_registry import generate_model_card
        _patch_registry_db["query_df"].side_effect = [_make_model_row(), pd.DataFrame()]
        card = generate_model_card("m1")
        assert "model_id" in card
        assert "methodology" in card
        assert "training_data" in card
        assert "performance" in card
        assert "governance" in card
        assert "assumptions" in card
        assert "limitations" in card

    def test_card_model_not_found_raises(self, _patch_registry_db):
        from domain.model_registry import generate_model_card
        with pytest.raises(ValueError, match="not found"):
            generate_model_card("nonexistent")

    def test_card_methodology_populated(self, _patch_registry_db):
        from domain.model_registry import generate_model_card
        _patch_registry_db["query_df"].side_effect = [_make_model_row(), pd.DataFrame()]
        card = generate_model_card("m1")
        assert card["methodology"]["algorithm"] == "logistic"
        assert card["methodology"]["product_type"] == "mortgage"

    def test_card_training_data_info(self, _patch_registry_db):
        from domain.model_registry import generate_model_card
        _patch_registry_db["query_df"].side_effect = [_make_model_row(), pd.DataFrame()]
        card = generate_model_card("m1")
        assert card["training_data"]["sample_size"] == 50000
        assert card["training_data"]["data_hash"] == "abc123"

    def test_card_governance_audit_count(self, _patch_registry_db):
        from domain.model_registry import generate_model_card
        audit_df = pd.DataFrame([
            {"audit_id": "a1", "model_id": "m1", "action": "registered",
             "old_status": None, "new_status": "draft",
             "performed_by": "analyst", "performed_at": datetime.now(timezone.utc), "comment": ""},
            {"audit_id": "a2", "model_id": "m1", "action": "approved",
             "old_status": "pending_review", "new_status": "approved",
             "performed_by": "manager", "performed_at": datetime.now(timezone.utc), "comment": ""},
        ])
        _patch_registry_db["query_df"].side_effect = [_make_model_row(), audit_df]
        card = generate_model_card("m1")
        assert card["governance"]["audit_trail_count"] == 2

    def test_card_with_empty_performance(self, _patch_registry_db):
        from domain.model_registry import generate_model_card
        row = _make_model_row({"performance_metrics": json.dumps({})})
        _patch_registry_db["query_df"].side_effect = [row, pd.DataFrame()]
        card = generate_model_card("m1")
        assert card["performance"]["metrics"] == {}
        assert card["performance"]["validation_type"] == "in_sample"


class TestExtractAssumptions:
    def test_pd_model_assumptions(self):
        from domain.model_registry import _extract_assumptions
        model = {"model_type": "PD", "algorithm": "logistic"}
        assumptions = _extract_assumptions(model)
        assert any("90+ DPD" in a for a in assumptions)
        assert any("logistic" in a.lower() for a in assumptions)
        assert any("forward-looking" in a.lower() for a in assumptions)

    def test_lgd_model_assumptions(self):
        from domain.model_registry import _extract_assumptions
        model = {"model_type": "LGD", "algorithm": "linear"}
        assumptions = _extract_assumptions(model)
        assert any("recovery" in a.lower() for a in assumptions)
        assert any("downturn" in a.lower() for a in assumptions)

    def test_ead_model_assumptions(self):
        from domain.model_registry import _extract_assumptions
        model = {"model_type": "EAD", "algorithm": "simple"}
        assumptions = _extract_assumptions(model)
        assert any("amortization" in a.lower() or "prepayment" in a.lower() for a in assumptions)

    def test_ensemble_algo_assumption(self):
        from domain.model_registry import _extract_assumptions
        model = {"model_type": "PD", "algorithm": "gradient_boosting"}
        assumptions = _extract_assumptions(model)
        assert any("ensemble" in a.lower() or "overfit" in a.lower() for a in assumptions)


class TestExtractLimitations:
    def test_low_r_squared_flagged(self):
        from domain.model_registry import _extract_limitations
        model = {"model_type": "PD", "performance_metrics": {"r_squared": 0.3}}
        lims = _extract_limitations(model)
        assert any("R²=0.3" in l or "R²" in l for l in lims)

    def test_high_r_squared_not_flagged(self):
        from domain.model_registry import _extract_limitations
        model = {"model_type": "PD", "performance_metrics": {"r_squared": 0.8}}
        lims = _extract_limitations(model)
        assert not any("R²=0.8" in l for l in lims)

    def test_pd_specific_limitation(self):
        from domain.model_registry import _extract_limitations
        model = {"model_type": "PD", "performance_metrics": {}}
        lims = _extract_limitations(model)
        assert any("idiosyncratic" in l.lower() for l in lims)

    def test_lgd_specific_limitation(self):
        from domain.model_registry import _extract_limitations
        model = {"model_type": "LGD", "performance_metrics": {}}
        lims = _extract_limitations(model)
        assert any("collateral" in l.lower() for l in lims)

    def test_always_includes_degradation_warning(self):
        from domain.model_registry import _extract_limitations
        model = {"model_type": "EAD", "performance_metrics": {}}
        lims = _extract_limitations(model)
        assert any("degrade" in l.lower() for l in lims)


class TestSensitivityFullFlow:
    def test_returns_sensitivities_for_matching_params(self, _patch_registry_db):
        from domain.model_registry import compute_sensitivity
        row = _make_model_row({"parameters": json.dumps({
            "intercept": -2.5, "unemployment_coeff": 0.3, "gdp_coeff": -0.15
        })})
        _patch_registry_db["query_df"].return_value = row
        result = compute_sensitivity("m1", perturbation_pct=10.0)
        assert len(result["sensitivities"]) == 3
        names = {s["parameter"] for s in result["sensitivities"]}
        assert "intercept" in names
        assert "unemployment_coeff" in names

    def test_custom_perturbation_pct(self, _patch_registry_db):
        from domain.model_registry import compute_sensitivity
        row = _make_model_row({"parameters": json.dumps({"base_pd": 0.05})})
        _patch_registry_db["query_df"].return_value = row
        result = compute_sensitivity("m1", perturbation_pct=20.0)
        assert result["perturbation_pct"] == 20.0
        s = result["sensitivities"][0]
        assert s["perturbed_up"] == round(0.05 * 1.2, 6)
        assert s["perturbed_down"] == round(0.05 * 0.8, 6)

    def test_sensitivity_non_numeric_param_skipped(self, _patch_registry_db):
        from domain.model_registry import compute_sensitivity
        row = _make_model_row({"parameters": json.dumps({
            "intercept": -2.5, "inflation_coeff": "N/A"
        })})
        _patch_registry_db["query_df"].return_value = row
        result = compute_sensitivity("m1")
        names = {s["parameter"] for s in result["sensitivities"]}
        assert "inflation_coeff" not in names
        assert "intercept" in names


class TestRecalibrationFullFlow:
    def test_old_model_is_due(self, _patch_registry_db):
        from domain.model_registry import check_recalibration_due
        old_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        row = _make_model_row({"approved_at": old_date, "created_at": old_date})
        _patch_registry_db["query_df"].return_value = row
        result = check_recalibration_due("m1", max_age_days=365)
        assert result["recalibration_due"] is True
        assert "required" in result["recommendation"].lower()

    def test_recent_model_not_due(self, _patch_registry_db):
        from domain.model_registry import check_recalibration_due
        recent = datetime.now(timezone.utc) - timedelta(days=30)
        row = _make_model_row({"approved_at": recent, "created_at": recent})
        _patch_registry_db["query_df"].return_value = row
        result = check_recalibration_due("m1", max_age_days=365)
        assert result["recalibration_due"] is False
        assert "within" in result["recommendation"].lower()

    def test_model_not_found_raises(self, _patch_registry_db):
        from domain.model_registry import check_recalibration_due
        with pytest.raises(ValueError, match="not found"):
            check_recalibration_due("bad-id")


# ===========================================================================
# MARKOV — Matrix Math, Forecast, List, Compare
# ===========================================================================


class TestMatMult:
    def test_identity_multiplication(self):
        from domain.markov import _mat_mult
        I = [[1, 0], [0, 1]]
        A = [[2, 3], [4, 5]]
        assert _mat_mult(I, A) == A
        assert _mat_mult(A, I) == A

    def test_simple_2x2(self):
        from domain.markov import _mat_mult
        A = [[1, 2], [3, 4]]
        B = [[5, 6], [7, 8]]
        result = _mat_mult(A, B)
        assert result == [[19, 22], [43, 50]]

    def test_stochastic_matrix_stays_stochastic(self):
        from domain.markov import _mat_mult
        P = [[0.9, 0.1], [0.3, 0.7]]
        P2 = _mat_mult(P, P)
        for row in P2:
            assert abs(sum(row) - 1.0) < 1e-10


class TestMatPower:
    def test_power_zero_is_identity(self):
        from domain.markov import _mat_power
        A = [[0.9, 0.1], [0.3, 0.7]]
        result = _mat_power(A, 0)
        assert result[0][0] == 1.0 and result[0][1] == 0.0
        assert result[1][0] == 0.0 and result[1][1] == 1.0

    def test_power_one_is_original(self):
        from domain.markov import _mat_power
        A = [[0.9, 0.1], [0.3, 0.7]]
        result = _mat_power(A, 1)
        for i in range(2):
            for j in range(2):
                assert abs(result[i][j] - A[i][j]) < 1e-10

    def test_absorbing_state_convergence(self):
        from domain.markov import _mat_power
        # State 2 is absorbing
        P = [[0.5, 0.5], [0.0, 1.0]]
        result = _mat_power(P, 100)
        # After many steps, all mass should be in absorbing state
        assert abs(result[0][1] - 1.0) < 1e-6
        assert abs(result[1][1] - 1.0) < 1e-10


@pytest.fixture
def _patch_markov_db():
    with patch("domain.markov.query_df") as mock_q, \
         patch("domain.markov.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


def _make_markov_matrix_row(matrix=None, matrix_id="m1"):
    """Build a markov transition matrix DataFrame row."""
    if matrix is None:
        matrix = [[0.9, 0.05, 0.03, 0.02],
                  [0.02, 0.8, 0.1, 0.08],
                  [0.0, 0.02, 0.7, 0.28],
                  [0.0, 0.0, 0.0, 1.0]]
    return pd.DataFrame([{
        "matrix_id": matrix_id,
        "model_name": "TM-All-All",
        "estimation_date": "2025-01-01",
        "matrix_data": json.dumps({
            "states": ["Stage 1", "Stage 2", "Stage 3", "Default"],
            "matrix": matrix,
        }),
        "matrix_type": "annual",
        "product_type": None,
        "segment": None,
        "methodology": "cohort",
        "n_observations": 5000,
        "computed_at": "2025-01-01",
    }])


class TestForecastStageDistribution:
    def test_month_zero_returns_initial(self, _patch_markov_db):
        from domain.markov import forecast_stage_distribution
        _patch_markov_db["query_df"].return_value = _make_markov_matrix_row()
        result = forecast_stage_distribution("m1", [0.8, 0.15, 0.05, 0.0], horizon_months=0)
        points = result["forecast_data"]["points"]
        assert len(points) == 1
        assert points[0]["month"] == 0

    def test_distribution_sums_to_100(self, _patch_markov_db):
        from domain.markov import forecast_stage_distribution
        _patch_markov_db["query_df"].return_value = _make_markov_matrix_row()
        result = forecast_stage_distribution("m1", [0.8, 0.15, 0.05, 0.0], horizon_months=12)
        for point in result["forecast_data"]["points"]:
            total = point["Stage 1"] + point["Stage 2"] + point["Stage 3"] + point["Default"]
            assert abs(total - 100.0) < 0.1

    def test_default_increases_over_time(self, _patch_markov_db):
        from domain.markov import forecast_stage_distribution
        _patch_markov_db["query_df"].return_value = _make_markov_matrix_row()
        result = forecast_stage_distribution("m1", [1.0, 0.0, 0.0, 0.0], horizon_months=12)
        points = result["forecast_data"]["points"]
        # Default should increase from 0 over time
        assert points[-1]["Default"] > points[0]["Default"]

    def test_short_initial_distribution_padded(self, _patch_markov_db):
        from domain.markov import forecast_stage_distribution
        _patch_markov_db["query_df"].return_value = _make_markov_matrix_row()
        # Only 2 elements — should be padded to 4
        result = forecast_stage_distribution("m1", [0.9, 0.1], horizon_months=1)
        assert "forecast_data" in result

    def test_matrix_not_found_raises(self, _patch_markov_db):
        from domain.markov import forecast_stage_distribution
        with pytest.raises(ValueError, match="not found"):
            forecast_stage_distribution("bad-id", [1, 0, 0, 0], 12)


class TestListTransitionMatrices:
    def test_empty_returns_empty(self, _patch_markov_db):
        from domain.markov import list_transition_matrices
        result = list_transition_matrices()
        assert result == []

    def test_returns_records(self, _patch_markov_db):
        from domain.markov import list_transition_matrices
        _patch_markov_db["query_df"].return_value = pd.DataFrame([{
            "matrix_id": "m1", "model_name": "TM-All",
            "estimation_date": "2025-01-01", "matrix_type": "annual",
            "product_type": None, "segment": None,
            "methodology": "cohort", "n_observations": 5000,
            "computed_at": "2025-01-01",
        }])
        result = list_transition_matrices()
        assert len(result) == 1

    def test_filter_by_product_type(self, _patch_markov_db):
        from domain.markov import list_transition_matrices
        _patch_markov_db["query_df"].return_value = pd.DataFrame()
        list_transition_matrices(product_type="mortgage")
        sql = _patch_markov_db["query_df"].call_args[0][0]
        assert "product_type" in sql.lower()


class TestCompareMatrices:
    def test_empty_ids_returns_empty(self, _patch_markov_db):
        from domain.markov import compare_matrices
        result = compare_matrices([])
        assert result == []

    def test_returns_found_matrices(self, _patch_markov_db):
        from domain.markov import compare_matrices
        row = _make_markov_matrix_row()
        _patch_markov_db["query_df"].side_effect = [row, pd.DataFrame()]
        result = compare_matrices(["m1", "m2"])
        assert len(result) == 1  # Only m1 found


# ===========================================================================
# HAZARD — Orchestrator, Compare, Survival with Covariates, List/Get
# ===========================================================================


class TestEstimateHazardModelOrchestrator:
    @patch("domain.hazard_estimation.execute")
    @patch("domain.hazard_estimation._get_portfolio_hazard_data")
    @patch("domain.hazard_estimation._estimate_cox_ph")
    @patch("domain.hazard_retrieval.query_df")
    def test_cox_ph_flow(self, mock_ret_q, mock_cox, mock_data, mock_exec):
        from domain.hazard_estimation import estimate_hazard_model
        rng = np.random.default_rng(42)
        n = 100
        mock_data.return_value = pd.DataFrame({
            "loan_id": [f"L{i}" for i in range(n)],
            "assessed_stage": rng.choice([1, 2, 3], n).tolist(),
            "days_past_due": rng.integers(0, 90, n).tolist(),
            "current_lifetime_pd": np.round(rng.uniform(0.01, 0.3, n), 4).tolist(),
            "gross_carrying_amount": np.round(rng.uniform(1000, 50000, n), 2).tolist(),
            "remaining_term": rng.integers(6, 60, n).tolist(),
        })
        mock_cox.return_value = {
            "coefficients": {"covariates": []},
            "baseline_hazard": {str(t): 0.01 for t in range(1, 25)},
            "concordance_index": 0.72,
            "log_likelihood": -500.0,
            "aic": 1004.0,
            "bic": 1010.0,
            "curves": [],
        }
        # Return value for get_hazard_model
        mock_ret_q.side_effect = [
            pd.DataFrame([{
                "model_id": "haz_cox_ph_test",
                "model_type": "cox_ph",
                "coefficients": json.dumps({"covariates": []}),
                "baseline_hazard": json.dumps({str(t): 0.01 for t in range(1, 25)}),
                "concordance_index": 0.72,
                "log_likelihood": -500.0,
                "aic": 1004.0,
                "bic": 1010.0,
                "estimation_date": "2025-01-01",
                "product_type": None,
                "segment": None,
                "n_observations": 100,
                "n_events": 10,
                "created_at": "2025-01-01",
            }]),
            pd.DataFrame(),  # curves
        ]
        result = estimate_hazard_model("cox_ph")
        assert result is not None
        assert result["model_type"] == "cox_ph"
        mock_cox.assert_called_once()

    @patch("domain.hazard_estimation._get_portfolio_hazard_data")
    def test_unknown_model_type_raises(self, mock_data):
        from domain.hazard_estimation import estimate_hazard_model
        mock_data.return_value = pd.DataFrame({"loan_id": ["L1"], "assessed_stage": [1]})
        with pytest.raises(ValueError, match="Unknown model type"):
            estimate_hazard_model("invalid_type")

    @patch("domain.hazard_estimation._get_portfolio_hazard_data")
    def test_empty_portfolio_raises(self, mock_data):
        from domain.hazard_estimation import estimate_hazard_model
        mock_data.return_value = pd.DataFrame()
        with pytest.raises(ValueError, match="No portfolio data"):
            estimate_hazard_model("cox_ph")


class TestCompareHazardModels:
    @patch("domain.hazard_retrieval.query_df")
    def test_empty_returns_empty(self, mock_q):
        from domain.hazard_analysis import compare_hazard_models
        result = compare_hazard_models([])
        assert result["models"] == []
        assert result["curves"] == []

    @patch("domain.hazard_retrieval.query_df")
    def test_single_model(self, mock_q):
        from domain.hazard_analysis import compare_hazard_models
        model_df = pd.DataFrame([{
            "model_id": "h1", "model_type": "cox_ph",
            "coefficients": json.dumps({}),
            "baseline_hazard": json.dumps({}),
            "concordance_index": 0.72,
            "log_likelihood": -500,
            "aic": 1004, "bic": 1010,
            "n_observations": 100, "n_events": 10,
            "product_type": None, "segment": None,
            "estimation_date": "2025-01-01",
            "created_at": "2025-01-01",
        }])
        curves_df = pd.DataFrame([{
            "curve_id": "c1", "segment": "all",
            "time_points": json.dumps([1, 2, 3]),
            "survival_probs": json.dumps([0.99, 0.98, 0.97]),
            "hazard_rates": json.dumps([0.01, 0.01, 0.01]),
        }])
        mock_q.side_effect = [model_df, curves_df]
        result = compare_hazard_models(["h1"])
        assert len(result["models"]) == 1
        assert len(result["curves"]) == 1


class TestSurvivalCurveWithCovariates:
    @patch("domain.hazard_retrieval.query_df")
    def test_covariates_affect_risk_multiplier(self, mock_q):
        from domain.hazard_analysis import compute_survival_curve
        model_df = pd.DataFrame([{
            "model_id": "h1", "model_type": "cox_ph",
            "coefficients": json.dumps({
                "covariates": [
                    {"name": "dpd", "coefficient": 0.02},
                    {"name": "utilization", "coefficient": 0.5},
                ]
            }),
            "baseline_hazard": json.dumps({str(t): 0.01 for t in range(1, 13)}),
        }])
        mock_q.side_effect = [model_df, pd.DataFrame()]
        result = compute_survival_curve("h1", covariate_values={"dpd": 30, "utilization": 0.8})
        # risk_mult = exp(0.02*30 + 0.5*0.8) = exp(1.0) ≈ 2.718
        assert result["risk_multiplier"] > 2.5
        # Higher risk = lower survival
        assert result["survival_probs"][-1] < 0.9

    @patch("domain.hazard_retrieval.query_df")
    def test_no_covariates_risk_mult_is_one(self, mock_q):
        from domain.hazard_analysis import compute_survival_curve
        model_df = pd.DataFrame([{
            "model_id": "h1", "model_type": "cox_ph",
            "coefficients": json.dumps({"covariates": []}),
            "baseline_hazard": json.dumps({str(t): 0.01 for t in range(1, 13)}),
        }])
        mock_q.side_effect = [model_df, pd.DataFrame()]
        result = compute_survival_curve("h1")
        assert result["risk_multiplier"] == 1.0

    @patch("domain.hazard_retrieval.query_df")
    def test_model_not_found_raises(self, mock_q):
        from domain.hazard_analysis import compute_survival_curve
        mock_q.return_value = pd.DataFrame()
        with pytest.raises(ValueError, match="not found"):
            compute_survival_curve("bad-id")


class TestListHazardModels:
    @patch("domain.hazard_retrieval.query_df")
    def test_empty_returns_empty(self, mock_q):
        from domain.hazard_retrieval import list_hazard_models
        mock_q.return_value = pd.DataFrame()
        assert list_hazard_models() == []

    @patch("domain.hazard_retrieval.query_df")
    def test_filter_by_model_type(self, mock_q):
        from domain.hazard_retrieval import list_hazard_models
        mock_q.return_value = pd.DataFrame()
        list_hazard_models(model_type="cox_ph")
        sql = mock_q.call_args[0][0]
        assert "model_type" in sql.lower()

    @patch("domain.hazard_retrieval.query_df")
    def test_filter_by_product_type(self, mock_q):
        from domain.hazard_retrieval import list_hazard_models
        mock_q.return_value = pd.DataFrame()
        list_hazard_models(product_type="mortgage")
        sql = mock_q.call_args[0][0]
        assert "product_type" in sql.lower()


class TestGetHazardModel:
    @patch("domain.hazard_retrieval.query_df")
    def test_not_found_returns_none(self, mock_q):
        from domain.hazard_retrieval import get_hazard_model
        mock_q.return_value = pd.DataFrame()
        assert get_hazard_model("bad-id") is None

    @patch("domain.hazard_retrieval.query_df")
    def test_parses_json_columns(self, mock_q):
        from domain.hazard_retrieval import get_hazard_model
        model_df = pd.DataFrame([{
            "model_id": "h1", "model_type": "cox_ph",
            "coefficients": json.dumps({"covariates": [{"name": "x", "coefficient": 0.5}]}),
            "baseline_hazard": json.dumps({"1": 0.01}),
            "concordance_index": 0.72,
        }])
        curves_df = pd.DataFrame()
        mock_q.side_effect = [model_df, curves_df]
        result = get_hazard_model("h1")
        assert isinstance(result["coefficients"], dict)
        assert isinstance(result["baseline_hazard"], dict)


# ===========================================================================
# ADVANCED — Compute structure, revolving logic, list functions
# ===========================================================================


@pytest.fixture
def _patch_advanced_db():
    with patch("domain.advanced.query_df") as mock_q, \
         patch("domain.advanced.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


class TestComputeCureRatesStructure:
    def test_returns_required_keys(self, _patch_advanced_db):
        from domain.advanced import compute_cure_rates
        result = compute_cure_rates()
        assert "cure_by_dpd" in result
        assert "cure_by_product" in result
        assert "cure_by_segment" in result
        assert "cure_trend" in result
        assert "time_to_cure" in result
        assert "overall_cure_rate" in result
        assert "methodology" in result

    def test_cure_by_dpd_has_four_buckets(self, _patch_advanced_db):
        from domain.advanced import compute_cure_rates
        result = compute_cure_rates()
        assert len(result["cure_by_dpd"]) == 4
        buckets = {r["dpd_bucket"] for r in result["cure_by_dpd"]}
        assert "1-30 DPD" in buckets
        assert "90+ DPD" in buckets

    def test_cure_rates_in_valid_range(self, _patch_advanced_db):
        from domain.advanced import compute_cure_rates
        result = compute_cure_rates()
        for entry in result["cure_by_dpd"]:
            assert 0 <= entry["cure_rate"] <= 1.0

    def test_cure_trend_has_12_months(self, _patch_advanced_db):
        from domain.advanced import compute_cure_rates
        result = compute_cure_rates()
        assert len(result["cure_trend"]) == 12

    def test_time_to_cure_has_12_entries(self, _patch_advanced_db):
        from domain.advanced import compute_cure_rates
        result = compute_cure_rates()
        assert len(result["time_to_cure"]) == 12

    def test_product_filter_passed(self, _patch_advanced_db):
        from domain.advanced import compute_cure_rates
        result = compute_cure_rates(product_type="mortgage")
        assert result["product_type"] == "mortgage"


class TestComputeCcfStructure:
    def test_returns_required_keys(self, _patch_advanced_db):
        from domain.advanced import compute_ccf
        result = compute_ccf()
        assert "ccf_by_stage" in result
        assert "ccf_by_utilization" in result
        assert "ccf_by_product_summary" in result
        assert "overall_avg_ccf" in result
        assert "total_ead" in result

    def test_ccf_by_utilization_has_5_bands(self, _patch_advanced_db):
        from domain.advanced import compute_ccf
        result = compute_ccf()
        assert len(result["ccf_by_utilization"]) == 5

    def test_revolving_ccf_lower_than_nonrevolving(self, _patch_advanced_db):
        from domain.advanced import compute_ccf
        result = compute_ccf()
        revolving = [r for r in result["ccf_by_stage"] if r["is_revolving"]]
        non_revolving = [r for r in result["ccf_by_stage"] if not r["is_revolving"]]
        if revolving and non_revolving:
            avg_rev = sum(r["ccf"] for r in revolving) / len(revolving)
            avg_nonrev = sum(r["ccf"] for r in non_revolving) / len(non_revolving)
            # Revolving CCFs should generally be lower (more undrawn)
            assert avg_rev < avg_nonrev

    def test_ccf_values_in_valid_range(self, _patch_advanced_db):
        from domain.advanced import compute_ccf
        result = compute_ccf()
        for entry in result["ccf_by_stage"]:
            assert 0 <= entry["ccf"] <= 1.5  # CCF can slightly exceed 1 due to random noise


class TestListCureAnalyses:
    def test_empty_returns_empty(self, _patch_advanced_db):
        from domain.advanced import list_cure_analyses
        result = list_cure_analyses()
        assert result == []

    def test_formats_created_at(self, _patch_advanced_db):
        from domain.advanced import list_cure_analyses
        _patch_advanced_db["query_df"].return_value = pd.DataFrame([{
            "analysis_id": "cure-1", "product_type": "all",
            "segment": "all", "observation_period": "12 months",
            "methodology": "test", "created_at": datetime(2025, 6, 15),
            "overall_cure_rate": "0.35", "total_observations": "5000",
        }])
        result = list_cure_analyses()
        assert len(result) == 1
        assert isinstance(result[0]["created_at"], str)
        assert result[0]["overall_cure_rate"] == 0.35
        assert result[0]["total_observations"] == 5000


class TestListCcfAnalyses:
    def test_empty_returns_empty(self, _patch_advanced_db):
        from domain.advanced import list_ccf_analyses
        result = list_ccf_analyses()
        assert result == []

    def test_formats_records(self, _patch_advanced_db):
        from domain.advanced import list_ccf_analyses
        _patch_advanced_db["query_df"].return_value = pd.DataFrame([{
            "analysis_id": "ccf-1", "product_type": "all",
            "methodology": "CCF formula", "created_at": datetime(2025, 6, 15),
        }])
        result = list_ccf_analyses()
        assert len(result) == 1
        assert isinstance(result[0]["created_at"], str)


# ===========================================================================
# BACKTESTING — Trend, List
# ===========================================================================


@pytest.fixture
def _patch_backtest_db():
    with patch("domain.backtesting.query_df") as mock_q, \
         patch("domain.backtesting.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


class TestGetBacktestTrendMulti:
    def test_multiple_backtests_returned(self, _patch_backtest_db):
        from domain.backtesting import get_backtest_trend
        _patch_backtest_db["query_df"].return_value = pd.DataFrame([
            {"backtest_id": "bt1", "backtest_date": "2025-01-01",
             "overall_traffic_light": "Green",
             "metric_name": "AUC", "metric_value": 0.82, "pass_fail": "Green"},
            {"backtest_id": "bt1", "backtest_date": "2025-01-01",
             "overall_traffic_light": "Green",
             "metric_name": "Gini", "metric_value": 0.64, "pass_fail": "Green"},
            {"backtest_id": "bt2", "backtest_date": "2025-06-01",
             "overall_traffic_light": "Amber",
             "metric_name": "AUC", "metric_value": 0.75, "pass_fail": "Amber"},
        ])
        result = get_backtest_trend("PD")
        assert len(result) == 2
        bt1 = [r for r in result if r["backtest_id"] == "bt1"][0]
        assert bt1["AUC"] == 0.82
        assert bt1["Gini"] == 0.64
        assert bt1["AUC_light"] == "Green"

    def test_empty_trend(self, _patch_backtest_db):
        from domain.backtesting import get_backtest_trend
        result = get_backtest_trend("PD")
        assert result == []


class TestListBacktestsFiltering:
    def test_filter_by_model_type(self, _patch_backtest_db):
        from domain.backtesting import list_backtests
        _patch_backtest_db["query_df"].return_value = pd.DataFrame()
        list_backtests(model_type="LGD")
        sql = _patch_backtest_db["query_df"].call_args[0][0]
        assert "model_type" in sql.lower()

    def test_no_filter(self, _patch_backtest_db):
        from domain.backtesting import list_backtests
        _patch_backtest_db["query_df"].return_value = pd.DataFrame()
        result = list_backtests()
        assert result == []


# ===========================================================================
# PERIOD CLOSE — Step Ordering, Constants, Unknown Step
# ===========================================================================


class TestPipelineStepsConstants:
    def test_six_steps_defined(self):
        from domain.period_close import PIPELINE_STEPS
        assert len(PIPELINE_STEPS) == 6

    def test_steps_have_sequential_order(self):
        from domain.period_close import PIPELINE_STEPS
        orders = [s["order"] for s in PIPELINE_STEPS]
        assert orders == sorted(orders)
        assert orders == list(range(1, 7))

    def test_all_steps_have_required_fields(self):
        from domain.period_close import PIPELINE_STEPS
        for step in PIPELINE_STEPS:
            assert "key" in step
            assert "label" in step
            assert "order" in step

    def test_step_keys_are_unique(self):
        from domain.period_close import PIPELINE_STEPS
        keys = [s["key"] for s in PIPELINE_STEPS]
        assert len(keys) == len(set(keys))


class TestRunStepLogicUnknownKey:
    def test_unknown_key_returns_generic_message(self):
        from domain.period_close import _run_step_logic
        result = _run_step_logic("unknown_step_xyz")
        assert "message" in result
        assert "unknown_step_xyz" in result["message"]


class TestPeriodCloseRunIdFormat:
    @patch("domain.period_close.execute")
    def test_run_id_contains_project_id(self, mock_exec):
        from domain.period_close import start_pipeline
        result = start_pipeline("my-project", "admin")
        assert "my-project" in result["run_id"]
        assert result["run_id"].startswith("PIPE-")


# ===========================================================================
# VALID STATUS TRANSITIONS — Exhaustive edge cases
# ===========================================================================


class TestStatusTransitionConstants:
    def test_all_statuses_in_transition_map(self):
        from domain.model_registry import VALID_MODEL_STATUSES, VALID_STATUS_TRANSITIONS
        for status in VALID_MODEL_STATUSES:
            assert status in VALID_STATUS_TRANSITIONS

    def test_retired_is_terminal(self):
        from domain.model_registry import VALID_STATUS_TRANSITIONS
        assert VALID_STATUS_TRANSITIONS["retired"] == []

    def test_draft_can_only_go_to_pending(self):
        from domain.model_registry import VALID_STATUS_TRANSITIONS
        assert VALID_STATUS_TRANSITIONS["draft"] == ["pending_review"]

    def test_active_can_only_retire(self):
        from domain.model_registry import VALID_STATUS_TRANSITIONS
        assert VALID_STATUS_TRANSITIONS["active"] == ["retired"]

    def test_valid_model_types_set(self):
        from domain.model_registry import VALID_MODEL_TYPES
        assert VALID_MODEL_TYPES == {"PD", "LGD", "EAD", "Staging"}


# ===========================================================================
# COLLATERAL — Additional formula and structure tests
# ===========================================================================


class TestCollateralHaircutStructure:
    def test_seven_collateral_types(self, _patch_advanced_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_advanced_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        assert len(result["haircut_results"]) == 7

    def test_unsecured_has_lgd_unsecured(self, _patch_advanced_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_advanced_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        unsecured = [r for r in result["haircut_results"] if r["collateral_type"] == "unsecured"]
        assert len(unsecured) == 1
        assert unsecured[0]["lgd_unsecured"] is not None
        assert unsecured[0]["haircut_pct"] > 0.95  # Near 1.0

    def test_cash_deposit_lowest_haircut(self, _patch_advanced_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_advanced_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        cash = [r for r in result["haircut_results"] if r["collateral_type"] == "cash_deposit"][0]
        others = [r for r in result["haircut_results"] if r["collateral_type"] != "cash_deposit"]
        assert all(cash["haircut_pct"] < o["haircut_pct"] for o in others)

    def test_lgd_waterfall_has_five_steps(self, _patch_advanced_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_advanced_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        assert len(result["lgd_waterfall"]) == 5
        assert result["lgd_waterfall"][0]["step"] == "Gross Exposure"

    def test_summary_keys(self, _patch_advanced_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_advanced_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        summary = result["summary"]
        assert "avg_haircut" in summary
        assert "avg_recovery_rate" in summary
        assert "net_lgd_pct" in summary
        assert "secured_pct" in summary
