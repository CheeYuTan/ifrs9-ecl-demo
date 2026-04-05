"""Tests for Sprint 2: API Layer + Route Protection.

Tests the require_project_access and require_admin middleware, the project
members REST endpoints, and the protection applied to projects/admin/jobs routes.
"""
import json
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id, role="analyst"):
    from governance.rbac import ROLE_PERMISSIONS
    return {
        "user_id": user_id,
        "email": f"{user_id}@bank.com",
        "display_name": user_id.replace("-", " ").title(),
        "role": role,
        "permissions": list(ROLE_PERMISSIONS.get(role, set())),
    }


def _make_project(project_id="proj-1", owner_id="usr-owner"):
    return {
        "project_id": project_id,
        "project_name": "Test Project",
        "owner_id": owner_id,
        "current_step": 1,
        "step_status": json.dumps({"create_project": "completed"}),
        "audit_log": json.dumps([]),
        "overlays": json.dumps([]),
        "scenario_weights": json.dumps({}),
        "signed_off_by": None,
        "signed_off_at": None,
    }


# ---------------------------------------------------------------------------
# require_project_access middleware
# ---------------------------------------------------------------------------

class TestRequireProjectAccess:
    """Tests for middleware.auth.require_project_access dependency."""

    def test_anonymous_bypasses_check(self, fastapi_client):
        """No auth header -> anonymous user with owner project_role."""
        resp = fastapi_client.get("/api/projects/proj-1")
        # Without auth headers, should not get 403 (anonymous bypass)
        # It may 404 because project doesn't exist in mock DB, but not 403
        assert resp.status_code != 403

    @patch("middleware.auth.get_current_user")
    def test_admin_overrides_project_check(self, mock_get_user, fastapi_client):
        """Admin RBAC role should override project-level check."""
        mock_get_user.return_value = _make_user("usr-004", "admin")
        resp = fastapi_client.get(
            "/api/projects/proj-1",
            headers={"X-User-Id": "usr-004"},
        )
        # Admin bypasses project check; may 404 but not 403
        assert resp.status_code != 403

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_member_with_sufficient_role_passes(
        self, mock_get_user, mock_check, fastapi_client
    ):
        """User with viewer+ role on project should pass viewer check."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": True, "reason": "", "effective_role": "editor",
        }
        resp = fastapi_client.get(
            "/api/projects/proj-1",
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code != 403
        mock_check.assert_called_once_with("usr-001", "proj-1", "viewer")

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_member_with_insufficient_role_denied(
        self, mock_get_user, mock_check, fastapi_client
    ):
        """User with viewer role should be denied editor-required endpoint."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "Role 'viewer' insufficient; requires 'editor'",
            "effective_role": "viewer",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/advance",
            json={"action": "data_processing", "user": "test", "detail": "test"},
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403
        assert "access denied" in resp.json()["detail"].lower()

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_non_member_denied(self, mock_get_user, mock_check, fastapi_client):
        """User with no project access should be denied."""
        mock_get_user.return_value = _make_user("usr-999", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "User 'usr-999' has no access to project 'proj-1'",
            "effective_role": None,
        }
        resp = fastapi_client.get(
            "/api/projects/proj-1",
            headers={"X-User-Id": "usr-999"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# require_admin middleware
# ---------------------------------------------------------------------------

class TestRequireAdmin:
    """Tests for middleware.auth.require_admin dependency on admin routes."""

    def test_anonymous_bypasses_admin_check(self, fastapi_client):
        """No auth header -> anonymous bypass for admin routes."""
        resp = fastapi_client.get("/api/admin/config")
        # No 403 — anonymous dev mode bypasses
        assert resp.status_code != 403

    @patch("middleware.auth.get_current_user")
    def test_admin_user_allowed(self, mock_get_user, fastapi_client):
        """Admin role should access admin routes."""
        mock_get_user.return_value = _make_user("usr-004", "admin")
        resp = fastapi_client.get(
            "/api/admin/config",
            headers={"X-User-Id": "usr-004"},
        )
        assert resp.status_code != 403

    @patch("middleware.auth.get_current_user")
    def test_analyst_denied_admin_routes(self, mock_get_user, fastapi_client):
        """Non-admin role should be denied admin routes."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        resp = fastapi_client.get(
            "/api/admin/config",
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403
        assert "admin access required" in resp.json()["detail"].lower()

    @patch("middleware.auth.get_current_user")
    def test_reviewer_denied_admin_routes(self, mock_get_user, fastapi_client):
        """Reviewer role should be denied admin routes."""
        mock_get_user.return_value = _make_user("usr-002", "reviewer")
        resp = fastapi_client.get(
            "/api/admin/config",
            headers={"X-User-Id": "usr-002"},
        )
        assert resp.status_code == 403

    @patch("middleware.auth.get_current_user")
    def test_approver_denied_admin_routes(self, mock_get_user, fastapi_client):
        """Approver role should be denied admin routes."""
        mock_get_user.return_value = _make_user("usr-003", "approver")
        resp = fastapi_client.get(
            "/api/admin/config",
            headers={"X-User-Id": "usr-003"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Project list filtering
# ---------------------------------------------------------------------------

class TestProjectListFiltering:
    """Tests for GET /api/projects filtering by access."""

    _PROJECTS_DF = pd.DataFrame([
        {"project_id": "p1", "project_name": "P1", "project_type": "ifrs9",
         "current_step": 1, "created_at": "2024-01-01", "signed_off_by": None},
        {"project_id": "p2", "project_name": "P2", "project_type": "ifrs9",
         "current_step": 2, "created_at": "2024-01-02", "signed_off_by": None},
    ])

    @patch("backend.list_projects")
    def test_anonymous_sees_all(self, mock_list, fastapi_client):
        """Anonymous user sees all projects."""
        mock_list.return_value = self._PROJECTS_DF
        resp = fastapi_client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @patch("governance.project_permissions.get_effective_role")
    @patch("backend.list_projects")
    @patch("middleware.auth.get_current_user")
    def test_authenticated_user_sees_only_accessible(
        self, mock_get_user, mock_list, mock_eff_role, fastapi_client
    ):
        """Authenticated non-admin user sees only projects they have access to."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_list.return_value = self._PROJECTS_DF
        # User has access to p1 but not p2
        mock_eff_role.side_effect = lambda uid, pid: "editor" if pid == "p1" else None
        resp = fastapi_client.get(
            "/api/projects", headers={"X-User-Id": "usr-001"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["project_id"] == "p1"

    @patch("backend.list_projects")
    @patch("middleware.auth.get_current_user")
    def test_admin_sees_all(self, mock_get_user, mock_list, fastapi_client):
        """Admin user sees all projects."""
        mock_get_user.return_value = _make_user("usr-004", "admin")
        mock_list.return_value = pd.DataFrame([
            {"project_id": "p1", "project_name": "P1", "project_type": "ifrs9",
             "current_step": 1, "created_at": "2024-01-01", "signed_off_by": None},
        ])
        resp = fastapi_client.get(
            "/api/projects", headers={"X-User-Id": "usr-004"}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# Protected project routes
# ---------------------------------------------------------------------------

class TestProtectedProjectRoutes:
    """Tests for project routes that require specific project roles."""

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_advance_requires_editor(self, mock_get_user, mock_check, fastapi_client):
        """POST /projects/{id}/advance requires editor+ project role."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "Role 'viewer' insufficient; requires 'editor'",
            "effective_role": "viewer",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/advance",
            json={"action": "data_processing", "user": "test"},
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403
        mock_check.assert_called_with("usr-001", "proj-1", "editor")

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_overlays_requires_editor(self, mock_get_user, mock_check, fastapi_client):
        """POST /projects/{id}/overlays requires editor+ project role."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "Role 'viewer' insufficient; requires 'editor'",
            "effective_role": "viewer",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/overlays",
            json={"overlays": [], "comment": ""},
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_weights_requires_editor(self, mock_get_user, mock_check, fastapi_client):
        """POST /projects/{id}/scenario-weights requires editor+ project role."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "insufficient",
            "effective_role": "viewer",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/scenario-weights",
            json={"weights": {"base": 0.5, "optimistic": 0.25, "pessimistic": 0.25}},
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_reset_requires_manager(self, mock_get_user, mock_check, fastapi_client):
        """POST /projects/{id}/reset requires manager+ project role."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "insufficient",
            "effective_role": "editor",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/reset",
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Jobs route protection
# ---------------------------------------------------------------------------

class TestJobsRouteProtection:
    """Tests for job trigger route requiring RBAC permission."""

    def test_anonymous_trigger_allowed(self, fastapi_client):
        """Anonymous user bypasses auth on job trigger."""
        resp = fastapi_client.post(
            "/api/jobs/trigger",
            json={"job_key": "satellite_ecl_sync"},
        )
        # May fail due to actual job logic, but not 403
        assert resp.status_code != 403

    @patch("middleware.auth.get_current_user")
    def test_analyst_can_trigger(self, mock_get_user, fastapi_client):
        """Analyst has run_backtests permission -> can trigger jobs."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        resp = fastapi_client.post(
            "/api/jobs/trigger",
            json={"job_key": "satellite_ecl_sync"},
            headers={"X-User-Id": "usr-001"},
        )
        # Analyst has run_backtests; may fail on job logic but not 403
        assert resp.status_code != 403


# ---------------------------------------------------------------------------
# Project members REST endpoints
# ---------------------------------------------------------------------------

class TestProjectMembersEndpoints:
    """Tests for routes/project_members.py endpoints."""

    def test_list_members_anonymous(self, fastapi_client):
        """Anonymous user can list members (dev mode bypass)."""
        resp = fastapi_client.get("/api/projects/proj-1/members")
        # Anonymous bypasses access check; may 404 or 500 but not 403
        assert resp.status_code != 403

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_add_member_requires_manager(
        self, mock_get_user, mock_check, fastapi_client
    ):
        """POST members requires manager+ project role."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "insufficient",
            "effective_role": "editor",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/members",
            json={"user_id": "usr-002", "role": "viewer"},
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403
        mock_check.assert_called_with("usr-001", "proj-1", "manager")

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_remove_member_requires_manager(
        self, mock_get_user, mock_check, fastapi_client
    ):
        """DELETE members requires manager+ project role."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "insufficient",
            "effective_role": "editor",
        }
        resp = fastapi_client.delete(
            "/api/projects/proj-1/members/usr-002",
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_transfer_ownership_requires_owner(
        self, mock_get_user, mock_check, fastapi_client
    ):
        """POST transfer-ownership requires owner project role."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        mock_check.return_value = {
            "allowed": False,
            "reason": "insufficient",
            "effective_role": "manager",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/transfer-ownership",
            json={"new_owner_id": "usr-002"},
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403
        mock_check.assert_called_with("usr-001", "proj-1", "owner")

    @patch("governance.project_members.list_project_members")
    @patch("governance.rbac.get_user")
    @patch("domain.workflow.get_project")
    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_list_members_success(
        self, mock_get_user, mock_check, mock_get_proj, mock_rbac_user,
        mock_list_members, fastapi_client
    ):
        """Successful member listing with enriched display names."""
        mock_get_user.return_value = _make_user("usr-owner", "approver")
        mock_check.return_value = {
            "allowed": True, "reason": "", "effective_role": "owner",
        }
        mock_get_proj.return_value = {
            "project_id": "proj-1",
            "project_name": "Test",
            "owner_id": "usr-owner",
        }
        mock_list_members.return_value = [
            {"project_id": "proj-1", "user_id": "usr-001", "role": "editor",
             "granted_by": "usr-owner", "granted_at": "2024-01-01"},
        ]
        mock_rbac_user.side_effect = lambda uid: _make_user(uid)

        resp = fastapi_client.get(
            "/api/projects/proj-1/members",
            headers={"X-User-Id": "usr-owner"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "proj-1"
        assert data["owner"]["user_id"] == "usr-owner"
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "editor"

    @patch("governance.project_members.add_project_member")
    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_add_member_success(
        self, mock_get_user, mock_check, mock_add, fastapi_client
    ):
        """Successful member addition."""
        mock_get_user.return_value = _make_user("usr-mgr", "approver")
        mock_check.return_value = {
            "allowed": True, "reason": "", "effective_role": "manager",
        }
        mock_add.return_value = {
            "project_id": "proj-1", "user_id": "usr-001", "role": "viewer",
            "granted_by": "usr-mgr", "granted_at": "2024-01-01",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/members",
            json={"user_id": "usr-001", "role": "viewer"},
            headers={"X-User-Id": "usr-mgr"},
        )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "usr-001"
        mock_add.assert_called_once_with("proj-1", "usr-001", "viewer", "usr-mgr")

    @patch("governance.project_members.add_project_member")
    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_add_member_invalid_role(
        self, mock_get_user, mock_check, mock_add, fastapi_client
    ):
        """Adding member with invalid role returns 422."""
        mock_get_user.return_value = _make_user("usr-mgr", "approver")
        mock_check.return_value = {
            "allowed": True, "reason": "", "effective_role": "manager",
        }
        mock_add.side_effect = ValueError("Invalid role 'superuser'")
        resp = fastapi_client.post(
            "/api/projects/proj-1/members",
            json={"user_id": "usr-001", "role": "superuser"},
            headers={"X-User-Id": "usr-mgr"},
        )
        assert resp.status_code == 422

    @patch("governance.project_members.remove_project_member")
    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_remove_member_success(
        self, mock_get_user, mock_check, mock_remove, fastapi_client
    ):
        """Successful member removal."""
        mock_get_user.return_value = _make_user("usr-mgr", "approver")
        mock_check.return_value = {
            "allowed": True, "reason": "", "effective_role": "manager",
        }
        mock_remove.return_value = True
        resp = fastapi_client.delete(
            "/api/projects/proj-1/members/usr-001",
            headers={"X-User-Id": "usr-mgr"},
        )
        assert resp.status_code == 200
        assert resp.json()["removed"] is True

    @patch("governance.project_members.remove_project_member")
    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_remove_member_not_found(
        self, mock_get_user, mock_check, mock_remove, fastapi_client
    ):
        """Removing non-existent member returns 404."""
        mock_get_user.return_value = _make_user("usr-mgr", "approver")
        mock_check.return_value = {
            "allowed": True, "reason": "", "effective_role": "manager",
        }
        mock_remove.return_value = False
        resp = fastapi_client.delete(
            "/api/projects/proj-1/members/usr-999",
            headers={"X-User-Id": "usr-mgr"},
        )
        assert resp.status_code == 404

    @patch("governance.project_members.transfer_ownership")
    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_transfer_ownership_success(
        self, mock_get_user, mock_check, mock_transfer, fastapi_client
    ):
        """Successful ownership transfer."""
        mock_get_user.return_value = _make_user("usr-owner", "approver")
        mock_check.return_value = {
            "allowed": True, "reason": "", "effective_role": "owner",
        }
        mock_transfer.return_value = {
            "project_id": "proj-1", "project_name": "Test", "owner_id": "usr-002",
            "current_step": 1, "step_status": {}, "audit_log": [],
            "overlays": [], "scenario_weights": {},
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/transfer-ownership",
            json={"new_owner_id": "usr-002"},
            headers={"X-User-Id": "usr-owner"},
        )
        assert resp.status_code == 200
        assert resp.json()["owner_id"] == "usr-002"


# ---------------------------------------------------------------------------
# Sign-off dual-gate
# ---------------------------------------------------------------------------

class TestSignOffDualGate:
    """Tests for sign-off requiring both RBAC + project owner role."""

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_signoff_denied_without_rbac_permission(
        self, mock_get_user, mock_check, fastapi_client
    ):
        """Analyst without sign_off_projects RBAC should be denied."""
        mock_get_user.return_value = _make_user("usr-001", "analyst")
        # Even with owner project role, RBAC check happens first
        resp = fastapi_client.post(
            "/api/projects/proj-1/sign-off",
            json={"name": "usr-001"},
            headers={"X-User-Id": "usr-001"},
        )
        assert resp.status_code == 403

    @patch("governance.project_permissions.check_project_access")
    @patch("middleware.auth.get_current_user")
    def test_signoff_denied_without_project_owner_role(
        self, mock_get_user, mock_check, fastapi_client
    ):
        """Approver without project owner role should be denied."""
        mock_get_user.return_value = _make_user("usr-003", "approver")
        mock_check.return_value = {
            "allowed": False,
            "reason": "Role 'editor' insufficient; requires 'owner'",
            "effective_role": "editor",
        }
        resp = fastapi_client.post(
            "/api/projects/proj-1/sign-off",
            json={"name": "usr-003"},
            headers={"X-User-Id": "usr-003"},
        )
        assert resp.status_code == 403
