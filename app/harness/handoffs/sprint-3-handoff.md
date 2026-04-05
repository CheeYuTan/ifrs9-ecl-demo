# Sprint 3 Handoff: Frontend Permission Infrastructure

## What Was Built

### Backend — Auth Routes (`routes/auth.py`)
- `GET /api/auth/me` — returns current user RBAC identity (user_id, email, display_name, role, permissions). Anonymous returns analyst fallback.
- `GET /api/auth/projects/{project_id}/my-role` — returns effective project role for current user (user_id, project_role, rbac_role). Anonymous returns owner (dev mode bypass). Returns 403 if user has no access.
- Registered in `app.py` as `auth_router`.

### Frontend — Permission Library (`frontend/src/lib/permissions.ts`)
- `ProjectRole` type: `viewer | editor | manager | owner`
- `RbacRole` type: `analyst | reviewer | approver | admin`
- `PROJECT_ROLE_LEVEL` — numeric hierarchy for comparison
- `PROJECT_ROLE_LABELS` — display labels
- `PROJECT_ROLES` — ordered array
- `ProjectAction` type — 9 defined actions
- `canPerformAction(role, action)` — checks role meets minimum for action
- `hasMinRole(role, minRole)` — general hierarchy check
- `isAdmin(rbacRole)` — admin check

### Frontend — useCurrentUser Hook (`frontend/src/hooks/useCurrentUser.ts`)
- Fetches `GET /api/auth/me` once and caches globally
- Returns `{ user, isLoading, error, refetch }`
- Deduplicates concurrent fetches

### Frontend — usePermissions Hook (`frontend/src/hooks/usePermissions.ts`)
- Fetches `GET /api/auth/projects/{id}/my-role` per project ID
- Caches by project ID
- Returns `{ data, projectRole, rbacRole, isLoading, error, canEdit, canManage, canOwn, isAdminUser, can(action), refetch }`

### Frontend — API Extensions (`frontend/src/lib/api.ts`)
- New interfaces: `ProjectMember`, `ProjectMembersResponse`, `MyProjectRoleResponse`, `AuthMeResponse`
- New API functions: `authMe()`, `getMyProjectRole()`, `getProjectMembers()`, `addProjectMember()`, `removeProjectMember()`, `transferOwnership()`
- Added `del<T>()` helper for DELETE requests

### Frontend — Sidebar Admin Visibility (`frontend/src/components/Sidebar.tsx`)
- Admin link now conditionally rendered based on `useCurrentUser` hook
- Only users with `role === 'admin'` see the Admin nav item
- Non-admin users see all other navigation items normally

## How to Test
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- Auth endpoint: `curl http://localhost:8000/api/auth/me`
- Project role: `curl http://localhost:8000/api/auth/projects/Q4-2025-IFRS9/my-role`
- Frontend: navigate to app — non-admin users should not see Admin link

## Test Results
- **Backend**: `pytest tests/` — **4214 passed**, 61 skipped, **0 failed** (baseline was 4206 — added 8 new tests)
- **Frontend**: `npx vitest run` — **540 passed** across 56 test files (added 54 new tests)
- **Frontend build**: `npm run build` — SUCCESS, no TypeScript errors

### New Test Files
- `tests/unit/test_auth_routes.py` — 8 tests (anonymous, auth headers, 403, admin, response fields)
- `frontend/src/lib/permissions.test.ts` — 22 tests (role hierarchy, canPerformAction matrix, edge cases)
- `frontend/src/hooks/useCurrentUser.test.ts` — 4 tests (loading, fetch, error, cache)
- `frontend/src/hooks/usePermissions.test.ts` — 8 tests (null projectId, loading, roles, can(), error, cache)
- `frontend/src/components/Sidebar.test.tsx` — 5 new tests (admin visible, analyst hidden, reviewer hidden, loading hidden, non-admin nav visible)

## Known Limitations
- `useCurrentUser` uses module-level cache; page refresh required to pick up role changes
- No WebSocket/SSE push for real-time permission updates
- Sprint 4 will integrate these hooks into the 8 workflow step pages (gating controls, read-only mode)

## Files Changed

### New Files
- `routes/auth.py` (59 lines)
- `frontend/src/lib/permissions.ts` (80 lines)
- `frontend/src/hooks/useCurrentUser.ts` (76 lines)
- `frontend/src/hooks/usePermissions.ts` (109 lines)
- `frontend/src/lib/permissions.test.ts` (131 lines)
- `frontend/src/hooks/useCurrentUser.test.ts` (70 lines)
- `frontend/src/hooks/usePermissions.test.ts` (138 lines)
- `tests/unit/test_auth_routes.py` (108 lines)

### Modified Files
- `app.py` — added auth_router import and registration
- `frontend/src/lib/api.ts` — added ProjectMember types, auth API functions, del() helper
- `frontend/src/components/Sidebar.tsx` — conditional Admin link with useCurrentUser
- `frontend/src/components/Sidebar.test.tsx` — added useCurrentUser mock and admin visibility tests
