# Sprint 2 Evaluation

**Sprint**: 2 — Backend API: Simulation & Satellite Model Tests
**Date**: 2026-04-02
**Quality Target**: 9.5/10
**Iteration**: 2

## Test Suite Results

| Suite | Result |
|-------|--------|
| Sprint 2 tests | **150 passed** in 0.70s |
| Full backend suite | **2868 passed, 61 skipped, 0 failed** in 115s |
| Regressions | **Zero** |

## Live Endpoint Verification (Independent)

All 18 endpoints independently verified against live dev server (localhost:8000):

### Simulation Endpoints (6/6 verified)
| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| `/api/simulate` | POST | 400 | Correct — pre-calc validation blocks (project at step 2, no scenario weights configured) |
| `/api/simulation-defaults` | GET | 200 | Returns full defaults: n_simulations, correlations, 8 scenario weights, 9 scenarios, 5 products |
| `/api/simulate-validate` (valid) | POST | 200 | `{valid: true, estimated_seconds: 25.0, estimated_memory_mb: 1344.0}` |
| `/api/simulate-validate` (n_sims too high) | POST | 200 | `{valid: false, errors: ["Maximum 50,000 simulations"]}` |
| `/api/simulate-validate` (weights != 1) | POST | 200 | `{valid: false, errors: ["Scenario weights must sum to 100%"]}` |
| `/api/simulate-validate` (pd_floor >= pd_cap) | POST | 200 | `{valid: false, errors: ["PD Floor must be less than PD Cap"]}` |
| `/api/simulate-validate` (lgd_floor >= lgd_cap) | POST | 200 | `{valid: false, errors: ["LGD Floor must be less than LGD Cap"]}` |
| `/api/simulate-validate` (n_sims < 100) | POST | 200 | `{valid: false, errors: ["Minimum 100 simulations required"]}` |
| `/api/simulate-validate` (boundary 50000) | POST | 200 | `{valid: true}` with warning about duration |
| `/api/simulate-stream` | POST | 200 | SSE stream with keepalive events |
| `/api/simulate-job` | POST | 200 | Returns `{run_id, job_id, run_url}` |
| `/api/simulation/compare` (missing params) | GET | 422 | Correct — `missing run_a, run_b` |
| `/api/simulation/compare` (nonexistent) | GET | 404 | Correct — `"Run(s) not found: fake1, fake2"` |

### Satellite Endpoints (12/12 verified)
| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| `/api/data/satellite-model-comparison` | GET | 200 | Returns model data with r_squared, rmse, aic, bic, coefficients |
| `/api/data/satellite-model-selected` | GET | 200 | Returns selected models with selection_reason |
| `/api/model-runs` | GET | 200 | Returns run history with parsed JSON fields |
| `/api/model-runs/{run_id}` (nonexistent) | GET | 404 | Correct |
| `/api/model-runs` (invalid POST) | POST | 422 | Correct — `{missing: run_id}` |
| `/api/data/cohort-summary` | GET | 200 | Returns cohort statistics |
| `/api/data/cohort-summary/{product}` | GET | 200 | Product-specific cohort data |
| `/api/data/drill-down-dimensions` | GET | 200 | Returns dimension list |
| `/api/data/ecl-by-cohort` (with product) | GET | 200 | Returns ECL by cohort |
| `/api/data/ecl-by-cohort` (missing product) | GET | 422 | Correct — `Field required` |
| `/api/data/stage-by-cohort` | GET | 200 | Returns stage distribution |
| `/api/data/portfolio-by-cohort` | GET | 200 | Returns portfolio metrics |
| `/api/data/ecl-by-product-drilldown` | GET | 200 | Returns 5 products with loan_count, total_gca, total_ecl, coverage_ratio |

## Contract Criteria Results

### Simulation Routes (20/20 criteria pass)
- [x] POST /api/simulate — happy path returns ecl_by_product, scenario_summary, loss_allowance_by_stage, run_metadata
- [x] POST /api/simulate — returns 400 when pre-calculation validation has critical failures
- [x] POST /api/simulate — returns 500 when ecl_engine.run_simulation raises
- [x] GET /api/simulation-defaults — returns flat structure with n_simulations, pd_lgd_correlation, scenario_weights, etc.
- [x] GET /api/simulation-defaults — returns 500 when ecl_engine.get_defaults raises
- [x] POST /api/simulate-stream — returns SSE text/event-stream with progress events then result
- [x] POST /api/simulate-stream — SSE stream emits error event on simulation failure
- [x] POST /api/simulate-job — triggers Databricks job and returns job metadata
- [x] POST /api/simulate-job — returns 500 when jobs module raises
- [x] POST /api/simulate-validate — valid params return {valid: true, errors: [], warnings: []}
- [x] POST /api/simulate-validate — pd_floor >= pd_cap returns error
- [x] POST /api/simulate-validate — lgd_floor >= lgd_cap returns error
- [x] POST /api/simulate-validate — n_simulations < 100 returns error
- [x] POST /api/simulate-validate — n_simulations > max_sims returns error
- [x] POST /api/simulate-validate — scenario weights not summing to 1.0 returns error
- [x] POST /api/simulate-validate — high n_sims, high correlation, high aging produce warnings
- [x] POST /api/simulate-validate — returns estimated_seconds and estimated_memory_mb
- [x] GET /api/simulation/compare — compares two runs by deltas and product deltas
- [x] GET /api/simulation/compare — returns 404 when run not found
- [x] GET /api/simulation/compare — returns 500 on unexpected error

### Satellite & Model Run Routes (17/17 criteria pass)
- [x] GET /api/data/satellite-model-comparison — returns records from backend
- [x] GET /api/data/satellite-model-comparison?run_id=X — filters by run_id
- [x] GET /api/data/satellite-model-selected — returns selected model records
- [x] GET /api/data/satellite-model-selected?run_id=X — filters by run_id
- [x] GET /api/model-runs — returns list with JSON-parsed fields
- [x] GET /api/model-runs?run_type=satellite_model — filters by type
- [x] GET /api/model-runs/{run_id} — returns serialized run
- [x] GET /api/model-runs/{run_id} — returns 404 when not found
- [x] POST /api/model-runs — saves and returns new run
- [x] GET /api/data/cohort-summary — returns cohort data
- [x] GET /api/data/cohort-summary/{product} — returns product-specific cohorts
- [x] GET /api/data/drill-down-dimensions — returns available dimensions
- [x] GET /api/data/drill-down-dimensions?product=X — product-specific dimensions
- [x] GET /api/data/ecl-by-cohort — returns ECL drill-down by dimension
- [x] GET /api/data/stage-by-cohort — returns stage distribution by cohort
- [x] GET /api/data/portfolio-by-cohort — returns portfolio by dimension
- [x] GET /api/data/ecl-by-product-drilldown — returns ECL grouped by product

### Edge Cases & Domain Tests (8/8 criteria pass)
- [x] Simulation with n_simulations at boundary (100, 50000)
- [x] Validation with scenario weights at tolerance boundary (0.999 vs 0.5)
- [x] _transform_simulation_result handles missing/empty stage_summary, scenario_results
- [x] _build_product_deltas with overlapping and non-overlapping product sets
- [x] Satellite routes return 500 on backend exceptions
- [x] Model run JSON field parsing handles malformed JSON gracefully
- [x] Empty DataFrames return empty lists (not errors)
- [x] SimulationConfig default values are correct

## Scores

| Criterion | Weight | Score | Notes | Remediation |
|-----------|--------|-------|-------|-------------|
| Feature Completeness | 25% | 10/10 | All 45 contract acceptance criteria pass. 18/18 endpoints tested live + 150 automated tests. | — |
| Code Quality & Architecture | 15% | 9/10 | Test file at 1713 lines is monolithic but well-organized with 28 test classes, clear section separators, and good helper factories. Test files naturally exceed the 200-line production code limit. | — |
| Testing Coverage | 15% | 10/10 | 150 tests covering all 18 endpoints + 10 internal helpers. Boundary values (50000/50001), tolerance boundaries (0.999/1.001/0.5), Decimal/NaN serialization, empty DataFrames, malformed JSON, all error codes (400/404/422/500). Iteration 2 added 22 tests to close gap. | — |
| UI/UX Polish | 20% | N/A | Sprint 2 is a backend test sprint — no UI changes. Weight redistributed. | — |
| Production Readiness | 15% | 10/10 | Zero regressions (2868 total suite). All error paths return structured responses with appropriate HTTP codes. NaN/Inf serialized to null. Decimal types handled. SSE has no-cache headers. | — |
| Deployment Compatibility | 10% | 10/10 | No new dependencies. No code changes to deployed files. Test-only sprint. | — |

**Weight redistribution** (UI/UX N/A, redistributed proportionally):
| Criterion | Adjusted Weight | Score |
|-----------|----------------|-------|
| Feature Completeness | 31.25% | 10 |
| Code Quality & Architecture | 18.75% | 9 |
| Testing Coverage | 18.75% | 10 |
| Production Readiness | 18.75% | 10 |
| Deployment Compatibility | 12.50% | 10 |

**Weighted Total**: (0.3125 x 10) + (0.1875 x 9) + (0.1875 x 10) + (0.1875 x 10) + (0.125 x 10) = 3.125 + 1.6875 + 1.875 + 1.875 + 1.25 = **9.81/10**

## Bugs Found

**None.** All 18 endpoints behave correctly under both normal and error conditions. Error responses are structured, consistent, and use correct HTTP status codes.

## Product Suggestions → New Sprints

| ID | Suggestion | Priority | Added to Backlog? |
|----|-----------|----------|-------------------|
| SUG-S2-001 | routes/simulation.py at 394 lines exceeds 200-line modularization limit — extract helpers to separate module | LOW | No — pre-existing, not in scope for QA audit sprints |
| SUG-S2-002 | SSE streaming tests can't verify real-time streaming behavior due to TestClient limitations — add integration test with actual async client | LOW | No — acknowledged limitation, minor |

## Recommendation: ADVANCE

**Score: 9.81/10** — exceeds quality target of 9.5/10.

Sprint 2 delivers comprehensive test coverage for all 18 simulation and satellite model endpoints. All 45 contract acceptance criteria pass. 150 well-structured tests with meaningful assertions covering happy paths, error cases, boundary values, domain validation, serialization edge cases, and internal helpers. Zero regressions across the 2868-test full suite. All endpoints verified independently against the live dev server.
