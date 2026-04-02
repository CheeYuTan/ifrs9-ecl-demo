# Sprint 2 Handoff: Backend API — Simulation & Satellite Model

## What Was Built

128 new tests covering all 18 simulation and satellite model endpoints in `routes/simulation.py` (6 endpoints) and `routes/satellite.py` (12 endpoints), plus unit tests for internal helpers.

### Test Coverage by Endpoint

**Simulation Routes (routes/simulation.py)**:
- `POST /api/simulate` — 14 tests (happy path, aggregation, transforms, 400/500 errors, config passthrough, pre-checks, empty data)
- `GET /api/simulation-defaults` — 3 tests (happy path, 500 error, fallback defaults)
- `POST /api/simulate-stream` — 5 tests (SSE content type, result event, error event, headers, progress callback)
- `POST /api/simulate-job` — 4 tests (happy path, 500 error, config passthrough, flag handling)
- `POST /api/simulate-validate` — 21 tests (valid defaults, PD/LGD floor/cap errors, n_sims bounds, scenario weights, warnings, multiple errors, estimates)
- `GET /api/simulation/compare` — 9 tests (happy path, deltas, 404, 500, zero denominator, non-overlapping products, improved/degraded counts, empty summaries)

**Satellite Routes (routes/satellite.py)**:
- `GET /api/data/satellite-model-comparison` — 4 tests
- `GET /api/data/satellite-model-selected` — 4 tests
- `GET /api/model-runs` — 5 tests (JSON field parsing, malformed JSON, run_type filter)
- `GET /api/model-runs/{run_id}` — 4 tests (found, 404, 500, datetime serialization)
- `POST /api/model-runs` — 4 tests (happy path, minimal payload, missing run_id 422, 500)
- `GET /api/data/cohort-summary` — 3 tests
- `GET /api/data/cohort-summary/{product}` — 3 tests
- `GET /api/data/drill-down-dimensions` — 4 tests
- `GET /api/data/ecl-by-cohort` — 4 tests (including missing product 422)
- `GET /api/data/stage-by-cohort` — 4 tests
- `GET /api/data/portfolio-by-cohort` — 4 tests
- `GET /api/data/ecl-by-product-drilldown` — 3 tests

**Internal Helper Unit Tests**:
- `SimulationConfig` model — 2 tests (defaults, custom values)
- `_transform_simulation_result` — 5 tests (stage rename, weighted contribution, product aggregation, zero GCA, empty)
- `_build_product_deltas` — 4 tests (matching, non-overlapping, empty, zero base)
- `_get_simulation_cap` — 3 tests (default, config, alt keys)
- `_run_pre_checks` — 3 tests (exception, empty loans, loan data)
- `_persist_simulation_run` — 2 tests (calls save, swallows exceptions)
- Serialization edge cases — 2 tests (Decimal, NaN/Inf)
- Pydantic validation — 5 tests (invalid types, empty body, extra fields)

### Files Changed
- `tests/unit/test_qa_sprint_2_simulation_satellite.py` (new, ~820 lines)
- `harness/contracts/sprint-2.md` (updated)
- `harness/state.json` (updated)

## How to Test
- Run Sprint 2 tests: `pytest tests/unit/test_qa_sprint_2_simulation_satellite.py -v`
- Run full backend suite: `pytest tests/ -v`

## Test Results
- Sprint 2 tests: **128 passed**
- Full backend suite: **2846 passed, 61 skipped, 0 failed**
- Zero regressions from existing 2718 tests

## Known Limitations
- SSE streaming tests verify response body content but don't test real-time streaming behavior (TestClient reads full response)
- `_persist_simulation_run` has internal try/except, so the "persist failure" test verifies the outer handler path (mock bypasses internal catch)
- Simulation job endpoint tested with mocked `jobs` module (requires live Databricks workspace for real execution)

## Bugs Found
- None — all endpoints behave as expected per their implementation
