"""Extended tests for domain/backtesting_traffic.py — boundary and edge cases."""
import pytest

from domain.backtesting_traffic import (
    METRIC_THRESHOLDS,
    _overall_traffic_light,
    _traffic_light,
)


class TestTrafficLightBoundaries:
    """Test exact boundary values for each metric."""

    def test_auc_below_green_threshold(self):
        assert _traffic_light("AUC", 0.699) == "Amber"

    def test_gini_below_green_threshold(self):
        assert _traffic_light("Gini", 0.399) == "Amber"

    def test_ks_below_green_threshold(self):
        assert _traffic_light("KS", 0.299) == "Amber"

    def test_psi_above_green_threshold(self):
        assert _traffic_light("PSI", 0.101) == "Amber"

    def test_brier_above_green_threshold(self):
        assert _traffic_light("Brier", 0.151) == "Amber"

    def test_mae_above_green_threshold(self):
        assert _traffic_light("MAE", 0.101) == "Amber"

    def test_rmse_above_green_threshold(self):
        assert _traffic_light("RMSE", 0.151) == "Amber"


class TestTrafficLightNone:
    def test_none_metric_name(self):
        result = _traffic_light("NonexistentXYZ", 0.5)
        assert result == "Green"


class TestOverallTrafficLightExtended:
    def test_many_greens_one_red(self):
        lights = ["Green"] * 10 + ["Red"]
        assert _overall_traffic_light(lights) == "Red"

    def test_many_greens_one_amber(self):
        lights = ["Green"] * 10 + ["Amber"]
        assert _overall_traffic_light(lights) == "Amber"

    def test_alternating_green_amber(self):
        lights = ["Green", "Amber"] * 5
        assert _overall_traffic_light(lights) == "Amber"

    def test_single_amber(self):
        assert _overall_traffic_light(["Amber"]) == "Amber"

    def test_three_reds(self):
        assert _overall_traffic_light(["Red", "Red", "Red"]) == "Red"

    def test_amber_and_red(self):
        assert _overall_traffic_light(["Amber", "Red"]) == "Red"

    def test_large_all_green(self):
        assert _overall_traffic_light(["Green"] * 100) == "Green"


class TestMetricThresholdsCompleteness:
    def test_auc_in_thresholds(self):
        assert "AUC" in METRIC_THRESHOLDS

    def test_gini_in_thresholds(self):
        assert "Gini" in METRIC_THRESHOLDS

    def test_ks_in_thresholds(self):
        assert "KS" in METRIC_THRESHOLDS

    def test_psi_in_thresholds(self):
        assert "PSI" in METRIC_THRESHOLDS

    def test_brier_in_thresholds(self):
        assert "Brier" in METRIC_THRESHOLDS

    def test_hosmer_lemeshow_in_thresholds(self):
        assert "Hosmer_Lemeshow_pvalue" in METRIC_THRESHOLDS

    def test_binomial_in_thresholds(self):
        assert "Binomial_pass_rate" in METRIC_THRESHOLDS

    def test_mae_in_thresholds(self):
        assert "MAE" in METRIC_THRESHOLDS

    def test_rmse_in_thresholds(self):
        assert "RMSE" in METRIC_THRESHOLDS

    def test_mean_bias_in_thresholds(self):
        assert "Mean_Bias" in METRIC_THRESHOLDS

    def test_green_is_numeric(self):
        for name, t in METRIC_THRESHOLDS.items():
            assert isinstance(t["green"], (int, float)), f"{name} green is not numeric"

    def test_amber_is_numeric(self):
        for name, t in METRIC_THRESHOLDS.items():
            assert isinstance(t["amber"], (int, float)), f"{name} amber is not numeric"
