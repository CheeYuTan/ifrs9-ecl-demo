# Sprint 1 Contract: Backend Permission Engine

## Acceptance Criteria
- [ ] `governance/project_permissions.py` implements `check_project_access(user_id, project_id, required_role)` returning `{allowed, reason, effective_role}`
- [ ] `get_effective_role(user_id, project_id)` resolves role from: admin override > owner_id match > project_members lookup > no access
- [ ] Role hierarchy: viewer(0) < editor(1) < manager(2) < owner(3)
- [ ] `ensure_project_members_table()` creates `{SCHEMA}.project_members` with correct schema
- [ ] CRUD: `add_project_member()`, `remove_project_member()`, `list_project_members()`, `get_project_member()`
- [ ] Anonymous/dev mode bypass: when no auth headers present, all access checks return True
- [ ] Admin override: users with RBAC role "admin" bypass all project-level checks
- [ ] Owner resolution: `ecl_workflow.owner_id` identifies project owner (role=owner without project_members entry)
- [ ] `domain/workflow.py`: `ecl_workflow` CREATE includes `owner_id TEXT` column
- [ ] `create_project()` accepts and stores `owner_id` parameter
- [ ] `get_project()` returns `owner_id` in result dict
- [ ] Existing projects backfilled with `owner_id = 'usr-004'` (admin) during `ensure_workflow_table()`
- [ ] All permission changes (add/remove member, transfer ownership) produce audit trail entries via `append_audit_entry()`
- [ ] `transfer_ownership(project_id, new_owner_id, performed_by)` updates `ecl_workflow.owner_id` and logs audit

## Test Plan
- Permission matrix: all 4 RBAC roles x 4 project roles x access check = 16+ combinations
- Admin override: admin user bypasses project-level checks regardless of membership
- Anonymous bypass: no auth headers returns allowed=True
- Owner resolution: project creator is owner, owner has full access
- CRUD: add/remove/list members, duplicate prevention, role validation
- Transfer ownership: changes owner_id, logs audit, old owner loses owner role
- Audit trail: every permission change produces valid audit entry
- Edge cases: non-existent user, non-existent project, invalid role name

## Production Readiness Items This Sprint
- Error handling: all functions return structured results or raise ValueError with clear messages
- Input validation: role must be in {viewer, editor, manager}, user_id and project_id must be non-empty
