# Sprint 1 Handoff: Backend Permission Engine (Iteration 3)

## What Was Built

### Core Permission Logic — `governance/project_permissions.py` (149 lines)
- `ensure_project_members_table()`: Creates `{SCHEMA}.project_members` table with role CHECK constraint and UNIQUE(project_id, user_id)
- `get_effective_role(user_id, project_id)`: Resolves effective role with priority: admin override > owner_id > project_members > None
- `check_project_access(user_id, project_id, required_role)`: Returns `{allowed, reason, effective_role}` dict
- `role_level(role)`: Numeric hierarchy — viewer(0) < editor(1) < manager(2) < owner(3)
- `_audit_permission_change()`: Best-effort audit trail logging for all permission changes
- Re-exports all CRUD operations from `project_members.py` for backward compatibility

### CRUD Operations — `governance/project_members.py` (149 lines, NEW in iter 3)
- `add_project_member()`, `remove_project_member()`, `list_project_members()`, `get_project_member()`
- `transfer_ownership(project_id, new_owner_id, performed_by)`: Updates ecl_workflow.owner_id, removes new owner from members table, audits

### Modified Files
- **`domain/workflow.py`**: Added `owner_id TEXT` column, ALTER TABLE, backfill, `create_project()` accepts `owner_id`
- **`backend.py`**: Re-exports for all project_permissions public symbols (unchanged — backward compat via re-exports)

### Docs-Site Fixes (from iteration 2 — unchanged)
- **`docs-site/src/pages/index.tsx`**: `title={siteConfig.title}` (no "Hello from" prefix), IFRS 9-specific description
- **`docs-site/src/components/HomepageFeatures/index.tsx`**: IFRS 9-relevant feature cards (3-Stage Impairment Model, Monte Carlo Simulation, Regulatory Reporting) with styled cards
- **`docs-site/docusaurus.config.ts`**: `onBrokenLinks: 'throw'`

### Iteration 3 Changes
- **Split `project_permissions.py`** (was 272 lines, now 149) → extracted CRUD to `project_members.py` (149 lines) — both well within 200-line limit
- **Split `test_project_permissions.py`** (was 547 lines) → extracted CRUD/transfer/audit tests to `test_project_members.py` (245 lines)
- Fixed test fixture `_patch_db` — no longer patches `query_df` in `project_permissions` (it was moved to `project_members`)

### Test Files
- **`tests/unit/test_project_permissions.py`** (37 tests): Role hierarchy, ensure table, effective role, access checks, permission matrix, backend re-exports, workflow integration
- **`tests/unit/test_project_members.py`** (28 tests): Add/remove/list/get member CRUD, transfer ownership, audit integration
- **`tests/regression/test_docs_homepage_bugs.py`** (8 tests): Guards all 4 eval bugs
- **`tests/regression/test_docs_content_quality.py`** (11 tests): Image references, links, content quality, config

## How to Test
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- Run tests: `cd /Users/steven.tan/Expected\ Credit\ Losses && python -m pytest tests/unit/test_project_permissions.py tests/unit/test_project_members.py tests/regression/test_docs_homepage_bugs.py tests/regression/test_docs_content_quality.py -v`
- Build docs: `cd docs-site && npm run build`
- No new HTTP endpoints this sprint (backend domain layer only)

## Test Results
- `pytest` exit code: 0
- Tests: **84 passed** (37 core permissions + 28 CRUD/members + 8 homepage regression + 11 content quality)
- Docs-site build: **SUCCESS** — 0 errors, 0 warnings, all pages generated

## Known Limitations
- No HTTP API endpoints yet (Sprint 2)
- No middleware integration yet (Sprint 2) — `require_project_access()` dependency not yet created
- Anonymous/dev mode bypass logic is designed but will be enforced at the middleware layer in Sprint 2

## Files Changed (iteration 3)
- `governance/project_permissions.py` — slimmed to 149 lines (core logic only)
- `governance/project_members.py` — NEW: 149 lines (CRUD operations extracted)
- `tests/unit/test_project_permissions.py` — slimmed to 333 lines (core logic tests only)
- `tests/unit/test_project_members.py` — NEW: 245 lines (CRUD/audit tests extracted)
- `harness/handoffs/sprint-1-handoff.md` — updated
- `harness/state.json` — updated
