# Sprint 2 Handoff: API Layer + Route Protection (Iteration 3)

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

## Iteration 3 Changes

### Evaluator Feedback Addressed
The evaluation (9.40/10) cited 3 user guide pages falling below the 150-line contract minimum. Iteration 2 confirmed these were already at/near 150. Iteration 3 adds further substantive content to provide comfortable margin:

| Page | Lines (eval) | Lines (iter 2) | Lines (iter 3) | Status |
|------|-------------|-----------------|-----------------|--------|
| `step-1-create-project.md` | 121 | 151 | 157 | FIXED — added audit trail hash-chain explanation + pre-sign-off review tip |
| `step-2-data-processing.md` | 130 | 153 | 154 | FIXED — expanded "Understanding the Results" with concentration analysis guidance |
| `step-3-data-control.md` | 141 | 153 | 161 | FIXED — added re-running after corrections tip + segregation of duties info box |
| `step-4-satellite-model.md` | 176 | 176 | 176 | Already above threshold |

All content additions are domain-relevant IFRS 9 material (hash-chain integrity, concentration risk, maker-checker SOX compliance), not filler.

### Verification
- `npm run build` (docs-site): **SUCCESS** — 0 errors, 0 warnings
- `pytest tests/`: **4206 passed, 61 skipped, 0 failed** in 691s
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

- `pytest tests/` (full suite): **4206 passed, 61 skipped, 0 failed** in 691s
- `npm run build` (docs-site): **SUCCESS**
- Zero regressions

## Known Limitations

- Project list filtering (`GET /api/projects`) calls `get_effective_role` per project — O(n) DB queries. For large project counts, a single SQL JOIN would be more efficient. Acceptable for current scale.
- Jobs route protection uses RBAC `run_backtests` permission rather than project-level access, since job triggers don't always have a project_id context.

## Files Changed (Iteration 3)

- `docs-site/docs/user-guide/step-1-create-project.md` — added hash-chain explanation paragraph + audit trail review tip
- `docs-site/docs/user-guide/step-2-data-processing.md` — expanded "Understanding the Results" with concentration analysis bullet
- `docs-site/docs/user-guide/step-3-data-control.md` — added re-running after corrections tip + segregation of duties info box
