# Sprint 7 Contract: Domain Logic — Registry, Backtesting, Markov, Hazard, Advanced

## Acceptance Criteria

- [ ] 180+ new tests across 10+ domain modules
- [ ] All existing 3,608 tests pass (zero regressions)
- [ ] Coverage gaps filled: model_registry lifecycle, backtesting integration, markov forecasting, hazard estimation pipeline, advanced get/list, period_close pipeline, health checks
- [ ] Every discovered bug fixed with regression test
- [ ] All domain validation rules tested with positive AND negative cases

## Modules Under Test

| Module | Existing Tests | New Tests Target | Priority |
|--------|---------------|-----------------|----------|
| model_registry.py | 18 | 25+ | P1 |
| backtesting.py | 40+ | 20+ | P1 |
| backtesting_stats.py | ~30 | 10+ | P2 |
| backtesting_traffic.py | ~10 | 10+ | P2 |
| markov.py | 45+ | 15+ | P2 |
| hazard*.py (6 files) | 50+ | 25+ | P2 |
| advanced.py | 30+ | 20+ | P2 |
| period_close.py | 25+ | 20+ | P1 |
| health.py | 0 | 15+ | P1 |

## Test Plan

### Unit Tests: `tests/unit/test_qa_sprint_7_domain_analytical.py`
- Model registry: register_model, list_models, update_model_status (all valid + invalid transitions), promote_champion, compare_models, audit_trail
- Backtesting: run_backtest PD/LGD, list/get/trend, cohort grouping
- Traffic lights: boundary values for all 10 metrics
- Markov: forecast correctness, lifetime PD monotonicity, absorbing state convergence
- Hazard: estimation pipeline (cox, discrete, KM), retrieval, survival curve, term structure
- Advanced: get/list round-trip, collateral LGD formula, product filter
- Period close: full pipeline flow, step failure, health aggregation
- Health: all 5 checks, degraded status, error paths
