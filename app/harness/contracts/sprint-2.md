# Sprint 2 Contract: Backend API — Simulation & Satellite Model

## Acceptance Criteria

### Simulation Routes (routes/simulation.py — 6 endpoints)
- [ ] POST /api/simulate — happy path returns ecl_by_product, scenario_summary, loss_allowance_by_stage, run_metadata
- [ ] POST /api/simulate — returns 400 when pre-calculation validation has critical failures
- [ ] POST /api/simulate — returns 500 when ecl_engine.run_simulation raises
- [ ] GET /api/simulation-defaults — returns flat structure with n_simulations, pd_lgd_correlation, scenario_weights, etc.
- [ ] GET /api/simulation-defaults — returns 500 when ecl_engine.get_defaults raises
- [ ] POST /api/simulate-stream — returns SSE text/event-stream with progress events then result
- [ ] POST /api/simulate-stream — SSE stream emits error event on simulation failure
- [ ] POST /api/simulate-job — triggers Databricks job and returns job metadata
- [ ] POST /api/simulate-job — returns 500 when jobs module raises
- [ ] POST /api/simulate-validate — valid params return {valid: true, errors: [], warnings: []}
- [ ] POST /api/simulate-validate — pd_floor >= pd_cap returns error
- [ ] POST /api/simulate-validate — lgd_floor >= lgd_cap returns error
- [ ] POST /api/simulate-validate — n_simulations < 100 returns error
- [ ] POST /api/simulate-validate — n_simulations > max_sims returns error
- [ ] POST /api/simulate-validate — scenario weights not summing to 1.0 returns error
- [ ] POST /api/simulate-validate — high n_sims, high correlation, high aging produce warnings
- [ ] POST /api/simulate-validate — returns estimated_seconds and estimated_memory_mb
- [ ] GET /api/simulation/compare — compares two runs by deltas and product deltas
- [ ] GET /api/simulation/compare — returns 404 when run not found
- [ ] GET /api/simulation/compare — returns 500 on unexpected error

### Satellite & Model Run Routes (routes/satellite.py — 12 endpoints)
- [ ] GET /api/data/satellite-model-comparison — returns records from backend
- [ ] GET /api/data/satellite-model-comparison?run_id=X — filters by run_id
- [ ] GET /api/data/satellite-model-selected — returns selected model records
- [ ] GET /api/data/satellite-model-selected?run_id=X — filters by run_id
- [ ] GET /api/model-runs — returns list with JSON-parsed fields
- [ ] GET /api/model-runs?run_type=satellite_model — filters by type
- [ ] GET /api/model-runs/{run_id} — returns serialized run
- [ ] GET /api/model-runs/{run_id} — returns 404 when not found
- [ ] POST /api/model-runs — saves and returns new run
- [ ] GET /api/data/cohort-summary — returns cohort data
- [ ] GET /api/data/cohort-summary/{product} — returns product-specific cohorts
- [ ] GET /api/data/drill-down-dimensions — returns available dimensions
- [ ] GET /api/data/drill-down-dimensions?product=X — product-specific dimensions
- [ ] GET /api/data/ecl-by-cohort — returns ECL drill-down by dimension
- [ ] GET /api/data/stage-by-cohort — returns stage distribution by cohort
- [ ] GET /api/data/portfolio-by-cohort — returns portfolio by dimension
- [ ] GET /api/data/ecl-by-product-drilldown — returns ECL grouped by product

### Edge Cases & Domain Tests
- [ ] Simulation with n_simulations at boundary (100, 50000)
- [ ] Validation with scenario weights at tolerance boundary (0.99 vs 0.5)
- [ ] _transform_simulation_result handles missing/empty stage_summary, scenario_results
- [ ] _build_product_deltas with overlapping and non-overlapping product sets
- [ ] Satellite routes return 500 on backend exceptions
- [ ] Model run JSON field parsing handles malformed JSON gracefully
- [ ] Empty DataFrames return empty lists (not errors)
- [ ] SimulationConfig default values are correct

## Test Plan
- Test file: `tests/unit/test_qa_sprint_2_simulation_satellite.py`
- Pattern: mock backend/ecl_engine/jobs at route level, test HTTP responses
- Target: 150+ test cases covering all 18 endpoints + edge cases + domain validation

## API Contract
All endpoints follow existing patterns:
- Success: 200 with JSON body
- Validation error: 422 (Pydantic) or 400 (custom)
- Not found: 404
- Server error: 500 with error message string
