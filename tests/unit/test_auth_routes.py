"""Tests for routes/auth.py — /api/auth/me and /api/auth/projects/{id}/my-role."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def _patch_db():
    """Patch database access to avoid real DB calls."""
    with patch("db.pool.execute"), \
         patch("db.pool.query_df"):
        yield


@pytest.fixture
def client(_patch_db):
    from app import app
    return TestClient(app)


class TestAuthMe:
    def test_anonymous_returns_analyst(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "anonymous"
        assert data["role"] == "analyst"
        assert isinstance(data["permissions"], list)

    def test_with_user_header_returns_user(self, client):
        with patch("routes.auth.get_current_user") as mock_user:
            mock_user.return_value = {
                "user_id": "usr-004",
                "email": "admin@bank.com",
                "display_name": "Admin User",
                "role": "admin",
                "permissions": [],
            }
            resp = client.get("/api/auth/me", headers={"X-User-Id": "usr-004"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["user_id"] == "usr-004"
            assert data["role"] == "admin"

    def test_me_has_expected_fields(self, client):
        resp = client.get("/api/auth/me")
        data = resp.json()
        assert "user_id" in data
        assert "email" in data
        assert "display_name" in data
        assert "role" in data
        assert "permissions" in data


class TestMyProjectRole:
    def test_anonymous_returns_owner(self, client):
        resp = client.get("/api/auth/projects/P1/my-role")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "anonymous"
        assert data["project_role"] == "owner"
        assert data["rbac_role"] == "analyst"

    def test_with_auth_header_returns_role(self, client):
        with patch("routes.auth.get_current_user") as mock_user, \
             patch("governance.project_permissions.get_effective_role") as mock_role:
            mock_user.return_value = {
                "user_id": "usr-001",
                "email": "ana@bank.com",
                "display_name": "Ana",
                "role": "analyst",
            }
            mock_role.return_value = "editor"
            resp = client.get(
                "/api/auth/projects/P1/my-role",
                headers={"X-User-Id": "usr-001"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["project_role"] == "editor"
            assert data["rbac_role"] == "analyst"

    def test_no_access_returns_403(self, client):
        with patch("routes.auth.get_current_user") as mock_user, \
             patch("governance.project_permissions.get_effective_role") as mock_role:
            mock_user.return_value = {
                "user_id": "usr-001",
                "email": "ana@bank.com",
                "display_name": "Ana",
                "role": "analyst",
            }
            mock_role.return_value = None
            resp = client.get(
                "/api/auth/projects/P1/my-role",
                headers={"X-User-Id": "usr-001"},
            )
            assert resp.status_code == 403

    def test_admin_gets_owner_role(self, client):
        with patch("routes.auth.get_current_user") as mock_user, \
             patch("governance.project_permissions.get_effective_role") as mock_role:
            mock_user.return_value = {
                "user_id": "usr-004",
                "email": "admin@bank.com",
                "display_name": "Admin",
                "role": "admin",
            }
            mock_role.return_value = "owner"
            resp = client.get(
                "/api/auth/projects/P1/my-role",
                headers={"X-User-Id": "usr-004"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["project_role"] == "owner"
            assert data["rbac_role"] == "admin"

    def test_response_has_required_fields(self, client):
        resp = client.get("/api/auth/projects/P1/my-role")
        data = resp.json()
        assert "user_id" in data
        assert "project_role" in data
        assert "rbac_role" in data
