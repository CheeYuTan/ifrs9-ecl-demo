"""Dedicated tests for ecl/constants.py — lookup tables and fallback defaults."""
import pytest

from ecl.constants import (
    BASE_LGD,
    DEFAULT_LGD,
    DEFAULT_SAT,
    DEFAULT_SCENARIO_WEIGHTS,
    SATELLITE_COEFFICIENTS,
    _FALLBACK_BASE_LGD,
    _FALLBACK_SATELLITE,
)


class TestFallbackBaseLgd:
    def test_has_five_product_types(self):
        assert len(_FALLBACK_BASE_LGD) == 5

    def test_credit_card_lgd(self):
        assert _FALLBACK_BASE_LGD["credit_card"] == 0.60

    def test_residential_mortgage_lgd(self):
        assert _FALLBACK_BASE_LGD["residential_mortgage"] == 0.15

    def test_commercial_loan_lgd(self):
        assert _FALLBACK_BASE_LGD["commercial_loan"] == 0.25

    def test_personal_loan_lgd(self):
        assert _FALLBACK_BASE_LGD["personal_loan"] == 0.50

    def test_auto_loan_lgd(self):
        assert _FALLBACK_BASE_LGD["auto_loan"] == 0.35

    def test_all_lgd_between_0_and_1(self):
        for product, lgd in _FALLBACK_BASE_LGD.items():
            assert 0 < lgd < 1, f"{product} has invalid LGD: {lgd}"

    def test_mortgage_lowest_lgd(self):
        assert _FALLBACK_BASE_LGD["residential_mortgage"] == min(_FALLBACK_BASE_LGD.values())

    def test_credit_card_highest_lgd(self):
        assert _FALLBACK_BASE_LGD["credit_card"] == max(_FALLBACK_BASE_LGD.values())


class TestFallbackSatellite:
    def test_has_five_product_types(self):
        assert len(_FALLBACK_SATELLITE) == 5

    def test_same_products_as_lgd(self):
        assert set(_FALLBACK_SATELLITE.keys()) == set(_FALLBACK_BASE_LGD.keys())

    def test_each_product_has_required_keys(self):
        for product, sat in _FALLBACK_SATELLITE.items():
            assert "pd_lgd_corr" in sat, f"{product} missing pd_lgd_corr"
            assert "annual_prepay_rate" in sat, f"{product} missing annual_prepay_rate"
            assert "lgd_std" in sat, f"{product} missing lgd_std"

    def test_pd_lgd_corr_range(self):
        for product, sat in _FALLBACK_SATELLITE.items():
            assert 0 < sat["pd_lgd_corr"] < 1, f"{product} pd_lgd_corr out of range"

    def test_prepay_rate_range(self):
        for product, sat in _FALLBACK_SATELLITE.items():
            assert 0 < sat["annual_prepay_rate"] < 1, f"{product} prepay rate out of range"

    def test_lgd_std_range(self):
        for product, sat in _FALLBACK_SATELLITE.items():
            assert 0 < sat["lgd_std"] < 1, f"{product} lgd_std out of range"

    def test_credit_card_highest_pd_lgd_corr(self):
        assert _FALLBACK_SATELLITE["credit_card"]["pd_lgd_corr"] == max(
            s["pd_lgd_corr"] for s in _FALLBACK_SATELLITE.values()
        )

    def test_mortgage_lowest_pd_lgd_corr(self):
        assert _FALLBACK_SATELLITE["residential_mortgage"]["pd_lgd_corr"] == min(
            s["pd_lgd_corr"] for s in _FALLBACK_SATELLITE.values()
        )

    def test_personal_loan_highest_prepay(self):
        assert _FALLBACK_SATELLITE["personal_loan"]["annual_prepay_rate"] == max(
            s["annual_prepay_rate"] for s in _FALLBACK_SATELLITE.values()
        )


class TestDefaultSat:
    def test_has_pd_lgd_corr(self):
        assert "pd_lgd_corr" in DEFAULT_SAT

    def test_has_annual_prepay_rate(self):
        assert "annual_prepay_rate" in DEFAULT_SAT

    def test_has_lgd_std(self):
        assert "lgd_std" in DEFAULT_SAT

    def test_pd_lgd_corr_value(self):
        assert DEFAULT_SAT["pd_lgd_corr"] == 0.30

    def test_prepay_rate_value(self):
        assert DEFAULT_SAT["annual_prepay_rate"] == 0.05

    def test_lgd_std_value(self):
        assert DEFAULT_SAT["lgd_std"] == 0.15


class TestDefaultLgd:
    def test_value(self):
        assert DEFAULT_LGD == 0.45

    def test_between_0_and_1(self):
        assert 0 < DEFAULT_LGD < 1


class TestDefaultScenarioWeights:
    def test_has_scenarios(self):
        assert len(DEFAULT_SCENARIO_WEIGHTS) > 0

    def test_has_baseline(self):
        assert "baseline" in DEFAULT_SCENARIO_WEIGHTS

    def test_baseline_is_highest_weight(self):
        assert DEFAULT_SCENARIO_WEIGHTS["baseline"] == max(DEFAULT_SCENARIO_WEIGHTS.values())

    def test_weights_sum_to_one(self):
        total = sum(DEFAULT_SCENARIO_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_all_weights_positive(self):
        for sc, w in DEFAULT_SCENARIO_WEIGHTS.items():
            assert w > 0, f"{sc} has non-positive weight"

    def test_all_weights_less_than_one(self):
        for sc, w in DEFAULT_SCENARIO_WEIGHTS.items():
            assert w < 1.0, f"{sc} has weight >= 1"

    def test_has_adverse_scenario(self):
        assert "adverse" in DEFAULT_SCENARIO_WEIGHTS

    def test_has_tail_risk_scenario(self):
        assert "tail_risk" in DEFAULT_SCENARIO_WEIGHTS

    def test_tail_risk_is_small(self):
        assert DEFAULT_SCENARIO_WEIGHTS["tail_risk"] <= 0.10

    def test_has_eight_scenarios(self):
        assert len(DEFAULT_SCENARIO_WEIGHTS) == 8

    def test_expected_scenarios_present(self):
        expected = {"baseline", "mild_recovery", "strong_growth", "mild_downturn",
                    "adverse", "stagflation", "severely_adverse", "tail_risk"}
        assert set(DEFAULT_SCENARIO_WEIGHTS.keys()) == expected


class TestModuleLevelAliases:
    def test_base_lgd_equals_fallback(self):
        assert BASE_LGD == _FALLBACK_BASE_LGD

    def test_satellite_equals_fallback(self):
        assert SATELLITE_COEFFICIENTS == _FALLBACK_SATELLITE
