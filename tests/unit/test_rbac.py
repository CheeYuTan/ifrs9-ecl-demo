"""
Unit tests for RBAC enforcement middleware and governance controls.

Tests:
  - User extraction from request headers
  - Permission checking by role
  - Segregation of duties enforcement
  - Project immutability after sign-off
  - ECL hash computation and verification
"""
import pytest
import json
import hashlib
from unittest.mock import patch, MagicMock

from governance.rbac import (
    ROLE_PERMISSIONS, SEED_USERS,
    check_permission,
)
from middleware.auth import (
    get_current_user, require_permission,
    compute_ecl_hash, verify_ecl_hash,
    ANONYMOUS_USER,
)


class TestRolePermissions:
    """Verify role-permission matrix is correctly defined."""

    def test_analyst_cannot_sign_off(self):
        assert "sign_off_projects" not in ROLE_PERMISSIONS["analyst"]

    def test_analyst_cannot_approve(self):
        assert "approve_requests" not in ROLE_PERMISSIONS["analyst"]

    def test_approver_can_sign_off(self):
        assert "sign_off_projects" in ROLE_PERMISSIONS["approver"]

    def test_approver_can_approve(self):
        assert "approve_requests" in ROLE_PERMISSIONS["approver"]

    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS["admin"]
        for role, perms in ROLE_PERMISSIONS.items():
            for p in perms:
                assert p in admin_perms, f"Admin missing permission '{p}' from role '{role}'"

    def test_reviewer_cannot_sign_off(self):
        assert "sign_off_projects" not in ROLE_PERMISSIONS["reviewer"]

    def test_all_roles_can_view_portfolio(self):
        for role, perms in ROLE_PERMISSIONS.items():
            assert "view_portfolio" in perms, f"Role '{role}' cannot view portfolio"


class TestCheckPermission:
    """Test the check_permission function from governance.rbac."""

    @patch("governance.rbac.get_user")
    def test_analyst_denied_sign_off(self, mock_get_user):
        mock_get_user.return_value = {
            "user_id": "usr-001", "role": "analyst",
            "permissions": list(ROLE_PERMISSIONS["analyst"]),
        }
        result = check_permission("usr-001", "sign_off_projects")
        assert result["allowed"] == False

    @patch("governance.rbac.get_user")
    def test_approver_allowed_sign_off(self, mock_get_user):
        mock_get_user.return_value = {
            "user_id": "usr-003", "role": "approver",
            "permissions": list(ROLE_PERMISSIONS["approver"]),
        }
        result = check_permission("usr-003", "sign_off_projects")
        assert result["allowed"] == True

    @patch("governance.rbac.get_user")
    def test_unknown_user_denied(self, mock_get_user):
        mock_get_user.return_value = None
        result = check_permission("unknown", "view_portfolio")
        assert result["allowed"] == False
        assert "not found" in result["reason"]


class TestGetCurrentUser:
    """Test user extraction from request headers."""

    def test_anonymous_when_no_headers(self):
        request = MagicMock()
        request.headers = {}
        user = get_current_user(request)
        assert user["user_id"] == "anonymous"
        assert user["role"] == "analyst"

    def test_extracts_x_forwarded_user(self):
        request = MagicMock()
        request.headers = {"X-Forwarded-User": "usr-003"}
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = {
                "user_id": "usr-003", "role": "approver",
                "display_name": "Sarah Chen",
                "permissions": list(ROLE_PERMISSIONS["approver"]),
            }
            user = get_current_user(request)
            assert user["user_id"] == "usr-003"
            assert user["role"] == "approver"

    def test_extracts_x_user_id(self):
        request = MagicMock()
        request.headers = {"X-User-Id": "usr-001"}
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = {
                "user_id": "usr-001", "role": "analyst",
                "display_name": "Ana Reyes",
                "permissions": list(ROLE_PERMISSIONS["analyst"]),
            }
            user = get_current_user(request)
            assert user["user_id"] == "usr-001"

    def test_unknown_user_gets_analyst_role(self):
        request = MagicMock()
        request.headers = {"X-User-Id": "unknown-user"}
        with patch("governance.rbac.get_user") as mock_get:
            mock_get.return_value = None
            user = get_current_user(request)
            assert user["user_id"] == "unknown-user"
            assert user["role"] == "analyst"


class TestECLHash:
    """Test cryptographic hash computation for immutability verification."""

    def test_deterministic_hash(self):
        data = {"total_ecl": 1234567.89, "stage_1": 500000, "stage_2": 300000}
        hash1 = compute_ecl_hash(data)
        hash2 = compute_ecl_hash(data)
        assert hash1 == hash2

    def test_different_data_different_hash(self):
        data1 = {"total_ecl": 1234567.89}
        data2 = {"total_ecl": 1234567.90}
        assert compute_ecl_hash(data1) != compute_ecl_hash(data2)

    def test_hash_is_sha256(self):
        data = {"test": "value"}
        h = compute_ecl_hash(data)
        assert len(h) == 64  # SHA-256 produces 64 hex chars

    def test_verify_correct_hash(self):
        data = {"total_ecl": 999.99, "products": ["credit_card", "mortgage"]}
        h = compute_ecl_hash(data)
        assert verify_ecl_hash(data, h) == True

    def test_verify_tampered_data(self):
        data = {"total_ecl": 999.99}
        h = compute_ecl_hash(data)
        data["total_ecl"] = 1000.00
        assert verify_ecl_hash(data, h) == False

    def test_key_order_independent(self):
        data1 = {"b": 2, "a": 1}
        data2 = {"a": 1, "b": 2}
        assert compute_ecl_hash(data1) == compute_ecl_hash(data2)


class TestSeedUsers:
    """Verify seed users cover required roles for segregation of duties."""

    def test_has_analyst(self):
        roles = [u[3] for u in SEED_USERS]
        assert "analyst" in roles

    def test_has_approver(self):
        roles = [u[3] for u in SEED_USERS]
        assert "approver" in roles

    def test_has_reviewer(self):
        roles = [u[3] for u in SEED_USERS]
        assert "reviewer" in roles

    def test_has_admin(self):
        roles = [u[3] for u in SEED_USERS]
        assert "admin" in roles

    def test_at_least_four_users(self):
        assert len(SEED_USERS) >= 4


# ── Extended coverage for list_users, get_user, approval lifecycle ─────

import pandas as pd

_M = "governance.rbac"


def _user_df(user_id="usr-001", role="analyst"):
    return pd.DataFrame([{
        "user_id": user_id, "email": f"{user_id}@bank.com",
        "display_name": "Test User", "role": role,
        "department": "Risk", "is_active": True,
    }])


def _approval_df(request_id="apr-1", status="pending"):
    return pd.DataFrame([{
        "request_id": request_id, "request_type": "model_approval",
        "entity_id": "model-1", "entity_type": "model",
        "status": status, "requested_by": "usr-001",
        "assigned_to": "usr-003", "approved_by": None,
        "approved_at": None, "rejection_reason": "",
        "comments": "", "priority": "normal", "due_date": None,
        "created_at": "2025-01-01T00:00:00",
        "requested_by_name": "Ana Reyes",
        "assigned_to_name": "Sarah Chen",
        "approved_by_name": None,
    }])


class TestListUsers:
    @patch(f"{_M}.query_df")
    def test_list_all(self, mock_qdf):
        mock_qdf.return_value = pd.DataFrame([
            {"user_id": "usr-001", "display_name": "Ana", "role": "analyst"},
            {"user_id": "usr-002", "display_name": "David", "role": "reviewer"},
        ])
        from governance.rbac import list_users
        result = list_users()
        assert len(result) == 2
        call_sql = mock_qdf.call_args[0][0]
        assert "is_active = TRUE" in call_sql

    @patch(f"{_M}.query_df")
    def test_filter_by_role(self, mock_qdf):
        mock_qdf.return_value = _user_df()
        from governance.rbac import list_users
        list_users(role="analyst")
        call_sql = mock_qdf.call_args[0][0]
        assert "role = %s" in call_sql


class TestGetUser:
    @patch(f"{_M}.query_df", return_value=_user_df("usr-001", "analyst"))
    def test_found_with_permissions(self, mock_qdf):
        from governance.rbac import get_user
        user = get_user("usr-001")
        assert user is not None
        assert user["user_id"] == "usr-001"
        assert "permissions" in user
        assert "view_portfolio" in user["permissions"]

    @patch(f"{_M}.query_df", return_value=pd.DataFrame())
    def test_not_found(self, mock_qdf):
        from governance.rbac import get_user
        assert get_user("nonexistent") is None


class TestApproveRequest:
    @patch(f"{_M}.query_df")
    @patch(f"{_M}.execute")
    def test_approve_success(self, mock_exec, mock_qdf):
        mock_qdf.side_effect = [
            _user_df("usr-003", "approver"),
            _approval_df("apr-1", "pending"),
            _approval_df("apr-1", "approved"),
        ]
        from governance.rbac import approve_request
        result = approve_request("apr-1", "usr-003", "Looks good")
        assert result is not None
        call_sql = mock_exec.call_args[0][0]
        assert "status = 'approved'" in call_sql

    @patch(f"{_M}.query_df")
    def test_approve_no_permission(self, mock_qdf):
        mock_qdf.return_value = _user_df("usr-001", "analyst")
        from governance.rbac import approve_request
        with pytest.raises(ValueError, match="does not have permission"):
            approve_request("apr-1", "usr-001")

    @patch(f"{_M}.query_df")
    def test_approve_already_approved(self, mock_qdf):
        mock_qdf.side_effect = [
            _user_df("usr-003", "approver"),
            _approval_df("apr-1", "approved"),
        ]
        from governance.rbac import approve_request
        with pytest.raises(ValueError, match="already approved"):
            approve_request("apr-1", "usr-003")

    @patch(f"{_M}.query_df")
    def test_approve_not_found(self, mock_qdf):
        mock_qdf.side_effect = [
            _user_df("usr-003", "approver"),
            pd.DataFrame(),
        ]
        from governance.rbac import approve_request
        with pytest.raises(ValueError, match="not found"):
            approve_request("apr-nonexist", "usr-003")


class TestRejectRequest:
    @patch(f"{_M}.query_df")
    @patch(f"{_M}.execute")
    def test_reject_success(self, mock_exec, mock_qdf):
        mock_qdf.side_effect = [
            _user_df("usr-003", "approver"),
            _approval_df("apr-1", "pending"),
            _approval_df("apr-1", "rejected"),
        ]
        from governance.rbac import reject_request
        result = reject_request("apr-1", "usr-003", "Needs revision")
        assert result is not None
        call_sql = mock_exec.call_args[0][0]
        assert "status = 'rejected'" in call_sql

    @patch(f"{_M}.query_df")
    def test_reject_no_permission(self, mock_qdf):
        mock_qdf.return_value = _user_df("usr-001", "analyst")
        from governance.rbac import reject_request
        with pytest.raises(ValueError, match="does not have permission"):
            reject_request("apr-1", "usr-001")


class TestApprovalHistory:
    @patch(f"{_M}.query_df")
    def test_returns_history(self, mock_qdf):
        mock_qdf.return_value = pd.DataFrame([
            {"request_id": "apr-1", "entity_id": "model-1", "status": "approved",
             "requested_by_name": "Ana", "approved_by_name": "Sarah"},
            {"request_id": "apr-2", "entity_id": "model-1", "status": "rejected",
             "requested_by_name": "Ana", "approved_by_name": "David"},
        ])
        from governance.rbac import get_approval_history
        result = get_approval_history("model-1")
        assert len(result) == 2

    @patch(f"{_M}.query_df", return_value=pd.DataFrame())
    def test_empty_history(self, mock_qdf):
        from governance.rbac import get_approval_history
        assert get_approval_history("no-entity") == []


class TestRoleHierarchy:
    def test_role_hierarchy_is_cumulative(self):
        analyst = ROLE_PERMISSIONS["analyst"]
        reviewer = ROLE_PERMISSIONS["reviewer"]
        approver = ROLE_PERMISSIONS["approver"]
        admin = ROLE_PERMISSIONS["admin"]
        assert analyst.issubset(reviewer)
        assert reviewer.issubset(approver)
        assert approver.issubset(admin)
