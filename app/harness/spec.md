# IFRS 9 ECL Platform — Two-Layer Permission Model

## Vision

Implement a comprehensive two-layer permission model for the IFRS 9 ECL Platform. Layer 1 is the existing RBAC system (analyst/reviewer/approver/admin) that governs global capabilities. Layer 2 introduces per-project roles (viewer/editor/manager/owner) via a new `project_members` table, controlling who can access and modify each project. Both layers must be satisfied for any operation — a user needs the right RBAC role AND the right project role. Admin overrides all project-level checks. Anonymous dev mode (no auth headers) bypasses all checks to preserve local development ergonomics.

## Domain Context: IFRS 9 Compliance

### Why Per-Project Permissions Matter
- **Segregation of duties** (SOX Section 302): Different teams must own different portfolio segments
- **Audit trail completeness**: Every permission grant/revoke must be logged with hash-chain integrity
- **Dual-gate sign-off**: Owner project role AND RBAC `sign_off_projects` permission both required
- **Data confidentiality**: Credit risk data for different portfolios may have different access levels

### Regulatory Alignment
- BCBS 239: Data governance requires clear ownership and access controls
- SOX: Management attestation requires traceable approval chains
- IFRS 7.35H-35N: Disclosure reports must track who produced and approved them

## Tech Stack (Existing — No Changes)
- **Backend**: FastAPI (Python) on Databricks Apps
- **Database**: Lakebase (managed PostgreSQL) via `db.pool`
- **Frontend**: React SPA (Vite) served by FastAPI
- **Auth**: Databricks OAuth (X-Forwarded-User) / X-User-Id header / anonymous fallback
- **Schema**: `{SCHEMA}` from `db.pool` (default: `expected_credit_loss`)

## Architecture: Two-Layer Permission Matrix

### Layer 1: RBAC Roles (existing — `governance/rbac.py`)
| Role | Key Permissions |
|------|----------------|
| analyst | create_models, run_backtests, view_portfolio, view_reports |
| reviewer | + submit_for_approval, review_models, review_overlays |
| approver | + approve/reject_requests, sign_off_projects, post_journals |
| admin | + manage_users, manage_config, manage_roles (overrides Layer 2) |

### Layer 2: Project Roles (new — `governance/project_permissions.py`)
| Project Role | Capabilities |
|-------------|-------------|
| viewer | Read-only access to project data, reports, audit trail |
| editor | + advance workflow steps, run models, modify overlays, save scenario weights |
| manager | + reset project, share/unshare project (manage project_members) |
| owner | + transfer ownership, sign-off (dual-gate: also needs RBAC sign_off_projects) |

### Combined Permission Logic
```
def has_access(user, project, required_project_role):
    # Dev mode bypass
    if no_auth_headers: return True
    
    # Admin override
    if user.role == "admin": return True
    
    # Owner of project always has access
    if project.owner_id == user.user_id: return True (as "owner")
    
    # Check project_members table
    member = get_project_member(project_id, user_id)
    if not member: return False  # Not a member = no access
    
    return role_level(member.role) >= role_level(required_project_role)
```

Role hierarchy: viewer(0) < editor(1) < manager(2) < owner(3)

## Database Changes

### New Table: `project_members`
```sql
CREATE TABLE {SCHEMA}.project_members (
    project_id  TEXT NOT NULL REFERENCES {SCHEMA}.ecl_workflow(project_id),
    user_id     TEXT NOT NULL REFERENCES {SCHEMA}.rbac_users(user_id),
    role        TEXT NOT NULL CHECK (role IN ('viewer', 'editor', 'manager')),
    granted_by  TEXT NOT NULL,
    granted_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (project_id, user_id)
);
```
Note: `owner` role is not stored in project_members — it lives in `ecl_workflow.owner_id`.

### ALTER: `ecl_workflow`
```sql
ALTER TABLE {SCHEMA}.ecl_workflow ADD COLUMN IF NOT EXISTS owner_id TEXT;
UPDATE {SCHEMA}.ecl_workflow SET owner_id = 'usr-004' WHERE owner_id IS NULL;
```
Backfill all existing projects with admin user (usr-004) as owner.

## Features by Sprint

### Sprint 1: Backend Permission Engine
- `governance/project_permissions.py`: Core permission logic — `check_project_access()`, `get_effective_role()`, role hierarchy, CRUD for project_members, `ensure_project_members_table()`
- `domain/workflow.py`: Add `owner_id` column to ecl_workflow CREATE, backfill existing projects, include owner_id in `create_project()` and `get_project()`
- Unit tests: Permission matrix coverage (all role × project-role combinations), admin override, anonymous bypass, owner resolution, CRUD operations
- Audit trail entries for all permission changes via `append_audit_entry()`

### Sprint 2: API Layer + Route Protection
- `routes/project_members.py`: REST API — `GET /api/projects/{id}/members`, `POST /api/projects/{id}/members`, `DELETE /api/projects/{id}/members/{user_id}`, `POST /api/projects/{id}/transfer-ownership`
- `middleware/auth.py`: New `require_project_access(min_role)` FastAPI dependency
- Protect `routes/projects.py`: Filter project list by access, gate advance/overlays/weights/sign-off by project role
- Protect `routes/admin.py`: Require admin RBAC role
- Protect `routes/jobs.py`: Require project editor+ role for job triggers
- Unit tests for all new endpoints with various user/role combinations

### Sprint 3: Frontend Permission Infrastructure
- `frontend/src/lib/permissions.ts`: ProjectRole enum, permission types, `canPerformAction()`, role hierarchy constants
- `frontend/src/hooks/usePermissions.ts`: React hook — fetches effective role for current project, caches result, provides `canEdit`, `canManage`, `canOwn` booleans
- `frontend/src/lib/api.ts`: Add `ProjectMember` interface, `getProjectMembers()`, `addProjectMember()`, `removeProjectMember()`, `transferOwnership()`, `getMyProjectRole()`
- Sidebar: Conditionally show Admin link only for admin RBAC role
- Loading/error states for permission resolution

### Sprint 4: Frontend UI Integration
- `frontend/src/pages/ProjectMembers.tsx`: Full sharing UI — member table with role badges, add member form (user picker + role selector), remove button, transfer ownership dialog
- Gate all 8 workflow step pages with `usePermissions` hook: viewers see read-only, editors can interact, disabled states for insufficient roles
- `frontend/src/components/AccessDenied.tsx`: Styled access denied component for unauthorized project access
- Visual indicators: role badges on project cards, "Read Only" banner for viewers, disabled buttons with tooltips explaining required role

### Sprint 5: Integration Testing + Deployment Verification
- End-to-end integration tests: complete permission flows across both layers (create project → add members → verify access → advance workflow → sign off with dual-gate)
- Installation test: fresh DB migration creates project_members table, backfills owner_id
- Audit trail verification: all permission grant/revoke/transfer events logged with valid hash chain
- Deployment: Databricks Apps compatibility (env vars, OAuth header flow)
- Regression sweep: verify all 4108+ existing tests still pass, no broken workflows

## Test Strategy

### Baseline Protection
- Current: 4108 tests passing
- Every sprint must maintain or increase this count
- Zero regressions allowed

### New Test Categories
- **Permission matrix**: Every (RBAC role x project role x action) combination
- **Admin override**: Admin bypasses all project-level checks
- **Anonymous bypass**: No auth headers = full access (dev mode preserved)
- **Ownership**: Creation sets owner, transfer changes owner, dual-gate sign-off
- **Audit**: Every permission change produces audit entry with valid hash chain
- **API**: All sharing endpoints with various auth header combinations
- **Frontend**: usePermissions hook states, UI gating, disabled controls

## Existing Patterns to Follow
- RBAC: `governance/rbac.py` — `ROLE_PERMISSIONS` dict, `check_permission()`, `ensure_rbac_tables()`
- Auth middleware: `middleware/auth.py` — `require_permission()` dependency, anonymous fallback
- Audit trail: `domain/audit_trail.py` — `append_audit_entry()`, `verify_audit_chain()`
- Workflow: `domain/workflow.py` — `ecl_workflow` table, `create_project()`, `get_project()`
- Tests: `tests/unit/test_audit_trail.py` pattern, `conftest.py` fixtures
- Frontend API: `frontend/src/lib/api.ts` — `get<T>()`, `post<T>()` pattern
