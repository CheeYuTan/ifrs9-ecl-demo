# IFRS 9 ECL Platform — SME Domain Brief (Run 4)

**Prepared by:** SME Agent (IFRS 9 / Credit Risk Domain Expert)
**Date:** 2026-03-29
**Application:** Expected Credit Loss Platform (React + FastAPI + Lakebase)
**Current Maturity:** ~80% production ready (422 tests, 13 domain modules, 16 route modules)

---

## 1. Assessment Summary

The platform has a strong technical foundation from Run 2 (modularization, backtesting, RBAC, attribution, model registry, validation rules). However, a deep code audit reveals **13 specific issues** that need fixing to reach production quality.

## 2. Critical Findings

### 2.1 Validation Rules Are Dead Code (CRITICAL)
The 16 validation rules in `validation_rules.py` are **never called from any route handler**. The simulation route has its own ad-hoc validation with different thresholds. This means the entire validation framework is unused.

**Fix:** Wire `run_all_pre_calculation_checks()` into the simulation route before ECL execution, and `run_all_post_calculation_checks()` after. Add the 7 missing rules (D7, D8, D9, D10, M-R3, M-R7, G-R4).

### 2.2 Advanced Features Are Entirely Synthetic (HIGH)
`domain/advanced.py` uses `random.seed(42/43/44)` with hardcoded base rates for cure rates, CCF, and collateral haircuts. No actual portfolio data is used for computation despite the functions claiming to be data-driven.

**Fix:** Compute cure rates from actual Stage 2/3 → Stage 1 transitions in the migration data. Compute CCF from drawn vs limit data. Compute haircuts from collateral recovery data. When data is insufficient, report `"status": "insufficient_data"` (matching the backtesting pattern).

### 2.3 Markov Default Rate Hardcoded (HIGH)
`markov.py` line 107: `default_rate = 0.15` for Stage 3 → Default transitions. Should be estimated from `historical_defaults` table.

### 2.4 Attribution Model Changes Is a Plug Figure (HIGH)
`attribution.py` computes `model_changes` as the residual after all other components, making the reconciliation check a tautology (it always passes). The overlay allocation is hardcoded 50/30/20 across stages.

### 2.5 Terminology: `current_lifetime_pd` (MEDIUM)
The field is used as an annual PD (converted quarterly via `1-(1-PD)^0.25`) but named "lifetime" PD. Rename to `current_annual_pd` or add clear documentation.

### 2.6 Silent Exception Swallowing (MEDIUM)
`ecl_engine.py` lines 61-62, 74-75: `except Exception: pass` silently swallows configuration errors. Should log warnings.

### 2.7 LGD Traffic Light Thresholds Missing (MEDIUM)
`backtesting.py` line 101: LGD metrics (MAE, RMSE, Mean_Bias) have no thresholds defined, so they always default to Green.

## 3. Test Coverage Gaps

### 3.1 Modules with ZERO Tests
- `domain/markov.py` (9 functions)
- `domain/hazard.py` (12 functions)
- `domain/advanced.py` (10 functions)
- `domain/model_runs.py` (16 functions)
- `domain/queries.py` (28 functions)
- `reporting/gl_journals.py` (10 functions)

### 3.2 Modules with Partial Tests
- `domain/attribution.py` — main `compute_attribution()` untested
- `domain/model_registry.py` — `register_model`, `update_model_status`, `promote_champion` untested
- `governance/rbac.py` — approval workflow functions untested
- `domain/backtesting.py` — `run_backtest` main runner untested

## 4. Priority Actions for Run 4

| Priority | Action | Impact |
|----------|--------|--------|
| 1 | Wire validation rules into routes + add missing 7 rules | Fixes dead code, enables enforcement |
| 2 | Add tests for untested domain modules (markov, hazard, advanced, gl_journals, model_runs) | 100+ new tests → 500+ total |
| 3 | Fix advanced.py synthetic data → honest reporting | Audit credibility |
| 4 | Fix Markov hardcoded default rate | Domain accuracy |
| 5 | Fix attribution plug figure + overlay allocation | IFRS 7.35I compliance |
| 6 | Add LGD traffic light thresholds | Backtesting completeness |
| 7 | Fix terminology (`current_lifetime_pd`) | Auditor clarity |
| 8 | Add logging for swallowed exceptions | Production reliability |
