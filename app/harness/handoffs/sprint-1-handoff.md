# Sprint 1 Handoff: Backend Permission Engine (Iteration 2)

## What Was Built

### New Files (from iteration 1 — unchanged)
- **`governance/project_permissions.py`** (190 lines): Core permission engine implementing Layer 2 (per-project) of the two-layer permission model
  - `ensure_project_members_table()`: Creates `{SCHEMA}.project_members` table with role CHECK constraint and UNIQUE(project_id, user_id)
  - `get_effective_role(user_id, project_id)`: Resolves effective role with priority: admin override > owner_id > project_members > None
  - `check_project_access(user_id, project_id, required_role)`: Returns `{allowed, reason, effective_role}` dict
  - `role_level(role)`: Numeric hierarchy — viewer(0) < editor(1) < manager(2) < owner(3)
  - CRUD: `add_project_member()`, `remove_project_member()`, `list_project_members()`, `get_project_member()`
  - `transfer_ownership(project_id, new_owner_id, performed_by)`: Updates ecl_workflow.owner_id, removes new owner from members table, audits
  - `_audit_permission_change()`: Best-effort audit trail logging for all permission changes

- **`tests/unit/test_project_permissions.py`** (65 tests): Comprehensive test coverage
  - Role hierarchy (6), ensure table DDL (5), get_effective_role (7), check_project_access (6)
  - Permission matrix — all RBAC role x project role combinations (16)
  - CRUD operations (12), transfer ownership (3), audit integration (4)
  - Backend re-export (1), workflow owner_id integration (3)

### Modified Files (from iteration 1 — unchanged)
- **`domain/workflow.py`**: Added `owner_id TEXT` column, ALTER TABLE, backfill, `create_project()` accepts `owner_id`
- **`backend.py`**: Re-exports for all project_permissions public symbols

### Iteration 2 Fixes (evaluation bugs BUG-S1-001 through BUG-S1-004)

All 4 bugs were already fixed in the codebase. Verified and confirmed:

- **`docs-site/src/pages/index.tsx`**: `title={siteConfig.title}` (no "Hello from" prefix), description is IFRS 9-specific
- **`docs-site/src/components/HomepageFeatures/index.tsx`**: IFRS 9-relevant feature cards (3-Stage Impairment Model, Monte Carlo Simulation, Regulatory Reporting) with emoji icons — no stock Docusaurus content
- **`docs-site/docusaurus.config.ts`**: `onBrokenLinks: 'throw'` (not 'warn')

### Regression Tests (already present)
- **`tests/regression/test_docs_homepage_bugs.py`** (8 tests): Guards all 4 eval bugs
- **`tests/regression/test_docs_content_quality.py`** (11 tests): Image reference verification, internal link resolution, content quality, config consistency

## How to Test
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- Run tests: `cd /Users/steven.tan/Expected\ Credit\ Losses && python -m pytest tests/unit/test_project_permissions.py tests/regression/test_docs_homepage_bugs.py tests/regression/test_docs_content_quality.py -v`
- Build docs: `cd docs-site && npm run build`
- No new HTTP endpoints this sprint (backend domain layer only)

## Test Results
- `pytest` exit code: 0
- Tests: **84 passed** (65 permission engine + 8 homepage regression + 11 content quality)
- Docs-site build: **SUCCESS** — 0 errors, 0 warnings, all pages generated

## Known Limitations
- No HTTP API endpoints yet (Sprint 2)
- No middleware integration yet (Sprint 2) — `require_project_access()` dependency not yet created
- Anonymous/dev mode bypass logic is designed but will be enforced at the middleware layer in Sprint 2

## Files Changed (iteration 2)
- `harness/handoffs/sprint-1-handoff.md` (updated)
- `harness/state.json` (updated)
