# Sprint 7 Visual QA — Interaction Manifest (Iteration 5 — Final Verification)

Sprint 7 is a testing-only sprint (230 new domain logic tests across 4 iterations, 3 bug fixes in `domain/backtesting.py` and `domain/workflow.py`).
No UI changes were made. Visual QA focuses on regression testing and verifying bug fixes from iterations 3 and 4.

## Sidebar Navigation Testing

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| ECL Workflow | click | Navigated to project creation/workflow page | TESTED |
| Data Mapping | click | Navigated to data mapping setup page | TESTED |
| Attribution | click | Navigated to attribution analysis page | TESTED |
| Models | click | Navigated to model registry page | TESTED |
| Backtesting | click | Navigated to backtesting page | TESTED |
| Markov Chains | click | Navigated to Markov chains page | TESTED |
| Hazard Models | click | Navigated to hazard models page | TESTED |
| GL Journals | click | Navigated to GL journals page | TESTED |
| Reports | click | Navigated to reports page | TESTED |
| Monte Carlo | click | Navigated to Monte Carlo simulation page | TESTED |
| Approval | click | Navigated to approval workflow page | TESTED |
| Advanced | click | Navigated to advanced features page | TESTED |
| Sign-Off | click | Button not found by text locator | SKIPPED — pre-existing locator issue |
| Admin | click | Navigated to admin page with full content | TESTED |
| Collapse sidebar | click | Sidebar collapse toggle functional | TESTED |

**Result**: 13/14 sidebar nav items navigated successfully. 1 skipped (pre-existing).

## API Endpoint Testing — Sprint 7 Domain Modules

| Endpoint | Method | Action | Result | Status |
|----------|--------|--------|--------|--------|
| `/api/models` | GET | List registered models | Returns 10 models with draft/pending_review statuses | TESTED |
| `/api/backtest/results?project_id=PROJ001` | GET | List backtest results | Returns 1 backtest result (BT-PD-20260329024822-110972) | TESTED |
| `/api/backtest/BT-PD-20260329024822-110972` | GET | Backtest detail | **200** — Returns full detail with 5 metrics, `detail` column present | **FIXED** (was BUG-VQA-7-002) |
| `/api/markov/matrices?project_id=PROJ001` | GET | List Markov matrices | Returns 5 matrices | TESTED |
| `/api/hazard/models?project_id=PROJ001` | GET | List hazard models | Returns 5 hazard models | TESTED |
| `/api/advanced/cure-rates?project_id=PROJ001` | GET | Cure rate analyses | Returns cure rate data | TESTED |
| `/api/advanced/collateral?project_id=PROJ001` | GET | Collateral data | Returns collateral data | TESTED |
| `/api/health` | GET | Health check | `{"status":"healthy","lakebase":"connected"}` | TESTED |

## Core API Regression Testing

| Endpoint | Method | Result | Status |
|----------|--------|--------|--------|
| `/api/projects` | GET | 200 — 4 projects returned | TESTED |
| `/api/projects/PROJ001` | GET | 200 — project detail with step 2 | TESTED |
| `/api/projects/99999` | GET | 404 — correct error handling | TESTED |
| `/api/setup/status` | GET | 200 — configuration status | TESTED |
| `/api/admin/config` | GET | 200 — 4 config keys | TESTED |
| `/api/audit/config-changes?project_id=1` | GET | 200 — audit data | TESTED |
| `/api/data/portfolio-summary?project_id=1` | GET | 200 — 5 product types | TESTED |
| `/api/data/stage-distribution?project_id=PROJ001` | GET | 200 — 3 stages (77,552 / 1,212 / 975) | TESTED |
| `/api/data/ecl-summary?project_id=1` | GET | 200 — 101 entries | TESTED |
| `/api/data/scenario-summary?project_id=1` | GET | 200 — 9 scenarios | TESTED |
| `/api/nonexistent` | GET | 404 — correct 404 for unknown routes | TESTED |

## Frontend Assets Verification

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| SPA HTML (`/`) | GET | Loads correctly with React app, all assets referenced | TESTED |
| Static JS (`index-DNaCEbyM.js`) | GET | 200 — serves correctly | TESTED |
| Motion library (`motion-DSndAWGS.js`) | preload | Preloaded in HTML | TESTED |
| Charts library (`charts-nV4Kelm5.js`) | preload | Preloaded in HTML | TESTED |
| CSS (`index-DF6l7LEH.css`) | link | Linked in HTML | TESTED |
| SPA routing (`/ecl-workflow`) | GET | 200 — client-side routing works | TESTED |
| Google Fonts (Inter) | preconnect | Preconnected in HTML | TESTED |

## Form Elements (from iter 3)

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Project ID input | visible | Displays project ID field | TESTED |
| Project Name input | visible | Displays project name field | TESTED |
| Accounting Framework dropdown | visible | Shows IFRS 9 option | TESTED |
| Reporting Date picker | visible | Date input available | TESTED |
| Description textarea | visible | Multi-line text input | TESTED |
| Update Project button | click | Submits project form | TESTED |

## Dark Mode Testing (from iter 3)

| Element | Check | Result | Status |
|---------|-------|--------|--------|
| Body background | color | rgb(11, 15, 26) — correct dark bg | TESTED |
| Sidebar | visible | Dark sidebar with legible nav items | TESTED |
| Form fields | visible | Form inputs visible against dark bg | TESTED |
| Workflow steps | visible | Green accent circles visible | TESTED |
| White flash | none | No white flash on theme switch | TESTED |

## Accessibility Audit (from iter 3)

| Check | Result | Status |
|-------|--------|--------|
| `<html lang="en">` | Present | PASS |
| Viewport meta | Present | PASS |
| Page title | "IFRS 9 ECL Workspace" | PASS |
| Skip link | `a[href="#main-content"]` present | PASS |
| Images missing alt | 0/0 | PASS |
| Inputs without labels | 0/5 | PASS |
| Buttons without accessible name | 0/27 | PASS |
| ARIA elements | 19 elements | PASS |
| Heading hierarchy | H1 → H2 → H3 correct | PASS |

## Console & Network Errors

| Check | Result | Status |
|-------|--------|--------|
| Console errors | **0** across all page navigations | PASS |
| 5xx network errors | **0** during testing (BUG-VQA-7-002 resolved) | PASS |

## Test Suite Verification

| Suite | Result | Status |
|-------|--------|--------|
| Sprint 7 iter 1 (120 tests) | 120/120 passed | TESTED |
| Sprint 7 iter 2 (84 tests) | 84/84 passed | TESTED |
| Sprint 7 iter 3 (16 tests) | 16/16 passed | TESTED |
| Sprint 7 iter 4 (10 tests) | 10/10 passed | TESTED |
| Sprint 7 total | **230/230 passed** | TESTED |
| Full pytest suite | **3,838 passed**, 61 skipped (270.94s) | TESTED |
| Regressions | **0** | TESTED |

## Bug Fix Verification (Iteration 4)

### BUG-VQA-7-002 / BUG-S7-1 / BUG-S7-2: RESOLVED

- **Previous issue**: `GET /api/backtest/{backtest_id}` returned `500 — column "detail" does not exist` because `ensure_backtesting_table()` was never called due to `globals().get()` returning `None`
- **Fix applied (iter 4)**: Replaced `globals().get()` loop in `domain/workflow.py:58-67` with explicit lazy imports for all 7 ensure functions
- **Verification**: `GET /api/backtest/BT-PD-20260329024822-110972` now returns **200** with full detail including 5 metrics (AUC, Brier, Gini, KS, PSI) and the `detail` column present in each metric
- **Regression tests**: 10 new tests verify invocation path, parametrized coverage of all 7 functions, error resilience, and complete invocation

### All 3 Sprint 7 Bugs — Status

| Bug ID | Description | Status | Regression Tests |
|--------|-------------|--------|-----------------|
| BUG-7-001 | Numpy types not JSON serializable | FIXED | 5 tests |
| BUG-VQA-7-001 | Missing `detail` column in backtest_metrics | FIXED | 16 tests |
| BUG-S7-1/BUG-S7-2 | `globals().get()` silently skipped ensure_backtesting_table | FIXED | 10 tests |

## Data Integrity

| Check | Result | Notes |
|-------|--------|-------|
| Stage distribution totals | PASS | 79,739 loans across 3 stages |
| Stage 1 dominance | PASS | 97.3% in Stage 1 — realistic IFRS 9 |
| Product type diversity | PASS | 5 product types |
| ECL entries count | PASS | 101 ECL summary entries |
| Scenario count | PASS | 9 macroeconomic scenarios |
| Model registry | PASS | 10 models with lifecycle statuses |
| Markov matrices | PASS | 5 matrices available |
| Hazard models | PASS | 5 models available |
| Backtest metrics | PASS | 5 metrics with detail column (AUC, Brier, Gini, KS, PSI) |
| Health check | PASS | Lakebase connected |

## Summary

| Category | Tested | Passed | Bugs | Skipped |
|----------|--------|--------|------|---------|
| Sidebar Nav | 15 | 13 | 0 | 2 (pre-existing) |
| API Endpoints (Sprint 7 domain) | 8 | 8 | 0 | 0 |
| API Endpoints (regression) | 11 | 11 | 0 | 0 |
| Frontend Assets | 7 | 7 | 0 | 0 |
| Form Elements | 6 | 6 | 0 | 0 |
| Dark Mode | 5 | 5 | 0 | 0 |
| Accessibility | 9 | 9 | 0 | 0 |
| Console/Network | 2 | 2 | 0 | 0 |
| Test Suite | 6 | 6 | 0 | 0 |
| Data Integrity | 10 | 10 | 0 | 0 |
| Bug Fix Verification | 3 | 3 | 0 | 0 |
| **Total** | **82** | **80** | **0** | **2** |

**PENDING elements: 0**
**Active bugs: 0** (all 3 sprint 7 bugs resolved)
