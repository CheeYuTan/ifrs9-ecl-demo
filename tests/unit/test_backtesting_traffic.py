"""Dedicated tests for domain/backtesting_traffic.py — traffic light classification."""
import pytest

from domain.backtesting_traffic import (
    METRIC_THRESHOLDS,
    _overall_traffic_light,
    _traffic_light,
)


class TestMetricThresholds:
    def test_all_metrics_have_required_keys(self):
        for name, t in METRIC_THRESHOLDS.items():
            assert "green" in t, f"{name} missing 'green'"
            assert "amber" in t, f"{name} missing 'amber'"
            assert "direction" in t, f"{name} missing 'direction'"

    def test_valid_directions(self):
        for name, t in METRIC_THRESHOLDS.items():
            assert t["direction"] in ("higher_better", "lower_better"), f"{name} has invalid direction"

    def test_threshold_ordering_higher_better(self):
        for name, t in METRIC_THRESHOLDS.items():
            if t["direction"] == "higher_better":
                assert t["green"] >= t["amber"], f"{name}: green ({t['green']}) < amber ({t['amber']})"

    def test_threshold_ordering_lower_better(self):
        for name, t in METRIC_THRESHOLDS.items():
            if t["direction"] == "lower_better":
                assert t["green"] <= t["amber"], f"{name}: green ({t['green']}) > amber ({t['amber']})"

    def test_expected_metrics_present(self):
        expected = ["AUC", "Gini", "KS", "PSI", "Brier", "Hosmer_Lemeshow_pvalue",
                     "Binomial_pass_rate", "MAE", "RMSE", "Mean_Bias"]
        for m in expected:
            assert m in METRIC_THRESHOLDS


class TestTrafficLight:
    def test_auc_green(self):
        assert _traffic_light("AUC", 0.85) == "Green"

    def test_auc_amber(self):
        assert _traffic_light("AUC", 0.65) == "Amber"

    def test_auc_red(self):
        assert _traffic_light("AUC", 0.50) == "Red"

    def test_auc_exactly_green(self):
        assert _traffic_light("AUC", 0.70) == "Green"

    def test_auc_exactly_amber(self):
        assert _traffic_light("AUC", 0.60) == "Amber"

    def test_gini_green(self):
        assert _traffic_light("Gini", 0.50) == "Green"

    def test_gini_amber(self):
        assert _traffic_light("Gini", 0.30) == "Amber"

    def test_gini_red(self):
        assert _traffic_light("Gini", 0.10) == "Red"

    def test_ks_green(self):
        assert _traffic_light("KS", 0.40) == "Green"

    def test_ks_amber(self):
        assert _traffic_light("KS", 0.20) == "Amber"

    def test_ks_red(self):
        assert _traffic_light("KS", 0.10) == "Red"

    def test_psi_green(self):
        assert _traffic_light("PSI", 0.05) == "Green"

    def test_psi_amber(self):
        assert _traffic_light("PSI", 0.15) == "Amber"

    def test_psi_red(self):
        assert _traffic_light("PSI", 0.30) == "Red"

    def test_brier_green(self):
        assert _traffic_light("Brier", 0.10) == "Green"

    def test_brier_amber(self):
        assert _traffic_light("Brier", 0.20) == "Amber"

    def test_brier_red(self):
        assert _traffic_light("Brier", 0.30) == "Red"

    def test_hosmer_lemeshow_green(self):
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.10) == "Green"

    def test_hosmer_lemeshow_amber(self):
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.03) == "Amber"

    def test_hosmer_lemeshow_red(self):
        assert _traffic_light("Hosmer_Lemeshow_pvalue", 0.005) == "Red"

    def test_binomial_pass_rate_green(self):
        assert _traffic_light("Binomial_pass_rate", 0.90) == "Green"

    def test_binomial_pass_rate_amber(self):
        assert _traffic_light("Binomial_pass_rate", 0.70) == "Amber"

    def test_binomial_pass_rate_red(self):
        assert _traffic_light("Binomial_pass_rate", 0.50) == "Red"

    def test_mae_green(self):
        assert _traffic_light("MAE", 0.05) == "Green"

    def test_mae_amber(self):
        assert _traffic_light("MAE", 0.15) == "Amber"

    def test_mae_red(self):
        assert _traffic_light("MAE", 0.25) == "Red"

    def test_rmse_green(self):
        assert _traffic_light("RMSE", 0.10) == "Green"

    def test_rmse_amber(self):
        assert _traffic_light("RMSE", 0.20) == "Amber"

    def test_rmse_red(self):
        assert _traffic_light("RMSE", 0.30) == "Red"

    def test_mean_bias_green(self):
        assert _traffic_light("Mean_Bias", 0.03) == "Green"

    def test_mean_bias_amber(self):
        assert _traffic_light("Mean_Bias", 0.07) == "Amber"

    def test_mean_bias_red(self):
        assert _traffic_light("Mean_Bias", 0.15) == "Red"

    def test_unknown_metric_returns_green(self):
        assert _traffic_light("Unknown_Metric", 0.0) == "Green"

    def test_zero_value_higher_better(self):
        assert _traffic_light("AUC", 0.0) == "Red"

    def test_zero_value_lower_better(self):
        assert _traffic_light("PSI", 0.0) == "Green"

    def test_negative_value(self):
        assert _traffic_light("Mean_Bias", -0.01) == "Green"

    def test_very_large_value_higher_better(self):
        assert _traffic_light("AUC", 1.0) == "Green"

    def test_very_large_value_lower_better(self):
        assert _traffic_light("PSI", 10.0) == "Red"


class TestOverallTrafficLight:
    def test_all_green(self):
        assert _overall_traffic_light(["Green", "Green", "Green"]) == "Green"

    def test_one_amber(self):
        assert _overall_traffic_light(["Green", "Amber", "Green"]) == "Amber"

    def test_one_red(self):
        assert _overall_traffic_light(["Green", "Red", "Green"]) == "Red"

    def test_mixed_amber_red(self):
        assert _overall_traffic_light(["Amber", "Red", "Green"]) == "Red"

    def test_all_amber(self):
        assert _overall_traffic_light(["Amber", "Amber"]) == "Amber"

    def test_all_red(self):
        assert _overall_traffic_light(["Red", "Red"]) == "Red"

    def test_empty_list(self):
        assert _overall_traffic_light([]) == "Green"

    def test_single_green(self):
        assert _overall_traffic_light(["Green"]) == "Green"

    def test_single_red(self):
        assert _overall_traffic_light(["Red"]) == "Red"

    def test_red_takes_precedence(self):
        assert _overall_traffic_light(["Green", "Amber", "Red"]) == "Red"
