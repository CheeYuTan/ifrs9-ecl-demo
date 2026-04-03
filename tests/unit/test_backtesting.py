"""
Unit tests for the backtesting engine — calibration tests and LGD backtesting.

Tests use known-answer cases to verify mathematical correctness of:
  - Binomial test (EBA/GL/2017/16 §71)
  - Jeffreys test (EBA/GL/2017/16 §72)
  - Hosmer-Lemeshow test (EBA/GL/2017/16 §74)
  - Spiegelhalter test
  - AUC/Gini/KS discrimination metrics
  - PSI and Brier score
  - LGD backtesting with insufficient data handling
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import pandas as pd

import backend
from domain.backtesting import (
    _compute_auc_gini_ks,
    _compute_psi,
    _compute_brier,
    _binomial_test,
    _jeffreys_test,
    _hosmer_lemeshow_test,
    _spiegelhalter_test,
    _traffic_light,
    _overall_traffic_light,
    _compute_lgd_backtest,
    METRIC_THRESHOLDS,
)


class TestDiscriminationMetrics:
    """Known-answer tests for AUC, Gini, KS."""

    def test_perfect_discrimination(self):
        predicted = [0.9, 0.8, 0.7, 0.1, 0.05, 0.01]
        actual = [1, 1, 1, 0, 0, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["auc"] == 1.0
        assert result["gini"] == 1.0

    def test_random_discrimination(self):
        np.random.seed(42)
        predicted = np.random.uniform(0, 1, 1000).tolist()
        actual = np.random.binomial(1, 0.1, 1000).tolist()
        result = _compute_auc_gini_ks(predicted, actual)
        assert 0.3 < result["auc"] < 0.7

    def test_no_positives(self):
        predicted = [0.5, 0.3, 0.1]
        actual = [0, 0, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["auc"] == 0.5
        assert result["gini"] == 0.0

    def test_empty_input(self):
        result = _compute_auc_gini_ks([], [])
        assert result["auc"] == 0.5

    def test_ks_bounded(self):
        predicted = [0.9, 0.8, 0.2, 0.1]
        actual = [1, 1, 0, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert 0 <= result["ks"] <= 1


class TestPSI:
    def test_identical_distributions(self):
        data = [0.1, 0.2, 0.3, 0.4, 0.5] * 20
        psi = _compute_psi(data, data)
        assert psi < 0.01

    def test_shifted_distribution(self):
        expected = [0.1, 0.2, 0.3] * 30
        actual = [0.5, 0.6, 0.7] * 30
        psi = _compute_psi(expected, actual)
        assert psi > 0.1

    def test_empty_input(self):
        assert _compute_psi([], []) == 0.0


class TestBrier:
    def test_perfect_predictions(self):
        predicted = [1.0, 0.0, 1.0, 0.0]
        actual = [1, 0, 1, 0]
        assert _compute_brier(predicted, actual) == 0.0

    def test_worst_predictions(self):
        predicted = [0.0, 1.0]
        actual = [1, 0]
        assert _compute_brier(predicted, actual) == 1.0

    def test_empty(self):
        assert _compute_brier([], []) == 0.0


class TestBinomialTest:
    """Known-answer tests for per-grade binomial test (EBA §71)."""

    def test_well_calibrated(self):
        result = _binomial_test(predicted_pd=0.05, n_obligors=1000, n_defaults=50)
        assert result["pass"] == True
        assert result["p_value"] > 0.05

    def test_underprediction_fails(self):
        result = _binomial_test(predicted_pd=0.01, n_obligors=1000, n_defaults=50)
        assert result["pass"] == False
        assert result["p_value"] < 0.01

    def test_zero_obligors(self):
        result = _binomial_test(predicted_pd=0.05, n_obligors=0, n_defaults=0)
        assert result["pass"] == True

    def test_zero_defaults_passes(self):
        result = _binomial_test(predicted_pd=0.05, n_obligors=100, n_defaults=0)
        assert result["pass"] == True

    def test_output_fields(self):
        result = _binomial_test(predicted_pd=0.05, n_obligors=200, n_defaults=10)
        assert "predicted_pd" in result
        assert "n_obligors" in result
        assert "n_defaults" in result
        assert "observed_dr" in result
        assert "expected_defaults" in result
        assert "ci_upper_95" in result
        assert "p_value" in result
        assert "pass" in result


class TestJeffreysTest:
    """Known-answer tests for Bayesian Jeffreys test (EBA §72)."""

    def test_well_calibrated(self):
        result = _jeffreys_test(predicted_pd=0.05, n_obligors=1000, n_defaults=50)
        assert result["pass"] == True

    def test_low_default_portfolio(self):
        result = _jeffreys_test(predicted_pd=0.02, n_obligors=500, n_defaults=5)
        assert "posterior_mean" in result
        assert "ci_lower_95" in result
        assert "ci_upper_95" in result
        assert result["ci_lower_95"] < result["ci_upper_95"]

    def test_zero_obligors(self):
        result = _jeffreys_test(predicted_pd=0.05, n_obligors=0, n_defaults=0)
        assert result["pass"] is True

    def test_posterior_mean_reasonable(self):
        result = _jeffreys_test(predicted_pd=0.10, n_obligors=100, n_defaults=10)
        assert 0.05 < result["posterior_mean"] < 0.15


class TestHosmerLemeshow:
    """Known-answer tests for Hosmer-Lemeshow goodness-of-fit (EBA §74)."""

    def test_well_calibrated_model(self):
        np.random.seed(42)
        n = 1000
        true_pd = np.random.uniform(0.01, 0.20, n)
        defaults = np.random.binomial(1, true_pd)
        result = _hosmer_lemeshow_test(true_pd.tolist(), defaults.tolist())
        assert result["p_value"] > 0.01
        assert len(result["groups"]) == 10

    def test_poorly_calibrated_model(self):
        n = 1000
        predicted = [0.01] * n
        actual = [1] * 200 + [0] * 800
        result = _hosmer_lemeshow_test(predicted, actual)
        assert result["p_value"] < 0.05
        assert result["traffic_light"] in ("Amber", "Red")

    def test_insufficient_data(self):
        result = _hosmer_lemeshow_test([0.1] * 10, [0] * 10)
        assert result["pass"] is True
        assert "Insufficient" in result.get("detail", "")

    def test_output_structure(self):
        np.random.seed(123)
        predicted = np.random.uniform(0, 0.3, 200).tolist()
        actual = np.random.binomial(1, 0.1, 200).tolist()
        result = _hosmer_lemeshow_test(predicted, actual)
        assert "chi_squared" in result
        assert "p_value" in result
        assert "df" in result
        assert "groups" in result
        for g in result["groups"]:
            assert "avg_predicted_pd" in g
            assert "observed_dr" in g


class TestSpiegelhalter:
    def test_well_calibrated(self):
        np.random.seed(42)
        n = 500
        p = np.random.uniform(0.01, 0.20, n)
        y = np.random.binomial(1, p)
        result = _spiegelhalter_test(p.tolist(), y.tolist())
        assert result["pass"] == True

    def test_empty_input(self):
        result = _spiegelhalter_test([], [])
        assert result["pass"] is True

    def test_output_fields(self):
        result = _spiegelhalter_test([0.1, 0.2, 0.3], [0, 1, 0])
        assert "z_statistic" in result
        assert "p_value" in result
        assert "traffic_light" in result


class TestTrafficLight:
    def test_auc_green(self):
        assert _traffic_light("AUC", 0.85) == "Green"

    def test_auc_amber(self):
        assert _traffic_light("AUC", 0.65) == "Amber"

    def test_auc_red(self):
        assert _traffic_light("AUC", 0.50) == "Red"

    def test_psi_green(self):
        assert _traffic_light("PSI", 0.05) == "Green"

    def test_psi_red(self):
        assert _traffic_light("PSI", 0.30) == "Red"

    def test_hl_pvalue_green(self):
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.10) == "Green"

    def test_hl_pvalue_red(self):
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.005) == "Red"

    def test_unknown_metric(self):
        assert _traffic_light("UnknownMetric", 0.5) == "Green"


class TestOverallTrafficLight:
    def test_all_green(self):
        assert _overall_traffic_light(["Green", "Green", "Green"]) == "Green"

    def test_one_amber(self):
        assert _overall_traffic_light(["Green", "Amber", "Green"]) == "Amber"

    def test_one_red(self):
        assert _overall_traffic_light(["Green", "Red", "Green"]) == "Red"

    def test_red_overrides_amber(self):
        assert _overall_traffic_light(["Amber", "Red", "Green"]) == "Red"


class TestLGDBacktest:
    """Tests for LGD backtesting with insufficient data handling."""

    @patch("domain.backtesting.query_df")
    def test_insufficient_data_returns_status(self, mock_query):
        mock_query.return_value = pd.DataFrame()
        result = _compute_lgd_backtest(pd.DataFrame())
        assert result["status"] == "insufficient_data"
        assert result["minimum_required"] == 20
        assert result["available"] == 0

    @patch("domain.backtesting.query_df")
    def test_sufficient_data_returns_metrics(self, mock_query):
        defaults_df = pd.DataFrame({
            "loan_id": [f"L{i}" for i in range(30)],
            "product_type": ["credit_card"] * 30,
            "gca_at_default": [10000.0] * 30,
            "total_recovery_amount": [4000.0] * 30,
            "realised_lgd": [0.60] * 30,
        })
        mock_query.return_value = defaults_df
        result = _compute_lgd_backtest(pd.DataFrame())
        assert result["status"] == "complete"
        assert result["n_defaults"] == 30
        assert "MAE" in result["metrics"]
        assert "RMSE" in result["metrics"]
        assert "Mean_Bias" in result["metrics"]

    @patch("domain.backtesting.query_df")
    def test_product_level_results(self, mock_query):
        defaults_df = pd.DataFrame({
            "loan_id": [f"L{i}" for i in range(40)],
            "product_type": ["credit_card"] * 20 + ["auto_loan"] * 20,
            "gca_at_default": [10000.0] * 40,
            "total_recovery_amount": [4000.0] * 20 + [6500.0] * 20,
            "realised_lgd": [0.60] * 20 + [0.35] * 20,
        })
        mock_query.return_value = defaults_df
        result = _compute_lgd_backtest(pd.DataFrame())
        assert result["status"] == "complete"
        assert len(result["product_results"]) == 2
        for pr in result["product_results"]:
            assert "predicted_lgd" in pr
            assert "mean_realised_lgd" in pr
            assert "bias" in pr


class TestMetricThresholds:
    """Verify calibration thresholds are defined for new metrics."""

    def test_hl_threshold_exists(self):
        assert "Hosmer_Lemeshow_pvalue" in METRIC_THRESHOLDS

    def test_binomial_threshold_exists(self):
        assert "Binomial_pass_rate" in METRIC_THRESHOLDS

    def test_all_thresholds_have_direction(self):
        for name, t in METRIC_THRESHOLDS.items():
            assert "direction" in t, f"{name} missing direction"
            assert t["direction"] in ("higher_better", "lower_better")
