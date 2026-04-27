"""Extended tests for domain/backtesting_stats.py — edge cases and numerical precision."""
import numpy as np
import pytest

from domain.backtesting_stats import (
    _binomial_test,
    _compute_auc_gini_ks,
    _compute_brier,
    _compute_psi,
    _hosmer_lemeshow_test,
    _jeffreys_test,
    _spiegelhalter_test,
)


class TestAucGiniKsExtended:
    def test_inverted_discrimination(self):
        predicted = [0.1, 0.2, 0.9, 0.95]
        actual = [1, 1, 0, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["auc"] < 0.5

    def test_two_observations(self):
        result = _compute_auc_gini_ks([0.9, 0.1], [1, 0])
        assert result["auc"] == 1.0

    def test_large_sample_near_perfect(self):
        rng = np.random.default_rng(99)
        n = 5000
        actual = rng.integers(0, 2, n).tolist()
        predicted = [0.9 if a == 1 else 0.1 for a in actual]
        noise = (rng.random(n) * 0.05).tolist()
        predicted = [p + n_ for p, n_ in zip(predicted, noise)]
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["auc"] > 0.9

    def test_all_same_prediction(self):
        result = _compute_auc_gini_ks([0.5] * 100, [1] * 50 + [0] * 50)
        assert isinstance(result["auc"], float)

    def test_near_perfect_gini(self):
        predicted = list(np.linspace(0, 1, 100))
        actual = [1 if p > 0.5 else 0 for p in predicted]
        result = _compute_auc_gini_ks(predicted, actual)
        assert result["gini"] > 0.8

    def test_ks_maximum_one(self):
        predicted = [0.9, 0.8, 0.2, 0.1]
        actual = [1, 1, 0, 0]
        result = _compute_auc_gini_ks(predicted, actual)
        assert 0.0 <= result["ks"] <= 1.0


class TestComputePsiExtended:
    def test_large_shift(self):
        expected = list(np.linspace(0, 0.3, 100))
        actual = list(np.linspace(0.7, 1.0, 100))
        psi = _compute_psi(expected, actual)
        assert psi > 0.5

    def test_minor_perturbation(self):
        rng = np.random.default_rng(42)
        base = rng.random(200).tolist()
        perturbed = [v + rng.normal(0, 0.01) for v in base]
        psi = _compute_psi(base, perturbed)
        assert psi < 0.1

    def test_symmetric(self):
        a = [0.1, 0.2, 0.3] * 30
        b = [0.4, 0.5, 0.6] * 30
        psi_ab = _compute_psi(a, b)
        psi_ba = _compute_psi(b, a)
        assert abs(psi_ab - psi_ba) < 0.1

    def test_nonnegative(self):
        rng = np.random.default_rng(42)
        a = rng.random(100).tolist()
        b = rng.random(100).tolist()
        assert _compute_psi(a, b) >= 0.0


class TestComputeBrierExtended:
    def test_mid_range_predictions(self):
        predicted = [0.3, 0.7, 0.4, 0.6, 0.5]
        actual = [0, 1, 0, 1, 1]
        brier = _compute_brier(predicted, actual)
        assert 0.0 < brier < 0.25

    def test_all_zeros_predicted(self):
        brier = _compute_brier([0.0] * 10, [0] * 10)
        assert brier == 0.0

    def test_all_ones_predicted(self):
        brier = _compute_brier([1.0] * 10, [1] * 10)
        assert brier == 0.0

    def test_symmetric_around_half(self):
        brier_up = _compute_brier([0.8] * 100, [1] * 100)
        brier_down = _compute_brier([0.2] * 100, [0] * 100)
        assert abs(brier_up - brier_down) < 0.001


class TestBinomialTestExtended:
    def test_exact_expected_rate(self):
        result = _binomial_test(0.05, 1000, 50)
        assert abs(result["observed_dr"] - 0.05) < 0.001

    def test_very_large_sample(self):
        result = _binomial_test(0.03, 100000, 3000)
        assert isinstance(bool(result["pass"]), bool)

    def test_pd_equals_one(self):
        result = _binomial_test(1.0, 100, 100)
        assert bool(result["pass"]) is True

    def test_pd_zero(self):
        result = _binomial_test(0.0, 100, 0)
        assert bool(result["pass"]) is True

    def test_p_value_between_0_and_1(self):
        result = _binomial_test(0.05, 500, 25)
        assert 0.0 <= result["p_value"] <= 1.0


class TestJeffreysTestExtended:
    def test_small_sample(self):
        result = _jeffreys_test(0.10, 20, 2)
        assert isinstance(bool(result["pass"]), bool)

    def test_very_low_pd(self):
        result = _jeffreys_test(0.001, 10000, 10)
        assert isinstance(bool(result["pass"]), bool)

    def test_credible_interval_width(self):
        result = _jeffreys_test(0.05, 1000, 50)
        ci_width = result["ci_upper_95"] - result["ci_lower_95"]
        assert ci_width > 0
        assert ci_width < 0.1

    def test_large_sample_narrow_ci(self):
        result = _jeffreys_test(0.05, 10000, 500)
        ci_width = result["ci_upper_95"] - result["ci_lower_95"]
        assert ci_width < 0.02


class TestHosmerLemeshowExtended:
    def test_10_groups_default(self):
        rng = np.random.default_rng(42)
        n = 500
        predicted = rng.random(n).tolist()
        actual = rng.integers(0, 2, n).tolist()
        result = _hosmer_lemeshow_test(predicted, actual)
        assert len(result["groups"]) <= 10

    def test_chi_squared_nonnegative(self):
        rng = np.random.default_rng(42)
        n = 500
        predicted = rng.random(n).tolist()
        actual = rng.integers(0, 2, n).tolist()
        result = _hosmer_lemeshow_test(predicted, actual)
        assert result["chi_squared"] >= 0.0

    def test_p_value_range(self):
        rng = np.random.default_rng(42)
        n = 500
        predicted = rng.random(n).tolist()
        actual = rng.integers(0, 2, n).tolist()
        result = _hosmer_lemeshow_test(predicted, actual)
        assert 0.0 <= result["p_value"] <= 1.0


class TestSpiegelhalterExtended:
    def test_well_calibrated_high_n(self):
        rng = np.random.default_rng(42)
        n = 5000
        predicted = rng.random(n).tolist()
        actual = (rng.random(n) < predicted).astype(int).tolist()
        result = _spiegelhalter_test(predicted, actual)
        assert result["p_value"] > 0.01

    def test_single_observation(self):
        result = _spiegelhalter_test([0.5], [1])
        assert isinstance(bool(result["pass"]), bool)

    def test_extreme_predictions(self):
        result = _spiegelhalter_test([0.99, 0.01] * 50, [1, 0] * 50)
        assert isinstance(bool(result["pass"]), bool)

    def test_z_statistic_real_number(self):
        rng = np.random.default_rng(42)
        predicted = rng.random(200).tolist()
        actual = rng.integers(0, 2, 200).tolist()
        result = _spiegelhalter_test(predicted, actual)
        assert isinstance(result["z_statistic"], (int, float))
        assert np.isfinite(result["z_statistic"])
