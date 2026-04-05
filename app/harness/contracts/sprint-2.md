# Sprint 2 Contract: API Layer + Route Protection

## Acceptance Criteria

- [ ] `routes/project_members.py` — REST API with 4 endpoints:
  - `GET /api/projects/{project_id}/members` — list project members (requires viewer+ role)
  - `POST /api/projects/{project_id}/members` — add member (requires manager+ role)
  - `DELETE /api/projects/{project_id}/members/{user_id}` — remove member (requires manager+ role)
  - `POST /api/projects/{project_id}/transfer-ownership` — transfer ownership (requires owner role)
- [ ] `middleware/auth.py` — new `require_project_access(min_role)` FastAPI dependency
  - Anonymous (no auth header) bypasses check
  - Admin RBAC role overrides project-level check
  - Returns user dict enriched with `project_role`
- [ ] `routes/projects.py` protected:
  - `GET /api/projects` filters by user access (returns only projects user can see)
  - `POST /api/projects/{id}/advance` requires editor+ project role
  - `POST /api/projects/{id}/overlays` requires editor+ project role
  - `POST /api/projects/{id}/scenario-weights` requires editor+ project role
  - `POST /api/projects/{id}/sign-off` requires owner role + RBAC sign_off_projects (dual-gate)
  - `POST /api/projects/{id}/reset` requires manager+ project role
- [ ] `routes/admin.py` protected: all endpoints require admin RBAC role
- [ ] `routes/jobs.py` protected: trigger endpoint requires editor+ project role
- [ ] All new endpoints return proper error codes (403 for access denied, 404 for not found)
- [ ] Audit trail entries for all permission-gated actions
- [ ] All existing tests continue passing + new tests for all above

## API Contract

### Project Members
- `GET /api/projects/{project_id}/members` -> `[{user_id, role, granted_by, granted_at, display_name}]`
- `POST /api/projects/{project_id}/members` body: `{user_id, role}` -> member object
- `DELETE /api/projects/{project_id}/members/{user_id}` -> `{removed: true}`
- `POST /api/projects/{project_id}/transfer-ownership` body: `{new_owner_id}` -> project object

### Error Responses
- `403 {"detail": "..."}` — access denied (insufficient role)
- `404 {"detail": "..."}` — project or member not found
- `422 {"detail": "..."}` — validation error

## Test Plan

- Unit tests for `require_project_access` middleware
- Unit tests for project members REST endpoints (list, add, remove, transfer)
- Unit tests for protected project routes (filter, gate advance/overlays/weights/sign-off/reset)
- Unit tests for admin route protection
- Unit tests for jobs route protection

## Production Readiness Items This Sprint
- Consistent error responses (403/404/422 JSON)
- No hardcoded user IDs in route logic
