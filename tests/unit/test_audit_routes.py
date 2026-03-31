"""Route handler tests for /api/audit/* endpoints — Sprint 1 Iteration 3."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

TRAIL_MOD = "routes.audit"


@pytest.fixture
def client(mock_db):
    """FastAPI TestClient with backend fully mocked."""
    import app as app_module
    return TestClient(app_module.app)


class TestAuditTrailRoute:
    def test_empty_trail_returns_zero_total(self, client):
        with patch(f"{TRAIL_MOD}.get_audit_trail", return_value=[]):
            resp = client.get("/api/audit/P1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["entries"] == []

    def test_returns_entries_with_verification(self, client):
        entries = [{"id": 1, "action": "created", "entry_hash": "abc"}]
        verification = {"valid": True, "entries": 1}
        with patch(f"{TRAIL_MOD}.get_audit_trail", return_value=entries), \
             patch(f"{TRAIL_MOD}.verify_audit_chain", return_value=verification):
            resp = client.get("/api/audit/P1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["chain_verification"]["valid"] is True

    def test_pagination_offset_limit(self, client):
        entries = [{"id": i, "action": f"act_{i}"} for i in range(10)]
        verification = {"valid": True, "entries": 10}
        with patch(f"{TRAIL_MOD}.get_audit_trail", return_value=entries), \
             patch(f"{TRAIL_MOD}.verify_audit_chain", return_value=verification):
            resp = client.get("/api/audit/P1?offset=2&limit=3")
        data = resp.json()
        assert data["total"] == 10
        assert data["offset"] == 2
        assert data["limit"] == 3
        assert len(data["entries"]) == 3
        assert data["entries"][0]["id"] == 2

    def test_invalid_project_id_returns_400(self, client):
        resp = client.get("/api/audit/bad!id@here")
        assert resp.status_code == 400
        assert "Invalid project_id" in resp.json()["detail"]

    def test_valid_project_id_formats(self, client):
        for pid in ["P1", "test-proj-001", "MY_PROJECT_123"]:
            with patch(f"{TRAIL_MOD}.get_audit_trail", return_value=[]):
                resp = client.get(f"/api/audit/{pid}")
            assert resp.status_code == 200, f"Failed for project_id={pid}"


class TestAuditVerifyRoute:
    def test_verify_valid_chain(self, client):
        with patch(f"{TRAIL_MOD}.verify_audit_chain",
                   return_value={"valid": True, "entries": 5}):
            resp = client.get("/api/audit/P1/verify")
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_verify_invalid_project_id(self, client):
        resp = client.get("/api/audit/bad!id/verify")
        assert resp.status_code == 400


class TestAuditExportRoute:
    def test_export_returns_attachment(self, client):
        package = {"project_id": "P1", "audit_entries": [],
                   "config_changes": [], "export_timestamp": "2025-01-01",
                   "chain_verification": {"valid": True}}
        with patch(f"{TRAIL_MOD}.export_audit_package", return_value=package):
            resp = client.get("/api/audit/P1/export")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_export_error_returns_500(self, client):
        with patch(f"{TRAIL_MOD}.export_audit_package",
                   side_effect=Exception("DB down")):
            resp = client.get("/api/audit/P1/export")
        assert resp.status_code == 500

    def test_export_invalid_project_id(self, client):
        resp = client.get("/api/audit/bad!id/export")
        assert resp.status_code == 400


class TestConfigChangesRoute:
    def test_get_config_changes(self, client):
        changes = [{"section": "model", "config_key": "lgd", "changed_by": "admin"}]
        with patch(f"{TRAIL_MOD}.get_config_audit_log", return_value=changes):
            resp = client.get("/api/audit/config/changes")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_config_changes_with_section_filter(self, client):
        with patch(f"{TRAIL_MOD}.get_config_audit_log", return_value=[]) as mock_fn:
            resp = client.get("/api/audit/config/changes?section=model&limit=50")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("model", 50)


class TestConfigDiffRoute:
    def test_config_diff(self, client):
        diff = [{"key": "lgd", "old": 0.3, "new": 0.25}]
        with patch(f"{TRAIL_MOD}.get_config_diff", return_value=diff):
            resp = client.get("/api/audit/config/diff?start=2025-01-01")
        assert resp.status_code == 200
