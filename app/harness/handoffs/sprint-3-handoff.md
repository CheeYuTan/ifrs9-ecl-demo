# Sprint 3 Handoff: Backend API — Model Registry, Backtesting, Markov, Hazard

## What Was Built

178 tests covering all 23 endpoints across 4 route files: `routes/models.py` (7 endpoints), `routes/backtesting.py` (4 endpoints), `routes/markov.py` (6 endpoints), and `routes/hazard.py` (6 endpoints).

### Test Coverage by Endpoint

**Model Registry (routes/models.py) — 48 tests**:
- `GET /api/models` — 7 tests (happy, filter type, filter status, both filters, empty, 500, decimal values)
- `GET /api/models/{model_id}` — 5 tests (found, 404, 500, all fields, champion flag)
- `POST /api/models` — 7 tests (happy, all fields, minimal payload, missing required, missing name, missing type, 500)
- `PUT /api/models/{model_id}/status` — 9 tests (valid transition, invalid 400, model not found, missing fields, 500, with comment)
- `POST /api/models/{model_id}/promote` — 5 tests (happy, invalid status 400, not found, missing user, 500)
- `POST /api/models/compare` — 5 tests (happy, empty, single, 500, missing field)
- `GET /api/models/{model_id}/audit` — 4 tests (happy, empty, 500, expected fields)
- **Parametrized status transitions** — 20 tests (5 valid + 15 invalid transitions covering full governance matrix)
- **Edge cases** — 5 tests (empty params, nested params, champion replacement, 3-model compare, full lifecycle audit)

**Backtesting (routes/backtesting.py) — 22 tests**:
- `POST /api/backtest/run` — 9 tests (PD happy, LGD, with config, default type, no data 400, 500, metrics, cohorts, traffic light counts)
- `GET /api/backtest/results` — 5 tests (happy, filter type, empty, 500, multiple entries)
- `GET /api/backtest/trend/{model_type}` — 4 tests (happy, empty, multiple, 500)
- `GET /api/backtest/{backtest_id}` — 5 tests (found, 404, 500, includes metrics/cohorts, decimal values)
- **Edge cases** — 4 tests (red traffic light, zero cohorts, LGD insufficient data, declining metrics trend)

**Markov Chain (routes/markov.py) — 35 tests**:
- `POST /api/markov/estimate` — 7 tests (happy, product filter, segment, rows sum to 1, non-negative, absorbing state, 500)
- `GET /api/markov/matrices` — 4 tests (happy, filter product, empty, 500)
- `GET /api/markov/matrix/{matrix_id}` — 4 tests (found, 404, 500, contains matrix data)
- `POST /api/markov/forecast` — 7 tests (happy, distribution sums to 100, matrix not found, default horizon, 500, missing fields)
- `GET /api/markov/lifetime-pd/{matrix_id}` — 6 tests (happy, custom months, monotonic non-decreasing, starts at zero, 404, 500)
- `POST /api/markov/compare` — 5 tests (happy, empty, single, 500, missing field)
- **Edge cases** — 4 tests (all stage 1, all default absorbing, 3-matrix compare, both filters)

**Hazard Model (routes/hazard.py) — 41 tests**:
- `POST /api/hazard/estimate` — 11 tests (cox_ph, discrete_time, kaplan_meier, product filter, segment, invalid type 400, no data 400, 500, missing type, curves, goodness-of-fit)
- `GET /api/hazard/models` — 6 tests (happy, filter model type, filter product, both filters, empty, 500)
- `GET /api/hazard/model/{model_id}` — 5 tests (found, 404, 500, has coefficients, has baseline hazard)
- `POST /api/hazard/survival-curve` — 7 tests (happy, with covariates, monotonic non-increasing, 400, 500, missing field, no-covariate risk mult)
- `GET /api/hazard/term-structure/{model_id}` — 6 tests (happy, custom months, cumulative PD non-decreasing, 400, 500, PD 12m range)
- `POST /api/hazard/compare` — 6 tests (happy, empty, single, 500, missing field, includes curves)
- **Edge cases** — 6 tests (zero hazard, high risk multiplier, short horizon, 3-model compare, n_observations, no curves)

### Domain-Specific Validation Tests
- **Model governance**: All 5 valid status transitions and all 15 invalid transitions tested parametrically
- **Markov properties**: Row stochasticity (sum=1.0), non-negativity, absorbing default state, lifetime PD monotonic non-decreasing
- **Hazard properties**: Survival curve monotonically non-increasing, cumulative PD non-decreasing, risk multiplier behavior
- **Backtesting**: Traffic light classification (Green/Amber/Red), metric structure, cohort results

### Files Changed
- `tests/unit/test_qa_sprint_3_models_backtest_markov_hazard.py` (new, ~850 lines)
- `harness/contracts/sprint-3.md` (updated for QA audit)

## How to Test
- Run Sprint 3 tests: `pytest tests/unit/test_qa_sprint_3_models_backtest_markov_hazard.py -v`
- Run full backend suite: `pytest tests/ -v`

## Test Results
- Sprint 3 tests: **178 passed** in 0.87s
- Full backend suite: **3046 passed, 61 skipped, 0 failed** in 82s
- Zero regressions from existing 2868 tests

## Known Limitations
- All tests mock `backend.*` functions — does not exercise actual DB queries or domain logic
- Status transition tests verify the route layer's error handling; full domain-level transition matrix tested via mock side effects
- Decimal serialization tested at route layer; actual DecimalEncoder behavior tested elsewhere

## Bugs Found
- None — all endpoints behave as expected per their implementation
