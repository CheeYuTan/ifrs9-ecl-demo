# Sprint 3 Contract: Frontend Permission Infrastructure

## Acceptance Criteria

- [ ] `frontend/src/lib/permissions.ts`: ProjectRole enum (`viewer`, `editor`, `manager`, `owner`), RbacRole type, `canPerformAction()` utility, role hierarchy constants, action-to-minimum-role mapping
- [ ] `frontend/src/hooks/usePermissions.ts`: React hook that fetches effective project role from `GET /api/projects/{id}/my-role`, caches by project ID, provides `canEdit`, `canManage`, `canOwn`, `isLoading`, `error`
- [ ] `frontend/src/lib/api.ts`: Add `ProjectMember` interface, `getProjectMembers()`, `addProjectMember()`, `removeProjectMember()`, `transferOwnership()`, `getMyProjectRole()` API functions
- [ ] Backend: `GET /api/projects/{project_id}/my-role` endpoint returning `{ user_id, project_role, rbac_role }`
- [ ] Sidebar: Admin link visible only when user has admin RBAC role
- [ ] `frontend/src/hooks/useCurrentUser.ts`: Hook that fetches RBAC user info from `GET /api/auth/me`
- [ ] Backend: `GET /api/auth/me` endpoint returning current user RBAC info
- [ ] Loading/error states for permission resolution

## API Contract

### `GET /api/auth/me`
Response: `{ user_id, email, display_name, role, permissions[] }`

### `GET /api/projects/{project_id}/my-role`
Response: `{ user_id, project_role, rbac_role }`

## Test Plan

- Unit: `permissions.ts` — canPerformAction for all role x action combos, role hierarchy, edge cases
- Unit: `usePermissions.ts` — loading state, successful fetch, error state
- Unit: `useCurrentUser.ts` — fetch, anonymous fallback
- Unit: Sidebar — admin sees Admin link, non-admin does not
- Backend: `/api/auth/me` with and without auth headers
- Backend: `/api/projects/{id}/my-role` for various role combinations
- Regression: all existing 4206 tests pass
