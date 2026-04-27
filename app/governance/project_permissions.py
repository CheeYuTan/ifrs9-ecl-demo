"""
Per-project permission layer (Layer 2) for IFRS 9 ECL Platform.

Implements project-level RBAC via the project_members table. Works in
concert with the global RBAC layer (governance/rbac.py) to form a
two-layer permission model:

  Layer 1 (RBAC): Global role determines what actions a user CAN do.
  Layer 2 (Project): Project membership determines WHICH projects.

Both layers must be satisfied. Admin RBAC role overrides Layer 2.
Anonymous/dev mode (no auth headers) bypasses all checks.

Complies with:
  - SOX Section 302: Segregation of duties via per-project roles
  - BCBS 239: Data governance with clear ownership and access controls
  - IFRS 7.35H-35N: Disclosure tracking via audit trail on permission changes

CRUD operations (add/remove/list/get member, transfer ownership) live in
governance/project_members.py.
"""

import logging

from db.pool import SCHEMA, execute

log = logging.getLogger(__name__)

PROJECT_MEMBERS_TABLE = f"{SCHEMA}.project_members"

VALID_PROJECT_ROLES = ("viewer", "editor", "manager")

ROLE_HIERARCHY = {
    "viewer": 0,
    "editor": 1,
    "manager": 2,
    "owner": 3,
}


def role_level(role: str) -> int:
    """Return numeric level for a project role. Unknown roles return -1."""
    return ROLE_HIERARCHY.get(role, -1)


def ensure_project_members_table():
    """Create the project_members table if it does not exist."""
    execute(f"""
        CREATE TABLE IF NOT EXISTS {PROJECT_MEMBERS_TABLE} (
            project_id  TEXT NOT NULL,
            user_id     TEXT NOT NULL,
            role        TEXT NOT NULL CHECK (role IN ('viewer', 'editor', 'manager')),
            granted_by  TEXT NOT NULL,
            granted_at  TIMESTAMP DEFAULT NOW(),
            UNIQUE (project_id, user_id)
        )
    """)
    try:
        execute(
            f"COMMENT ON TABLE {PROJECT_MEMBERS_TABLE} IS "
            f"'ifrs9ecl: Per-project role assignments for two-layer permission model'"
        )
    except Exception:
        pass
    log.info("Ensured %s table exists", PROJECT_MEMBERS_TABLE)


def get_effective_role(user_id: str, project_id: str) -> str | None:
    """Resolve the effective project role for a user.

    Resolution order:
      1. Admin RBAC role -> "owner" (admin overrides all)
      2. ecl_workflow.owner_id matches user -> "owner"
      3. project_members entry -> stored role
      4. None (no access)
    """
    from domain.workflow import get_project

    from governance.rbac import get_user

    user = get_user(user_id)
    if user and user.get("role") == "admin":
        return "owner"

    project = get_project(project_id)
    if not project:
        return None

    if project.get("owner_id") == user_id:
        return "owner"

    member = get_project_member(project_id, user_id)
    if member:
        return member["role"]

    return None


def check_project_access(user_id: str, project_id: str, required_role: str = "viewer") -> dict:
    """Check if a user has the required project role.

    Returns dict with keys: allowed, reason, effective_role.
    """
    if required_role not in ROLE_HIERARCHY:
        return {
            "allowed": False,
            "reason": f"Invalid required role: {required_role}",
            "effective_role": None,
        }

    effective = get_effective_role(user_id, project_id)
    if effective is None:
        return {
            "allowed": False,
            "reason": f"User '{user_id}' has no access to project '{project_id}'",
            "effective_role": None,
        }

    allowed = role_level(effective) >= role_level(required_role)
    reason = "" if allowed else (f"Role '{effective}' insufficient; requires '{required_role}'")
    return {
        "allowed": allowed,
        "reason": reason,
        "effective_role": effective,
    }


def _audit_permission_change(project_id: str, action: str, performed_by: str, detail: dict):
    """Log a permission change to the immutable audit trail."""
    try:
        from domain.audit_trail import append_audit_entry

        append_audit_entry(
            project_id,
            "project_permission",
            "project_members",
            project_id,
            action,
            performed_by,
            detail,
        )
    except Exception as exc:
        log.warning("Audit trail write failed for permission change: %s", exc)


# Re-export CRUD operations for backward compatibility
from governance.project_members import (  # noqa: F401, E402
    add_project_member,
    get_project_member,
    list_project_members,
    remove_project_member,
    transfer_ownership,
)
