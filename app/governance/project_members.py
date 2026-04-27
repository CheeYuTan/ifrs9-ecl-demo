"""
CRUD operations for project membership — add, remove, list, get, transfer.

Part of the two-layer permission model. Core permission logic (role hierarchy,
access checks) lives in governance/project_permissions.py.
"""

import logging

from db.pool import execute, query_df

from governance.project_permissions import (
    PROJECT_MEMBERS_TABLE,
    VALID_PROJECT_ROLES,
    _audit_permission_change,
)

log = logging.getLogger(__name__)


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


def add_project_member(project_id: str, user_id: str, role: str, granted_by: str) -> dict:
    """Add a user to a project with the given role.

    Raises ValueError if role is invalid or user is already a member.
    """
    if not project_id or not user_id:
        raise ValueError("project_id and user_id are required")
    if role not in VALID_PROJECT_ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of: {', '.join(VALID_PROJECT_ROLES)}")

    from domain.workflow import get_project

    project = get_project(project_id)
    if not project:
        raise ValueError(f"Project '{project_id}' not found")

    if project.get("owner_id") == user_id:
        raise ValueError(f"User '{user_id}' is the project owner; cannot add as member")

    existing = get_project_member(project_id, user_id)
    if existing:
        raise ValueError(f"User '{user_id}' is already a member with role '{existing['role']}'")

    execute(
        f"""
        INSERT INTO {PROJECT_MEMBERS_TABLE} (project_id, user_id, role, granted_by)
        VALUES (%s, %s, %s, %s)
        """,
        (project_id, user_id, role, granted_by),
    )

    _audit_permission_change(
        project_id,
        "member_added",
        granted_by,
        {"user_id": user_id, "role": role},
    )

    log.info("Added member %s to project %s with role %s", user_id, project_id, role)
    return get_project_member(project_id, user_id)


def remove_project_member(project_id: str, user_id: str, removed_by: str) -> bool:
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
        project_id,
        "member_removed",
        removed_by,
        {"user_id": user_id, "previous_role": existing["role"]},
    )

    log.info("Removed member %s from project %s", user_id, project_id)
    return True


def transfer_ownership(project_id: str, new_owner_id: str, performed_by: str) -> dict:
    """Transfer project ownership to a new user.

    The old owner loses the owner role. The new owner is removed from
    project_members if present (since ownership is stored in ecl_workflow).
    """
    if not project_id or not new_owner_id:
        raise ValueError("project_id and new_owner_id are required")

    from domain.workflow import WF_TABLE, get_project

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
        project_id,
        "ownership_transferred",
        performed_by,
        {"old_owner_id": old_owner_id, "new_owner_id": new_owner_id},
    )

    log.info(
        "Transferred ownership of project %s from %s to %s",
        project_id,
        old_owner_id,
        new_owner_id,
    )
    return get_project(project_id)
