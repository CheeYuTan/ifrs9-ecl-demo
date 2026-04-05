"""Project membership routes — /api/projects/{project_id}/members/*

REST API for managing per-project role assignments (Layer 2).
All endpoints enforce project-level access via require_project_access.
"""
import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from middleware.auth import (
    get_current_user,
    require_project_access,
)
from routes._utils import serialize_project

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["project-members"])


class AddMemberRequest(BaseModel):
    user_id: str
    role: str  # viewer | editor | manager


class TransferOwnershipRequest(BaseModel):
    new_owner_id: str


@router.get("/{project_id}/members")
def list_members(
    project_id: str,
    user: dict = Depends(require_project_access("viewer")),
):
    """List all members of a project (excludes owner — owner is on ecl_workflow)."""
    from governance.project_members import list_project_members
    from governance.rbac import get_user
    from domain.workflow import get_project

    project = get_project(project_id)
    if not project:
        raise HTTPException(404, f"Project '{project_id}' not found")

    members = list_project_members(project_id)

    # Enrich with display names
    enriched = []
    for m in members:
        u = get_user(m["user_id"])
        enriched.append({
            **m,
            "display_name": u["display_name"] if u else m["user_id"],
            "email": u["email"] if u else "",
        })

    # Include owner info
    owner_id = project.get("owner_id")
    owner_user = get_user(owner_id) if owner_id else None

    return {
        "project_id": project_id,
        "owner": {
            "user_id": owner_id,
            "display_name": owner_user["display_name"] if owner_user else owner_id,
            "email": owner_user["email"] if owner_user else "",
        } if owner_id else None,
        "members": enriched,
    }


@router.post("/{project_id}/members")
def add_member(
    project_id: str,
    body: AddMemberRequest,
    user: dict = Depends(require_project_access("manager")),
):
    """Add a user to a project with a given role. Requires manager+ role."""
    from governance.project_members import add_project_member

    try:
        member = add_project_member(
            project_id, body.user_id, body.role, user["user_id"]
        )
        return member
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.delete("/{project_id}/members/{member_user_id}")
def remove_member(
    project_id: str,
    member_user_id: str,
    user: dict = Depends(require_project_access("manager")),
):
    """Remove a user from a project. Requires manager+ role."""
    from governance.project_members import remove_project_member

    removed = remove_project_member(project_id, member_user_id, user["user_id"])
    if not removed:
        raise HTTPException(404, f"Member '{member_user_id}' not found in project")
    return {"removed": True, "user_id": member_user_id, "project_id": project_id}


@router.post("/{project_id}/transfer-ownership")
def transfer_ownership(
    project_id: str,
    body: TransferOwnershipRequest,
    user: dict = Depends(require_project_access("owner")),
):
    """Transfer project ownership. Requires owner role."""
    from governance.project_members import transfer_ownership as do_transfer

    try:
        project = do_transfer(project_id, body.new_owner_id, user["user_id"])
        return serialize_project(project)
    except ValueError as e:
        raise HTTPException(422, str(e))
