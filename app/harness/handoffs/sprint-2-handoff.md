# Sprint 2 Handoff: Backend API — Simulation & Satellite Model

## What Was Built

150 tests covering all 18 simulation and satellite model endpoints in `routes/simulation.py` (6 endpoints) and `routes/satellite.py` (12 endpoints), plus unit tests for internal helpers. Iteration 2 added 22 tests to close the 150-test contract target per evaluator feedback.

### Test Coverage by Endpoint

**Simulation Routes (routes/simulation.py)**:
- `POST /api/simulate` — 14 tests (happy path, aggregation, transforms, 400/500 errors, config passthrough, pre-checks, empty data)
- `GET /api/simulation-defaults` — 3 tests (happy path, 500 error, fallback defaults)
- `POST /api/simulate-stream` — 5 tests (SSE content type, result event, error event, headers, progress callback)
- `POST /api/simulate-job` — 4 tests (happy path, 500 error, config passthrough, flag handling)
- `POST /api/simulate-validate` — 29 tests (+8 iter 2: exact boundary 50000/50001, scenario weights at 0.999/1.001/0.5, estimated_seconds/memory scaling)
- `GET /api/simulation/compare` — 12 tests (+3 iter 2: specific improved/degraded counts, identical runs zero deltas, missing query params)

**Satellite Routes (routes/satellite.py)**:
- `GET /api/data/satellite-model-comparison` — 4 tests
- `GET /api/data/satellite-model-selected` — 4 tests
- `GET /api/model-runs` — 5 tests (JSON field parsing, malformed JSON, run_type filter)
- `GET /api/model-runs/{run_id}` — 4 tests (found, 404, 500, datetime serialization)
- `POST /api/model-runs` — 6 tests (+2 iter 2: extra fields ignored, full payload round trip)
- `GET /api/data/cohort-summary` — 3 tests
- `GET /api/data/cohort-summary/{product}` — 3 tests
- `GET /api/data/drill-down-dimensions` — 4 tests
- `GET /api/data/ecl-by-cohort` — 4 tests (including missing product 422)
- `GET /api/data/stage-by-cohort` — 4 tests
- `GET /api/data/portfolio-by-cohort` — 4 tests
- `GET /api/data/ecl-by-product-drilldown` — 5 tests (+2 iter 2: dimension param passthrough, single product)

**Additional Test Classes (iteration 2)**:
- `TestSatelliteAdditionalEdgeCases` — 5 tests (dimension variations, multi-product cohort, multi-stage cohort, default dimension)
- `TestSimulationDefaultsStructure` — 3 tests (key presence, numeric types, scenarios list)

**Internal Helper Unit Tests**:
- `SimulationConfig` model — 2 tests
- `_transform_simulation_result` — 5 tests
- `_build_product_deltas` — 4 tests
- `_get_simulation_cap` — 3 tests
- `_run_pre_checks` — 3 tests
- `_persist_simulation_run` — 2 tests
- Serialization edge cases — 2 tests
- Pydantic validation — 5 tests

### Iteration 2 Additions (22 tests)
Per evaluator feedback (score 9.41, gap in Testing Coverage):
1. `test_n_simulations_exactly_50000` — route-level exact upper boundary
2. `test_n_simulations_exactly_50001` — one above max
3. `test_scenario_weights_sum_0_999` — within tolerance
4. `test_scenario_weights_sum_1_001` — within tolerance
5. `test_scenario_weights_sum_0_5_should_fail` — far from 1.0
6. `test_estimated_seconds_scales_with_nsims` — scaling check
7. `test_estimated_memory_scales_with_nsims` — scaling check
8. `test_specific_improved_degraded_counts` — known 3-metric comparison
9. `test_identical_runs_zero_deltas` — identical runs produce zero deltas
10. `test_missing_query_params` — compare without run_a/run_b → 422
11. `test_extra_fields_ignored` — POST model-runs extra fields
12. `test_full_payload_round_trip` — POST model-runs all fields
13. `test_with_dimension_param` — drilldown ignores unknown params
14. `test_single_product_drilldown` — single product result
15. `test_portfolio_by_cohort_dimension_vintage_year` — vintage_year dimension
16. `test_portfolio_by_cohort_dimension_credit_grade` — credit_grade dimension
17. `test_ecl_by_cohort_default_dimension` — default risk_band
18. `test_stage_by_cohort_multiple_stages_per_cohort` — multi-stage multi-cohort
19. `test_cohort_summary_all_products_mixed` — 4-product mixed cohort
20. `test_defaults_contains_all_expected_keys` — structure validation
21. `test_defaults_params_are_numeric` — type validation
22. `test_defaults_scenarios_is_list` — scenarios type check

### Files Changed
- `tests/unit/test_qa_sprint_2_simulation_satellite.py` (updated, ~1550 lines)

## How to Test
- Run Sprint 2 tests: `pytest tests/unit/test_qa_sprint_2_simulation_satellite.py -v`
- Run full backend suite: `pytest tests/ -v`

## Test Results
- Sprint 2 tests: **150 passed** (was 128, +22 iter 2)
- Full backend suite: **2868 passed, 61 skipped, 0 failed**
- Zero regressions from existing 2846 tests

## Known Limitations
- SSE streaming tests verify response body content but don't test real-time streaming behavior (TestClient reads full response)
- `_persist_simulation_run` has internal try/except, so the "persist failure" test verifies the outer handler path
- Simulation job endpoint tested with mocked `jobs` module (requires live Databricks workspace for real execution)

## Bugs Found
- None — all endpoints behave as expected per their implementation
