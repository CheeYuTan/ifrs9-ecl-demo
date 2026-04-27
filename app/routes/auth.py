"""Authentication info routes -- /api/auth/*

Provides endpoints for the frontend to discover the current user's identity
and their effective role within a specific project.
"""

from fastapi import APIRouter, HTTPException, Request
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
def auth_me(request: Request):
    """Return the current user's RBAC identity.

    Anonymous (no auth header) returns the anonymous fallback user.
    """
    user = get_current_user(request)
    from governance.rbac import ROLE_PERMISSIONS

    role = user.get("role", "analyst")
    permissions = list(ROLE_PERMISSIONS.get(role, set()))
    return {
        "user_id": user["user_id"],
        "email": user.get("email", ""),
        "display_name": user.get("display_name", ""),
        "role": role,
        "permissions": permissions,
    }


@router.get("/projects/{project_id}/my-role")
def my_project_role(project_id: str, request: Request):
    """Return the current user's effective role within a project.

    Anonymous (no auth header) returns owner (dev mode bypass).
    """
    has_auth = bool(
        request.headers.get("X-Forwarded-User") or request.headers.get("X-User-Id") or request.headers.get("x-user-id")
    )
    if not has_auth:
        return {
            "user_id": "anonymous",
            "project_role": "owner",
            "rbac_role": "analyst",
        }

    user = get_current_user(request)
    from governance.project_permissions import get_effective_role

    effective = get_effective_role(user["user_id"], project_id)
    if effective is None:
        raise HTTPException(
            403,
            f"User '{user['user_id']}' has no access to project '{project_id}'",
        )

    return {
        "user_id": user["user_id"],
        "project_role": effective,
        "rbac_role": user.get("role", "analyst"),
    }
