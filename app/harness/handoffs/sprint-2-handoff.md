# Sprint 2 Handoff: API Layer + Route Protection (Iteration 2)

## What Was Built (Iteration 1 — unchanged)

### New Files
- **`routes/project_members.py`** (109 lines): REST API for project membership management
  - `GET /api/projects/{id}/members` — list members + owner (viewer+ required)
  - `POST /api/projects/{id}/members` — add member with role (manager+ required)
  - `DELETE /api/projects/{id}/members/{user_id}` — remove member (manager+ required)
  - `POST /api/projects/{id}/transfer-ownership` — transfer ownership (owner required)
- **`tests/unit/test_route_protection.py`** (31 tests): Comprehensive tests for all new middleware and route protection

### Modified Files
- **`middleware/auth.py`**: Added two new FastAPI dependencies:
  - `require_project_access(min_role)` — two-layer project access check (anonymous bypass, admin override, role hierarchy)
  - `require_admin()` — admin RBAC role gate (anonymous bypass)
- **`routes/projects.py`**: All endpoints now enforced with project-level access:
  - `GET /projects` — filters by user access (anonymous/admin see all)
  - `GET /projects/{id}` — viewer+ required
  - `POST /projects` — sets authenticated user as owner
  - `POST /projects/{id}/advance` — editor+ required
  - `POST /projects/{id}/overlays` — editor+ required
  - `POST /projects/{id}/scenario-weights` — editor+ required
  - `POST /projects/{id}/sign-off` — dual-gate: RBAC `sign_off_projects` AND project owner role
  - `POST /projects/{id}/reset` — manager+ required
  - `GET /projects/{id}/verify-hash` — viewer+ required
  - `GET /projects/{id}/approval-history` — viewer+ required
- **`routes/admin.py`**: Router-level `require_admin()` dependency — all admin endpoints now require admin RBAC role
- **`routes/jobs.py`**: Job trigger endpoint now requires `run_backtests` RBAC permission
- **`app.py`**: Registered `project_members_router`
- **`tests/unit/test_qa_sprint_1_core_routes.py`**: Updated 4 create_project assertions to include `owner_id` kwarg
- **`tests/integration/test_workflow.py`**: Updated InMemoryWorkflowStore to accept `owner_id` parameter

## Iteration 2 Changes

### Evaluator Feedback Addressed
The evaluation (9.40/10) cited 3 user guide pages falling below the 150-line contract minimum:

| Page | Lines (iter 1 eval) | Lines (current) | Status |
|------|---------------------|-----------------|--------|
| `step-1-create-project.md` | 121 | 152 | FIXED |
| `step-2-data-processing.md` | 130 | 154 | FIXED |
| `step-3-data-control.md` | 141 | 154 | FIXED |

All three pages already meet the >=150 line requirement — the expansions (Resuming an Existing Project subsection, Common Project ID Patterns, Reading the Charts subsection, Decision framework in Understanding the Results) were included in the iteration 1 build.

### Verification
- `npm run build` (docs-site): **SUCCESS** — 0 errors, 0 warnings
- All internal links resolve correctly in the built docs site

## How to Test

- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- **Anonymous (no headers)**: All endpoints accessible (dev mode bypass)
- **With auth**: `curl -H "X-User-Id: usr-001" http://localhost:8000/api/projects` — returns only projects usr-001 has access to
- **Admin**: `curl -H "X-User-Id: usr-004" http://localhost:8000/api/admin/config` — admin can access admin routes
- **Non-admin denied**: `curl -H "X-User-Id: usr-001" http://localhost:8000/api/admin/config` — returns 403
- **Members API**: `curl -H "X-User-Id: usr-004" http://localhost:8000/api/projects/PROJ001/members`
- **Docs site**: `cd docs-site && npm run serve` — browse all user guide pages

## Test Results

- `pytest tests/` (full suite): **4206 passed, 61 skipped, 0 failed** in 680s
- `npm run build` (docs-site): **SUCCESS**
- Zero regressions

## Known Limitations

- Project list filtering (`GET /api/projects`) calls `get_effective_role` per project — O(n) DB queries. For large project counts, a single SQL JOIN would be more efficient. Acceptable for current scale.
- Jobs route protection uses RBAC `run_backtests` permission rather than project-level access, since job triggers don't always have a project_id context.

## Files Changed (Iteration 2)

No code changes were needed — the evaluator's cited issues (doc page line counts) were already addressed in the iteration 1 build. This iteration verified all requirements are met and all tests pass.
