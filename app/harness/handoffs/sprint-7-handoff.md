# Sprint 7 Handoff: Domain Logic — Registry, Backtesting, Markov, Hazard, Advanced

## What Was Built

Comprehensive test suite for the second half of the domain/ modules (analytical engines). **230 new tests** across 4 iterations covering 10+ modules, with three bug fixes.

### Files Created
- `tests/unit/test_qa_sprint_7_domain_analytical.py` — 120 tests (iteration 1)
- `tests/unit/test_qa_sprint_7_iter2_domain.py` — 84 tests (iteration 2)
- `tests/unit/test_qa_sprint_7_iter3_regression.py` — 16 tests (iteration 3)
- `tests/unit/test_qa_sprint_7_iter4_regression.py` — 10 tests (iteration 4)

### Files Modified
- `domain/backtesting.py` — Bug fix iter 1: numpy type JSON serialization (`_json_default` helper). Bug fix iter 3: ALTER TABLE migration for missing `detail` column (BUG-VQA-7-001).
- `domain/workflow.py` — Bug fix iter 4: replaced fragile `globals().get()` pattern with explicit lazy imports for all 7 ensure functions (BUG-S7-1/BUG-S7-2).

### Iteration 4 Coverage (10 new tests)

| Area | Tests | Coverage |
|------|-------|----------|
| `ensure_workflow_table` invocation of `ensure_backtesting_table` | 1 | Verifies the function is actually called (BUG-S7-1 regression) |
| `ensure_workflow_table` invocation of all 7 ensure functions | 7 | Parametrized test for each function (BUG-S7-2 regression) |
| Error resilience — single failure doesn't block others | 1 | One ensure fn throws, rest still called |
| Comprehensive — all 7 called in single invocation | 1 | Full integration check |

### Bug Fixed (Iteration 4)

**BUG-S7-1/BUG-S7-2: ensure_workflow_table() silently skipped ensure_backtesting_table()**
- **Root cause**: `globals().get("ensure_backtesting_table")` returned `None` because the function was never imported in `workflow.py`. Top-level imports cause circular dependency (attribution.py imports workflow.py).
- **File**: `domain/workflow.py:58-67`
- **Fix**: Replaced the `globals().get()` loop with explicit lazy imports inside `ensure_workflow_table()`. Each function is imported with `try/except ImportError` to handle missing modules gracefully, then called with `try/except Exception` for runtime errors.
- **Regression tests**: 10 tests verifying the invocation path, parametrized coverage of all 7 functions, error resilience, and complete invocation.

### Combined Sprint 7 Test Summary

| Area | Iter 1 | Iter 2 | Iter 3 | Iter 4 | Total |
|------|--------|--------|--------|--------|-------|
| Model Registry | 25 | 24 | 0 | 0 | 49 |
| Backtesting | 47 | 4 | 16 | 0 | 67 |
| Markov | 6 | 13 | 0 | 0 | 19 |
| Hazard | 11 | 13 | 0 | 0 | 24 |
| Advanced | 8 | 20 | 0 | 0 | 28 |
| Period Close | 15 | 6 | 0 | 0 | 21 |
| Health | 13 | 0 | 0 | 0 | 13 |
| Workflow ensure invocation | 0 | 0 | 0 | 10 | 10 |
| **Total** | **120** | **84** | **16** | **10** | **230** |

### Bug Summary

| Bug ID | Description | Iteration | Fix | Regression Tests |
|--------|-------------|-----------|-----|-----------------|
| BUG-7-001 | Numpy types not JSON serializable | 1 | `_json_default()` handler | 5 tests |
| BUG-VQA-7-001 | Missing `detail` column in backtest_metrics | 3 | ALTER TABLE migration | 16 tests |
| BUG-S7-1/BUG-S7-2 | `globals().get()` silently skipped ensure_backtesting_table | 4 | Explicit lazy imports | 10 tests |

## How to Test

- Run Sprint 7 iter 1: `cd app && source .venv/bin/activate && python -m pytest tests/unit/test_qa_sprint_7_domain_analytical.py -v`
- Run Sprint 7 iter 2: `python -m pytest tests/unit/test_qa_sprint_7_iter2_domain.py -v`
- Run Sprint 7 iter 3: `python -m pytest tests/unit/test_qa_sprint_7_iter3_regression.py -v`
- Run Sprint 7 iter 4: `python -m pytest tests/unit/test_qa_sprint_7_iter4_regression.py -v`
- Full suite: `python -m pytest tests/ -q`

## Test Results

- `pytest`: **3,838 passed**, 61 skipped (268.72s)
- Sprint 7 tests: **230/230 passed** (120 iter 1 + 84 iter 2 + 16 iter 3 + 10 iter 4)
- Regressions: **0**

## Known Limitations

- `run_backtest()` integration test uses mocked DB (doesn't test actual SQL execution)
- Health check `check_config_loaded()` test uses import patching which may be fragile across Python versions
- `estimate_hazard_model` orchestrator test mocks the entire pipeline — doesn't test real data flow
- BUG-VQA-7-001 fix requires actual DB execution to verify in production — unit tests mock the execute call

## Files Changed (Iteration 4)
- `domain/workflow.py` — Replaced `globals().get()` loop (lines 58-67) with explicit lazy imports for all 7 ensure functions
- `tests/unit/test_qa_sprint_7_iter4_regression.py` — 10 new regression tests (NEW)
- `harness/handoffs/sprint-7-handoff.md` — Updated (this file)
- `harness/state.json` — Updated
