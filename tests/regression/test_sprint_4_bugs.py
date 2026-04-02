"""
Regression tests for bugs discovered during Sprint 4 Visual QA.

BUG-S4-001: Audit export HTTP 500 — pandas.Timestamp not JSON serializable
BUG-S4-002: IFRS 7.35I — column "reconciliation" missing from ecl_attribution
BUG-S4-003: IFRS 7.35J — historical_defaults table does not exist
"""
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest


# ===================================================================
# BUG-S4-001: Audit export Timestamp serialization
# ===================================================================

class TestBugS4001AuditExportTimestamp:
    """Audit trail and config audit entries with pandas.Timestamp fields
    must be serializable to JSON (no 'Object of type Timestamp is not
    JSON serializable' errors)."""

    def test_audit_trail_converts_timestamp_to_iso(self):
        """get_audit_trail() must convert created_at Timestamp to string."""
        ts = pd.Timestamp("2025-12-15 10:30:00+00:00")
        rows = pd.DataFrame([{
            "id": 1, "project_id": "P1", "event_type": "STEP_ADVANCE",
            "entity_type": "project", "entity_id": "P1", "action": "advance",
            "performed_by": "admin", "detail": '{"step": 1}',
            "previous_hash": "GENESIS", "entry_hash": "abc123",
            "created_at": ts,
        }])
        with patch("domain.audit_trail.query_df", return_value=rows):
            from domain.audit_trail import get_audit_trail
            result = get_audit_trail("P1")
        assert len(result) == 1
        # Must be a string, not a Timestamp
        assert isinstance(result[0]["created_at"], str)
        # Must be JSON-serializable
        json.dumps(result)

    def test_audit_trail_handles_datetime_object(self):
        """get_audit_trail() must handle native datetime objects too."""
        dt = datetime(2025, 12, 15, 10, 30, 0, tzinfo=timezone.utc)
        rows = pd.DataFrame([{
            "id": 1, "project_id": "P1", "event_type": "CREATE",
            "entity_type": "project", "entity_id": "P1", "action": "create",
            "performed_by": "admin", "detail": "{}",
            "previous_hash": "GENESIS", "entry_hash": "def456",
            "created_at": dt,
        }])
        with patch("domain.audit_trail.query_df", return_value=rows):
            from domain.audit_trail import get_audit_trail
            result = get_audit_trail("P1")
        assert isinstance(result[0]["created_at"], str)
        json.dumps(result)

    def test_audit_trail_preserves_string_timestamp(self):
        """If created_at is already a string, it must remain unchanged."""
        rows = pd.DataFrame([{
            "id": 1, "project_id": "P1", "event_type": "CREATE",
            "entity_type": "project", "entity_id": "P1", "action": "create",
            "performed_by": "admin", "detail": "{}",
            "previous_hash": "GENESIS", "entry_hash": "ghi789",
            "created_at": "2025-12-15T10:30:00+00:00",
        }])
        with patch("domain.audit_trail.query_df", return_value=rows):
            from domain.audit_trail import get_audit_trail
            result = get_audit_trail("P1")
        assert result[0]["created_at"] == "2025-12-15T10:30:00+00:00"

    def test_config_audit_log_converts_timestamp(self):
        """get_config_audit_log() must convert changed_at Timestamp to string."""
        ts = pd.Timestamp("2025-11-20 09:15:00+00:00")
        rows = pd.DataFrame([{
            "id": 1, "section": "model_config", "config_key": "lgd",
            "old_value": '{"default": 0.4}', "new_value": '{"default": 0.35}',
            "changed_by": "admin", "changed_at": ts,
        }])
        with patch("domain.config_audit.query_df", return_value=rows):
            from domain.config_audit import get_config_audit_log
            result = get_config_audit_log()
        assert len(result) == 1
        assert isinstance(result[0]["changed_at"], str)
        json.dumps(result)

    def test_config_diff_converts_timestamp(self):
        """get_config_diff() must convert changed_at Timestamp to string."""
        ts = pd.Timestamp("2025-11-20 09:15:00+00:00")
        rows = pd.DataFrame([{
            "section": "model_config", "config_key": "lgd",
            "old_value": '{"default": 0.4}', "new_value": '{"default": 0.35}',
            "changed_by": "admin", "changed_at": ts,
        }])
        with patch("domain.config_audit.query_df", return_value=rows):
            from domain.config_audit import get_config_diff
            result = get_config_diff("2025-01-01")
        assert len(result) == 1
        assert isinstance(result[0]["changed_at"], str)
        json.dumps(result)

    def test_export_audit_package_fully_serializable(self):
        """export_audit_package() return value must be fully JSON-serializable."""
        ts = pd.Timestamp("2025-12-15 10:30:00+00:00")
        audit_rows = pd.DataFrame([{
            "id": 1, "project_id": "P1", "event_type": "CREATE",
            "entity_type": "project", "entity_id": "P1", "action": "create",
            "performed_by": "admin", "detail": "{}",
            "previous_hash": "GENESIS", "entry_hash": "abc",
            "created_at": ts,
        }])
        config_rows = pd.DataFrame([{
            "id": 1, "section": "model_config", "config_key": "lgd",
            "old_value": '{"default": 0.4}', "new_value": '{"default": 0.35}',
            "changed_by": "admin", "changed_at": ts,
        }])

        def mock_query(sql, params=None):
            sql_lower = sql.lower()
            if "audit_trail" in sql_lower:
                return audit_rows
            if "config_audit" in sql_lower:
                return config_rows
            return pd.DataFrame()

        with patch("domain.audit_trail.query_df", side_effect=mock_query), \
             patch("domain.config_audit.query_df", side_effect=mock_query):
            from domain.audit_trail import export_audit_package
            package = export_audit_package("P1")

        # This is the critical assertion — must not raise TypeError
        serialized = json.dumps(package)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert parsed["project_id"] == "P1"
        assert len(parsed["audit_entries"]) == 1
        assert len(parsed["config_changes"]) == 1


# ===================================================================
# BUG-S4-002: IFRS 7.35I — reconciliation column migration
# ===================================================================

class TestBugS4002AttributionReconciliation:
    """ensure_attribution_table() must add the reconciliation column to
    existing tables that were created without it."""

    def test_ensure_table_adds_reconciliation_column(self):
        """The ALTER TABLE ADD COLUMN IF NOT EXISTS must be called."""
        calls = []

        def mock_execute(sql, params=None):
            calls.append(sql)

        with patch("domain.attribution.execute", side_effect=mock_execute):
            from domain.attribution import ensure_attribution_table
            ensure_attribution_table()

        # Must have both CREATE TABLE and ALTER TABLE calls
        assert any("CREATE TABLE" in c for c in calls)
        assert any("ADD COLUMN" in c and "reconciliation" in c for c in calls)

    def test_compute_attribution_calls_ensure_table(self):
        """compute_attribution() must call ensure_attribution_table() before INSERT."""
        ensure_called = {"value": False}
        original_ensure = None

        def track_ensure():
            ensure_called["value"] = True

        with patch("domain.attribution.ensure_attribution_table", side_effect=track_ensure), \
             patch("domain.attribution.get_project", return_value={"reporting_date": "2025-12-31"}), \
             patch("domain.attribution._safe_query", return_value=(None, "mocked")), \
             patch("domain.attribution._get_prior_attribution", return_value=None), \
             patch("domain.attribution._estimate_opening_ecl", return_value={"stage1": 0, "stage2": 0, "stage3": 0, "total": 0}), \
             patch("domain.attribution.execute"):
            from domain.attribution import compute_attribution
            try:
                compute_attribution("P1")
            except Exception:
                pass  # May fail on other mocked calls, that's OK
        assert ensure_called["value"], "compute_attribution must call ensure_attribution_table()"


# ===================================================================
# BUG-S4-003: IFRS 7.35J — missing historical_defaults table
# ===================================================================

class TestBugS4003HistoricalDefaultsTable:
    """IFRS 7.35J section must handle missing historical_defaults table
    gracefully with a user-friendly error message."""

    def test_35j_missing_table_returns_helpful_error(self):
        """When historical_defaults doesn't exist, the error message must
        guide the user to run the data pipeline or configure Data Mapping."""
        from psycopg2.errors import UndefinedTable

        def fail_query(sql, params=None):
            raise Exception(
                'relation "expected_credit_loss.lb_historical_defaults" does not exist\n'
                'LINE 3:             FROM expected_credit_loss.lb_historical_defaults'
            )

        sections = {}
        with patch("reporting.report_helpers.query_df", side_effect=fail_query), \
             patch("reporting.report_helpers._t", return_value="expected_credit_loss.lb_historical_defaults"):
            from reporting._ifrs7_sections_a import _build_35j
            _build_35j(sections)

        result = sections["ifrs7_35j"]
        assert result["data"] == []
        assert "error" in result
        # Must contain helpful guidance, not raw SQL error
        assert "data pipeline" in result["error"].lower() or "data mapping" in result["error"].lower()

    def test_35j_with_valid_data(self):
        """When historical_defaults exists, the section produces correct output."""
        wo_data = pd.DataFrame([{
            "product_type": "mortgage",
            "default_count": 5,
            "gross_writeoff": 50000.0,
            "recovery_amount": 20000.0,
            "net_writeoff": 30000.0,
            "recovery_rate_pct": 40.0,
        }])
        summary_data = pd.DataFrame([{
            "total_defaults": 5,
            "total_gross": 50000.0,
            "total_recovered": 20000.0,
            "total_net_writeoff": 30000.0,
            "contractual_outstanding": 30000.0,
        }])

        call_count = {"n": 0}

        def mock_query(sql, params=None):
            call_count["n"] += 1
            if call_count["n"] <= 2:  # First two calls: existence check + wo_df
                if "COUNT" in sql.upper() and "GROUP BY" not in sql.upper():
                    return pd.DataFrame([{"cnt": 5}])
                return wo_data
            return summary_data  # Third call: outstanding_df

        sections = {}
        with patch("reporting.report_helpers.query_df", side_effect=mock_query), \
             patch("reporting.report_helpers._t", return_value="expected_credit_loss.lb_historical_defaults"):
            from reporting._ifrs7_sections_a import _build_35j
            _build_35j(sections)

        result = sections["ifrs7_35j"]
        assert "error" not in result
        assert len(result["data"]) == 1
        assert result["data"][0]["product_type"] == "mortgage"

    def test_35j_other_sql_error_shows_raw_message(self):
        """Non-table-existence errors should show the actual error message."""
        def fail_query(sql, params=None):
            raise Exception("column \"nonexistent\" does not exist")

        sections = {}
        with patch("reporting.report_helpers.query_df", side_effect=fail_query), \
             patch("reporting.report_helpers._t", return_value="expected_credit_loss.lb_historical_defaults"):
            from reporting._ifrs7_sections_a import _build_35j
            _build_35j(sections)

        result = sections["ifrs7_35j"]
        assert "error" in result
        # Non-table-existence errors keep the raw message
        assert "nonexistent" in result["error"]
