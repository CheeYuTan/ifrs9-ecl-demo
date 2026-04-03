"""Tests for Sprint 4: Attestation Persistence & ECL Hash Verification.

Covers:
  - Attestation data passed through sign-off and stored
  - ECL hash computation and verification
  - Hash verification endpoint
  - Approval history endpoint
"""
import json
import hashlib
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


# ── ECL Hash Tests ──────────────────────────────────────────────────────────

class TestECLHashComputation:
    """Tests for compute_ecl_hash and verify_ecl_hash."""

    def test_compute_hash_returns_sha256(self):
        from middleware.auth import compute_ecl_hash
        ecl_data = {"project_id": "test", "step_status": {"sign_off": "completed"}}
        result = compute_ecl_hash(ecl_data)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest length

    def test_same_data_produces_same_hash(self):
        from middleware.auth import compute_ecl_hash
        data = {"project_id": "test", "overlays": [{"amount": 100}]}
        h1 = compute_ecl_hash(data)
        h2 = compute_ecl_hash(data)
        assert h1 == h2

    def test_different_data_produces_different_hash(self):
        from middleware.auth import compute_ecl_hash
        d1 = {"project_id": "test", "overlays": [{"amount": 100}]}
        d2 = {"project_id": "test", "overlays": [{"amount": 200}]}
        assert compute_ecl_hash(d1) != compute_ecl_hash(d2)

    def test_verify_ecl_hash_valid(self):
        from middleware.auth import compute_ecl_hash, verify_ecl_hash
        data = {"project_id": "test", "step_status": {}}
        h = compute_ecl_hash(data)
        assert verify_ecl_hash(data, h) is True

    def test_verify_ecl_hash_invalid(self):
        from middleware.auth import compute_ecl_hash, verify_ecl_hash
        data = {"project_id": "test", "step_status": {}}
        assert verify_ecl_hash(data, "wrong_hash") is False

    def test_hash_is_deterministic_with_key_order(self):
        """Ensure key ordering doesn't affect hash (sorted keys)."""
        from middleware.auth import compute_ecl_hash
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        assert compute_ecl_hash(d1) == compute_ecl_hash(d2)


# ── Hash Verification Endpoint Tests ────────────────────────────────────────

class TestVerifyHashEndpoint:
    """Tests for GET /api/projects/{id}/verify-hash"""

    def test_verify_hash_valid(self, fastapi_client, mock_db):
        from middleware.auth import compute_ecl_hash
        ecl_data = {
            "project_id": "proj-001",
            "step_status": {"sign_off": "completed"},
            "overlays": [],
            "scenario_weights": {},
        }
        stored_hash = compute_ecl_hash(ecl_data)
        proj = {
            "project_id": "proj-001",
            "ecl_hash": stored_hash,
            "step_status": {"sign_off": "completed"},
            "overlays": [],
            "scenario_weights": {},
            "signed_off_by": "CFO",
            "signed_off_at": "2025-12-31T10:00:00Z",
        }
        with patch("backend.get_project", return_value=proj):
            resp = fastapi_client.get("/api/projects/proj-001/verify-hash")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "valid"
        assert data["match"] is True

    def test_verify_hash_invalid(self, fastapi_client, mock_db):
        proj = {
            "project_id": "proj-002",
            "ecl_hash": "tampered_hash_value",
            "step_status": {"sign_off": "completed"},
            "overlays": [],
            "scenario_weights": {},
            "signed_off_by": "CFO",
            "signed_off_at": "2025-12-31T10:00:00Z",
        }
        with patch("backend.get_project", return_value=proj):
            resp = fastapi_client.get("/api/projects/proj-002/verify-hash")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "invalid"
        assert data["match"] is False

    def test_verify_hash_not_computed(self, fastapi_client, mock_db):
        proj = {
            "project_id": "proj-003",
            "ecl_hash": None,
            "step_status": {},
            "overlays": [],
            "scenario_weights": {},
        }
        with patch("backend.get_project", return_value=proj):
            resp = fastapi_client.get("/api/projects/proj-003/verify-hash")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_computed"

    def test_verify_hash_project_not_found(self, fastapi_client, mock_db):
        with patch("backend.get_project", return_value=None):
            resp = fastapi_client.get("/api/projects/nonexistent/verify-hash")
        assert resp.status_code == 404


# ── Sign-Off with Attestation Tests ─────────────────────────────────────────

class TestSignOffWithAttestation:
    """Tests for sign-off passing attestation_data through."""

    def test_signoff_accepts_attestation_data(self, fastapi_client, mock_db):
        proj = {
            "project_id": "proj-att-001",
            "signed_off": False,
            "signed_off_by": None,
            "audit_log": [],
        }
        signed_proj = {**proj, "signed_off_by": "CFO", "signed_off": True, "ecl_hash": "abc123"}
        with patch("backend.get_project", return_value=proj):
            with patch("backend.sign_off_project", return_value=signed_proj) as mock_sign:
                resp = fastapi_client.post("/api/projects/proj-att-001/sign-off", json={
                    "name": "CFO",
                    "attestation_data": {
                        "items": [
                            {"checked": True, "label": "ECL model compliant"},
                            {"checked": True, "label": "Overlays reviewed"},
                        ],
                        "signed_by": "CFO",
                    },
                })
        assert resp.status_code == 200
        # Verify attestation_data was passed to backend
        mock_sign.assert_called_once()
        call_kwargs = mock_sign.call_args
        assert call_kwargs[1].get("attestation_data") is not None or (
            len(call_kwargs[0]) > 2 if call_kwargs[0] else False
        )

    def test_signoff_without_attestation_still_works(self, fastapi_client, mock_db):
        proj = {"project_id": "proj-att-002", "signed_off": False, "audit_log": []}
        signed_proj = {**proj, "signed_off_by": "CRO", "signed_off": True}
        with patch("backend.get_project", return_value=proj):
            with patch("backend.sign_off_project", return_value=signed_proj):
                resp = fastapi_client.post("/api/projects/proj-att-002/sign-off", json={
                    "name": "CRO",
                })
        assert resp.status_code == 200


# ── Approval History Endpoint Tests ─────────────────────────────────────────

class TestApprovalHistoryEndpoint:
    """Tests for GET /api/projects/{id}/approval-history"""

    def test_approval_history_returns_list(self, fastapi_client, mock_db):
        history = [
            {"request_id": "r-1", "status": "approved", "approved_by": "admin"},
            {"request_id": "r-2", "status": "rejected", "rejection_reason": "Incomplete"},
        ]
        with patch("governance.rbac.get_approval_history", return_value=history):
            resp = fastapi_client.get("/api/projects/proj-001/approval-history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_approval_history_empty(self, fastapi_client, mock_db):
        with patch("governance.rbac.get_approval_history", return_value=[]):
            resp = fastapi_client.get("/api/projects/proj-new/approval-history")
        assert resp.status_code == 200
        assert resp.json() == []
