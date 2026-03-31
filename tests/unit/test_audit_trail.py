"""Tests for domain/audit_trail.py — Immutable hash-chained audit trail."""
import json
import pytest
import pandas as pd
from unittest.mock import patch, call, MagicMock


@pytest.fixture
def _patch_db():
    with patch("domain.audit_trail.query_df") as mock_q, \
         patch("domain.audit_trail.execute") as mock_e, \
         patch("domain.config_audit.query_df") as mock_cq, \
         patch("domain.config_audit.execute") as mock_ce:
        mock_q.return_value = pd.DataFrame()
        mock_cq.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e,
               "config_query_df": mock_cq, "config_execute": mock_ce}


class TestComputeHash:
    def test_deterministic(self):
        from domain.audit_trail import _compute_hash
        h1 = _compute_hash("GENESIS", "workflow", "P1", "created", {}, "2025-01-01T00:00:00")
        h2 = _compute_hash("GENESIS", "workflow", "P1", "created", {}, "2025-01-01T00:00:00")
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        from domain.audit_trail import _compute_hash
        h1 = _compute_hash("GENESIS", "workflow", "P1", "created", {}, "2025-01-01T00:00:00")
        h2 = _compute_hash("GENESIS", "workflow", "P2", "created", {}, "2025-01-01T00:00:00")
        assert h1 != h2

    def test_hash_is_sha256_hex(self):
        from domain.audit_trail import _compute_hash
        h = _compute_hash("GENESIS", "workflow", "P1", "created", {}, "2025-01-01T00:00:00")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_previous_hash_changes_result(self):
        from domain.audit_trail import _compute_hash
        h1 = _compute_hash("GENESIS", "workflow", "P1", "created", {}, "2025-01-01T00:00:00")
        h2 = _compute_hash("abc123", "workflow", "P1", "created", {}, "2025-01-01T00:00:00")
        assert h1 != h2

    def test_detail_changes_result(self):
        from domain.audit_trail import _compute_hash
        h1 = _compute_hash("GENESIS", "workflow", "P1", "created", {"a": 1}, "2025-01-01T00:00:00")
        h2 = _compute_hash("GENESIS", "workflow", "P1", "created", {"a": 2}, "2025-01-01T00:00:00")
        assert h1 != h2


class TestGetLastHash:
    def test_returns_genesis_when_empty(self, _patch_db):
        from domain.audit_trail import _get_last_hash
        assert _get_last_hash("P1") == "GENESIS"

    def test_returns_last_entry_hash(self, _patch_db):
        from domain.audit_trail import _get_last_hash
        _patch_db["query_df"].return_value = pd.DataFrame([{"entry_hash": "abc123"}])
        assert _get_last_hash("P1") == "abc123"

    def test_global_last_hash(self, _patch_db):
        from domain.audit_trail import _get_last_hash
        _patch_db["query_df"].return_value = pd.DataFrame([{"entry_hash": "xyz789"}])
        assert _get_last_hash(None) == "xyz789"


class TestAppendAuditEntry:
    def test_inserts_with_hash_chain(self, _patch_db):
        from domain.audit_trail import append_audit_entry
        result = append_audit_entry("P1", "workflow", "project", "P1", "created", "user1")
        assert result["previous_hash"] == "GENESIS"
        assert len(result["entry_hash"]) == 64
        assert result["project_id"] == "P1"
        assert result["performed_by"] == "user1"
        assert _patch_db["execute"].called

    def test_chains_from_previous(self, _patch_db):
        from domain.audit_trail import append_audit_entry
        _patch_db["query_df"].return_value = pd.DataFrame([{"entry_hash": "prev_hash_abc"}])
        result = append_audit_entry("P1", "workflow", "project", "P1", "advanced", "user2")
        assert result["previous_hash"] == "prev_hash_abc"

    def test_detail_included_in_entry(self, _patch_db):
        from domain.audit_trail import append_audit_entry
        detail = {"step": "data_processing", "status": "completed"}
        result = append_audit_entry("P1", "workflow", "step", "P1", "step_advanced", "user1", detail)
        assert result["detail"] == detail

    def test_null_project_id_allowed(self, _patch_db):
        from domain.audit_trail import append_audit_entry
        result = append_audit_entry(None, "config", "config", "model", "updated", "admin")
        assert result["project_id"] is None


class TestGetAuditTrail:
    def test_returns_empty_for_no_entries(self, _patch_db):
        from domain.audit_trail import get_audit_trail
        assert get_audit_trail("P1") == []

    def test_returns_ordered_entries(self, _patch_db):
        from domain.audit_trail import get_audit_trail
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"id": 1, "project_id": "P1", "event_type": "workflow",
             "entity_type": "project", "entity_id": "P1", "action": "created",
             "performed_by": "user1", "detail": json.dumps({}),
             "previous_hash": "GENESIS", "entry_hash": "abc",
             "created_at": "2025-01-01"},
        ])
        result = get_audit_trail("P1")
        assert len(result) == 1
        assert result[0]["action"] == "created"


class TestVerifyAuditChain:
    def test_empty_chain_is_valid(self, _patch_db):
        from domain.audit_trail import verify_audit_chain
        result = verify_audit_chain("P1")
        assert result["valid"] is True
        assert result["entries"] == 0

    def test_valid_single_entry(self, _patch_db):
        from domain.audit_trail import verify_audit_chain, _compute_hash
        created_at = "2025-01-01T00:00:00"
        entry_hash = _compute_hash("GENESIS", "workflow", "P1", "created", {}, created_at)
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"id": 1, "project_id": "P1", "event_type": "workflow",
             "entity_type": "project", "entity_id": "P1", "action": "created",
             "performed_by": "user1", "detail": {},
             "previous_hash": "GENESIS", "entry_hash": entry_hash,
             "created_at": created_at},
        ])
        result = verify_audit_chain("P1")
        assert result["valid"] is True
        assert result["entries"] == 1

    def test_broken_chain_detected(self, _patch_db):
        from domain.audit_trail import verify_audit_chain
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"id": 1, "project_id": "P1", "event_type": "workflow",
             "entity_type": "project", "entity_id": "P1", "action": "created",
             "performed_by": "user1", "detail": {},
             "previous_hash": "GENESIS", "entry_hash": "tampered_hash",
             "created_at": "2025-01-01T00:00:00"},
        ])
        result = verify_audit_chain("P1")
        assert result["valid"] is False
        assert result["broken_at_index"] == 0

    def test_valid_two_entry_chain(self, _patch_db):
        from domain.audit_trail import verify_audit_chain, _compute_hash
        ts1 = "2025-01-01T00:00:00"
        ts2 = "2025-01-01T01:00:00"
        h1 = _compute_hash("GENESIS", "workflow", "P1", "created", {}, ts1)
        h2 = _compute_hash(h1, "workflow", "P1", "advanced", {"step": "dp"}, ts2)
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"id": 1, "project_id": "P1", "event_type": "workflow",
             "entity_type": "project", "entity_id": "P1", "action": "created",
             "performed_by": "user1", "detail": {},
             "previous_hash": "GENESIS", "entry_hash": h1,
             "created_at": ts1},
            {"id": 2, "project_id": "P1", "event_type": "workflow",
             "entity_type": "project", "entity_id": "P1", "action": "advanced",
             "performed_by": "user1", "detail": {"step": "dp"},
             "previous_hash": h1, "entry_hash": h2,
             "created_at": ts2},
        ])
        result = verify_audit_chain("P1")
        assert result["valid"] is True
        assert result["entries"] == 2


class TestLogConfigChange:
    def test_inserts_change_record(self, _patch_db):
        from domain.audit_trail import log_config_change
        log_config_change("model", "lgd_assumptions", {"mortgage": 0.3}, {"mortgage": 0.25}, "admin")
        assert _patch_db["config_execute"].called
        args = _patch_db["config_execute"].call_args[0][1]
        assert args[0] == "model"
        assert args[4] == "admin"


class TestGetConfigAuditLog:
    def test_returns_empty(self, _patch_db):
        from domain.audit_trail import get_config_audit_log
        assert get_config_audit_log() == []

    def test_with_section_filter(self, _patch_db):
        from domain.audit_trail import get_config_audit_log
        _patch_db["config_query_df"].return_value = pd.DataFrame([{
            "id": 1, "section": "model", "config_key": None,
            "old_value": json.dumps({"a": 1}), "new_value": json.dumps({"a": 2}),
            "changed_by": "admin", "changed_at": "2025-01-01",
        }])
        result = get_config_audit_log("model")
        assert len(result) == 1
        assert result[0]["section"] == "model"


class TestExportAuditPackage:
    def test_returns_complete_package(self, _patch_db):
        from domain.audit_trail import export_audit_package
        result = export_audit_package("P1")
        assert result["project_id"] == "P1"
        assert "chain_verification" in result
        assert "audit_entries" in result
        assert "config_changes" in result
        assert "export_timestamp" in result


class TestMultiEntryBrokenChain:
    def test_broken_at_entry_2(self, _patch_db):
        from domain.audit_trail import verify_audit_chain, _compute_hash
        ts1 = "2025-01-01T00:00:00"
        ts2 = "2025-01-01T01:00:00"
        ts3 = "2025-01-01T02:00:00"
        h1 = _compute_hash("GENESIS", "workflow", "P1", "created", {}, ts1)
        h2 = _compute_hash(h1, "workflow", "P1", "advanced", {}, ts2)
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"id": 1, "project_id": "P1", "event_type": "workflow",
             "entity_type": "project", "entity_id": "P1", "action": "created",
             "performed_by": "u1", "detail": {},
             "previous_hash": "GENESIS", "entry_hash": h1, "created_at": ts1},
            {"id": 2, "project_id": "P1", "event_type": "workflow",
             "entity_type": "project", "entity_id": "P1", "action": "advanced",
             "performed_by": "u1", "detail": {},
             "previous_hash": h1, "entry_hash": h2, "created_at": ts2},
            {"id": 3, "project_id": "P1", "event_type": "workflow",
             "entity_type": "project", "entity_id": "P1", "action": "signed",
             "performed_by": "u1", "detail": {},
             "previous_hash": h2, "entry_hash": "TAMPERED_HASH", "created_at": ts3},
        ])
        result = verify_audit_chain("P1")
        assert result["valid"] is False
        assert result["broken_at_index"] == 2


class TestWorkflowAuditIntegration:
    def test_create_project_calls_audit(self):
        with patch("domain.workflow.query_df") as mock_q, \
             patch("domain.workflow.execute"), \
             patch("domain.audit_trail.query_df") as mock_aq, \
             patch("domain.audit_trail.execute") as mock_ae:
            mock_q.return_value = pd.DataFrame([{
                "project_id": "P1", "project_name": "Test", "project_type": "quarterly",
                "description": "d", "reporting_date": "2025-12-31", "current_step": 1,
                "step_status": '{"create_project":"completed"}', "audit_log": "[]",
                "overlays": "[]", "scenario_weights": "{}",
                "signed_off_by": None, "signed_off_at": None,
                "created_at": "2025-01-01", "updated_at": "2025-01-01",
            }])
            mock_aq.return_value = pd.DataFrame()
            from domain.workflow import create_project
            create_project("P1", "Test", "quarterly", "d", "2025-12-31")
            assert mock_ae.called

    def test_sign_off_stores_attestation_and_hash(self):
        with patch("domain.workflow.query_df") as mock_q, \
             patch("domain.workflow.execute") as mock_e, \
             patch("domain.audit_trail.query_df") as mock_aq, \
             patch("domain.audit_trail.execute"):
            proj_data = {
                "project_id": "P1", "project_name": "Test", "project_type": "quarterly",
                "description": "d", "reporting_date": "2025-12-31", "current_step": 7,
                "step_status": '{"sign_off":"pending"}', "audit_log": "[]",
                "overlays": "[]", "scenario_weights": "{}",
                "signed_off_by": None, "signed_off_at": None,
                "created_at": "2025-01-01", "updated_at": "2025-01-01",
            }
            mock_q.return_value = pd.DataFrame([proj_data])
            mock_aq.return_value = pd.DataFrame()
            from domain.workflow import sign_off_project
            attestation = {"confirmed_ecl_review": True, "confirmed_data_quality": True}
            sign_off_project("P1", "cfo@bank.com", attestation_data=attestation)
            update_call = mock_e.call_args_list[-1]
            sql = update_call[0][0]
            params = update_call[0][1]
            assert "attestation_data" in sql
            assert "ecl_hash" in sql
            attestation_param = params[3]
            ecl_hash_param = params[4]
            assert attestation_param is not None
            assert ecl_hash_param is not None and len(ecl_hash_param) == 64

    def test_save_overlays_calls_audit(self):
        with patch("domain.workflow.query_df") as mock_q, \
             patch("domain.workflow.execute"), \
             patch("domain.audit_trail.query_df") as mock_aq, \
             patch("domain.audit_trail.execute") as mock_ae:
            mock_q.return_value = pd.DataFrame([{
                "project_id": "P1", "project_name": "Test", "project_type": "quarterly",
                "description": "d", "reporting_date": "2025-12-31", "current_step": 5,
                "step_status": '{}', "audit_log": "[]",
                "overlays": "[]", "scenario_weights": "{}",
                "signed_off_by": None, "signed_off_at": None,
                "created_at": "2025-01-01", "updated_at": "2025-01-01",
            }])
            mock_aq.return_value = pd.DataFrame()
            from domain.workflow import save_overlays
            save_overlays("P1", [{"amount": 50000}], "analyst1")
            assert mock_ae.called


class TestEnsureAuditTables:
    def test_creates_tables(self, _patch_db):
        from domain.audit_trail import ensure_audit_tables
        ensure_audit_tables()
        assert _patch_db["execute"].call_count == 2
