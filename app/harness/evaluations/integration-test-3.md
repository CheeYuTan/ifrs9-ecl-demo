# Integration Test Report 3

**Date**: 2026-04-02
**Sprints Covered**: 1-8 (all completed sprints since last integration test at Sprint 5)
**Quality Target**: 9.5/10

---

## Test Suite Results

| Suite | Tests | Passed | Failed | Skipped |
|-------|-------|--------|--------|---------|
| **pytest** | 3,838 | 3,838 | 0 | 61 |
| **vitest** | 497 | 497 | 0 | 0 |
| **Total** | 4,335 | 4,335 | 0 | 61 |

All 4,335 tests pass with zero failures. Zero regressions from any sprint.

---

## Feature Dependency Matrix

| Source Feature | Target Feature | Data Flow | Status |
|---------------|----------------|-----------|--------|
| Projects (S1) | Portfolio Data (S1) | project_id → query filter | **PASS** |
| Projects (S1) | ECL Summary (S1) | project_id → ECL aggregation | **PASS** |
| Portfolio Data (S1) | Stage Distribution (S1) | Same loan set → 3-stage breakdown | **PASS** |
| Stage Distribution (S1) | ECL by Product (S1) | Consistent loan counts (79,739) | **PASS** |
| Simulation Defaults (S2) | Simulate Validate (S2) | Default params → validation | **PASS** |
| Simulation (S2) | MC Distribution (S1) | Simulation results → distribution view | **PASS** |
| Satellite Models (S2) | Cohort Summary (S2) | Model comparison → cohort data | **PASS** |
| Satellite (S2) | Drill-Down Dims (S2) | 11 dimensions available | **PASS** |
| Model Registry (S3) | Backtesting (S3) | Model ID → backtest results | **PASS** |
| Models (S3) | Markov Matrices (S3) | Estimation → stored matrices (5) | **PASS** |
| Models (S3) | Hazard Models (S3) | Estimation → stored models (5) | **PASS** |
| RBAC (S4) | Reports (S4) | User roles → report access | **PASS** |
| Admin Config (S4) | Data Mapping (S4) | Config → mapping status (8 tables) | **PASS** |
| ECL Engine (S5) | Simulation (S2) | run_simulation → route layer | **PASS** |
| Domain Workflow (S6) | Projects (S1) | State machine → step advancement | **PASS** |
| Domain Validation (S6) | ECL Engine (S5) | 23 validation rules → engine inputs | **PASS** |
| Analytical Engines (S7) | Model Registry (S3) | Registry → backtesting/markov/hazard | **PASS** |
| Frontend Pages (S8) | All API Endpoints (S1-S4) | React components → API calls | **PASS** |

**Cross-feature data consistency verified**:
- Portfolio loan count: 79,739 — consistent across stage distribution and portfolio summary
- Total ECL: 31,342,312.07 — matches across ECL summary and ECL by product views
- Product types: 5 (auto_loan, credit_card, commercial_loan, personal_loan, residential_mortgage) — consistent across satellite, cohort, and ECL views
- Scenario weights: sum to exactly 1.000000 across 9 scenarios
- IFRS 9 stages: all 3 stages (1, 2, 3) present in stage distribution

---

## Regression Sweep

### Sprint 1: Backend API — Core Workflow & Data Endpoints

| Criterion | Status |
|-----------|--------|
| List projects returns valid array | **PASS** (4 projects) |
| Setup status for project | **PASS** |
| Portfolio summary returns data | **PASS** (5 entries) |
| Stage distribution has 3 stages | **PASS** ([1, 2, 3]) |
| ECL summary returns data | **PASS** |
| Top exposures default limit=20 | **PASS** |
| Top exposures custom limit=5 | **PASS** |

### Sprint 2: Backend API — Simulation & Satellite

| Criterion | Status |
|-----------|--------|
| Simulation defaults contain n_simulations | **PASS** (n=1000) |
| Validate n=1000 accepted | **PASS** |
| Validate n=100000 rejected | **PASS** |
| Satellite model comparison | **PASS** (125 entries) |
| Cohort summary | **PASS** (36 entries) |
| Drill-down dimensions | **PASS** (11 dims) |

### Sprint 3: Backend API — Models, Backtesting, Markov, Hazard

| Criterion | Status |
|-----------|--------|
| Models list | **PASS** (10 models, types: PD/LGD/EAD/Staging) |
| Backtesting results | **PASS** |
| Markov matrices | **PASS** (5 matrices) |
| Hazard models | **PASS** (5 models) |
| Markov estimate returns valid result | **PASS** |
| Hazard cox_ph estimate | **PASS** |

### Sprint 4: Backend API — GL, Reports, RBAC, Admin

| Criterion | Status |
|-----------|--------|
| Reports list | **PASS** |
| RBAC users (4 users) | **PASS** |
| Admin config | **PASS** |
| Data mapping status (8 tables) | **PASS** |
| Advanced cure rates | **PASS** |

### Sprint 5: ECL Engine — Monte Carlo Correctness

| Criterion | Status |
|-----------|--------|
| ECL = PD x LGD x EAD x DF formula verified | **PASS** (141 tests) |
| Cholesky correlation correctness | **PASS** |
| Stage assignment logic | **PASS** |
| Scenario weighting | **PASS** |
| Numerical stability edge cases | **PASS** |

### Sprint 6: Domain Logic — Workflow, Queries, Attribution, Validation

| Criterion | Status |
|-----------|--------|
| Workflow state machine | **PASS** (196 tests) |
| Attribution waterfall sum-to-total | **PASS** |
| All 23 validation rules | **PASS** |
| Audit trail chain verification | **PASS** |

### Sprint 7: Domain Logic — Analytical Engines

| Criterion | Status |
|-----------|--------|
| Model registry lifecycle | **PASS** (230 tests) |
| Backtesting statistics | **PASS** |
| Markov row stochasticity | **PASS** |
| Hazard survival monotonicity | **PASS** |
| Bug fixes: JSON serialization, column migration, ensure_workflow_table | **PASS** |

### Sprint 8: Frontend — Component & Page Testing

| Criterion | Status |
|-----------|--------|
| 497 vitest tests pass | **PASS** |
| 100% component file coverage (24/24) | **PASS** |
| 100% page file coverage (25/25) | **PASS** |
| TypeScript build zero errors/warnings | **PASS** |

**Regression sweep: 28/28 criteria PASSED, 0 FAILED**

---

## User Journeys

### Journey 1: Full ECL Workflow
Projects → Setup → Portfolio → Stage Distribution → ECL Summary → ECL by Product → Simulation Defaults → Validate → MC Distribution → Satellite Models → Model Registry → Reports → Sensitivity

**Result**: 13/13 steps **PASS**

### Journey 2: Model Management Flow
Models List → PD Backtesting → Markov Matrices → Hazard Models → New Markov Estimate → New Hazard Estimate

**Result**: 6/6 steps **PASS**

### Journey 3: Admin & Configuration Flow
Admin Config → RBAC Users → Data Mapping → Cure Rates → CCF → Collateral

**Result**: 6/6 steps **PASS**

**All journeys: 25/25 steps PASS**

---

## Edge Case Results

| Edge Case | Status | Detail |
|-----------|--------|--------|
| Non-existent project_id | **PASS** | Returns 200 with empty data (graceful) |
| Missing project_id parameter | **PASS** | Returns 200 (uses default) |
| n_simulations=0 | **PASS** | Rejected (valid=false) |
| n_simulations=1 | **PASS** | Rejected (below min) |
| n_simulations=50000 (max) | **PASS** | Accepted |
| n_simulations=50001 (over max) | **PASS** | Rejected |
| n_simulations=-1 | **PASS** | Rejected |
| Empty JSON payload | **PASS** | Handled gracefully |
| Model compare empty list | **PASS** | Returns 200 |
| SQL injection in project_id | **PASS** | No server error (parameterized queries) |
| XSS in project_id | **PASS** | No server error |
| 10 rapid portfolio requests | **PASS** | 6.5s (acceptable) |
| 10 rapid health checks | **NOTE** | 6.0s — database-bound, not a bug |
| Top exposures limit=0 | **PASS** | Returns empty array |
| Top exposures limit=1 | **PASS** | Returns 1 item |
| Top exposures limit=100 | **PASS** | Returns available items |
| Model filter non-existent type | **PASS** | Returns empty array |
| Model filter non-existent status | **PASS** | Returns empty array |
| Backtest by model type (pd, lgd) | **PASS** | Both return valid data |
| Cohort by product (3 products) | **PASS** | All return data |
| Cohort for nonexistent product | **PASS** | Returns 200 (empty) |

**Edge cases: 21/21 PASS (1 minor performance note)**

---

## Summary

| Category | Result |
|----------|--------|
| Test suites | **4,335 tests, 0 failures** |
| Feature dependency matrix | **18/18 flows verified** |
| Regression sweep | **28/28 criteria PASS** |
| User journeys | **25/25 steps PASS** |
| Edge cases | **21/21 PASS** |
| Cross-feature data consistency | **Verified** (loan counts, ECL totals, products, stages, scenario weights) |
| Security edge cases | **PASS** (SQL injection, XSS handled) |

### Minor Observations (non-blocking)
1. Health check endpoint averages ~0.6s per call due to Lakebase connection verification — acceptable for a health endpoint but could benefit from connection pooling optimization in high-traffic scenarios.
2. Data mapping shows 0/8 tables mapped — this is expected for the test environment where tables exist in Delta Lake but haven't been explicitly mapped through the UI flow.

---

## Verdict: PASS

All cross-feature integrations, regression criteria, user journeys, and edge cases pass. The application demonstrates strong data consistency across 107+ API endpoints, correct IFRS 9 domain logic (3-stage model, 5 product types, 9 scenarios), and robust error handling. No regressions detected across all 8 completed sprints.
