"""
Authentication and RBAC middleware for IFRS 9 ECL Platform.

Extracts user identity from:
  1. Databricks OAuth token (X-Forwarded-User header in Databricks Apps)
  2. X-User-Id header (for development/testing)
  3. Falls back to anonymous with analyst role

Provides FastAPI dependencies for:
  - get_current_user: Extract authenticated user
  - require_permission(action): Check user has specific permission
  - require_not_same_user(project_field): Segregation of duties
"""

import hashlib
import json
import logging

from fastapi import HTTPException, Request

log = logging.getLogger(__name__)

ANONYMOUS_USER = {
    "user_id": "anonymous",
    "email": "anonymous@local",
    "display_name": "Anonymous User",
    "role": "analyst",
    "permissions": [],
}


def get_current_user(request: Request) -> dict:
    """Extract authenticated user from request headers."""
    user_id = (
        request.headers.get("X-Forwarded-User") or request.headers.get("X-User-Id") or request.headers.get("x-user-id")
    )

    if not user_id:
        return dict(ANONYMOUS_USER)

    try:
        from governance.rbac import ROLE_PERMISSIONS, get_user

        user = get_user(user_id)
        if user:
            return user
        return {
            "user_id": user_id,
            "email": user_id,
            "display_name": user_id,
            "role": "analyst",
            "permissions": list(ROLE_PERMISSIONS.get("analyst", set())),
        }
    except Exception:
        return {
            "user_id": user_id,
            "email": user_id,
            "display_name": user_id,
            "role": "analyst",
            "permissions": [],
        }


def require_permission(action: str):
    """FastAPI dependency that checks if the current user has a specific permission.

    In Databricks Apps, the X-Forwarded-User header is always set by the OAuth proxy.
    In local dev/testing (no header), RBAC is bypassed to allow unauthenticated access.
    """

    def _check(request: Request):
        has_auth_header = bool(
            request.headers.get("X-Forwarded-User")
            or request.headers.get("X-User-Id")
            or request.headers.get("x-user-id")
        )
        if not has_auth_header:
            return dict(ANONYMOUS_USER)

        user = get_current_user(request)
        from governance.rbac import ROLE_PERMISSIONS

        role = user.get("role", "analyst")
        perms = ROLE_PERMISSIONS.get(role, set())
        if action not in perms:
            raise HTTPException(
                status_code=403, detail=f"Permission denied: role '{role}' does not have '{action}' permission"
            )
        return user

    return _check


def require_project_access(min_role: str = "viewer", project_id_param: str = "project_id"):
    """FastAPI dependency that checks project-level access (Layer 2).

    Combines with Layer 1 RBAC: user must have the right global role AND
    the right project role.  Anonymous (no auth header) bypasses all checks.
    Admin RBAC role overrides project-level checks.

    Returns the user dict enriched with ``project_role``.
    """

    def _check(request: Request):
        has_auth_header = bool(
            request.headers.get("X-Forwarded-User")
            or request.headers.get("X-User-Id")
            or request.headers.get("x-user-id")
        )
        if not has_auth_header:
            user = dict(ANONYMOUS_USER)
            user["project_role"] = "owner"
            return user

        user = get_current_user(request)

        # Admin override — full access to all projects
        if user.get("role") == "admin":
            user["project_role"] = "owner"
            return user

        pid = request.path_params.get(project_id_param)
        if not pid:
            raise HTTPException(400, "Missing project_id in path")

        from governance.project_permissions import check_project_access

        result = check_project_access(user["user_id"], pid, min_role)
        if not result["allowed"]:
            raise HTTPException(403, f"Project access denied: {result['reason']}")
        user["project_role"] = result["effective_role"]
        return user

    return _check


def require_admin():
    """FastAPI dependency that requires admin RBAC role.

    Anonymous (no auth header) bypasses the check (dev mode).
    """

    def _check(request: Request):
        has_auth_header = bool(
            request.headers.get("X-Forwarded-User")
            or request.headers.get("X-User-Id")
            or request.headers.get("x-user-id")
        )
        if not has_auth_header:
            return dict(ANONYMOUS_USER)

        user = get_current_user(request)
        if user.get("role") != "admin":
            raise HTTPException(403, f"Admin access required. Current role: '{user.get('role')}'")
        return user

    return _check


def require_project_not_locked(project_id_param: str = "project_id"):
    """FastAPI dependency that blocks mutations on signed-off projects."""

    def _check(request: Request, **kwargs):
        pid = request.path_params.get(project_id_param)
        if not pid:
            return
        try:
            from domain.workflow import get_project

            project = get_project(pid)
            if project and project.get("signed_off"):
                raise HTTPException(
                    status_code=403, detail=f"Project {pid} is signed off and immutable. No modifications allowed."
                )
        except HTTPException:
            raise
        except Exception:
            pass

    return _check


def compute_ecl_hash(ecl_data: dict) -> str:
    """Compute SHA-256 hash of ECL results for immutability verification."""
    canonical = json.dumps(ecl_data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify_ecl_hash(ecl_data: dict, expected_hash: str) -> bool:
    """Verify that ECL results have not been tampered with since sign-off."""
    return compute_ecl_hash(ecl_data) == expected_hash
