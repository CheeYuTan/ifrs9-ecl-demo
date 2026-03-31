"""
Tests for attribution and audit trail routes — Sprint 4c coverage push.

These fill the remaining gaps in routes/attribution.py and routes/audit.py.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_db):
    import app as app_module
    return TestClient(app_module.app)


# ---------------------------------------------------------------------------
# Attribution routes — /api/data/attribution/*
# ---------------------------------------------------------------------------

class TestAttributionRoutes:
    def test_get_attribution_found_in_cache(self, client):
        attr = {"project_id": "proj-001", "waterfall": [{"label": "Stage 1 ECL", "value": 500000}]}
        with patch("backend.get_attribution", return_value=attr):
            resp = client.get("/api/data/attribution/proj-001")
        assert resp.status_code == 200
        assert resp.json()["project_id"] == "proj-001"

    def test_get_attribution_returns_null_when_not_cached(self, client):
        with patch("backend.get_attribution", return_value=None):
            resp = client.get("/api/data/attribution/proj-001")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_get_attribution_error_returns_500(self, client):
        with patch("backend.get_attribution", side_effect=Exception("db error")):
            resp = client.get("/api/data/attribution/proj-001")
        assert resp.status_code == 500

    def test_compute_attribution_success(self, client):
        attr = {"project_id": "proj-001", "waterfall": [{"label": "ECL Change", "value": 12000}]}
        with patch("backend.compute_attribution", return_value=attr):
            resp = client.post("/api/data/attribution/proj-001/compute")
        assert resp.status_code == 200
        assert resp.json()["project_id"] == "proj-001"

    def test_compute_attribution_error_returns_500(self, client):
        with patch("backend.compute_attribution", side_effect=Exception("not enough data")):
            resp = client.post("/api/data/attribution/proj-001/compute")
        assert resp.status_code == 500

    def test_attribution_history_success(self, client):
        history = [{"run_id": "r-001", "total_ecl": 1000000}]
        with patch("backend.get_attribution_history", return_value=history):
            resp = client.get("/api/data/attribution/proj-001/history")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_attribution_history_error_returns_500(self, client):
        with patch("backend.get_attribution_history", side_effect=Exception("db error")):
            resp = client.get("/api/data/attribution/proj-001/history")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Audit trail routes — /api/audit/*
# Patch at routes.audit module level since functions are imported directly
# ---------------------------------------------------------------------------

_AUDIT_BASE = "routes.audit"


class TestAuditRoutes:
    def test_get_project_audit_trail_found(self, client):
        trail = [{"entry_id": "e-001", "action": "sign_off", "user": "cfo"}]
        verification = {"valid": True, "entries": 1}
        with patch(f"{_AUDIT_BASE}.get_audit_trail", return_value=trail), \
             patch(f"{_AUDIT_BASE}.verify_audit_chain", return_value=verification):
            resp = client.get("/api/audit/proj-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "proj-001"
        assert data["chain_verification"]["valid"] is True
        assert len(data["entries"]) == 1

    def test_get_project_audit_trail_empty(self, client):
        with patch(f"{_AUDIT_BASE}.get_audit_trail", return_value=None):
            resp = client.get("/api/audit/proj-empty")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entries"] == []
        assert data["chain_verification"]["valid"] is True

    def test_verify_project_audit_success(self, client):
        verification = {"valid": True, "entries": 5, "hash_chain_ok": True}
        with patch(f"{_AUDIT_BASE}.verify_audit_chain", return_value=verification):
            resp = client.get("/api/audit/proj-001/verify")
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_export_project_audit_success(self, client):
        package = {"project_id": "proj-001", "entries": [], "export_ts": "2025-01-01T00:00:00Z"}
        with patch(f"{_AUDIT_BASE}.export_audit_package", return_value=package):
            resp = client.get("/api/audit/proj-001/export")
        assert resp.status_code == 200

    def test_export_project_audit_error_returns_500(self, client):
        with patch(f"{_AUDIT_BASE}.export_audit_package", side_effect=Exception("export failed")):
            resp = client.get("/api/audit/proj-001/export")
        assert resp.status_code == 500
