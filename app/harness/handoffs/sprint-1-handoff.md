# Sprint 1 Handoff: Backend Permission Engine (Iteration 4)

## What Was Built

### Core Permission Logic — `governance/project_permissions.py` (149 lines)
- `ensure_project_members_table()`: Creates `{SCHEMA}.project_members` table with role CHECK constraint and UNIQUE(project_id, user_id)
- `get_effective_role(user_id, project_id)`: Resolves effective role with priority: admin override > owner_id > project_members > None
- `check_project_access(user_id, project_id, required_role)`: Returns `{allowed, reason, effective_role}` dict
- `role_level(role)`: Numeric hierarchy — viewer(0) < editor(1) < manager(2) < owner(3)
- `_audit_permission_change()`: Best-effort audit trail logging for all permission changes
- Re-exports all CRUD operations from `project_members.py` for backward compatibility

### CRUD Operations — `governance/project_members.py` (149 lines)
- `add_project_member()`, `remove_project_member()`, `list_project_members()`, `get_project_member()`
- `transfer_ownership(project_id, new_owner_id, performed_by)`: Updates ecl_workflow.owner_id, removes new owner from members table, audits

### Modified Files
- **`domain/workflow.py`**: Added `owner_id TEXT` column, ALTER TABLE, backfill, `create_project()` accepts `owner_id`
- **`backend.py`**: Re-exports for all project_permissions public symbols

### Docs-Site Fixes (from iteration 2 — all 4 eval bugs fixed)
- **BUG-S1-001**: `docs-site/src/pages/index.tsx` — `title={siteConfig.title}` (no "Hello from" prefix)
- **BUG-S1-002**: `docs-site/src/pages/index.tsx` — IFRS 9-specific meta description
- **BUG-S1-003**: `docs-site/src/components/HomepageFeatures/index.tsx` — IFRS 9-relevant feature cards (3-Stage Impairment Model, Monte Carlo Simulation, Regulatory Reporting) with styled cards, no stock Docusaurus dinosaur SVGs
- **BUG-S1-004**: `docs-site/docusaurus.config.ts` — `onBrokenLinks: 'throw'`

### Iteration 3 Changes
- Split `project_permissions.py` (272→149 lines) → extracted CRUD to `project_members.py` (149 lines)
- Split `test_project_permissions.py` (547 lines) → extracted CRUD/transfer/audit tests to `test_project_members.py` (245 lines)
- Both source files well within 200-line limit

### Iteration 4 Changes
- Verified all 84 tests still pass after iteration 3 changes
- Verified docs-site build succeeds with 0 errors, 0 warnings
- All 4 eval bugs confirmed fixed with regression tests guarding them
- No new code changes needed — all eval feedback addressed in iterations 2-3

### Test Files
- **`tests/unit/test_project_permissions.py`** (37 tests): Role hierarchy, ensure table, effective role, access checks, permission matrix, backend re-exports, workflow integration
- **`tests/unit/test_project_members.py`** (28 tests): Add/remove/list/get member CRUD, transfer ownership, audit integration
- **`tests/regression/test_docs_homepage_bugs.py`** (8 tests): Guards all 4 eval bugs (BUG-S1-001 through BUG-S1-004)
- **`tests/regression/test_docs_content_quality.py`** (11 tests): Image references, links, content quality, config

## How to Test
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- Run tests: `cd /Users/steven.tan/Expected\ Credit\ Losses && python -m pytest tests/unit/test_project_permissions.py tests/unit/test_project_members.py tests/regression/test_docs_homepage_bugs.py tests/regression/test_docs_content_quality.py -v`
- Build docs: `cd docs-site && npm run build`
- Docs site homepage: http://localhost:PORT/docs/
- No new HTTP endpoints this sprint (backend domain layer only — API in Sprint 2)

## Test Results
- `pytest` exit code: 0
- Tests: **84 passed** (37 permissions + 28 members + 8 homepage regression + 11 content quality)
- Docs-site build: **SUCCESS** — 0 errors, 0 warnings, all pages generated

## Known Limitations
- No HTTP API endpoints yet (Sprint 2)
- No middleware integration yet (Sprint 2) — `require_project_access()` dependency not yet created
- Anonymous/dev mode bypass logic is designed but will be enforced at the middleware layer in Sprint 2

## Files Changed (cumulative across all iterations)
- `governance/project_permissions.py` — 149 lines (core logic)
- `governance/project_members.py` — 149 lines (CRUD operations)
- `domain/workflow.py` — owner_id column additions
- `backend.py` — re-exports
- `docs-site/src/pages/index.tsx` — fixed title + meta description
- `docs-site/src/components/HomepageFeatures/index.tsx` — IFRS 9 feature cards
- `docs-site/docusaurus.config.ts` — onBrokenLinks: 'throw'
- `tests/unit/test_project_permissions.py` — 37 tests
- `tests/unit/test_project_members.py` — 28 tests
- `tests/regression/test_docs_homepage_bugs.py` — 8 regression tests
- `tests/regression/test_docs_content_quality.py` — 11 content quality tests
