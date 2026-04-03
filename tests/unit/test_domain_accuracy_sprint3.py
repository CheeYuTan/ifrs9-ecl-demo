"""
Sprint 3 (Run 7): Domain Accuracy Validation Tests

Tests for IFRS 9 domain accuracy rules DA-1 through DA-6,
with SME-derived test scenarios covering boundary conditions,
edge cases, and IFRS 9 regulatory requirements.
"""
import pytest
from domain.validation_rules import (
    check_ead_non_negative,
    check_lgd_unit_interval,
    check_stage3_pd_consistency,
    check_discount_rate_valid,
    check_ecl_non_negative,
    check_minimum_scenario_count,
    run_all_pre_calculation_checks,
)


# ── DA-1: EAD Non-Negative (IFRS 9.B5.5.31) ────────────────────────────────

class TestEadNonNegative:
    """EAD represents gross carrying amount + undrawn. Must be >= 0."""

    def test_all_positive(self):
        result = check_ead_non_negative([100_000, 250_000, 500_000])
        assert result.passed is True
        assert result.rule_id == "DA-1"

    def test_zero_ead_allowed(self):
        """Zero EAD is valid (fully drawn, no exposure)."""
        result = check_ead_non_negative([0, 100_000, 0])
        assert result.passed is True

    def test_negative_ead_fails(self):
        result = check_ead_non_negative([100_000, -50_000, 200_000])
        assert result.passed is False
        assert result.detail["violations_count"] == 1

    def test_all_negative_fails(self):
        result = check_ead_non_negative([-100, -200, -300])
        assert result.passed is False
        assert result.detail["violations_count"] == 3

    def test_empty_list_passes(self):
        result = check_ead_non_negative([])
        assert result.passed is True

    def test_ifrs_reference(self):
        result = check_ead_non_negative([100])
        assert result.detail["ifrs_ref"] == "IFRS 9.B5.5.31"

    def test_severity_is_critical(self):
        result = check_ead_non_negative([-1])
        assert result.severity == "CRITICAL"


# ── DA-2: LGD Unit Interval (IFRS 9.B5.5.28) ────────────────────────────────

class TestLgdUnitInterval:
    """LGD must be in [0, 1]. Unlike D3, this enforces inclusive bounds."""

    def test_valid_range(self):
        result = check_lgd_unit_interval([0.0, 0.45, 0.60, 1.0])
        assert result.passed is True

    def test_zero_lgd_valid(self):
        """LGD=0 means full recovery — valid."""
        result = check_lgd_unit_interval([0.0])
        assert result.passed is True

    def test_one_lgd_valid(self):
        """LGD=1 means total loss — valid."""
        result = check_lgd_unit_interval([1.0])
        assert result.passed is True

    def test_negative_lgd_fails(self):
        result = check_lgd_unit_interval([0.45, -0.01])
        assert result.passed is False

    def test_lgd_above_one_fails(self):
        result = check_lgd_unit_interval([0.45, 1.01])
        assert result.passed is False

    def test_multiple_violations(self):
        result = check_lgd_unit_interval([-0.1, 1.5, 0.5])
        assert result.passed is False
        assert result.detail["violations_count"] == 2


# ── DA-3: Stage 3 PD Consistency (IFRS 9.B5.5.37) ──────────────────────────

class TestStage3PdConsistency:
    """Stage 3 loans are credit-impaired; PD should be near 1.0."""

    def test_stage3_high_pd_passes(self):
        pairs = [(3, 0.95), (3, 1.0), (1, 0.05)]
        result = check_stage3_pd_consistency(pairs)
        assert result.passed is True

    def test_stage3_low_pd_fails(self):
        pairs = [(3, 0.50), (1, 0.05)]
        result = check_stage3_pd_consistency(pairs)
        assert result.passed is False
        assert result.detail["violations_count"] == 1

    def test_no_stage3_loans_passes(self):
        pairs = [(1, 0.05), (2, 0.20)]
        result = check_stage3_pd_consistency(pairs)
        assert result.passed is True
        assert result.detail["total_stage3"] == 0

    def test_custom_threshold(self):
        pairs = [(3, 0.85)]
        result = check_stage3_pd_consistency(pairs, min_stage3_pd=0.80)
        assert result.passed is True

    def test_boundary_at_threshold(self):
        pairs = [(3, 0.90)]
        result = check_stage3_pd_consistency(pairs, min_stage3_pd=0.90)
        assert result.passed is True

    def test_just_below_threshold(self):
        pairs = [(3, 0.899)]
        result = check_stage3_pd_consistency(pairs, min_stage3_pd=0.90)
        assert result.passed is False


# ── DA-4: Discount Rate Valid (IFRS 9.B5.5.44) ──────────────────────────────

class TestDiscountRateValid:
    """EIR must be > -1 for discount factor 1/(1+EIR)^t to be defined."""

    def test_positive_eir_passes(self):
        result = check_discount_rate_valid([0.05, 0.08, 0.12])
        assert result.passed is True

    def test_zero_eir_passes(self):
        result = check_discount_rate_valid([0.0])
        assert result.passed is True

    def test_small_negative_eir_passes(self):
        """Slightly negative EIR is mathematically valid (unusual but possible)."""
        result = check_discount_rate_valid([-0.01])
        assert result.passed is True

    def test_eir_at_minus_one_fails(self):
        """EIR=-1 creates division by zero in discount factor."""
        result = check_discount_rate_valid([-1.0])
        assert result.passed is False

    def test_eir_below_minus_one_fails(self):
        result = check_discount_rate_valid([-1.5])
        assert result.passed is False

    def test_mixed_valid_invalid(self):
        result = check_discount_rate_valid([0.05, -1.0, 0.08, -2.0])
        assert result.passed is False
        assert result.detail["violations_count"] == 2


# ── DA-5: ECL Non-Negative ──────────────────────────────────────────────────

class TestEclNonNegative:
    """ECL represents expected cash shortfalls — cannot be negative."""

    def test_positive_ecl_passes(self):
        result = check_ecl_non_negative([1000, 5000, 250])
        assert result.passed is True

    def test_zero_ecl_passes(self):
        result = check_ecl_non_negative([0, 0, 1000])
        assert result.passed is True

    def test_negative_ecl_fails(self):
        result = check_ecl_non_negative([1000, -500])
        assert result.passed is False

    def test_empty_list_passes(self):
        result = check_ecl_non_negative([])
        assert result.passed is True


# ── DA-6: Minimum Scenario Count (IFRS 9.B5.5.42) ──────────────────────────

class TestMinimumScenarioCount:
    """IFRS 9 requires at least base, upside, and downside scenarios."""

    def test_three_scenarios_passes(self):
        result = check_minimum_scenario_count(3)
        assert result.passed is True

    def test_eight_scenarios_passes(self):
        result = check_minimum_scenario_count(8)
        assert result.passed is True

    def test_two_scenarios_fails(self):
        result = check_minimum_scenario_count(2)
        assert result.passed is False

    def test_one_scenario_fails(self):
        result = check_minimum_scenario_count(1)
        assert result.passed is False

    def test_custom_minimum(self):
        result = check_minimum_scenario_count(2, minimum=2)
        assert result.passed is True


# ── Integration: run_all_pre_calculation_checks with new rules ──────────────

class TestPreCalcWithDomainRules:
    """Verify new DA rules are included in aggregate pre-calculation checks."""

    def _base_args(self):
        return dict(
            scenario_weights={"base": 0.5, "adverse": 0.3, "optimistic": 0.2},
            pd_values=[0.05, 0.10, 0.20],
            lgd_values=[0.45, 0.60, 0.35],
            eir_values=[0.05, 0.08, 0.06],
            remaining_months=[12.0, 24.0, 36.0],
            gca_values=[100_000, 200_000, 300_000],
        )

    def test_new_rules_included(self):
        results = run_all_pre_calculation_checks(**self._base_args())
        rule_ids = [r["rule_id"] for r in results]
        assert "DA-2" in rule_ids  # LGD unit interval
        assert "DA-4" in rule_ids  # Discount rate valid
        assert "DA-6" in rule_ids  # Min scenario count

    def test_ead_included_when_provided(self):
        args = self._base_args()
        args["ead_values"] = [100_000, 200_000, 300_000]
        results = run_all_pre_calculation_checks(**args)
        rule_ids = [r["rule_id"] for r in results]
        assert "DA-1" in rule_ids

    def test_stage3_pd_included_when_provided(self):
        args = self._base_args()
        args["stage_pd_pairs"] = [(3, 0.95), (1, 0.05)]
        results = run_all_pre_calculation_checks(**args)
        rule_ids = [r["rule_id"] for r in results]
        assert "DA-3" in rule_ids

    def test_negative_ead_flagged(self):
        args = self._base_args()
        args["ead_values"] = [100_000, -50_000]
        results = run_all_pre_calculation_checks(**args)
        da1 = next(r for r in results if r["rule_id"] == "DA-1")
        assert da1["passed"] is False

    def test_invalid_lgd_flagged(self):
        args = self._base_args()
        args["lgd_values"] = [0.45, 1.5, 0.35]
        results = run_all_pre_calculation_checks(**args)
        da2 = next(r for r in results if r["rule_id"] == "DA-2")
        assert da2["passed"] is False

    def test_too_few_scenarios_flagged(self):
        results = run_all_pre_calculation_checks(
            scenario_weights={"base": 0.5, "adverse": 0.5},
            pd_values=[0.05],
            lgd_values=[0.45],
            eir_values=[0.05],
            remaining_months=[12.0],
            gca_values=[100_000],
        )
        da6 = next(r for r in results if r["rule_id"] == "DA-6")
        assert da6["passed"] is False
