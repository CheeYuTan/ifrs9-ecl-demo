# Sprint 4 Handoff: Backend API — GL Journals, Reports, RBAC, Audit, Admin, Data Mapping, Advanced, Period Close

## What Was Built

### Iteration 1: 214 new tests across 3 test files covering 67 endpoints in 8 route modules

#### Test Files
- `tests/unit/test_qa_sprint_4_gl_reports_rbac.py` — 84 tests
  - GL Journals (7 endpoints): generate, list, get, post, reverse, trial-balance, chart-of-accounts
  - Reports (6 endpoints x 5 types): generate, list, get, finalize, export CSV, export PDF
  - RBAC (8 endpoints): users list/get, approvals CRUD/approve/reject, history, permissions
  - Domain tests: double-entry journal integrity, maker-checker segregation of duties

- `tests/unit/test_qa_sprint_4_audit_admin_mapping.py` — 62 tests
  - Audit (5 endpoints): config changes, config diff, project trail, verify chain, export
  - Admin (16 endpoints): config CRUD, validate-mapping, tables, columns, connection, defaults, schemas, preview, validate-typed, suggest, auto-detect, discover-products, auto-setup-lgd
  - Data Mapping (9 endpoints): catalogs, schemas, tables, columns, preview, validate, suggest, apply, status

- `tests/unit/test_qa_sprint_4_advanced_pipeline.py` — 68 tests
  - Advanced (9 endpoints): cure-rates compute/list/get, CCF compute/list/get, collateral compute/list/get
  - Period Close (7 endpoints): start, steps, run get, execute-step, complete, health, run-all
  - Domain tests: cure rate bounds, CCF bounds, collateral bounds, pipeline step ordering, run-all stops on failure

### Iteration 2: 3 bug fixes + 11 regression tests

#### Bugs Fixed (from Visual QA report)

**BUG-S4-001: Audit export HTTP 500 — Timestamp serialization** (MAJOR)
- **Root cause**: `get_audit_trail()` and `get_config_audit_log()` returned `pandas.Timestamp` objects for `created_at`/`changed_at` columns. `JSONResponse` cannot serialize these.
- **Fix**: Added Timestamp-to-ISO-string conversion in `get_audit_trail()` (`domain/audit_trail.py:131-133`), `get_config_audit_log()` (`domain/config_audit.py:45-47`), and `get_config_diff()` (`domain/config_audit.py:82-84`).
- **Regression tests**: 6 tests in `tests/regression/test_sprint_4_bugs.py::TestBugS4001AuditExportTimestamp`

**BUG-S4-002: IFRS 7.35I — reconciliation column missing** (MAJOR)
- **Root cause**: `ecl_attribution` table created before `reconciliation` column was added to schema. `CREATE TABLE IF NOT EXISTS` doesn't add columns to existing tables, so `compute_attribution()` INSERT failed.
- **Fix**: Added `ALTER TABLE ADD COLUMN IF NOT EXISTS reconciliation JSONB` migration in `ensure_attribution_table()` (`domain/attribution.py:61-64`). Also added `ensure_attribution_table()` call at start of `compute_attribution()` (`domain/attribution.py:97`).
- **Regression tests**: 2 tests in `tests/regression/test_sprint_4_bugs.py::TestBugS4002AttributionReconciliation`

**BUG-S4-003: IFRS 7.35J — historical_defaults table not found** (MAJOR)
- **Root cause**: `historical_defaults` is a user-provided data table created by the data pipeline (`scripts/01_generate_data.py`). When the table hasn't been synced to Lakebase, IFRS 7.35J report section fails with raw SQL error.
- **Fix**: Improved error message in `_build_35j()` (`reporting/_ifrs7_sections_a.py:143-148`) to detect table-not-found errors specifically and return user-friendly guidance pointing to the data pipeline/Data Mapping.
- **Regression tests**: 3 tests in `tests/regression/test_sprint_4_bugs.py::TestBugS4003HistoricalDefaultsTable`

## How to Test
```bash
cd '/Users/steven.tan/Expected Credit Losses/app'
source .venv/bin/activate

# Sprint 4 iteration 1 tests (214 tests)
pytest tests/unit/test_qa_sprint_4_gl_reports_rbac.py tests/unit/test_qa_sprint_4_audit_admin_mapping.py tests/unit/test_qa_sprint_4_advanced_pipeline.py -v

# Sprint 4 iteration 2 regression tests (11 tests)
pytest tests/regression/test_sprint_4_bugs.py -v

# Full suite
pytest tests/ -q
```

## Test Results
- `pytest` exit code: 0
- Sprint 4 tests: 214 (iter 1) + 11 (iter 2 regression) = 225
- Full suite: 3,271 passed, 61 skipped, 0 failed
- Regressions: 0

## Known Limitations
- Tests mock all backend/domain functions — no real DB calls
- PDF export test verifies content-type and byte prefix, not full PDF validity
- Data mapping tests mock WorkspaceClient (no real Unity Catalog)
- BUG-S4-003 fix improves error messaging; the actual fix requires running the data pipeline to create the `historical_defaults` table

## Files Changed

### Iteration 1 (new test files)
- `tests/unit/test_qa_sprint_4_gl_reports_rbac.py`
- `tests/unit/test_qa_sprint_4_audit_admin_mapping.py`
- `tests/unit/test_qa_sprint_4_advanced_pipeline.py`

### Iteration 2 (bug fixes + regression tests)
- `domain/audit_trail.py` — Timestamp-to-string conversion in `get_audit_trail()`
- `domain/config_audit.py` — Timestamp-to-string conversion in `get_config_audit_log()` and `get_config_diff()`
- `domain/attribution.py` — `ALTER TABLE ADD COLUMN` migration + `ensure_attribution_table()` call in `compute_attribution()`
- `reporting/_ifrs7_sections_a.py` — User-friendly error message for missing `historical_defaults` table
- `tests/regression/test_sprint_4_bugs.py` (new) — 11 regression tests for all 3 bugs
