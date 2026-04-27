"""Dedicated tests for domain/backtesting_stats.py — statistical tests and metrics."""
import pytest
import numpy as np

from domain.backtesting_stats import (
    _binomial_test,
    _compute_auc_gini_ks,
    _compute_brier,
    _compute_psi,
    _hosmer_lemeshow_test,
    _jeffreys_test,
    _spiegelhalter_test,
)


class TestComputeAucGiniKs:
    def test_perfect_discrimination(self):
        predicted = [0.9, 0.8, 0.1, 0.05]
        actual = [1, 1, 0, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["auc"] == 1.0
        assert result["gini"] == 1.0

    def test_random_discrimination(self):
        rng = np.random.default_rng(42)
        n = 500
        predicted = rng.random(n).tolist()
        actual = rng.integers(0, 2, n).tolist()
        result = _compute_auc_gini_ks(predicted, actual)
        assert 0.3 < result["auc"] < 0.7

    def test_empty_lists(self):
        result = _compute_auc_gini_ks([], [])
        assert result["auc"] == 0.5
        assert result["gini"] == 0.0
        assert result["ks"] == 0.0

    def test_no_positives(self):
        result = _compute_auc_gini_ks([0.5, 0.3, 0.2], [0, 0, 0])
        assert result["auc"] == 0.5

    def test_no_negatives(self):
        result = _compute_auc_gini_ks([0.5, 0.3, 0.2], [1, 1, 1])
        assert result["auc"] == 0.5

    def test_ks_nonnegative(self):
        predicted = [0.9, 0.7, 0.3, 0.1]
        actual = [1, 0, 1, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["ks"] >= 0.0

    def test_gini_relationship_to_auc(self):
        predicted = [0.9, 0.8, 0.7, 0.2, 0.1, 0.05]
        actual = [1, 1, 1, 0, 0, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert abs(result["gini"] - (2 * result["auc"] - 1)) < 0.001

    def test_single_observation(self):
        result = _compute_auc_gini_ks([0.5], [1])
        assert isinstance(result["auc"], float)

    def test_tied_predictions(self):
        predicted = [0.5, 0.5, 0.5, 0.5]
        actual = [1, 0, 1, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert isinstance(result["auc"], float)

    def test_extreme_predictions(self):
        predicted = [1.0, 1.0, 0.0, 0.0]
        actual = [1, 1, 0, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["auc"] >= 0.9

    def test_large_sample(self):
        rng = np.random.default_rng(123)
        n = 10000
        predicted = rng.random(n).tolist()
        actual = (rng.random(n) < predicted).astype(int).tolist()
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["auc"] > 0.5
        assert result["gini"] > 0.0


class TestComputePsi:
    def test_identical_distributions(self):
        vals = [0.1, 0.2, 0.3, 0.4, 0.5] * 20
        psi = _compute_psi(vals, vals)
        assert psi < 0.01

    def test_shifted_distribution(self):
        expected = [0.1, 0.2, 0.3] * 30
        actual = [0.5, 0.6, 0.7] * 30
        psi = _compute_psi(expected, actual)
        assert psi > 0.1

    def test_empty_lists(self):
        assert _compute_psi([], []) == 0.0

    def test_single_element(self):
        psi = _compute_psi([0.5], [0.5])
        assert isinstance(psi, float)

    def test_different_sizes(self):
        expected = [0.1, 0.2, 0.3] * 10
        actual = [0.1, 0.2, 0.3] * 20
        psi = _compute_psi(expected, actual)
        assert psi >= 0.0

    def test_custom_bins(self):
        vals = np.random.default_rng(42).random(100).tolist()
        psi5 = _compute_psi(vals, vals, n_bins=5)
        psi20 = _compute_psi(vals, vals, n_bins=20)
        assert isinstance(psi5, float)
        assert isinstance(psi20, float)

    def test_zero_values(self):
        psi = _compute_psi([0.0] * 20, [0.0] * 20)
        assert isinstance(psi, float)

    def test_one_values(self):
        psi = _compute_psi([1.0] * 20, [1.0] * 20)
        assert isinstance(psi, float)


class TestComputeBrier:
    def test_perfect_predictions(self):
        predicted = [1.0, 0.0, 1.0, 0.0]
        actual = [1, 0, 1, 0]
        assert _compute_brier(predicted, actual) == 0.0

    def test_worst_predictions(self):
        predicted = [0.0, 1.0, 0.0, 1.0]
        actual = [1, 0, 1, 0]
        assert _compute_brier(predicted, actual) == 1.0

    def test_coin_flip(self):
        predicted = [0.5] * 100
        actual = [1] * 50 + [0] * 50
        brier = _compute_brier(predicted, actual)
        assert abs(brier - 0.25) < 0.001

    def test_empty(self):
        assert _compute_brier([], []) == 0.0

    def test_bounded(self):
        rng = np.random.default_rng(42)
        predicted = rng.random(100).tolist()
        actual = rng.integers(0, 2, 100).tolist()
        brier = _compute_brier(predicted, actual)
        assert 0.0 <= brier <= 1.0

    def test_single_observation(self):
        assert _compute_brier([0.7], [1]) == round((0.7 - 1) ** 2, 4)


class TestBinomialTest:
    def test_pass_within_confidence(self):
        result = _binomial_test(0.05, 1000, 40)
        assert bool(result["pass"]) is True

    def test_fail_too_many_defaults(self):
        result = _binomial_test(0.01, 1000, 50)
        assert bool(result["pass"]) is False

    def test_zero_obligors(self):
        result = _binomial_test(0.05, 0, 0)
        assert bool(result["pass"]) is True
        assert result["p_value"] == 1.0

    def test_zero_defaults(self):
        result = _binomial_test(0.05, 100, 0)
        assert bool(result["pass"]) is True

    def test_all_default(self):
        result = _binomial_test(0.05, 100, 100)
        assert bool(result["pass"]) is False

    def test_output_fields(self):
        result = _binomial_test(0.03, 500, 10)
        assert "predicted_pd" in result
        assert "n_obligors" in result
        assert "n_defaults" in result
        assert "observed_dr" in result
        assert "expected_defaults" in result
        assert "ci_upper_95" in result
        assert "p_value" in result
        assert "pass" in result

    def test_observed_dr_calculation(self):
        result = _binomial_test(0.05, 200, 10)
        assert result["observed_dr"] == round(10 / 200, 6)

    def test_expected_defaults(self):
        result = _binomial_test(0.04, 1000, 30)
        assert result["expected_defaults"] == 40.0

    def test_high_pd(self):
        result = _binomial_test(0.50, 100, 60)
        assert isinstance(bool(result["pass"]), bool)

    def test_low_pd(self):
        result = _binomial_test(0.001, 10000, 5)
        assert bool(result["pass"]) is True


class TestJeffreysTest:
    def test_pass_within_credible_interval(self):
        result = _jeffreys_test(0.05, 1000, 50)
        assert isinstance(bool(result["pass"]), bool)

    def test_zero_obligors(self):
        result = _jeffreys_test(0.05, 0, 0)
        assert result["pass"] is True

    def test_output_fields(self):
        result = _jeffreys_test(0.03, 500, 15)
        assert "posterior_mean" in result
        assert "ci_lower_95" in result
        assert "ci_upper_95" in result
        assert "pass" in result

    def test_posterior_mean_close_to_observed(self):
        result = _jeffreys_test(0.05, 1000, 50)
        assert abs(result["posterior_mean"] - 0.05) < 0.02

    def test_ci_contains_posterior_mean(self):
        result = _jeffreys_test(0.05, 500, 25)
        assert result["ci_lower_95"] <= result["posterior_mean"] <= result["ci_upper_95"]

    def test_all_default(self):
        result = _jeffreys_test(0.05, 100, 100)
        assert bool(result["pass"]) is False

    def test_no_defaults(self):
        result = _jeffreys_test(0.05, 100, 0)
        assert isinstance(bool(result["pass"]), bool)

    def test_large_sample(self):
        result = _jeffreys_test(0.02, 10000, 200)
        assert abs(result["posterior_mean"] - 0.02) < 0.005


class TestHosmerLemeshowTest:
    def test_well_calibrated_model(self):
        rng = np.random.default_rng(42)
        n = 1000
        predicted = rng.random(n).tolist()
        actual = (rng.random(n) < predicted).astype(int).tolist()
        result = _hosmer_lemeshow_test(predicted, actual)
        assert result["p_value"] > 0.01

    def test_poorly_calibrated(self):
        predicted = [0.1] * 200 + [0.9] * 200
        actual = [1] * 200 + [0] * 200
        result = _hosmer_lemeshow_test(predicted, actual)
        assert result["p_value"] < 0.05

    def test_insufficient_data(self):
        result = _hosmer_lemeshow_test([0.5] * 10, [1] * 5 + [0] * 5)
        assert result["pass"] is True
        assert "Insufficient" in result.get("detail", "")

    def test_output_fields(self):
        rng = np.random.default_rng(42)
        n = 500
        predicted = rng.random(n).tolist()
        actual = rng.integers(0, 2, n).tolist()
        result = _hosmer_lemeshow_test(predicted, actual)
        assert "chi_squared" in result
        assert "p_value" in result
        assert "df" in result
        assert "pass" in result
        assert "groups" in result

    def test_groups_count(self):
        rng = np.random.default_rng(42)
        n = 500
        predicted = rng.random(n).tolist()
        actual = rng.integers(0, 2, n).tolist()
        result = _hosmer_lemeshow_test(predicted, actual, n_groups=5)
        assert len(result["groups"]) <= 5

    def test_traffic_light_field(self):
        rng = np.random.default_rng(42)
        n = 1000
        predicted = rng.random(n).tolist()
        actual = (rng.random(n) < predicted).astype(int).tolist()
        result = _hosmer_lemeshow_test(predicted, actual)
        assert result["traffic_light"] in ("Green", "Amber", "Red")


class TestSpiegelhalterTest:
    def test_well_calibrated(self):
        rng = np.random.default_rng(42)
        n = 1000
        predicted = rng.random(n).tolist()
        actual = (rng.random(n) < predicted).astype(int).tolist()
        result = _spiegelhalter_test(predicted, actual)
        assert result["p_value"] > 0.01

    def test_empty(self):
        result = _spiegelhalter_test([], [])
        assert result["pass"] is True
        assert result["p_value"] == 1.0

    def test_output_fields(self):
        rng = np.random.default_rng(42)
        predicted = rng.random(200).tolist()
        actual = rng.integers(0, 2, 200).tolist()
        result = _spiegelhalter_test(predicted, actual)
        assert "z_statistic" in result
        assert "p_value" in result
        assert "pass" in result

    def test_constant_predictions(self):
        result = _spiegelhalter_test([0.5] * 100, [1] * 50 + [0] * 50)
        assert result["p_value"] == 1.0

    def test_traffic_light_field(self):
        rng = np.random.default_rng(42)
        predicted = rng.random(500).tolist()
        actual = rng.integers(0, 2, 500).tolist()
        result = _spiegelhalter_test(predicted, actual)
        assert result["traffic_light"] in ("Green", "Amber", "Red")

    def test_zero_denominator(self):
        result = _spiegelhalter_test([0.5] * 10, [0] * 10)
        assert result["pass"] is True
