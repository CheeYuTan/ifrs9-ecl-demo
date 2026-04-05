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
"""
import logging

from db.pool import query_df, execute, SCHEMA

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
    from domain.workflow import WF_TABLE
    from governance.rbac import RBAC_USERS_TABLE

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
    execute(
        f"COMMENT ON TABLE {PROJECT_MEMBERS_TABLE} IS "
        f"'ifrs9ecl: Per-project role assignments for two-layer permission model'"
    )
    log.info("Ensured %s table exists", PROJECT_MEMBERS_TABLE)


def get_effective_role(user_id: str, project_id: str) -> str | None:
    """Resolve the effective project role for a user.

    Resolution order:
      1. Admin RBAC role -> "owner" (admin overrides all)
      2. ecl_workflow.owner_id matches user -> "owner"
      3. project_members entry -> stored role
      4. None (no access)
    """
    from governance.rbac import get_user
    from domain.workflow import get_project

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


def check_project_access(
    user_id: str, project_id: str, required_role: str = "viewer"
) -> dict:
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
    reason = "" if allowed else (
        f"Role '{effective}' insufficient; requires '{required_role}'"
    )
    return {
        "allowed": allowed,
        "reason": reason,
        "effective_role": effective,
    }


def get_project_member(project_id: str, user_id: str) -> dict | None:
    """Retrieve a single project member entry, or None."""
    df = query_df(
        f"SELECT * FROM {PROJECT_MEMBERS_TABLE} WHERE project_id = %s AND user_id = %s",
        (project_id, user_id),
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def list_project_members(project_id: str) -> list[dict]:
    """List all members for a project (excludes owner — owner is in ecl_workflow)."""
    df = query_df(
        f"SELECT * FROM {PROJECT_MEMBERS_TABLE} WHERE project_id = %s ORDER BY granted_at",
        (project_id,),
    )
    return df.to_dict("records")


def add_project_member(
    project_id: str, user_id: str, role: str, granted_by: str
) -> dict:
    """Add a user to a project with the given role.

    Raises ValueError if role is invalid or user is already a member.
    """
    if not project_id or not user_id:
        raise ValueError("project_id and user_id are required")
    if role not in VALID_PROJECT_ROLES:
        raise ValueError(
            f"Invalid role '{role}'. Must be one of: {', '.join(VALID_PROJECT_ROLES)}"
        )

    from domain.workflow import get_project

    project = get_project(project_id)
    if not project:
        raise ValueError(f"Project '{project_id}' not found")

    if project.get("owner_id") == user_id:
        raise ValueError(f"User '{user_id}' is the project owner; cannot add as member")

    existing = get_project_member(project_id, user_id)
    if existing:
        raise ValueError(
            f"User '{user_id}' is already a member with role '{existing['role']}'"
        )

    execute(
        f"""
        INSERT INTO {PROJECT_MEMBERS_TABLE} (project_id, user_id, role, granted_by)
        VALUES (%s, %s, %s, %s)
        """,
        (project_id, user_id, role, granted_by),
    )

    _audit_permission_change(
        project_id, "member_added", granted_by,
        {"user_id": user_id, "role": role},
    )

    log.info("Added member %s to project %s with role %s", user_id, project_id, role)
    return get_project_member(project_id, user_id)


def remove_project_member(
    project_id: str, user_id: str, removed_by: str
) -> bool:
    """Remove a user from a project. Returns True if removed, False if not found."""
    if not project_id or not user_id:
        raise ValueError("project_id and user_id are required")

    existing = get_project_member(project_id, user_id)
    if not existing:
        return False

    execute(
        f"DELETE FROM {PROJECT_MEMBERS_TABLE} WHERE project_id = %s AND user_id = %s",
        (project_id, user_id),
    )

    _audit_permission_change(
        project_id, "member_removed", removed_by,
        {"user_id": user_id, "previous_role": existing["role"]},
    )

    log.info("Removed member %s from project %s", user_id, project_id)
    return True


def transfer_ownership(
    project_id: str, new_owner_id: str, performed_by: str
) -> dict:
    """Transfer project ownership to a new user.

    The old owner loses the owner role. The new owner is removed from
    project_members if present (since ownership is stored in ecl_workflow).
    """
    if not project_id or not new_owner_id:
        raise ValueError("project_id and new_owner_id are required")

    from domain.workflow import get_project, WF_TABLE

    project = get_project(project_id)
    if not project:
        raise ValueError(f"Project '{project_id}' not found")

    old_owner_id = project.get("owner_id")

    execute(
        f"UPDATE {WF_TABLE} SET owner_id = %s, updated_at = NOW() WHERE project_id = %s",
        (new_owner_id, project_id),
    )

    # Remove new owner from project_members if they were a member
    execute(
        f"DELETE FROM {PROJECT_MEMBERS_TABLE} WHERE project_id = %s AND user_id = %s",
        (project_id, new_owner_id),
    )

    _audit_permission_change(
        project_id, "ownership_transferred", performed_by,
        {"old_owner_id": old_owner_id, "new_owner_id": new_owner_id},
    )

    log.info(
        "Transferred ownership of project %s from %s to %s",
        project_id, old_owner_id, new_owner_id,
    )
    return get_project(project_id)


def _audit_permission_change(
    project_id: str, action: str, performed_by: str, detail: dict
):
    """Log a permission change to the immutable audit trail."""
    try:
        from domain.audit_trail import append_audit_entry
        append_audit_entry(
            project_id, "project_permission", "project_members",
            project_id, action, performed_by, detail,
        )
    except Exception as exc:
        log.warning("Audit trail write failed for permission change: %s", exc)
