"""
Sprint 7: Domain Logic — Registry, Backtesting, Markov, Hazard, Advanced, Period Close, Health.

Comprehensive tests for the analytical domain modules covering:
  - Model registry lifecycle (register, status transitions, promote, audit, sensitivity, recalibration)
  - Backtesting integration (run_backtest, list, get, trend, cohort)
  - Backtesting traffic lights (boundary values for all 10 metrics)
  - Backtesting stats edge cases (numerical stability)
  - Markov (forecast stage distribution, lifetime PD monotonicity, absorbing convergence)
  - Hazard (estimation orchestrator, retrieval, survival curve math, term structure PD)
  - Advanced (cure/ccf/collateral get/list, product filter, LGD waterfall)
  - Period close (full pipeline, step failure, health aggregation)
  - Health checks (all 5 checks, degraded status, error paths)
"""
import json
import math
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


# ===========================================================================
# MODEL REGISTRY — Lifecycle, Audit, Sensitivity, Recalibration
# ===========================================================================


class TestRegisterModel:
    """Tests for register_model() — new model creation."""

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_register_returns_model(self, mock_get, mock_exec):
        from domain.model_registry import register_model
        mock_get.return_value = {"model_id": "m1", "status": "draft", "model_type": "PD"}
        result = register_model({"model_name": "PD v1", "model_type": "PD", "algorithm": "logistic"})
        assert result["status"] == "draft"
        assert result["model_type"] == "PD"

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_register_with_custom_id(self, mock_get, mock_exec):
        from domain.model_registry import register_model
        mock_get.return_value = {"model_id": "custom-id", "status": "draft"}
        result = register_model({"model_id": "custom-id", "model_type": "LGD", "algorithm": "linear"})
        assert result["model_id"] == "custom-id"

    def test_register_invalid_model_type_raises(self):
        from domain.model_registry import register_model
        with pytest.raises(ValueError, match="Invalid model_type"):
            register_model({"model_type": "INVALID", "algorithm": "test"})

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_register_logs_audit(self, mock_get, mock_exec):
        from domain.model_registry import register_model
        mock_get.return_value = {"model_id": "m1", "status": "draft"}
        register_model({"model_type": "PD", "algorithm": "logistic"})
        # execute called twice: INSERT model + INSERT audit
        assert mock_exec.call_count == 2

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_register_defaults(self, mock_get, mock_exec):
        from domain.model_registry import register_model
        mock_get.return_value = {"model_id": "x", "status": "draft", "version": 1}
        result = register_model({"model_type": "EAD", "algorithm": "calc"})
        assert result["version"] == 1
        assert result["status"] == "draft"


class TestListModels:
    @patch("domain.model_registry.query_df")
    def test_empty_returns_empty(self, mock_q):
        from domain.model_registry import list_models
        mock_q.return_value = pd.DataFrame()
        assert list_models() == []

    @patch("domain.model_registry.query_df")
    def test_filter_by_type(self, mock_q):
        from domain.model_registry import list_models
        mock_q.return_value = pd.DataFrame([{
            "model_id": "m1", "model_name": "PD v1", "model_type": "PD",
            "algorithm": "logistic", "version": 1, "description": "",
            "status": "draft", "product_type": "", "cohort": "",
            "parameters": "{}", "performance_metrics": "{}",
            "training_data_info": "{}", "is_champion": False,
            "created_by": "system", "created_at": "2025-01-01",
            "approved_by": None, "approved_at": None,
            "promoted_by": None, "promoted_at": None,
            "retired_by": None, "retired_at": None,
            "notes": "", "parent_model_id": None,
        }])
        result = list_models(model_type="PD")
        assert len(result) == 1
        assert result[0]["model_type"] == "PD"
        # Verify query used WHERE clause
        call_args = mock_q.call_args[0][0]
        assert "model_type = %s" in call_args

    @patch("domain.model_registry.query_df")
    def test_filter_by_status(self, mock_q):
        from domain.model_registry import list_models
        mock_q.return_value = pd.DataFrame()
        list_models(status="active")
        call_args = mock_q.call_args[0][0]
        assert "status = %s" in call_args

    @patch("domain.model_registry.query_df")
    def test_filter_by_both(self, mock_q):
        from domain.model_registry import list_models
        mock_q.return_value = pd.DataFrame()
        list_models(model_type="PD", status="draft")
        call_args = mock_q.call_args[0][0]
        assert "model_type = %s" in call_args
        assert "status = %s" in call_args


class TestUpdateModelStatus:
    """Tests for the governance state machine."""

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_draft_to_pending(self, mock_get, mock_exec):
        from domain.model_registry import update_model_status
        mock_get.side_effect = [
            {"model_id": "m1", "status": "draft"},
            {"model_id": "m1", "status": "pending_review"},
        ]
        result = update_model_status("m1", "pending_review", "analyst")
        assert result["status"] == "pending_review"

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_pending_to_approved(self, mock_get, mock_exec):
        from domain.model_registry import update_model_status
        mock_get.side_effect = [
            {"model_id": "m1", "status": "pending_review"},
            {"model_id": "m1", "status": "approved", "approved_by": "reviewer"},
        ]
        result = update_model_status("m1", "approved", "reviewer")
        assert result["status"] == "approved"

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_pending_to_draft_rejected(self, mock_get, mock_exec):
        from domain.model_registry import update_model_status
        mock_get.side_effect = [
            {"model_id": "m1", "status": "pending_review"},
            {"model_id": "m1", "status": "draft"},
        ]
        result = update_model_status("m1", "draft", "reviewer", "Needs rework")
        assert result["status"] == "draft"

    @patch("domain.model_registry.get_model")
    def test_invalid_transition_raises(self, mock_get):
        from domain.model_registry import update_model_status
        mock_get.return_value = {"model_id": "m1", "status": "draft"}
        with pytest.raises(ValueError, match="Cannot transition"):
            update_model_status("m1", "active", "user")

    @patch("domain.model_registry.get_model")
    def test_draft_to_approved_raises(self, mock_get):
        from domain.model_registry import update_model_status
        mock_get.return_value = {"model_id": "m1", "status": "draft"}
        with pytest.raises(ValueError, match="Cannot transition"):
            update_model_status("m1", "approved", "user")

    @patch("domain.model_registry.get_model")
    def test_retired_no_transitions(self, mock_get):
        from domain.model_registry import update_model_status
        mock_get.return_value = {"model_id": "m1", "status": "retired"}
        with pytest.raises(ValueError, match="Cannot transition"):
            update_model_status("m1", "draft", "user")

    @patch("domain.model_registry.get_model")
    def test_not_found_raises(self, mock_get):
        from domain.model_registry import update_model_status
        mock_get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            update_model_status("missing", "approved", "user")

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_approved_to_active_sets_promoted_by(self, mock_get, mock_exec):
        from domain.model_registry import update_model_status
        mock_get.side_effect = [
            {"model_id": "m1", "status": "approved"},
            {"model_id": "m1", "status": "active", "promoted_by": "admin"},
        ]
        result = update_model_status("m1", "active", "admin")
        # Verify promoted_by was set in the UPDATE
        update_call = mock_exec.call_args_list[0]
        sql = update_call[0][0]
        assert "promoted_by" in sql

    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_active_to_retired_sets_retired_by(self, mock_get, mock_exec):
        from domain.model_registry import update_model_status
        mock_get.side_effect = [
            {"model_id": "m1", "status": "active"},
            {"model_id": "m1", "status": "retired"},
        ]
        update_model_status("m1", "retired", "admin")
        update_call = mock_exec.call_args_list[0]
        sql = update_call[0][0]
        assert "retired_by" in sql
        assert "is_champion = FALSE" in sql


class TestPromoteChampion:
    @patch("domain.model_registry.execute")
    @patch("domain.model_registry.get_model")
    def test_promote_approved_model(self, mock_get, mock_exec):
        from domain.model_registry import promote_champion
        mock_get.side_effect = [
            {"model_id": "m1", "status": "approved", "model_type": "PD"},
            {"model_id": "m1", "is_champion": True},
        ]
        result = promote_champion("m1", "admin")
        assert result["is_champion"] is True
        # Unset previous champion + set new + audit = 3 execute calls
        assert mock_exec.call_count == 3

    @patch("domain.model_registry.get_model")
    def test_promote_draft_raises(self, mock_get):
        from domain.model_registry import promote_champion
        mock_get.return_value = {"model_id": "m1", "status": "draft", "model_type": "PD"}
        with pytest.raises(ValueError, match="Only approved or active"):
            promote_champion("m1", "admin")

    @patch("domain.model_registry.get_model")
    def test_promote_not_found_raises(self, mock_get):
        from domain.model_registry import promote_champion
        mock_get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            promote_champion("missing", "admin")


class TestCompareModels:
    @patch("domain.model_registry.query_df")
    def test_empty_list(self, mock_q):
        from domain.model_registry import compare_models
        assert compare_models([]) == []

    @patch("domain.model_registry.query_df")
    def test_returns_parsed_rows(self, mock_q):
        from domain.model_registry import compare_models
        mock_q.return_value = pd.DataFrame([{
            "model_id": "m1", "model_name": "PD v1", "model_type": "PD",
            "algorithm": "logistic", "version": 1, "description": "",
            "status": "active", "product_type": "all",
            "parameters": '{"intercept": -2.0}', "performance_metrics": '{"auc": 0.8}',
            "is_champion": True, "created_by": "system", "created_at": "2025-01-01",
        }])
        result = compare_models(["m1"])
        assert len(result) == 1
        assert isinstance(result[0]["parameters"], dict)


class TestGetModelAuditTrail:
    @patch("domain.model_registry.query_df")
    def test_empty_audit(self, mock_q):
        from domain.model_registry import get_model_audit_trail
        mock_q.return_value = pd.DataFrame()
        assert get_model_audit_trail("m1") == []

    @patch("domain.model_registry.query_df")
    def test_returns_records(self, mock_q):
        from domain.model_registry import get_model_audit_trail
        mock_q.return_value = pd.DataFrame([
            {"audit_id": "a1", "model_id": "m1", "action": "registered",
             "old_status": None, "new_status": "draft",
             "performed_by": "system", "performed_at": "2025-01-01", "comment": "created"},
            {"audit_id": "a2", "model_id": "m1", "action": "submitted_for_review",
             "old_status": "draft", "new_status": "pending_review",
             "performed_by": "analyst", "performed_at": "2025-01-02", "comment": ""},
        ])
        result = get_model_audit_trail("m1")
        assert len(result) == 2
        assert result[0]["action"] == "registered"


class TestSensitivityEdgeCases:
    @patch("domain.model_registry.get_model")
    def test_no_matching_params(self, mock_get):
        from domain.model_registry import compute_sensitivity
        mock_get.return_value = {
            "model_id": "m1", "model_name": "Empty",
            "parameters": {"custom_param": "non_numeric"},
            "performance_metrics": {},
        }
        result = compute_sensitivity("m1")
        assert result["sensitivities"] == []

    @patch("domain.model_registry.get_model")
    def test_zero_base_value(self, mock_get):
        from domain.model_registry import compute_sensitivity
        mock_get.return_value = {
            "model_id": "m1", "model_name": "Zero",
            "parameters": {"intercept": 0.0},
            "performance_metrics": {},
        }
        result = compute_sensitivity("m1", perturbation_pct=10.0)
        assert len(result["sensitivities"]) == 1
        s = result["sensitivities"][0]
        assert s["base_value"] == 0.0
        assert s["perturbed_up"] == 0.0


class TestRecalibrationEdgeCases:
    @patch("domain.model_registry.get_model")
    def test_no_dates(self, mock_get):
        from domain.model_registry import check_recalibration_due
        mock_get.return_value = {
            "model_id": "m1", "model_name": "No dates",
            "status": "draft", "created_at": None, "approved_at": None,
        }
        result = check_recalibration_due("m1")
        assert result["age_days"] == 0
        assert result["recalibration_due"] is False

    @patch("domain.model_registry.get_model")
    def test_custom_max_age(self, mock_get):
        from domain.model_registry import check_recalibration_due
        old_date = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        mock_get.return_value = {
            "model_id": "m1", "model_name": "Custom",
            "status": "active", "created_at": old_date, "approved_at": old_date,
        }
        result = check_recalibration_due("m1", max_age_days=180)
        assert result["recalibration_due"] is True
        result2 = check_recalibration_due("m1", max_age_days=365)
        assert result2["recalibration_due"] is False


# ===========================================================================
# BACKTESTING — Traffic Light Boundaries
# ===========================================================================


class TestTrafficLightBoundaries:
    """Test exact boundary values for all 10 metrics in METRIC_THRESHOLDS."""

    def test_auc_exact_green_boundary(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("AUC", 0.70) == "Green"

    def test_auc_just_below_green(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("AUC", 0.699) == "Amber"

    def test_auc_exact_amber_boundary(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("AUC", 0.60) == "Amber"

    def test_auc_just_below_amber(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("AUC", 0.599) == "Red"

    def test_gini_boundaries(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("Gini", 0.40) == "Green"
        assert _traffic_light("Gini", 0.39) == "Amber"
        assert _traffic_light("Gini", 0.20) == "Amber"
        assert _traffic_light("Gini", 0.19) == "Red"

    def test_ks_boundaries(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("KS", 0.30) == "Green"
        assert _traffic_light("KS", 0.15) == "Amber"
        assert _traffic_light("KS", 0.14) == "Red"

    def test_psi_boundaries_lower_better(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("PSI", 0.10) == "Green"
        assert _traffic_light("PSI", 0.11) == "Amber"
        assert _traffic_light("PSI", 0.25) == "Amber"
        assert _traffic_light("PSI", 0.26) == "Red"

    def test_brier_boundaries(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("Brier", 0.15) == "Green"
        assert _traffic_light("Brier", 0.16) == "Amber"
        assert _traffic_light("Brier", 0.25) == "Amber"
        assert _traffic_light("Brier", 0.26) == "Red"

    def test_hl_pvalue_boundaries(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.05) == "Green"
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.049) == "Amber"
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.01) == "Amber"
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.009) == "Red"

    def test_binomial_pass_rate_boundaries(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("Binomial_pass_rate", 0.80) == "Green"
        assert _traffic_light("Binomial_pass_rate", 0.79) == "Amber"
        assert _traffic_light("Binomial_pass_rate", 0.60) == "Amber"
        assert _traffic_light("Binomial_pass_rate", 0.59) == "Red"

    def test_mae_boundaries(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("MAE", 0.10) == "Green"
        assert _traffic_light("MAE", 0.11) == "Amber"
        assert _traffic_light("MAE", 0.20) == "Amber"
        assert _traffic_light("MAE", 0.21) == "Red"

    def test_rmse_boundaries(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("RMSE", 0.15) == "Green"
        assert _traffic_light("RMSE", 0.16) == "Amber"
        assert _traffic_light("RMSE", 0.25) == "Amber"
        assert _traffic_light("RMSE", 0.26) == "Red"

    def test_mean_bias_boundaries(self):
        from domain.backtesting_traffic import _traffic_light
        assert _traffic_light("Mean_Bias", 0.05) == "Green"
        assert _traffic_light("Mean_Bias", 0.06) == "Amber"
        assert _traffic_light("Mean_Bias", 0.10) == "Amber"
        assert _traffic_light("Mean_Bias", 0.11) == "Red"


class TestOverallTrafficLightEdge:
    def test_empty_list(self):
        from domain.backtesting_traffic import _overall_traffic_light
        assert _overall_traffic_light([]) == "Green"

    def test_single_green(self):
        from domain.backtesting_traffic import _overall_traffic_light
        assert _overall_traffic_light(["Green"]) == "Green"

    def test_all_red(self):
        from domain.backtesting_traffic import _overall_traffic_light
        assert _overall_traffic_light(["Red", "Red", "Red"]) == "Red"

    def test_mixed_amber_only(self):
        from domain.backtesting_traffic import _overall_traffic_light
        assert _overall_traffic_light(["Amber", "Amber"]) == "Amber"


# ===========================================================================
# BACKTESTING STATS — Edge Cases
# ===========================================================================


class TestBacktestingStatsEdgeCases:
    def test_auc_single_observation(self):
        from domain.backtesting_stats import _compute_auc_gini_ks
        result = _compute_auc_gini_ks([0.5], [1])
        assert result["auc"] == 0.5  # no negatives, AUC = 0.5

    def test_psi_single_value_each(self):
        from domain.backtesting_stats import _compute_psi
        result = _compute_psi([0.5], [0.5])
        assert result >= 0  # Non-negative

    def test_brier_single_prediction(self):
        from domain.backtesting_stats import _compute_brier
        assert _compute_brier([0.5], [1]) == pytest.approx(0.25, abs=0.01)

    def test_hosmer_lemeshow_with_all_defaults(self):
        from domain.backtesting_stats import _hosmer_lemeshow_test
        n = 100
        result = _hosmer_lemeshow_test([0.5] * n, [1] * n)
        assert "chi_squared" in result

    def test_spiegelhalter_with_constant_predictions(self):
        from domain.backtesting_stats import _spiegelhalter_test
        result = _spiegelhalter_test([0.5] * 100, [0] * 50 + [1] * 50)
        assert result["pass"] is True  # Well-calibrated at 50%

    def test_binomial_high_default_rate(self):
        from domain.backtesting_stats import _binomial_test
        result = _binomial_test(predicted_pd=0.50, n_obligors=100, n_defaults=50)
        assert result["pass"] == True  # Observed matches predicted

    def test_jeffreys_single_default(self):
        from domain.backtesting_stats import _jeffreys_test
        result = _jeffreys_test(predicted_pd=0.05, n_obligors=100, n_defaults=1)
        assert "posterior_mean" in result
        assert result["posterior_mean"] < 0.05  # 1/100 < 5%


# ===========================================================================
# BACKTESTING — Run Backtest Integration
# ===========================================================================


class TestJsonDefaultHelper:
    """Regression: numpy types must be JSON-serializable in backtesting detail."""

    def test_numpy_bool_serializable(self):
        from domain.backtesting import _json_default
        assert _json_default(np.bool_(True)) is True
        assert _json_default(np.bool_(False)) is False

    def test_numpy_int_serializable(self):
        from domain.backtesting import _json_default
        assert _json_default(np.int64(42)) == 42
        assert isinstance(_json_default(np.int64(42)), int)

    def test_numpy_float_serializable(self):
        from domain.backtesting import _json_default
        assert abs(_json_default(np.float64(3.14)) - 3.14) < 1e-10
        assert isinstance(_json_default(np.float64(3.14)), float)

    def test_numpy_array_serializable(self):
        from domain.backtesting import _json_default
        result = _json_default(np.array([1, 2, 3]))
        assert result == [1, 2, 3]

    def test_unknown_type_raises(self):
        from domain.backtesting import _json_default
        with pytest.raises(TypeError):
            _json_default(object())


class TestRunBacktest:
    """Test run_backtest() with mocked DB."""

    @patch("domain.backtesting.get_backtest")
    @patch("domain.backtesting.execute")
    @patch("domain.backtesting.query_df")
    def test_pd_backtest_computes_metrics(self, mock_q, mock_exec, mock_get):
        from domain.backtesting import run_backtest
        rng = np.random.default_rng(42)
        n = 200
        loan_df = pd.DataFrame({
            "loan_id": [f"L{i}" for i in range(n)],
            "product_type": rng.choice(["mortgage", "personal"], n).tolist(),
            "assessed_stage": rng.choice([1, 1, 1, 2, 3], n).tolist(),
            "current_lifetime_pd": np.round(rng.uniform(0.01, 0.3, n), 4).tolist(),
            "days_past_due": rng.integers(0, 120, n).tolist(),
            "segment": ["retail"] * n,
            "vintage_cohort": rng.choice(["2022", "2023"], n).tolist(),
            "gross_carrying_amount": np.round(rng.uniform(1000, 50000, n), 2).tolist(),
            "defaulted": (rng.random(n) < 0.1).astype(int).tolist(),
        })
        mock_q.return_value = loan_df
        mock_get.return_value = {"backtest_id": "BT-PD-test", "metrics": [], "cohort_results": []}
        result = run_backtest("PD")
        assert result is not None
        # Verify metrics were inserted (execute called for metrics + cohorts + result)
        assert mock_exec.call_count > 0

    @patch("domain.backtesting.query_df")
    def test_empty_portfolio_raises(self, mock_q):
        from domain.backtesting import run_backtest
        mock_q.return_value = pd.DataFrame()
        with pytest.raises(ValueError, match="No portfolio data"):
            run_backtest("PD")


class TestListBacktests:
    @patch("domain.backtesting.query_df")
    def test_empty(self, mock_q):
        from domain.backtesting import list_backtests
        mock_q.return_value = pd.DataFrame()
        assert list_backtests() == []

    @patch("domain.backtesting.query_df")
    def test_filter_by_type(self, mock_q):
        from domain.backtesting import list_backtests
        mock_q.return_value = pd.DataFrame([{
            "backtest_id": "BT-PD-1", "model_type": "PD",
            "backtest_date": "2025-01-01", "observation_window": "12M",
            "outcome_window": "12M", "overall_traffic_light": "Green",
            "pass_count": 5, "amber_count": 0, "fail_count": 0,
            "total_loans": 1000, "created_by": "system",
        }])
        result = list_backtests("PD")
        assert len(result) == 1
        assert "model_type = %s" in mock_q.call_args[0][0]


class TestGetBacktest:
    @patch("domain.backtesting.query_df")
    def test_not_found(self, mock_q):
        from domain.backtesting import get_backtest
        mock_q.return_value = pd.DataFrame()
        assert get_backtest("nonexistent") is None

    @patch("domain.backtesting.query_df")
    def test_returns_with_metrics_and_cohorts(self, mock_q):
        from domain.backtesting import get_backtest
        result_df = pd.DataFrame([{
            "backtest_id": "BT-1", "model_type": "PD",
            "backtest_date": "2025-01-01", "observation_window": "12M",
            "outcome_window": "12M", "overall_traffic_light": "Green",
            "pass_count": 5, "amber_count": 0, "fail_count": 0,
            "total_loans": 1000, "config": '{}', "created_by": "system",
        }])
        metrics_df = pd.DataFrame([{
            "metric_id": "m1", "metric_name": "AUC", "metric_value": 0.85,
            "threshold_green": 0.70, "threshold_amber": 0.60,
            "pass_fail": "Green", "detail": None,
        }])
        cohort_df = pd.DataFrame([{
            "cohort_id": "c1", "cohort_name": "mortgage",
            "predicted_rate": 0.05, "actual_rate": 0.04, "count": 500, "abs_diff": 0.01,
        }])
        mock_q.side_effect = [result_df, metrics_df, cohort_df]
        result = get_backtest("BT-1")
        assert result is not None
        assert len(result["metrics"]) == 1
        assert len(result["cohort_results"]) == 1


class TestGetBacktestTrend:
    @patch("domain.backtesting.query_df")
    def test_empty(self, mock_q):
        from domain.backtesting import get_backtest_trend
        mock_q.return_value = pd.DataFrame()
        assert get_backtest_trend("PD") == []

    @patch("domain.backtesting.query_df")
    def test_returns_trend(self, mock_q):
        from domain.backtesting import get_backtest_trend
        mock_q.return_value = pd.DataFrame([
            {"backtest_id": "BT-1", "backtest_date": "2025-01-01",
             "overall_traffic_light": "Green", "metric_name": "AUC",
             "metric_value": 0.85, "pass_fail": "Green"},
            {"backtest_id": "BT-1", "backtest_date": "2025-01-01",
             "overall_traffic_light": "Green", "metric_name": "Gini",
             "metric_value": 0.70, "pass_fail": "Green"},
        ])
        result = get_backtest_trend("PD")
        assert len(result) == 1  # grouped by backtest_id
        assert "AUC" in result[0]
        assert "Gini" in result[0]


# ===========================================================================
# MARKOV — Additional Edge Cases
# ===========================================================================


@pytest.fixture
def _patch_markov_db():
    with patch("domain.markov.query_df") as mock_q, \
         patch("domain.markov.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


class TestMarkovForecastCorrectness:
    def test_identity_matrix_no_change(self, _patch_markov_db):
        from domain.markov import forecast_stage_distribution
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["S1", "S2", "S3", "Default"],
                "matrix": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            }),
        }])
        _patch_markov_db["query_df"].return_value = mat_row
        result = forecast_stage_distribution("m1", [0.7, 0.2, 0.1, 0.0], 12)
        points = result["forecast_data"]["points"]
        # With identity matrix, distribution should not change
        for pt in points:
            assert abs(pt["S1"] - 70.0) < 0.01
            assert abs(pt["S2"] - 20.0) < 0.01

    def test_absorbing_converges_to_default(self, _patch_markov_db):
        from domain.markov import forecast_stage_distribution
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["S1", "S2", "Default"],
                "matrix": [[0.5, 0.3, 0.2], [0.0, 0.5, 0.5], [0.0, 0.0, 1.0]],
            }),
        }])
        _patch_markov_db["query_df"].return_value = mat_row
        result = forecast_stage_distribution("m1", [1.0, 0.0, 0.0], 50)
        last_point = result["forecast_data"]["points"][-1]
        # After many steps, should converge to absorbing state
        assert last_point["Default"] > 90.0

    def test_short_distribution_padded(self, _patch_markov_db):
        from domain.markov import forecast_stage_distribution
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["S1", "S2", "S3"],
                "matrix": [[0.9, 0.05, 0.05], [0.1, 0.8, 0.1], [0.0, 0.1, 0.9]],
            }),
        }])
        _patch_markov_db["query_df"].return_value = mat_row
        # Pass only 2 elements for 3 states — should pad
        result = forecast_stage_distribution("m1", [0.8, 0.2], 3)
        assert result is not None


class TestMarkovLifetimePdProperties:
    def test_stage3_higher_pd_than_stage1(self, _patch_markov_db):
        from domain.markov import compute_lifetime_pd
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["Stage 1", "Stage 2", "Stage 3", "Default"],
                "matrix": [[0.9, 0.05, 0.03, 0.02],
                           [0.02, 0.8, 0.1, 0.08],
                           [0.0, 0.02, 0.7, 0.28],
                           [0.0, 0.0, 0.0, 1.0]],
            }),
        }])
        _patch_markov_db["query_df"].return_value = mat_row
        result = compute_lifetime_pd("m1", max_months=24)
        s1_end = result["pd_curves"]["Stage 1"][-1]["cumulative_pd"]
        s3_end = result["pd_curves"]["Stage 3"][-1]["cumulative_pd"]
        assert s3_end > s1_end

    def test_all_stages_start_at_zero(self, _patch_markov_db):
        from domain.markov import compute_lifetime_pd
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["Stage 1", "Stage 2", "Stage 3", "Default"],
                "matrix": [[0.9, 0.05, 0.03, 0.02],
                           [0.02, 0.8, 0.1, 0.08],
                           [0.0, 0.02, 0.7, 0.28],
                           [0.0, 0.0, 0.0, 1.0]],
            }),
        }])
        _patch_markov_db["query_df"].return_value = mat_row
        result = compute_lifetime_pd("m1", max_months=12)
        for stage_name, curve in result["pd_curves"].items():
            assert curve[0]["cumulative_pd"] == 0.0, f"{stage_name} should start at 0"
            assert curve[0]["month"] == 0

    def test_missing_matrix_raises(self, _patch_markov_db):
        from domain.markov import compute_lifetime_pd
        with pytest.raises(ValueError, match="not found"):
            compute_lifetime_pd("bad-id")


# ===========================================================================
# HAZARD — Estimation Pipeline, Retrieval, Analysis
# ===========================================================================


@pytest.fixture
def hazard_portfolio():
    rng = np.random.default_rng(42)
    n = 200
    return pd.DataFrame({
        "loan_id": [f"L{i}" for i in range(n)],
        "product_type": rng.choice(["mortgage", "personal_loan"], n).tolist(),
        "segment": rng.choice(["retail", "sme"], n).tolist(),
        "assessed_stage": rng.choice([1, 1, 1, 2, 3], n).tolist(),
        "days_past_due": rng.integers(0, 120, n).tolist(),
        "current_lifetime_pd": np.round(rng.uniform(0.01, 0.4, n), 4).tolist(),
        "gross_carrying_amount": np.round(rng.uniform(1000, 50000, n), 2).tolist(),
        "remaining_term": rng.integers(6, 60, n).tolist(),
        "vintage_cohort": rng.choice(["2022", "2023"], n).tolist(),
    })


class TestHazardCoxPhEdgeCases:
    def test_zero_events(self, hazard_portfolio):
        from domain.hazard_cox_ph import _estimate_cox_ph
        result = _estimate_cox_ph(hazard_portfolio, 200, 0)
        # Should still produce coefficients (0 events means zero default rate)
        assert "coefficients" in result

    def test_all_events(self, hazard_portfolio):
        from domain.hazard_cox_ph import _estimate_cox_ph
        result = _estimate_cox_ph(hazard_portfolio, 200, 200)
        assert result["concordance_index"] > 0

    def test_survival_probs_all_in_range(self, hazard_portfolio):
        from domain.hazard_cox_ph import _estimate_cox_ph
        result = _estimate_cox_ph(hazard_portfolio, 200, 20)
        for curve in result["curves"]:
            for p in curve["survival_probs"]:
                assert 0 <= p <= 1.0


class TestHazardDiscreteTimeEdgeCases:
    def test_produces_time_coefficient(self, hazard_portfolio):
        from domain.hazard_nonparam import _estimate_discrete_time
        result = _estimate_discrete_time(hazard_portfolio, 200, 20)
        assert "time_coefficient" in result["coefficients"]
        assert isinstance(result["coefficients"]["time_coefficient"], float)

    def test_curves_have_correct_length(self, hazard_portfolio):
        from domain.hazard_nonparam import _estimate_discrete_time
        result = _estimate_discrete_time(hazard_portfolio, 200, 20)
        for curve in result["curves"]:
            assert len(curve["time_points"]) == len(curve["survival_probs"])
            assert len(curve["time_points"]) == len(curve["hazard_rates"])


class TestHazardKaplanMeierEdgeCases:
    def test_survival_starts_near_one(self, hazard_portfolio):
        from domain.hazard_nonparam import _estimate_kaplan_meier
        result = _estimate_kaplan_meier(hazard_portfolio, 200, 20)
        first_surv = result["curves"][0]["survival_probs"][0]
        assert first_surv > 0.9

    def test_hazard_rates_non_negative(self, hazard_portfolio):
        from domain.hazard_nonparam import _estimate_kaplan_meier
        result = _estimate_kaplan_meier(hazard_portfolio, 200, 20)
        for curve in result["curves"]:
            for h in curve["hazard_rates"]:
                assert h >= 0


class TestHazardSurvivalCurveMath:
    """Verify S(t) = exp(-H(t)) where H(t) = cumulative hazard."""

    @patch("domain.hazard_retrieval.query_df")
    def test_survival_formula(self, mock_q):
        from domain.hazard_analysis import compute_survival_curve
        baseline = {str(t): 0.01 for t in range(1, 25)}
        model_row = pd.DataFrame([{
            "model_id": "h1", "model_type": "cox_ph",
            "coefficients": json.dumps({"covariates": []}),
            "baseline_hazard": json.dumps(baseline),
            "concordance_index": 0.7,
        }])
        curves_df = pd.DataFrame()
        mock_q.side_effect = [model_row, curves_df]
        result = compute_survival_curve("h1")
        # Verify S(t) = exp(-sum(h(tau) for tau=1..t))
        cum_h = 0.0
        for i, t in enumerate(result["time_points"]):
            cum_h += result["hazard_rates"][i]
            expected_s = math.exp(-cum_h)
            assert abs(result["survival_probs"][i] - expected_s) < 1e-4


class TestHazardTermStructureMath:
    @patch("domain.hazard_retrieval.query_df")
    def test_marginal_pd_sums_correctly(self, mock_q):
        from domain.hazard_analysis import compute_term_structure_pd
        baseline = {str(t): 0.01 for t in range(1, 25)}
        model_row = pd.DataFrame([{
            "model_id": "h1", "model_type": "cox_ph",
            "coefficients": json.dumps({}),
            "baseline_hazard": json.dumps(baseline),
        }])
        curves_df = pd.DataFrame()
        mock_q.side_effect = [model_row, curves_df]
        result = compute_term_structure_pd("h1", max_months=24)
        # Cumulative PD should be non-decreasing
        for i in range(1, len(result["cumulative_pd"])):
            assert result["cumulative_pd"][i] >= result["cumulative_pd"][i - 1] - 1e-10

    @patch("domain.hazard_retrieval.query_df")
    def test_marginal_pd_non_negative(self, mock_q):
        from domain.hazard_analysis import compute_term_structure_pd
        baseline = {str(t): 0.005 + 0.001 * t for t in range(1, 13)}
        model_row = pd.DataFrame([{
            "model_id": "h1", "model_type": "cox_ph",
            "coefficients": json.dumps({}),
            "baseline_hazard": json.dumps(baseline),
        }])
        curves_df = pd.DataFrame()
        mock_q.side_effect = [model_row, curves_df]
        result = compute_term_structure_pd("h1", max_months=12)
        for mp in result["marginal_pd"]:
            assert mp >= 0


# ===========================================================================
# ADVANCED — Get/List Round-Trip, Collateral Formula
# ===========================================================================


@pytest.fixture
def _patch_advanced_db():
    with patch("domain.advanced.query_df") as mock_q, \
         patch("domain.advanced.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


class TestCureRateGetRoundTrip:
    def test_get_existing_analysis(self, _patch_advanced_db):
        from domain.advanced import get_cure_analysis
        _patch_advanced_db["query_df"].return_value = pd.DataFrame([{
            "analysis_id": "cure-abc",
            "product_type": "all",
            "segment": "all",
            "observation_period": "12 months",
            "methodology": "Transition matrix",
            "created_at": "2025-12-31",
            "cure_rates": json.dumps({
                "cure_by_dpd": [{"dpd_bucket": "1-30 DPD", "cure_rate": 0.72}],
                "overall_cure_rate": 0.35,
            }),
        }])
        result = get_cure_analysis("cure-abc")
        assert result is not None
        assert result["analysis_id"] == "cure-abc"
        assert "cure_by_dpd" in result


class TestCcfGetRoundTrip:
    def test_get_existing_analysis(self, _patch_advanced_db):
        from domain.advanced import get_ccf_analysis
        _patch_advanced_db["query_df"].return_value = pd.DataFrame([{
            "analysis_id": "ccf-abc",
            "product_type": "all",
            "methodology": "CCF formula",
            "created_at": "2025-12-31",
            "ccf_by_stage": json.dumps([{"product_type": "mortgage", "ccf": 0.95}]),
            "ccf_by_utilization": json.dumps([{"band": "0-20%", "ccf": 0.85}]),
        }])
        result = get_ccf_analysis("ccf-abc")
        assert result is not None
        assert len(result["ccf_by_stage"]) == 1


class TestCollateralFormula:
    def test_lgd_secured_formula(self, _patch_advanced_db):
        """Verify LGD_secured = (1 - recovery) * (1 - haircut) + haircut."""
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_advanced_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        for item in result["haircut_results"]:
            if item["lgd_secured"] is not None:
                haircut = item["haircut_pct"]
                recovery = item["recovery_rate"]
                expected_lgd = (1 - recovery) * (1 - haircut) + haircut
                assert abs(item["lgd_secured"] - round(expected_lgd, 4)) < 0.001

    def test_forced_sale_discount_bounded(self, _patch_advanced_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 500_000_000}])
        _patch_advanced_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        for item in result["haircut_results"]:
            assert item["forced_sale_discount"] <= 1.0

    def test_time_to_recovery_positive(self, _patch_advanced_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 500_000_000}])
        _patch_advanced_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        for item in result["haircut_results"]:
            assert item["time_to_recovery_months"] >= 0.5


class TestCcfProductFilter:
    def test_filter_passed_to_query(self, _patch_advanced_db):
        from domain.advanced import compute_ccf
        portfolio = pd.DataFrame({
            "product_type": ["mortgage"],
            "assessed_stage": [1],
            "cnt": [5000],
            "total_gca": [250e6],
            "avg_gca": [50000.0],
        })
        _patch_advanced_db["query_df"].return_value = portfolio
        result = compute_ccf("mortgage")
        assert result["product_type"] == "mortgage"


class TestListCollateralAnalyses:
    def test_returns_formatted_records(self, _patch_advanced_db):
        from domain.advanced import list_collateral_analyses
        _patch_advanced_db["query_df"].return_value = pd.DataFrame([{
            "analysis_id": "col-1", "collateral_type": "vehicle",
            "haircut_pct": 0.35, "recovery_rate": 0.52,
            "time_to_recovery_months": 6.0, "methodology": "test",
            "created_at": datetime(2025, 12, 31),
        }])
        result = list_collateral_analyses()
        assert len(result) == 1
        assert isinstance(result[0]["created_at"], str)


# ===========================================================================
# PERIOD CLOSE — Pipeline Flow, Step Failure, Health
# ===========================================================================


class TestPeriodClosePipeline:
    @patch("domain.period_close.execute")
    def test_start_pipeline_returns_all_pending_steps(self, mock_exec):
        from domain.period_close import start_pipeline
        result = start_pipeline("proj-001", "admin")
        assert result["status"] == "running"
        assert len(result["steps"]) == 6
        assert all(s["status"] == "pending" for s in result["steps"])
        assert result["run_id"].startswith("PIPE-proj-001-")

    @patch("domain.period_close.execute")
    def test_start_pipeline_default_trigger(self, mock_exec):
        from domain.period_close import start_pipeline
        result = start_pipeline("proj-002")
        assert result["triggered_by"] == "system"


class TestPeriodCloseStepExecution:
    @patch("domain.period_close.execute")
    @patch("domain.period_close.query_df")
    def test_data_freshness_success(self, mock_q, mock_exec):
        from domain.period_close import execute_step
        steps_json = json.dumps([
            {"key": "data_freshness", "status": "pending",
             "started_at": None, "completed_at": None,
             "duration_seconds": None, "error": None}
        ])
        run_df = pd.DataFrame([{"steps": steps_json}])
        fresh_df = pd.DataFrame([{"last_updated": "2025-12-31", "record_count": 5000}])

        def side_effect(query, *args, **kwargs):
            if "pipeline_runs" in str(query):
                return run_df
            return fresh_df

        mock_q.side_effect = side_effect
        result = execute_step("PIPE-001", "data_freshness")
        assert result["status"] == "completed"
        assert result["duration_seconds"] >= 0

    @patch("domain.period_close.execute")
    @patch("domain.period_close.query_df")
    def test_data_quality_all_pass(self, mock_q, mock_exec):
        from domain.period_close import execute_step
        steps_json = json.dumps([
            {"key": "data_quality", "status": "pending",
             "started_at": None, "completed_at": None,
             "duration_seconds": None, "error": None}
        ])
        run_df = pd.DataFrame([{"steps": steps_json}])
        quality_df = pd.DataFrame([{
            "total": 5000, "neg_gca": 0, "invalid_pd": 0, "invalid_stage": 0,
        }])

        def side_effect(query, *args, **kwargs):
            if "pipeline_runs" in str(query):
                return run_df
            return quality_df

        mock_q.side_effect = side_effect
        result = execute_step("PIPE-001", "data_quality")
        assert result["status"] == "completed"

    @patch("domain.period_close.execute")
    @patch("domain.period_close.query_df")
    def test_data_quality_failure(self, mock_q, mock_exec):
        from domain.period_close import execute_step
        steps_json = json.dumps([
            {"key": "data_quality", "status": "pending",
             "started_at": None, "completed_at": None,
             "duration_seconds": None, "error": None}
        ])
        run_df = pd.DataFrame([{"steps": steps_json}])
        quality_df = pd.DataFrame([{
            "total": 5000, "neg_gca": 10, "invalid_pd": 5, "invalid_stage": 0,
        }])

        def side_effect(query, *args, **kwargs):
            if "pipeline_runs" in str(query):
                return run_df
            return quality_df

        mock_q.side_effect = side_effect
        result = execute_step("PIPE-001", "data_quality")
        assert result["status"] == "failed"
        assert "error" in result

    @patch("domain.period_close.execute")
    @patch("domain.period_close.query_df")
    def test_model_execution_success(self, mock_q, mock_exec):
        from domain.period_close import execute_step
        steps_json = json.dumps([
            {"key": "model_execution", "status": "pending",
             "started_at": None, "completed_at": None,
             "duration_seconds": None, "error": None}
        ])
        run_df = pd.DataFrame([{"steps": steps_json}])
        model_df = pd.DataFrame([{"cnt": 10000}])

        def side_effect(query, *args, **kwargs):
            if "pipeline_runs" in str(query):
                return run_df
            return model_df

        mock_q.side_effect = side_effect
        result = execute_step("PIPE-001", "model_execution")
        assert result["status"] == "completed"

    @patch("domain.period_close.execute")
    @patch("domain.period_close.query_df")
    def test_ecl_calculation_success(self, mock_q, mock_exec):
        from domain.period_close import execute_step
        steps_json = json.dumps([
            {"key": "ecl_calculation", "status": "pending",
             "started_at": None, "completed_at": None,
             "duration_seconds": None, "error": None}
        ])
        run_df = pd.DataFrame([{"steps": steps_json}])
        ecl_df = pd.DataFrame([{"cnt": 10000, "total_ecl": 5000000.0}])

        def side_effect(query, *args, **kwargs):
            if "pipeline_runs" in str(query):
                return run_df
            return ecl_df

        mock_q.side_effect = side_effect
        result = execute_step("PIPE-001", "ecl_calculation")
        assert result["status"] == "completed"

    def test_report_generation_step(self):
        from domain.period_close import _run_step_logic
        result = _run_step_logic("report_generation")
        assert "message" in result

    def test_attribution_step(self):
        from domain.period_close import _run_step_logic
        result = _run_step_logic("attribution")
        assert "message" in result


class TestPeriodCloseComplete:
    @patch("domain.period_close.execute")
    def test_complete_pipeline(self, mock_exec):
        from domain.period_close import complete_pipeline
        complete_pipeline("PIPE-001", "completed")
        assert mock_exec.called
        sql = mock_exec.call_args[0][0]
        assert "completed" in str(mock_exec.call_args[0][1])

    @patch("domain.period_close.execute")
    def test_complete_with_error(self, mock_exec):
        from domain.period_close import complete_pipeline
        complete_pipeline("PIPE-001", "failed", "Step 2 failed")
        params = mock_exec.call_args[0][1]
        assert "failed" in params
        assert "Step 2 failed" in params


class TestPeriodCloseGetRun:
    @patch("domain.period_close.query_df")
    def test_not_found(self, mock_q):
        from domain.period_close import get_pipeline_run
        mock_q.return_value = pd.DataFrame()
        assert get_pipeline_run("PIPE-nonexistent") is None

    @patch("domain.period_close.query_df")
    def test_found_with_parsed_steps(self, mock_q):
        from domain.period_close import get_pipeline_run
        steps = [{"key": "data_freshness", "status": "completed"}]
        mock_q.return_value = pd.DataFrame([{
            "run_id": "PIPE-001", "project_id": "proj-001",
            "status": "completed", "started_at": "2025-12-31",
            "completed_at": "2025-12-31", "duration_seconds": 60.0,
            "steps": json.dumps(steps), "error_message": None,
            "triggered_by": "admin",
        }])
        result = get_pipeline_run("PIPE-001")
        assert result is not None
        assert isinstance(result["steps"], list)


class TestPeriodCloseHealth:
    @patch("domain.period_close.query_df")
    def test_no_runs(self, mock_q):
        from domain.period_close import get_pipeline_health
        mock_q.return_value = pd.DataFrame()
        result = get_pipeline_health("proj-new")
        assert result["total_runs"] == 0
        assert result["status"] == "no_runs"

    @patch("domain.period_close.query_df")
    def test_with_recent_run(self, mock_q):
        from domain.period_close import get_pipeline_health
        mock_q.return_value = pd.DataFrame([{
            "run_id": "PIPE-001", "status": "completed",
            "started_at": "2025-12-31", "completed_at": "2025-12-31",
            "duration_seconds": 120.0,
            "steps": json.dumps([{"key": "data_freshness", "status": "completed"}]),
        }])
        result = get_pipeline_health("proj-001")
        assert result["total_runs"] >= 1
        assert result["last_status"] == "completed"
        assert result["last_duration"] == 120.0


# ===========================================================================
# HEALTH CHECKS — All 5 checks + aggregation
# ===========================================================================


class TestCheckLakebaseConnection:
    @patch("domain.health.query_df")
    def test_success(self, mock_q):
        from domain.health import check_lakebase_connection
        mock_q.return_value = pd.DataFrame([{"ok": 1}])
        result = check_lakebase_connection()
        assert result["healthy"] is True
        assert result["status"] == "connected"

    @patch("domain.health.query_df")
    def test_failure(self, mock_q):
        from domain.health import check_lakebase_connection
        mock_q.side_effect = Exception("Connection refused")
        result = check_lakebase_connection()
        assert result["healthy"] is False
        assert "error" in result


class TestCheckRequiredTables:
    @patch("domain.health.query_df")
    def test_all_present(self, mock_q):
        from domain.health import check_required_tables
        mock_q.return_value = pd.DataFrame([{"cnt": 100}])
        result = check_required_tables()
        assert result["all_present"] is True
        assert len(result["missing"]) == 0

    @patch("domain.health.query_df")
    def test_missing_table(self, mock_q):
        from domain.health import check_required_tables
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 3:  # Third table fails
                raise Exception("table not found")
            return pd.DataFrame([{"cnt": 50}])
        mock_q.side_effect = side_effect
        result = check_required_tables()
        assert result["all_present"] is False
        assert len(result["missing"]) == 1


class TestCheckConfigLoaded:
    @patch("domain.health.admin_config", create=True)
    def test_success(self, mock_config):
        # Reload to pick up patched admin_config
        from domain.health import check_config_loaded
        with patch("builtins.__import__", side_effect=lambda name, *a, **k: mock_config if name == "admin_config" else __import__(name, *a, **k)):
            pass
        # Direct test: mock admin_config.get_config
        import domain.health as health_mod
        with patch.object(health_mod, "admin_config", create=True) as mc:
            mc = MagicMock()
            mc.get_config.return_value = {"model": {}, "scenarios": {}, "display": {}}
            with patch.dict("sys.modules", {"admin_config": mc}):
                result = check_config_loaded()
                assert result["loaded"] is True

    def test_import_failure(self):
        from domain.health import check_config_loaded
        with patch.dict("sys.modules", {"admin_config": None}):
            with patch("builtins.__import__", side_effect=ImportError("not found")):
                result = check_config_loaded()
                assert result["loaded"] is False


class TestCheckScipyAvailable:
    def test_scipy_available(self):
        from domain.health import check_scipy_available
        result = check_scipy_available()
        assert result["available"] is True
        assert "version" in result


class TestRunHealthCheck:
    @patch("domain.health.check_scipy_available")
    @patch("domain.health.check_config_loaded")
    @patch("domain.health.check_required_tables")
    @patch("domain.health.check_lakebase_connection")
    def test_all_healthy(self, mock_lb, mock_tables, mock_config, mock_scipy):
        from domain.health import run_health_check
        mock_lb.return_value = {"healthy": True, "status": "connected"}
        mock_tables.return_value = {"all_present": True, "missing": [], "tables": {}}
        mock_config.return_value = {"loaded": True, "sections": ["a"], "section_count": 1}
        mock_scipy.return_value = {"available": True, "version": "1.11"}
        result = run_health_check()
        assert result["status"] == "healthy"

    @patch("domain.health.check_scipy_available")
    @patch("domain.health.check_config_loaded")
    @patch("domain.health.check_required_tables")
    @patch("domain.health.check_lakebase_connection")
    def test_degraded_when_db_down(self, mock_lb, mock_tables, mock_config, mock_scipy):
        from domain.health import run_health_check
        mock_lb.return_value = {"healthy": False, "status": "error", "error": "timeout"}
        mock_tables.return_value = {"all_present": True, "missing": [], "tables": {}}
        mock_config.return_value = {"loaded": True, "sections": ["a"], "section_count": 1}
        mock_scipy.return_value = {"available": True, "version": "1.11"}
        result = run_health_check()
        assert result["status"] == "degraded"

    @patch("domain.health.check_scipy_available")
    @patch("domain.health.check_config_loaded")
    @patch("domain.health.check_required_tables")
    @patch("domain.health.check_lakebase_connection")
    def test_degraded_when_tables_missing(self, mock_lb, mock_tables, mock_config, mock_scipy):
        from domain.health import run_health_check
        mock_lb.return_value = {"healthy": True, "status": "connected"}
        mock_tables.return_value = {"all_present": False, "missing": ["ecl_workflow"], "tables": {}}
        mock_config.return_value = {"loaded": True, "sections": ["a"], "section_count": 1}
        mock_scipy.return_value = {"available": True, "version": "1.11"}
        result = run_health_check()
        assert result["status"] == "degraded"

    @patch("domain.health.check_scipy_available")
    @patch("domain.health.check_config_loaded")
    @patch("domain.health.check_required_tables")
    @patch("domain.health.check_lakebase_connection")
    def test_degraded_when_scipy_missing(self, mock_lb, mock_tables, mock_config, mock_scipy):
        from domain.health import run_health_check
        mock_lb.return_value = {"healthy": True, "status": "connected"}
        mock_tables.return_value = {"all_present": True, "missing": [], "tables": {}}
        mock_config.return_value = {"loaded": True, "sections": ["a"], "section_count": 1}
        mock_scipy.return_value = {"available": False, "error": "not installed"}
        result = run_health_check()
        assert result["status"] == "degraded"

    @patch("domain.health.check_scipy_available")
    @patch("domain.health.check_config_loaded")
    @patch("domain.health.check_required_tables")
    @patch("domain.health.check_lakebase_connection")
    def test_degraded_when_config_not_loaded(self, mock_lb, mock_tables, mock_config, mock_scipy):
        from domain.health import run_health_check
        mock_lb.return_value = {"healthy": True, "status": "connected"}
        mock_tables.return_value = {"all_present": True, "missing": [], "tables": {}}
        mock_config.return_value = {"loaded": False, "error": "import failed"}
        mock_scipy.return_value = {"available": True, "version": "1.11"}
        result = run_health_check()
        assert result["status"] == "degraded"


# ===========================================================================
# METRIC THRESHOLDS — Completeness
# ===========================================================================


class TestMetricThresholdsCompleteness:
    def test_all_lgd_metrics_have_thresholds(self):
        from domain.backtesting_traffic import METRIC_THRESHOLDS
        for metric in ["MAE", "RMSE", "Mean_Bias"]:
            assert metric in METRIC_THRESHOLDS, f"Missing threshold for {metric}"

    def test_all_thresholds_have_required_fields(self):
        from domain.backtesting_traffic import METRIC_THRESHOLDS
        for name, t in METRIC_THRESHOLDS.items():
            assert "green" in t, f"{name} missing green threshold"
            assert "amber" in t, f"{name} missing amber threshold"
            assert "direction" in t, f"{name} missing direction"

    def test_higher_better_green_above_amber(self):
        from domain.backtesting_traffic import METRIC_THRESHOLDS
        for name, t in METRIC_THRESHOLDS.items():
            if t["direction"] == "higher_better":
                assert t["green"] >= t["amber"], f"{name}: green should be >= amber"

    def test_lower_better_green_below_amber(self):
        from domain.backtesting_traffic import METRIC_THRESHOLDS
        for name, t in METRIC_THRESHOLDS.items():
            if t["direction"] == "lower_better":
                assert t["green"] <= t["amber"], f"{name}: green should be <= amber"
