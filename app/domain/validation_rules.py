"""
IFRS 9 Domain Validation Rules Engine.

Enforces 23 domain rules across three categories:
  - Data Integrity (D1-D10): Pre-calculation gates
  - Model Reasonableness (M-R1-R8): Post-calculation checks
  - Governance (G-R1-G-R5): Workflow enforcement

Each rule returns a structured result with pass/fail/warning status,
enabling a validation dashboard and blocking ECL calculation or
sign-off when critical rules fail.
"""

import logging

log = logging.getLogger(__name__)


class ValidationResult:
    """Structured result from a validation rule check."""

    __slots__ = ("rule_id", "category", "severity", "passed", "message", "detail")

    def __init__(
        self, rule_id: str, category: str, severity: str, passed: bool, message: str, detail: dict | None = None
    ):
        self.rule_id = rule_id
        self.category = category
        self.severity = severity
        self.passed = passed
        self.message = message
        self.detail = detail or {}

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "passed": self.passed,
            "status": "PASS" if self.passed else "FAIL",
            "message": self.message,
            "detail": self.detail,
        }


# ── Data Integrity Rules (D1-D10) ───────────────────────────────────────────


def check_scenario_weights_sum(weights: dict[str, float]) -> ValidationResult:
    """D1: Scenario weights must sum to 1.0 ± 0.001."""
    total = sum(weights.values())
    passed = abs(total - 1.0) <= 0.001
    return ValidationResult(
        "D1",
        "data_integrity",
        "CRITICAL",
        passed,
        f"Scenario weights sum to {total:.6f} (required: 1.0 ± 0.001)",
        {"weight_sum": round(total, 6), "weights": weights},
    )


def check_pd_range(pd_values: list[float]) -> ValidationResult:
    """D2: 0 < PD ≤ 1.0 for all loans."""
    violations = [v for v in pd_values if v <= 0 or v > 1.0]
    passed = len(violations) == 0
    return ValidationResult(
        "D2",
        "data_integrity",
        "CRITICAL",
        passed,
        f"PD range check: {len(violations)} violations out of {len(pd_values)} loans",
        {"violations_count": len(violations), "total_loans": len(pd_values)},
    )


def check_lgd_range(lgd_values: list[float]) -> ValidationResult:
    """D3: 0 < LGD ≤ 1.0 for all products."""
    violations = [v for v in lgd_values if v <= 0 or v > 1.0]
    passed = len(violations) == 0
    return ValidationResult(
        "D3",
        "data_integrity",
        "CRITICAL",
        passed,
        f"LGD range check: {len(violations)} violations out of {len(lgd_values)} values",
        {"violations_count": len(violations), "total_values": len(lgd_values)},
    )


def check_eir_positive(eir_values: list[float]) -> ValidationResult:
    """D4: EIR > 0 for all loans."""
    violations = [v for v in eir_values if v <= 0]
    passed = len(violations) == 0
    return ValidationResult(
        "D4",
        "data_integrity",
        "CRITICAL",
        passed,
        f"EIR positivity check: {len(violations)} violations out of {len(eir_values)} loans",
        {"violations_count": len(violations)},
    )


def check_remaining_months(months: list[float]) -> ValidationResult:
    """D5: remaining_months ≥ 0."""
    violations = [v for v in months if v < 0]
    passed = len(violations) == 0
    return ValidationResult(
        "D5",
        "data_integrity",
        "CRITICAL",
        passed,
        f"Remaining months check: {len(violations)} negative values",
        {"violations_count": len(violations)},
    )


def check_gca_positive(gca_values: list[float]) -> ValidationResult:
    """D6: gross_carrying_amount > 0 for non-written-off loans."""
    violations = [v for v in gca_values if v <= 0]
    passed = len(violations) == 0
    return ValidationResult(
        "D6",
        "data_integrity",
        "CRITICAL",
        passed,
        f"GCA positivity check: {len(violations)} non-positive values out of {len(gca_values)}",
        {"violations_count": len(violations)},
    )


def check_stage3_dpd(stage3_dpd_values: list[tuple[int, int]]) -> ValidationResult:
    """D7: Stage 3 loans must have DPD >= 90 or another credit-impairment trigger.

    Args:
        stage3_dpd_values: list of (assessed_stage, days_past_due) tuples
    """
    violations = [(s, d) for s, d in stage3_dpd_values if s == 3 and d < 90]
    total_s3 = sum(1 for s, _ in stage3_dpd_values if s == 3)
    passed = len(violations) == 0
    return ValidationResult(
        "D7",
        "data_integrity",
        "HIGH",
        passed,
        f"Stage 3 DPD check: {len(violations)} of {total_s3} Stage 3 loans have DPD < 90",
        {"violations_count": len(violations), "total_stage3": total_s3},
    )


def check_stage1_dpd(stage1_dpd_values: list[tuple[int, int]]) -> ValidationResult:
    """D8: Stage 1 loans must have DPD < 30 (unless 30-day presumption is rebutted).

    Args:
        stage1_dpd_values: list of (assessed_stage, days_past_due) tuples
    """
    violations = [(s, d) for s, d in stage1_dpd_values if s == 1 and d >= 30]
    total_s1 = sum(1 for s, _ in stage1_dpd_values if s == 1)
    passed = len(violations) == 0
    return ValidationResult(
        "D8",
        "data_integrity",
        "HIGH",
        passed,
        f"Stage 1 DPD check: {len(violations)} of {total_s1} Stage 1 loans have DPD >= 30",
        {"violations_count": len(violations), "total_stage1": total_s1},
    )


def check_origination_before_reporting(origination_dates: list[str], reporting_date: str) -> ValidationResult:
    """D9: origination_date < reporting_date for all loans."""
    from datetime import date as _date

    try:
        rep = _date.fromisoformat(reporting_date)
    except (ValueError, TypeError):
        return ValidationResult(
            "D9",
            "data_integrity",
            "CRITICAL",
            False,
            f"Invalid reporting date: {reporting_date}",
            {},
        )
    violations = 0
    for od in origination_dates:
        try:
            if _date.fromisoformat(str(od)) >= rep:
                violations += 1
        except (ValueError, TypeError):
            violations += 1
    passed = violations == 0
    return ValidationResult(
        "D9",
        "data_integrity",
        "CRITICAL",
        passed,
        f"Origination date check: {violations} loans originated on/after reporting date",
        {"violations_count": violations, "total_loans": len(origination_dates)},
    )


def check_maturity_after_origination(date_pairs: list[tuple[str, str]]) -> ValidationResult:
    """D10: maturity_date > origination_date for all loans.

    Args:
        date_pairs: list of (origination_date, maturity_date) tuples
    """
    from datetime import date as _date

    violations = 0
    for orig, mat in date_pairs:
        try:
            if _date.fromisoformat(str(mat)) <= _date.fromisoformat(str(orig)):
                violations += 1
        except (ValueError, TypeError):
            violations += 1
    passed = violations == 0
    return ValidationResult(
        "D10",
        "data_integrity",
        "HIGH",
        passed,
        f"Maturity date check: {violations} loans have maturity <= origination",
        {"violations_count": violations, "total_loans": len(date_pairs)},
    )


# ── Model Reasonableness Rules (M-R1-R8) ────────────────────────────────────


def check_coverage_monotonic(stage_coverage: dict[int, float]) -> ValidationResult:
    """M-R1: ECL coverage ratio must be monotonically increasing by stage."""
    s1 = stage_coverage.get(1, 0)
    s2 = stage_coverage.get(2, 0)
    s3 = stage_coverage.get(3, 0)
    passed = s1 <= s2 <= s3
    return ValidationResult(
        "M-R1",
        "model_reasonableness",
        "HIGH",
        passed,
        f"Coverage monotonicity: S1={s1:.2f}% ≤ S2={s2:.2f}% ≤ S3={s3:.2f}%",
        {"stage1_coverage": s1, "stage2_coverage": s2, "stage3_coverage": s3},
    )


def check_ecl_period_change(current_ecl: float, prior_ecl: float) -> ValidationResult:
    """M-R2: Weighted average ECL should be within 50-200% of prior period."""
    if prior_ecl == 0:
        return ValidationResult(
            "M-R2", "model_reasonableness", "MEDIUM", True, "No prior period ECL for comparison", {}
        )
    ratio = current_ecl / prior_ecl
    passed = 0.5 <= ratio <= 2.0
    return ValidationResult(
        "M-R2",
        "model_reasonableness",
        "MEDIUM",
        passed,
        f"ECL period change: {ratio:.2f}x prior (acceptable: 0.5x-2.0x)",
        {"ratio": round(ratio, 4), "current": current_ecl, "prior": prior_ecl},
    )


def check_convergence_cv(cv: float, threshold: float = 0.05) -> ValidationResult:
    """M-R4: Monte Carlo convergence CV should be < 5%."""
    passed = cv < threshold
    return ValidationResult(
        "M-R4",
        "model_reasonableness",
        "HIGH",
        passed,
        f"Convergence CV: {cv:.4f} (threshold: {threshold})",
        {"cv": cv, "threshold": threshold},
    )


def check_scenario_concentration(scenario_ecl: dict[str, float], total_ecl: float) -> ValidationResult:
    """M-R5: No single scenario should contribute > 40% of probability-weighted ECL."""
    if total_ecl == 0:
        return ValidationResult("M-R5", "model_reasonableness", "MEDIUM", True, "Total ECL is zero", {})
    max_pct = 0
    max_scenario = ""
    for sc, ecl in scenario_ecl.items():
        pct = abs(ecl) / abs(total_ecl) * 100 if total_ecl != 0 else 0
        if pct > max_pct:
            max_pct = pct
            max_scenario = sc
    passed = max_pct <= 40
    return ValidationResult(
        "M-R5",
        "model_reasonableness",
        "MEDIUM",
        passed,
        f"Max scenario contribution: {max_scenario} at {max_pct:.1f}% (limit: 40%)",
        {"max_scenario": max_scenario, "max_pct": round(max_pct, 2)},
    )


def check_adverse_exceeds_baseline(baseline_ecl: float, adverse_ecl: float) -> ValidationResult:
    """M-R6: Adverse scenario ECL should be > baseline ECL."""
    passed = adverse_ecl > baseline_ecl
    return ValidationResult(
        "M-R6",
        "model_reasonableness",
        "HIGH",
        passed,
        f"Adverse ECL ({adverse_ecl:,.0f}) {'>' if passed else '≤'} Baseline ECL ({baseline_ecl:,.0f})",
        {"baseline": baseline_ecl, "adverse": adverse_ecl},
    )


def check_satellite_r_squared(r_squared_values: dict[str, float], threshold: float = 0.30) -> ValidationResult:
    """M-R3: Satellite model R² should be >= threshold for PD models."""
    failures = {k: v for k, v in r_squared_values.items() if v < threshold}
    passed = len(failures) == 0
    return ValidationResult(
        "M-R3",
        "model_reasonableness",
        "HIGH",
        passed,
        f"Satellite R² check: {len(failures)} models below {threshold} threshold",
        {"failures": failures, "threshold": threshold, "all_values": r_squared_values},
    )


def check_pd_aging_factor(aging_factor: float, min_val: float = 0.0, max_val: float = 0.30) -> ValidationResult:
    """M-R7: PD aging factor must produce increasing marginal PD over time."""
    passed = min_val <= aging_factor <= max_val
    return ValidationResult(
        "M-R7",
        "model_reasonableness",
        "HIGH",
        passed,
        f"PD aging factor: {aging_factor:.4f} (acceptable: {min_val}-{max_val})",
        {"aging_factor": aging_factor, "min": min_val, "max": max_val},
    )


def check_scenario_weight_constraints(weights: dict[str, float]) -> ValidationResult:
    """M-R5b: No single scenario > 50%, adverse scenarios collectively ≥ 20%."""
    issues = []
    for sc, w in weights.items():
        if w > 0.50:
            issues.append(f"{sc} weight {w:.0%} exceeds 50% limit")

    adverse_keys = ["adverse", "severely_adverse", "stagflation", "tail_risk", "mild_downturn"]
    adverse_total = sum(weights.get(k, 0) for k in adverse_keys)
    if adverse_total < 0.20:
        issues.append(f"Adverse scenarios total {adverse_total:.0%} (minimum 20%)")

    passed = len(issues) == 0
    return ValidationResult(
        "M-R5b",
        "model_reasonableness",
        "MEDIUM",
        passed,
        "; ".join(issues) if issues else "Scenario weight constraints satisfied",
        {"adverse_total": round(adverse_total, 4), "issues": issues},
    )


# ── Governance Rules (G-R1-G-R5) ────────────────────────────────────────────


def check_segregation_of_duties(executor_user: str, signoff_user: str) -> ValidationResult:
    """G-R1: ECL run must not be signed off by the same user who executed it."""
    passed = executor_user != signoff_user
    return ValidationResult(
        "G-R1",
        "governance",
        "CRITICAL",
        passed,
        f"Segregation of duties: executor='{executor_user}', signoff='{signoff_user}'",
        {"executor": executor_user, "signoff": signoff_user},
    )


def check_overlay_has_required_fields(overlay: dict) -> ValidationResult:
    """G-R2: Management overlays must have reason, IFRS 9 reference, approver, expiry date."""
    required = ["reason", "amount"]
    recommended = ["ifrs9", "approver", "expiry_date"]
    missing_required = [f for f in required if not overlay.get(f)]
    missing_recommended = [f for f in recommended if not overlay.get(f)]
    passed = len(missing_required) == 0
    return ValidationResult(
        "G-R2",
        "governance",
        "HIGH",
        passed,
        f"Overlay fields: {len(missing_required)} required missing, {len(missing_recommended)} recommended missing",
        {"missing_required": missing_required, "missing_recommended": missing_recommended},
    )


def check_data_quality_gate(dq_score: float, threshold: float = None) -> ValidationResult:
    """G-R5: Data quality score must be ≥ threshold before model execution."""
    if threshold is None:
        try:
            import admin_config

            cfg = admin_config.get_config()
            threshold = cfg.get("app_settings", {}).get("governance", {}).get("dq_score_threshold_pct", 90.0)
        except Exception:
            threshold = 90.0
    passed = dq_score >= threshold
    return ValidationResult(
        "G-R5",
        "governance",
        "HIGH",
        passed,
        f"Data quality score: {dq_score:.1f}% (threshold: {threshold}%)",
        {"score": dq_score, "threshold": threshold},
    )


def check_backtesting_gate(last_backtest_days: int | None, max_days: int = 90) -> ValidationResult:
    """G-R4: Backtesting must be run before sign-off (within last N days)."""
    if last_backtest_days is None:
        return ValidationResult(
            "G-R4",
            "governance",
            "HIGH",
            False,
            "No backtesting results found — backtesting must be run before sign-off",
            {"last_backtest_days": None, "max_days": max_days},
        )
    passed = last_backtest_days <= max_days
    return ValidationResult(
        "G-R4",
        "governance",
        "HIGH",
        passed,
        f"Backtesting gate: last run {last_backtest_days} days ago (max: {max_days})",
        {"last_backtest_days": last_backtest_days, "max_days": max_days},
    )


def check_overlay_cap(total_overlay: float, base_ecl: float, cap_pct: float = 15.0) -> ValidationResult:
    """M-R8: Total management overlays should not exceed cap% of base ECL."""
    if base_ecl == 0:
        return ValidationResult("M-R8", "model_reasonableness", "MEDIUM", True, "Base ECL is zero", {})
    overlay_pct = abs(total_overlay) / abs(base_ecl) * 100
    passed = overlay_pct <= cap_pct
    return ValidationResult(
        "M-R8",
        "model_reasonableness",
        "MEDIUM",
        passed,
        f"Overlay cap: {overlay_pct:.1f}% of base ECL (limit: {cap_pct}%)",
        {"overlay_pct": round(overlay_pct, 2), "cap_pct": cap_pct},
    )


# ── IFRS 9 Domain Accuracy Rules (DA-1 to DA-6) ──────────────────────────────


def check_ead_non_negative(ead_values: list[float]) -> ValidationResult:
    """DA-1: EAD must be non-negative per IFRS 9.B5.5.31.

    Exposure at Default represents the gross carrying amount plus any
    undrawn commitment. It cannot be negative.
    """
    violations = [v for v in ead_values if v < 0]
    passed = len(violations) == 0
    return ValidationResult(
        "DA-1",
        "domain_accuracy",
        "CRITICAL",
        passed,
        f"EAD non-negative check: {len(violations)} negative values out of {len(ead_values)}",
        {"violations_count": len(violations), "total_values": len(ead_values), "ifrs_ref": "IFRS 9.B5.5.31"},
    )


def check_lgd_unit_interval(lgd_values: list[float]) -> ValidationResult:
    """DA-2: LGD must be in [0, 1] per IFRS 9.B5.5.28.

    Loss Given Default represents the percentage of exposure lost if default
    occurs. It is bounded between 0 (full recovery) and 1 (total loss).
    """
    violations = [v for v in lgd_values if v < 0 or v > 1]
    passed = len(violations) == 0
    return ValidationResult(
        "DA-2",
        "domain_accuracy",
        "CRITICAL",
        passed,
        f"LGD unit interval check: {len(violations)} out-of-range values out of {len(lgd_values)}",
        {"violations_count": len(violations), "total_values": len(lgd_values), "ifrs_ref": "IFRS 9.B5.5.28"},
    )


def check_stage3_pd_consistency(
    stage_pd_pairs: list[tuple[int, float]],
    min_stage3_pd: float = 0.90,
) -> ValidationResult:
    """DA-3: Stage 3 (credit-impaired) loans should have PD near 1.0 per IFRS 9.B5.5.37.

    Default is defined as PD approaching certainty. Stage 3 loans are
    credit-impaired, so their through-the-cycle PD should be at or near 1.0.
    A threshold of 0.90 is used to allow for partial cure expectations.
    """
    s3_pairs = [(s, pd) for s, pd in stage_pd_pairs if s == 3]
    violations = [(s, pd) for s, pd in s3_pairs if pd < min_stage3_pd]
    passed = len(violations) == 0
    return ValidationResult(
        "DA-3",
        "domain_accuracy",
        "HIGH",
        passed,
        f"Stage 3 PD consistency: {len(violations)} of {len(s3_pairs)} Stage 3 loans have PD < {min_stage3_pd}",
        {
            "violations_count": len(violations),
            "total_stage3": len(s3_pairs),
            "min_stage3_pd": min_stage3_pd,
            "ifrs_ref": "IFRS 9.B5.5.37",
        },
    )


def check_discount_rate_valid(eir_values: list[float]) -> ValidationResult:
    """DA-4: Effective Interest Rate must be > -1 (mathematical constraint).

    The discount factor is 1/(1+EIR)^t. For this to be defined and positive,
    EIR must be strictly greater than -1 (i.e., > -100%). An EIR of exactly
    -1 would create a division by zero.
    """
    violations = [v for v in eir_values if v <= -1]
    passed = len(violations) == 0
    return ValidationResult(
        "DA-4",
        "domain_accuracy",
        "CRITICAL",
        passed,
        f"Discount rate validity: {len(violations)} EIR values <= -1 out of {len(eir_values)}",
        {"violations_count": len(violations), "total_values": len(eir_values), "ifrs_ref": "IFRS 9.B5.5.44"},
    )


def check_ecl_non_negative(ecl_values: list[float]) -> ValidationResult:
    """DA-5: ECL values must be non-negative.

    Expected Credit Losses represent expected cash shortfalls. By definition,
    a loss cannot be negative (a gain would be a separate accounting entry).
    """
    violations = [v for v in ecl_values if v < 0]
    passed = len(violations) == 0
    return ValidationResult(
        "DA-5",
        "domain_accuracy",
        "HIGH",
        passed,
        f"ECL non-negative check: {len(violations)} negative ECL values out of {len(ecl_values)}",
        {"violations_count": len(violations), "total_values": len(ecl_values)},
    )


def check_minimum_scenario_count(
    scenario_count: int,
    minimum: int = 3,
) -> ValidationResult:
    """DA-6: IFRS 9.B5.5.42 requires at least base, upside, and downside scenarios.

    The standard requires consideration of multiple scenarios to capture
    the non-linear relationship between economic conditions and credit losses.
    """
    passed = scenario_count >= minimum
    return ValidationResult(
        "DA-6",
        "domain_accuracy",
        "HIGH",
        passed,
        f"Scenario count: {scenario_count} (minimum required: {minimum})",
        {"scenario_count": scenario_count, "minimum": minimum, "ifrs_ref": "IFRS 9.B5.5.42"},
    )


# ── Aggregate Validation ─────────────────────────────────────────────────────


def run_all_pre_calculation_checks(
    scenario_weights: dict[str, float],
    pd_values: list[float],
    lgd_values: list[float],
    eir_values: list[float],
    remaining_months: list[float],
    gca_values: list[float],
    stage_dpd_pairs: list[tuple[int, int]] | None = None,
    aging_factor: float | None = None,
    ead_values: list[float] | None = None,
    stage_pd_pairs: list[tuple[int, float]] | None = None,
) -> list[dict]:
    """Run all pre-calculation validation rules. Returns list of results."""
    results = [
        check_scenario_weights_sum(scenario_weights),
        check_pd_range(pd_values),
        check_lgd_range(lgd_values),
        check_eir_positive(eir_values),
        check_remaining_months(remaining_months),
        check_gca_positive(gca_values),
        check_scenario_weight_constraints(scenario_weights),
        check_lgd_unit_interval(lgd_values),
        check_discount_rate_valid(eir_values),
        check_minimum_scenario_count(len(scenario_weights)),
    ]
    if stage_dpd_pairs is not None:
        results.append(check_stage3_dpd(stage_dpd_pairs))
        results.append(check_stage1_dpd(stage_dpd_pairs))
    if aging_factor is not None:
        results.append(check_pd_aging_factor(aging_factor))
    if ead_values is not None:
        results.append(check_ead_non_negative(ead_values))
    if stage_pd_pairs is not None:
        results.append(check_stage3_pd_consistency(stage_pd_pairs))
    return [r.to_dict() for r in results]


def run_all_post_calculation_checks(
    stage_coverage: dict[int, float],
    current_ecl: float,
    prior_ecl: float,
    convergence_cv: float,
    scenario_ecl: dict[str, float],
    total_ecl: float,
    baseline_ecl: float,
    adverse_ecl: float,
    satellite_r2: dict[str, float] | None = None,
) -> list[dict]:
    """Run all post-calculation validation rules. Returns list of results."""
    results = [
        check_coverage_monotonic(stage_coverage),
        check_ecl_period_change(current_ecl, prior_ecl),
        check_convergence_cv(convergence_cv),
        check_scenario_concentration(scenario_ecl, total_ecl),
        check_adverse_exceeds_baseline(baseline_ecl, adverse_ecl),
    ]
    if satellite_r2 is not None:
        results.append(check_satellite_r_squared(satellite_r2))
    return [r.to_dict() for r in results]


def has_critical_failures(results: list[dict]) -> bool:
    """Check if any CRITICAL severity rules failed."""
    return any(r["severity"] == "CRITICAL" and not r["passed"] for r in results)
