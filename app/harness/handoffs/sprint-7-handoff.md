# Sprint 7 Handoff: Domain Logic — Registry, Backtesting, Markov, Hazard, Advanced

## What Was Built

Comprehensive test suite for the second half of the domain/ modules (analytical engines). **220 new tests** across 3 iterations covering 10+ modules, with two production bug fixes.

### Files Created
- `tests/unit/test_qa_sprint_7_domain_analytical.py` — 120 tests (iteration 1)
- `tests/unit/test_qa_sprint_7_iter2_domain.py` — 84 tests (iteration 2)
- `tests/unit/test_qa_sprint_7_iter3_regression.py` — 16 tests (iteration 3)

### Files Modified
- `domain/backtesting.py` — Bug fix iter 1: numpy type JSON serialization (`_json_default` helper). Bug fix iter 3: ALTER TABLE migration for missing `detail` column (BUG-VQA-7-001).

### Iteration 3 Coverage (16 new tests)

| Area | Tests | Coverage |
|------|-------|----------|
| `ensure_backtesting_table` migration | 5 | ALTER TABLE ADD COLUMN runs, ordering, idempotency, exception handling, legacy migration |
| `get_backtest` detail column handling | 8 | JSON string detail, dict detail, None detail, malformed JSON, multiple metrics, not found, config deser, cohort results |
| API route `GET /api/backtest/{id}` | 3 | 200 with detail data, 404 not found, 500 on exception |

### Bug Fixed (Iteration 3)

**BUG-VQA-7-001: Backtest detail endpoint 500 — missing `detail` column**
- **Root cause**: `CREATE TABLE IF NOT EXISTS` does not add new columns to existing tables. The `detail JSONB` column was defined in the schema but the table pre-dated it.
- **File**: `domain/backtesting.py:113`
- **Fix**: Added `ALTER TABLE {SCHEMA}.backtest_metrics ADD COLUMN IF NOT EXISTS detail JSONB` after the CREATE TABLE statements in `ensure_backtesting_table()`.
- **Regression tests**: 16 tests covering migration logic, detail column handling, and API route behavior.

### Combined Sprint 7 Test Summary

| Area | Iter 1 | Iter 2 | Iter 3 | Total |
|------|--------|--------|--------|-------|
| Model Registry | 25 | 24 | 0 | 49 |
| Backtesting | 47 | 4 | 16 | 67 |
| Markov | 6 | 13 | 0 | 19 |
| Hazard | 11 | 13 | 0 | 24 |
| Advanced | 8 | 20 | 0 | 28 |
| Period Close | 15 | 6 | 0 | 21 |
| Health | 13 | 0 | 0 | 13 |
| **Total** | **120** | **84** | **16** | **220** |

### Bug Summary

| Bug ID | Description | Iteration | Fix | Regression Tests |
|--------|-------------|-----------|-----|-----------------|
| BUG-7-001 | Numpy types not JSON serializable | 1 | `_json_default()` handler | 5 tests |
| BUG-VQA-7-001 | Missing `detail` column in backtest_metrics | 3 | ALTER TABLE migration | 16 tests |

## How to Test

- Run Sprint 7 iter 1: `cd app && source .venv/bin/activate && python -m pytest tests/unit/test_qa_sprint_7_domain_analytical.py -v`
- Run Sprint 7 iter 2: `python -m pytest tests/unit/test_qa_sprint_7_iter2_domain.py -v`
- Run Sprint 7 iter 3: `python -m pytest tests/unit/test_qa_sprint_7_iter3_regression.py -v`
- Full suite: `python -m pytest tests/ -q`

## Test Results

- `pytest`: **3,828 passed**, 61 skipped (114.49s)
- Sprint 7 tests: **220/220 passed** (120 iter 1 + 84 iter 2 + 16 iter 3)
- Regressions: **0**

## Known Limitations

- `run_backtest()` integration test uses mocked DB (doesn't test actual SQL execution)
- Health check `check_config_loaded()` test uses import patching which may be fragile across Python versions
- `estimate_hazard_model` orchestrator test mocks the entire pipeline — doesn't test real data flow
- BUG-VQA-7-001 fix requires actual DB execution to verify in production — unit tests mock the execute call

## Files Changed (Iteration 3)
- `domain/backtesting.py` — Added ALTER TABLE migration (lines 113-116)
- `tests/unit/test_qa_sprint_7_iter3_regression.py` — 16 new regression tests (NEW)
- `harness/handoffs/sprint-7-handoff.md` — Updated (this file)
- `harness/state.json` — Updated
