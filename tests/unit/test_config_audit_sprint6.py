"""Tests for Sprint 6: Config Change Tracking.

Covers:
  - Config audit log table and logging
  - Config change history endpoint (GET /api/audit/config/changes)
  - Config diff endpoint (GET /api/audit/config/diff)
  - save_config and save_config_section both log changes
  - Config diff with section filter
  - Config diff with time range
"""
import json
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone
import pandas as pd

AUDIT_MOD = "domain.config_audit"


# ── Config Audit Log Function Tests ────────────────────────────────────────

class TestLogConfigChange:
    """Tests for log_config_change in domain/audit_trail.py."""

    def test_log_config_change_calls_execute(self):
        with patch(f"{AUDIT_MOD}.execute") as mock_exec:
            from domain.audit_trail import log_config_change
            log_config_change("model_config", "lgd_assumptions",
                              {"old": 0.4}, {"new": 0.5}, "risk_mgr")
            mock_exec.assert_called_once()
            args = mock_exec.call_args[0]
            assert "config_audit_log" in args[0]
            params = args[1]
            assert params[0] == "model_config"
            assert params[1] == "lgd_assumptions"
            assert params[4] == "risk_mgr"

    def test_log_config_change_serializes_values(self):
        with patch(f"{AUDIT_MOD}.execute") as mock_exec:
            from domain.audit_trail import log_config_change
            log_config_change("scenarios", None,
                              {"weights": [0.5, 0.3, 0.2]},
                              {"weights": [0.4, 0.3, 0.3]}, "admin")
            params = mock_exec.call_args[0][1]
            old_val = json.loads(params[2])
            new_val = json.loads(params[3])
            assert old_val["weights"] == [0.5, 0.3, 0.2]
            assert new_val["weights"] == [0.4, 0.3, 0.3]


# ── Config Audit Log Retrieval Tests ───────────────────────────────────────

class TestGetConfigAuditLog:
    """Tests for get_config_audit_log."""

    def test_empty_log(self):
        with patch(f"{AUDIT_MOD}.query_df", return_value=pd.DataFrame()):
            from domain.audit_trail import get_config_audit_log
            result = get_config_audit_log()
            assert result == []

    def test_returns_records_with_parsed_json(self):
        df = pd.DataFrame([{
            "id": 1, "section": "model_config", "config_key": "lgd",
            "old_value": '{"val": 0.4}', "new_value": '{"val": 0.5}',
            "changed_by": "admin", "changed_at": "2025-12-31T10:00:00",
        }])
        with patch(f"{AUDIT_MOD}.query_df", return_value=df):
            from domain.audit_trail import get_config_audit_log
            result = get_config_audit_log()
            assert len(result) == 1
            assert result[0]["old_value"] == {"val": 0.4}
            assert result[0]["new_value"] == {"val": 0.5}

    def test_filter_by_section(self):
        with patch(f"{AUDIT_MOD}.query_df", return_value=pd.DataFrame()) as mock_q:
            from domain.audit_trail import get_config_audit_log
            get_config_audit_log(section="model_config")
            query_str = mock_q.call_args[0][0]
            assert "section = %s" in query_str


# ── Config Diff Tests ──────────────────────────────────────────────────────

class TestGetConfigDiff:
    """Tests for get_config_diff."""

    def test_empty_diff(self):
        with patch(f"{AUDIT_MOD}.query_df", return_value=pd.DataFrame()):
            from domain.audit_trail import get_config_diff
            result = get_config_diff("2025-01-01")
            assert result == []

    def test_diff_with_results(self):
        df = pd.DataFrame([{
            "section": "scenarios", "config_key": None,
            "old_value": '{"weight": 0.5}', "new_value": '{"weight": 0.4}',
            "changed_by": "admin", "changed_at": "2025-06-15T14:00:00",
        }])
        with patch(f"{AUDIT_MOD}.query_df", return_value=df):
            from domain.audit_trail import get_config_diff
            result = get_config_diff("2025-01-01", "2025-12-31")
            assert len(result) == 1
            assert result[0]["section"] == "scenarios"
            assert result[0]["old_value"] == {"weight": 0.5}

    def test_diff_with_section_filter(self):
        with patch(f"{AUDIT_MOD}.query_df", return_value=pd.DataFrame()) as mock_q:
            from domain.audit_trail import get_config_diff
            get_config_diff("2025-01-01", section="model_config")
            query_str = mock_q.call_args[0][0]
            assert "section = %s" in query_str

    def test_diff_without_end_time(self):
        with patch(f"{AUDIT_MOD}.query_df", return_value=pd.DataFrame()) as mock_q:
            from domain.audit_trail import get_config_diff
            get_config_diff("2025-01-01")
            params = mock_q.call_args[0][1]
            assert len(params) == 1  # only start_time


# ── Config Changes Endpoint Tests ──────────────────────────────────────────

class TestConfigChangesEndpoint:
    """Tests for GET /api/audit/config/changes"""

    def test_get_changes_empty(self, fastapi_client, mock_db):
        with patch(f"{AUDIT_MOD}.query_df", return_value=pd.DataFrame()):
            resp = fastapi_client.get("/api/audit/config/changes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_changes_with_section(self, fastapi_client, mock_db):
        df = pd.DataFrame([{
            "id": 1, "section": "model_config", "config_key": "lgd",
            "old_value": '{"val": 0.4}', "new_value": '{"val": 0.5}',
            "changed_by": "admin", "changed_at": "2025-12-31T10:00:00",
        }])
        with patch(f"{AUDIT_MOD}.query_df", return_value=df):
            resp = fastapi_client.get("/api/audit/config/changes?section=model_config")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["section"] == "model_config"


# ── Config Diff Endpoint Tests ─────────────────────────────────────────────

class TestConfigDiffEndpoint:
    """Tests for GET /api/audit/config/diff"""

    def test_diff_endpoint_empty(self, fastapi_client, mock_db):
        with patch(f"{AUDIT_MOD}.query_df", return_value=pd.DataFrame()):
            resp = fastapi_client.get("/api/audit/config/diff?start=2025-01-01")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_diff_endpoint_with_range(self, fastapi_client, mock_db):
        df = pd.DataFrame([{
            "section": "scenarios", "config_key": None,
            "old_value": '{"w": 0.5}', "new_value": '{"w": 0.4}',
            "changed_by": "admin", "changed_at": "2025-06-15T14:00:00",
        }])
        with patch(f"{AUDIT_MOD}.query_df", return_value=df):
            resp = fastapi_client.get(
                "/api/audit/config/diff?start=2025-01-01&end=2025-12-31"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_diff_endpoint_with_section(self, fastapi_client, mock_db):
        with patch(f"{AUDIT_MOD}.query_df", return_value=pd.DataFrame()):
            resp = fastapi_client.get(
                "/api/audit/config/diff?start=2025-01-01&section=model_config"
            )
        assert resp.status_code == 200


# ── Save Config Logs Changes Tests ─────────────────────────────────────────

class TestSaveConfigLogsChanges:
    """Tests that save_config and save_config_section both log audit entries."""

    def test_save_config_section_logs_change(self, mock_db):
        with patch(f"{AUDIT_MOD}.execute") as audit_exec:
            import admin_config
            admin_config._initialized = True
            admin_config.save_config_section("model_config", {"lgd": 0.5}, "risk_mgr")
            # The function calls log_config_change which calls execute
            audit_exec.assert_called()
            any_audit = any(
                "config_audit_log" in str(c) for c in audit_exec.call_args_list
            )
            assert any_audit

    def test_save_config_bulk_logs_changes(self, mock_db):
        with patch(f"{AUDIT_MOD}.execute") as audit_exec:
            import admin_config
            admin_config._initialized = True
            admin_config.save_config({"scenarios": {"w": 0.5}}, "admin")
            audit_exec.assert_called()
