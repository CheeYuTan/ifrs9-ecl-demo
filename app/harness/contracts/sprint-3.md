# Sprint 3 Contract: Backend API — Model Registry, Backtesting, Markov, Hazard

## Scope

Test all 23 endpoints across 4 route files with mocked database layer.

### Model Registry (`routes/models.py` — 7 endpoints)
- `GET /api/models` — list with optional `model_type`/`status` filters
- `GET /api/models/{model_id}` — get single model, 404 if missing
- `POST /api/models` — register new model with Pydantic validation
- `PUT /api/models/{model_id}/status` — status transitions with governance rules
- `POST /api/models/{model_id}/promote` — promote to champion
- `POST /api/models/compare` — side-by-side comparison
- `GET /api/models/{model_id}/audit` — audit trail

### Backtesting (`routes/backtesting.py` — 4 endpoints)
- `POST /api/backtest/run` — execute PD/LGD backtest
- `GET /api/backtest/results` — list with optional `model_type` filter
- `GET /api/backtest/trend/{model_type}` — historical metric trend
- `GET /api/backtest/{backtest_id}` — get single result, 404 if missing

### Markov (`routes/markov.py` — 6 endpoints)
- `POST /api/markov/estimate` — estimate transition matrix
- `GET /api/markov/matrices` — list with optional `product_type` filter
- `GET /api/markov/matrix/{matrix_id}` — get single matrix, 404 if missing
- `POST /api/markov/forecast` — project stage distribution
- `GET /api/markov/lifetime-pd/{matrix_id}` — cumulative PD curves
- `POST /api/markov/compare` — side-by-side comparison

### Hazard (`routes/hazard.py` — 6 endpoints)
- `POST /api/hazard/estimate` — estimate cox_ph/discrete_time/kaplan_meier
- `GET /api/hazard/models` — list with optional filters
- `GET /api/hazard/model/{model_id}` — get single model, 404 if missing
- `POST /api/hazard/survival-curve` — compute survival curve with covariates
- `GET /api/hazard/term-structure/{model_id}` — PD term structure
- `POST /api/hazard/compare` — side-by-side comparison

## Acceptance Criteria

- [ ] 150+ new tests covering all 23 endpoints
- [ ] Every endpoint has happy path, error (500), and edge case tests
- [ ] Model Registry: status transition validation (valid + invalid transitions)
- [ ] Model Registry: promote champion with prior champion demotion
- [ ] Backtesting: PD and LGD model types tested
- [ ] Markov: forecast distribution sums to ~100% at each time point
- [ ] Markov: lifetime PD monotonically non-decreasing
- [ ] Hazard: all 3 model types (cox_ph, discrete_time, kaplan_meier)
- [ ] Hazard: survival curve monotonically non-increasing
- [ ] Hazard: invalid model_type returns 400
- [ ] All existing 2868 tests continue to pass (zero regressions)

## Test Plan

- File: `tests/unit/test_qa_sprint_3_models_backtest_markov_hazard.py`
- Mock pattern: patch `backend.*` functions (same pattern as Sprint 2)
- Use `mock_db` fixture from conftest.py
- Organize into test classes: `TestModelRegistry`, `TestBacktesting`, `TestMarkov`, `TestHazard`
- Edge cases: empty lists, missing IDs (404), backend exceptions (500), invalid inputs (400/422)
