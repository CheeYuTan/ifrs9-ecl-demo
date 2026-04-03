"""
Unit tests for IFRS 9 Domain Validation Rules Engine.

Tests all 23 rules across data integrity, model reasonableness, and governance.
"""
import pytest
from domain.validation_rules import (
    ValidationResult,
    check_scenario_weights_sum,
    check_pd_range,
    check_lgd_range,
    check_eir_positive,
    check_remaining_months,
    check_gca_positive,
    check_coverage_monotonic,
    check_ecl_period_change,
    check_convergence_cv,
    check_scenario_concentration,
    check_adverse_exceeds_baseline,
    check_scenario_weight_constraints,
    check_segregation_of_duties,
    check_overlay_has_required_fields,
    check_data_quality_gate,
    check_overlay_cap,
    run_all_pre_calculation_checks,
    run_all_post_calculation_checks,
    has_critical_failures,
)


class TestValidationResult:
    def test_to_dict(self):
        r = ValidationResult("D1", "data_integrity", "CRITICAL", True, "OK")
        d = r.to_dict()
        assert d["rule_id"] == "D1"
        assert d["status"] == "PASS"
        assert d["passed"] == True

    def test_fail_status(self):
        r = ValidationResult("D1", "data_integrity", "CRITICAL", False, "Failed")
        assert r.to_dict()["status"] == "FAIL"


class TestDataIntegrityRules:
    def test_d1_weights_sum_to_one(self):
        weights = {"baseline": 0.30, "adverse": 0.30, "optimistic": 0.40}
        result = check_scenario_weights_sum(weights)
        assert result.passed == True

    def test_d1_weights_dont_sum(self):
        weights = {"baseline": 0.30, "adverse": 0.30}
        result = check_scenario_weights_sum(weights)
        assert result.passed == False

    def test_d2_valid_pd(self):
        result = check_pd_range([0.01, 0.05, 0.10, 0.50, 1.0])
        assert result.passed == True

    def test_d2_invalid_pd_zero(self):
        result = check_pd_range([0.0, 0.05, 0.10])
        assert result.passed == False

    def test_d2_invalid_pd_above_one(self):
        result = check_pd_range([0.05, 1.5])
        assert result.passed == False

    def test_d3_valid_lgd(self):
        result = check_lgd_range([0.15, 0.35, 0.60])
        assert result.passed == True

    def test_d3_invalid_lgd(self):
        result = check_lgd_range([0.0, 0.35])
        assert result.passed == False

    def test_d4_valid_eir(self):
        result = check_eir_positive([0.03, 0.05, 0.08])
        assert result.passed == True

    def test_d4_invalid_eir(self):
        result = check_eir_positive([0.0, 0.05])
        assert result.passed == False

    def test_d5_valid_months(self):
        result = check_remaining_months([0, 12, 36, 60])
        assert result.passed == True

    def test_d5_negative_months(self):
        result = check_remaining_months([-1, 12])
        assert result.passed == False

    def test_d6_valid_gca(self):
        result = check_gca_positive([1000, 50000, 100000])
        assert result.passed == True

    def test_d6_zero_gca(self):
        result = check_gca_positive([0, 50000])
        assert result.passed == False


class TestModelReasonablenessRules:
    def test_mr1_monotonic_coverage(self):
        result = check_coverage_monotonic({1: 0.5, 2: 2.0, 3: 15.0})
        assert result.passed == True

    def test_mr1_non_monotonic(self):
        result = check_coverage_monotonic({1: 5.0, 2: 2.0, 3: 15.0})
        assert result.passed == False

    def test_mr2_within_range(self):
        result = check_ecl_period_change(1100000, 1000000)
        assert result.passed == True

    def test_mr2_too_large_increase(self):
        result = check_ecl_period_change(3000000, 1000000)
        assert result.passed == False

    def test_mr2_too_large_decrease(self):
        result = check_ecl_period_change(400000, 1000000)
        assert result.passed == False

    def test_mr2_zero_prior(self):
        result = check_ecl_period_change(1000000, 0)
        assert result.passed == True

    def test_mr4_good_convergence(self):
        result = check_convergence_cv(0.02)
        assert result.passed == True

    def test_mr4_poor_convergence(self):
        result = check_convergence_cv(0.08)
        assert result.passed == False

    def test_mr5_no_concentration(self):
        result = check_scenario_concentration(
            {"baseline": 200000, "adverse": 200000, "optimistic": 200000},
            600000
        )
        assert result.passed == True

    def test_mr5_concentrated(self):
        result = check_scenario_concentration(
            {"baseline": 500000, "adverse": 50000},
            550000
        )
        assert result.passed == False

    def test_mr6_adverse_exceeds(self):
        result = check_adverse_exceeds_baseline(1000000, 1500000)
        assert result.passed == True

    def test_mr6_adverse_below(self):
        result = check_adverse_exceeds_baseline(1000000, 800000)
        assert result.passed == False

    def test_mr5b_valid_weights(self):
        weights = {
            "baseline": 0.30, "mild_recovery": 0.15, "strong_growth": 0.05,
            "mild_downturn": 0.15, "adverse": 0.15, "stagflation": 0.08,
            "severely_adverse": 0.07, "tail_risk": 0.05,
        }
        result = check_scenario_weight_constraints(weights)
        assert result.passed == True

    def test_mr5b_single_scenario_too_high(self):
        weights = {"baseline": 0.60, "adverse": 0.40}
        result = check_scenario_weight_constraints(weights)
        assert result.passed == False


class TestGovernanceRules:
    def test_gr1_different_users(self):
        result = check_segregation_of_duties("analyst@bank.com", "approver@bank.com")
        assert result.passed == True

    def test_gr1_same_user(self):
        result = check_segregation_of_duties("user@bank.com", "user@bank.com")
        assert result.passed == False

    def test_gr2_complete_overlay(self):
        overlay = {"reason": "COVID adjustment", "amount": 50000,
                   "ifrs9": "5.5.17", "approver": "mgr", "expiry_date": "2025-12-31"}
        result = check_overlay_has_required_fields(overlay)
        assert result.passed == True

    def test_gr2_missing_reason(self):
        overlay = {"amount": 50000}
        result = check_overlay_has_required_fields(overlay)
        assert result.passed == False

    def test_gr5_good_dq(self):
        result = check_data_quality_gate(95.0)
        assert result.passed == True

    def test_gr5_poor_dq(self):
        result = check_data_quality_gate(85.0)
        assert result.passed == False

    def test_mr8_within_cap(self):
        result = check_overlay_cap(100000, 1000000, cap_pct=15.0)
        assert result.passed == True

    def test_mr8_exceeds_cap(self):
        result = check_overlay_cap(200000, 1000000, cap_pct=15.0)
        assert result.passed == False


class TestAggregateChecks:
    def test_pre_calculation_returns_list(self):
        results = run_all_pre_calculation_checks(
            scenario_weights={"baseline": 0.5, "adverse": 0.5},
            pd_values=[0.05, 0.10],
            lgd_values=[0.35, 0.60],
            eir_values=[0.05, 0.08],
            remaining_months=[12, 36],
            gca_values=[100000, 200000],
        )
        assert isinstance(results, list)
        assert len(results) == 10  # 7 original + 3 new DA rules (DA-2, DA-4, DA-6)
        assert all("rule_id" in r for r in results)

    def test_post_calculation_returns_list(self):
        results = run_all_post_calculation_checks(
            stage_coverage={1: 0.5, 2: 2.0, 3: 15.0},
            current_ecl=1000000, prior_ecl=900000,
            convergence_cv=0.02,
            scenario_ecl={"baseline": 500000, "adverse": 500000},
            total_ecl=1000000,
            baseline_ecl=800000, adverse_ecl=1200000,
        )
        assert isinstance(results, list)
        assert len(results) == 5

    def test_has_critical_failures_true(self):
        results = [
            {"severity": "CRITICAL", "passed": False, "rule_id": "D1"},
            {"severity": "HIGH", "passed": True, "rule_id": "M-R1"},
        ]
        assert has_critical_failures(results) == True

    def test_has_critical_failures_false(self):
        results = [
            {"severity": "CRITICAL", "passed": True, "rule_id": "D1"},
            {"severity": "HIGH", "passed": False, "rule_id": "M-R1"},
        ]
        assert has_critical_failures(results) == False

    def test_pre_checks_with_stage_dpd(self):
        from domain.validation_rules import run_all_pre_calculation_checks
        results = run_all_pre_calculation_checks(
            scenario_weights={"baseline": 0.5, "adverse": 0.5},
            pd_values=[0.05, 0.1], lgd_values=[0.3], eir_values=[0.08],
            remaining_months=[24], gca_values=[10000],
            stage_dpd_pairs=[(1, 5), (2, 45), (3, 95)],
            aging_factor=0.08,
        )
        rule_ids = {r["rule_id"] for r in results}
        assert "D7" in rule_ids
        assert "D8" in rule_ids
        assert "M-R7" in rule_ids

    def test_post_checks_with_satellite_r2(self):
        from domain.validation_rules import run_all_post_calculation_checks
        results = run_all_post_calculation_checks(
            stage_coverage={1: 0.5, 2: 2.0, 3: 15.0},
            current_ecl=1000000, prior_ecl=900000,
            convergence_cv=0.02,
            scenario_ecl={"baseline": 500000, "adverse": 500000},
            total_ecl=1000000,
            baseline_ecl=800000, adverse_ecl=1200000,
            satellite_r2={"logistic": 0.85, "linear": 0.25},
        )
        rule_ids = {r["rule_id"] for r in results}
        assert "M-R3" in rule_ids


class TestNewValidationRules:
    """Tests for the 7 new rules added in Run 4."""

    def test_d7_stage3_dpd_pass(self):
        from domain.validation_rules import check_stage3_dpd
        result = check_stage3_dpd([(3, 95), (3, 120), (1, 10)])
        assert result.passed is True

    def test_d7_stage3_dpd_fail(self):
        from domain.validation_rules import check_stage3_dpd
        result = check_stage3_dpd([(3, 50), (3, 120), (1, 10)])
        assert result.passed is False
        assert result.detail["violations_count"] == 1

    def test_d8_stage1_dpd_pass(self):
        from domain.validation_rules import check_stage1_dpd
        result = check_stage1_dpd([(1, 0), (1, 15), (2, 45)])
        assert result.passed is True

    def test_d8_stage1_dpd_fail(self):
        from domain.validation_rules import check_stage1_dpd
        result = check_stage1_dpd([(1, 35), (1, 10), (2, 45)])
        assert result.passed is False
        assert result.detail["violations_count"] == 1

    def test_d9_origination_before_reporting_pass(self):
        from domain.validation_rules import check_origination_before_reporting
        result = check_origination_before_reporting(
            ["2024-01-15", "2023-06-01"], "2025-12-31"
        )
        assert result.passed is True

    def test_d9_origination_before_reporting_fail(self):
        from domain.validation_rules import check_origination_before_reporting
        result = check_origination_before_reporting(
            ["2024-01-15", "2026-03-01"], "2025-12-31"
        )
        assert result.passed is False

    def test_d9_invalid_reporting_date(self):
        from domain.validation_rules import check_origination_before_reporting
        result = check_origination_before_reporting(["2024-01-15"], "bad-date")
        assert result.passed is False

    def test_d10_maturity_after_origination_pass(self):
        from domain.validation_rules import check_maturity_after_origination
        result = check_maturity_after_origination([
            ("2024-01-15", "2029-01-15"),
            ("2023-06-01", "2028-06-01"),
        ])
        assert result.passed is True

    def test_d10_maturity_after_origination_fail(self):
        from domain.validation_rules import check_maturity_after_origination
        result = check_maturity_after_origination([
            ("2024-01-15", "2024-01-15"),
            ("2023-06-01", "2022-01-01"),
        ])
        assert result.passed is False
        assert result.detail["violations_count"] == 2

    def test_mr3_satellite_r_squared_pass(self):
        from domain.validation_rules import check_satellite_r_squared
        result = check_satellite_r_squared({"logistic": 0.85, "ridge": 0.45})
        assert result.passed is True

    def test_mr3_satellite_r_squared_fail(self):
        from domain.validation_rules import check_satellite_r_squared
        result = check_satellite_r_squared({"logistic": 0.85, "linear": 0.20})
        assert result.passed is False
        assert "linear" in result.detail["failures"]

    def test_mr7_aging_factor_pass(self):
        from domain.validation_rules import check_pd_aging_factor
        result = check_pd_aging_factor(0.08)
        assert result.passed is True

    def test_mr7_aging_factor_fail_too_high(self):
        from domain.validation_rules import check_pd_aging_factor
        result = check_pd_aging_factor(0.50)
        assert result.passed is False

    def test_mr7_aging_factor_fail_negative(self):
        from domain.validation_rules import check_pd_aging_factor
        result = check_pd_aging_factor(-0.05)
        assert result.passed is False

    def test_gr4_backtesting_gate_pass(self):
        from domain.validation_rules import check_backtesting_gate
        result = check_backtesting_gate(30)
        assert result.passed is True

    def test_gr4_backtesting_gate_fail_too_old(self):
        from domain.validation_rules import check_backtesting_gate
        result = check_backtesting_gate(120)
        assert result.passed is False

    def test_gr4_backtesting_gate_fail_none(self):
        from domain.validation_rules import check_backtesting_gate
        result = check_backtesting_gate(None)
        assert result.passed is False
