# Sprint 1 Handoff: Backend Permission Engine (Iteration 1)

## What Was Built

### New Files
- **`governance/project_permissions.py`** (190 lines): Core permission engine implementing Layer 2 (per-project) of the two-layer permission model
  - `ensure_project_members_table()`: Creates `{SCHEMA}.project_members` table with role CHECK constraint and UNIQUE(project_id, user_id)
  - `get_effective_role(user_id, project_id)`: Resolves effective role with priority: admin override > owner_id > project_members > None
  - `check_project_access(user_id, project_id, required_role)`: Returns `{allowed, reason, effective_role}` dict
  - `role_level(role)`: Numeric hierarchy — viewer(0) < editor(1) < manager(2) < owner(3)
  - CRUD: `add_project_member()`, `remove_project_member()`, `list_project_members()`, `get_project_member()`
  - `transfer_ownership(project_id, new_owner_id, performed_by)`: Updates ecl_workflow.owner_id, removes new owner from members table, audits
  - `_audit_permission_change()`: Best-effort audit trail logging for all permission changes

- **`tests/unit/test_project_permissions.py`** (65 tests): Comprehensive test coverage
  - Role hierarchy tests (6)
  - ensure_project_members_table DDL tests (5)
  - get_effective_role tests (7): admin override, owner match, member role, no access, non-existent user/project
  - check_project_access tests (6): owner, viewer, editor, manager, no access, invalid role
  - Permission matrix tests (16): all RBAC role x project role x access combinations
  - CRUD tests (12): add/remove/list/get members, validation, edge cases
  - Transfer ownership tests (3)
  - Audit integration tests (4): add/remove/transfer all audit, audit failure resilience
  - Backend re-export tests (1)
  - Workflow owner_id integration tests (3)

### Modified Files
- **`domain/workflow.py`**: 
  - Added `owner_id TEXT` column to ecl_workflow CREATE TABLE DDL
  - Added `ALTER TABLE ... ADD COLUMN IF NOT EXISTS owner_id TEXT` for existing tables
  - Added backfill: `UPDATE ... SET owner_id = 'usr-004' WHERE owner_id IS NULL`
  - Updated `create_project()` to accept `owner_id` parameter (default: `'usr-004'`)
  - Updated INSERT to include `owner_id` column
  - Wired `ensure_project_members_table()` into init chain
- **`backend.py`**: Added re-exports for all project_permissions public symbols

## How to Test
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- Run tests: `cd /Users/steven.tan/Expected\ Credit\ Losses && python -m pytest tests/unit/test_project_permissions.py -v`
- No new HTTP endpoints this sprint (backend domain layer only)

## Test Results
- `pytest` exit code: 0
- Tests: 65 passed (new), 103 passed including related modules
- Coverage: permission matrix covers all RBAC role x project role x action combinations

## Known Limitations
- No HTTP API endpoints yet (Sprint 2)
- No middleware integration yet (Sprint 2) — `require_project_access()` dependency not yet created
- Anonymous/dev mode bypass logic is designed but will be enforced at the middleware layer in Sprint 2
- Foreign key references in DDL comment are noted but not enforced (to avoid circular dependency during table creation)

## Files Changed
- `governance/project_permissions.py` (new)
- `tests/unit/test_project_permissions.py` (new)
- `domain/workflow.py` (modified)
- `backend.py` (modified)
- `harness/contracts/sprint-1.md` (updated)
- `harness/state.json` (updated)
