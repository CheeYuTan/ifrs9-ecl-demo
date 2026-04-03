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
