# Sprint 5 Contract: ECL Engine — Monte Carlo Correctness

## Acceptance Criteria

### helpers.py
- [ ] `_emit()` calls callback when provided, no-op when None
- [ ] `_convergence_check()` returns correct keys and CV for constant/random data
- [ ] `_convergence_check_from_paths()` returns correct keys and CV for constant/random data
- [ ] `_df_to_records()` handles Decimal, datetime, date, NaN, empty DataFrame

### constants.py
- [ ] `_FALLBACK_BASE_LGD` keys match expected product types
- [ ] `_FALLBACK_SATELLITE` keys match expected product types, values have required keys
- [ ] `DEFAULT_SCENARIO_WEIGHTS` sums to 1.0
- [ ] `DEFAULT_SAT` and `DEFAULT_LGD` have expected values

### config.py
- [ ] `_t()` returns fully qualified table name with schema.prefix
- [ ] `_schema()` and `_prefix()` return backend.SCHEMA and backend.PREFIX
- [ ] `_build_product_maps()` returns correct LGD dict and satellite dict from fallbacks
- [ ] `_build_product_maps()` falls back gracefully when admin_config or DB unavailable
- [ ] `_load_config()` returns (None, None) when admin_config fails
- [ ] `_load_config()` returns correct LGD and weights when admin_config is available

### data_loader.py
- [ ] `_load_loans()` calls backend.query_df with correct SQL
- [ ] `_load_scenarios()` calls backend.query_df and fills missing columns with defaults

### monte_carlo.py — Core Math
- [ ] `prepare_loan_columns()` adds all derived columns (stage, gca, eir, base_pd, rem_q, rem_months_f, base_lgd)
- [ ] `prepare_loan_columns()` drops rows with critical nulls
- [ ] `prepare_loan_columns()` handles missing EIR (fillna 0), missing PD (fillna 0)
- [ ] Cholesky correlation: z_lgd has expected correlation with z_pd (rho)
- [ ] PD/LGD shocks are lognormal-distributed (mean ~1.0)
- [ ] Stressed PD/LGD are clipped within floor/cap bounds
- [ ] ECL formula per quarter: default_this_q × stressed_lgd × ead_q × discount
- [ ] Survival probability decreases each quarter
- [ ] Stage 1 horizon capped at 4 quarters (12 months)
- [ ] Stage 2/3 horizon = remaining quarters
- [ ] Aging factor only applies to Stage 2/3
- [ ] Amortizing EAD decreases over time for non-bullet loans
- [ ] Bullet loans maintain constant EAD
- [ ] Discount factor = 1/(1 + EIR/4)^q
- [ ] Prepayment survival reduces EAD correctly

### aggregation.py
- [ ] `aggregate_results()` produces all required keys in output dict
- [ ] Portfolio summary groups by product_type and stage
- [ ] Coverage ratio = ECL / GCA × 100
- [ ] Scenario results include percentile statistics (p50, p75, p95, p99)
- [ ] Product × scenario cross-product has correct count
- [ ] Stage summary covers all stages in input
- [ ] Convergence diagnostics per product include CI width

### simulation.py — Integration
- [ ] `run_simulation()` with known seed produces deterministic output
- [ ] Custom scenario_weights override defaults
- [ ] `_build_scenario_map()` converts DataFrame rows to dict correctly
- [ ] Missing scenario in scenario_map gets default multipliers

### Edge Cases & Numerical Stability
- [ ] Zero exposure (GCA=0) → ECL=0
- [ ] PD=0 → ECL=0
- [ ] PD=1.0 (certain default) → max ECL
- [ ] LGD=0 → ECL=0 (full recovery)
- [ ] LGD=1.0 → total loss
- [ ] Single-loan portfolio
- [ ] Single scenario
- [ ] Very small PD (1e-6) — no NaN/Inf
- [ ] Very large EAD (1e12) — no overflow
- [ ] Negative correlation coefficient — Cholesky still works

## Test Plan
- All tests in `tests/unit/test_qa_sprint_5_ecl_engine.py`
- Target: 150+ new tests
- No modifications to existing passing tests
- All 3,271 existing tests must continue to pass

## Parallel Execution Plan
- Helpers + constants + config tests (independent, write first)
- data_loader tests (mocked backend)
- monte_carlo math tests (numpy-only, no DB needed)
- aggregation tests (pure function, mock inputs)
- simulation integration tests (mock data_loader + config)
- Edge case tests (extend simulation mocks)
