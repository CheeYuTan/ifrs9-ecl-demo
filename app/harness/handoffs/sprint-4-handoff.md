# Sprint 4 Handoff: Backend API — GL Journals, Reports, RBAC, Audit, Admin, Data Mapping, Advanced, Period Close

## What Was Built
214 new tests across 3 test files covering 67 endpoints in 8 route modules:

### Test Files
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

### Test Coverage Areas
- Happy path for every endpoint
- Error paths: 404 (not found), 400 (invalid input / ValueError), 500 (backend exception)
- GL double-entry invariant: debits = credits verified with parametrized amounts
- RBAC segregation: analyst cannot approve, approver can approve/reject, admin has all permissions
- Audit chain integrity: intact and broken chain verification
- Audit input validation: invalid project_id format rejected
- Pipeline ordering: all 6 steps present in correct order
- Pipeline failure: run-all stops on first step failure
- Report generation: all 5 IFRS report types tested
- PDF export: report data as dict and JSON string handled
- Admin preview: limit capped at 20

## How to Test
```bash
cd '/Users/steven.tan/Expected Credit Losses/app'
source .venv/bin/activate
pytest tests/unit/test_qa_sprint_4_gl_reports_rbac.py tests/unit/test_qa_sprint_4_audit_admin_mapping.py tests/unit/test_qa_sprint_4_advanced_pipeline.py -v
```

## Test Results
- `pytest` exit code: 0
- Sprint 4 tests: 214 passed
- Full suite: 3,260 passed, 61 skipped, 0 failed
- Regressions: 0

## Known Limitations
- Tests mock all backend/domain functions — no real DB calls
- PDF export test verifies content-type and byte prefix, not full PDF validity
- Data mapping tests mock WorkspaceClient (no real Unity Catalog)

## Files Changed
- `tests/unit/test_qa_sprint_4_gl_reports_rbac.py` (new)
- `tests/unit/test_qa_sprint_4_audit_admin_mapping.py` (new)
- `tests/unit/test_qa_sprint_4_advanced_pipeline.py` (new)
- `harness/contracts/sprint-4.md` (updated)
