# Sprint 7 Handoff: Domain Logic — Registry, Backtesting, Markov, Hazard, Advanced

## What Was Built

Comprehensive test suite for the second half of the domain/ modules (analytical engines). 120 new tests covering 10+ modules with one production bug fix.

### Files Created
- `tests/unit/test_qa_sprint_7_domain_analytical.py` — 120 new tests across 30+ test classes

### Files Modified
- `domain/backtesting.py` — Bug fix: numpy type JSON serialization (added `_json_default` helper)
- `harness/contracts/sprint-7.md` — Sprint contract

### Modules Tested (10+)

| Module | Tests Added | Coverage Areas |
|--------|------------|----------------|
| `model_registry.py` | 25 | register, list, status transitions (all valid + invalid), promote_champion, compare, audit_trail, sensitivity edge cases, recalibration |
| `backtesting.py` | 15 | run_backtest PD, empty portfolio, list/get/trend, cohort grouping |
| `backtesting_stats.py` | 7 | single observation, constant predictions, high default rate, numerical edge cases |
| `backtesting_traffic.py` | 20 | exact boundary values for all 10 metrics, overall aggregation (empty, single, all-red) |
| `markov.py` | 6 | identity matrix no-change, absorbing state convergence, lifetime PD monotonicity, Stage 3 > Stage 1 |
| `hazard_*.py` (6 files) | 11 | Cox PH edge cases (0 events, all events), discrete-time coefficients, KM properties, survival formula S(t)=exp(-H(t)), term structure PD |
| `advanced.py` | 8 | cure/ccf get round-trip, collateral LGD formula verification, forced sale discount bounds, product filter |
| `period_close.py` | 15 | start pipeline, all 6 step executions (success + failure), complete (success/error), get run, health aggregation |
| `health.py` | 13 | lakebase connection (success/fail), required tables (present/missing), config loaded, scipy available, full health check (healthy + 4 degraded scenarios) |
| `backtesting._json_default` | 5 | Regression tests for numpy bool_, int64, float64, ndarray, unknown type |

### Bug Found & Fixed

**BUG-7-001: Numpy types not JSON serializable in backtesting**
- **File**: `domain/backtesting.py:305`
- **Issue**: `_json.dumps(metrics_detail.get(name))` fails with `TypeError: Object of type bool_ is not JSON serializable` when Hosmer-Lemeshow test results contain numpy `bool_` from comparison operations
- **Fix**: Added `_json_default()` handler for `numpy.integer`, `numpy.floating`, `numpy.bool_`, and `numpy.ndarray` types
- **Regression tests**: 5 tests in `TestJsonDefaultHelper`

## How to Test

- Run: `cd app && source .venv/bin/activate && python -m pytest tests/unit/test_qa_sprint_7_domain_analytical.py -v`
- Full suite: `python -m pytest tests/ -q`

## Test Results

- `pytest`: **3,728 passed**, 61 skipped (114.89s)
- New Sprint 7 tests: **120/120 passed**
- Regressions: **0**

## Known Limitations

- `run_backtest()` integration test uses mocked DB (doesn't test actual SQL execution)
- Health check `check_config_loaded()` test uses import patching which may be fragile across Python versions
