# Integration Test Report — Run 7

**Date**: 2026-03-30
**Agent**: Integration Agent
**Scope**: Full regression sweep and cross-feature verification after Run 7 refactoring

---

## 1. Test Suite Results

| Metric | Value |
|--------|-------|
| **Total tests** | 1,086 |
| **Passed** | 1,025 |
| **Skipped** | 61 |
| **Failed** | 0 |
| **Duration** | ~65s |

**Verdict**: PASS — zero failures across the entire test suite.

The 61 skipped tests are expected (typically database-dependent tests that require a live Lakebase connection).

---

## 2. Cross-Module Import Verification

All 11 refactored module groups import and resolve correctly with `PYTHONPATH=app`:

| Module | Key Exports Verified | Status |
|--------|---------------------|--------|
| `ecl_engine` | `run_simulation`, `aggregate_results`, `get_defaults` | PASS |
| `reporting.reports` | `generate_ifrs7_disclosure`, `generate_ecl_movement_report` | PASS |
| `domain.hazard` | `estimate_hazard_model`, `compute_survival_curve` | PASS |
| `domain.validation_rules` | `run_all_pre_calculation_checks`, `check_ead_non_negative`, `check_pd_range`, `check_lgd_range` | PASS |
| `domain.backtesting` | `run_backtest` | PASS |
| `governance.rbac` | `create_approval_request`, `approve_request`, `reject_request` | PASS |
| `routes.*` (projects, simulation, data, reports) | `router` objects | PASS |
| `admin_config` | `get_config`, `save_config` | PASS |
| `jobs` | `trigger_full_pipeline`, `get_run_status` | PASS |
| `db.pool` | `query_df`, `execute` | PASS |
| `middleware.auth` | `get_current_user` | PASS |

**Note**: The `backend.py` module is a monolith re-exporting from sub-modules. It does not export a FastAPI `app` object itself — that lives in `app.py` (the entrypoint). This is by design.

---

## 3. Frontend TypeScript Compilation

```
npx tsc --noEmit -> exit code 0, no errors
```

**Verdict**: PASS — all TypeScript files compile cleanly with no type errors.

---

## 4. Domain Accuracy Tests (Sprint 3)

Ran `tests/unit/test_domain_accuracy_sprint3.py`:

| Test Class | Tests | Status |
|-----------|-------|--------|
| TestEadNonNegative | 5 | PASS |
| TestLgdUnitInterval | 6 | PASS |
| TestStage3PdConsistency | 6 | PASS |
| TestDiscountRateValid | 6 | PASS |
| TestEclNonNegative | 4 | PASS |
| TestMinimumScenarioCount | 5 | PASS |
| TestPreCalcWithDomainRules | 6 | PASS |
| **Total** | **40** | **ALL PASS** |

---

## 5. Regression Sweep Summary

All test files executed without failure:

- **Unit tests**: ECL engine, validation rules, domain accuracy, hazard models, backtesting, reporting, governance — all pass
- **Integration tests**: Cross-module data flow between ecl_engine, domain, reporting, and governance modules — verified via import chains and test suite
- **Frontend**: TypeScript compilation clean, no regressions

---

## 6. Observations

1. **Module naming**: Some function names differ from what earlier harness phases assumed (e.g., `run_backtest` not `run_pd_backtest`, `get_config` not `get_admin_config`, `trigger_full_pipeline` not `submit_job_run`). The tests and actual codebase are consistent with each other — no broken references.

2. **Backend monolith**: `backend.py` re-exports ~200+ symbols from sub-modules. This works but is a maintenance concern. The refactored sub-modules (`domain/`, `governance/`, `reporting/`, `routes/`, `db/`, `middleware/`) are the canonical import paths.

3. **No `app` export from `backend`**: The FastAPI application object is created in `app.py`, not `backend.py`. Import path is `from app import app`.

---

## 7. Overall Verdict

**PASS** — Full regression sweep confirms:
- 1,025 tests passing, 0 failures
- All refactored modules import correctly
- Frontend TypeScript compiles without errors
- Domain accuracy tests (40/40) all pass
- No regressions detected from Run 7 refactoring
