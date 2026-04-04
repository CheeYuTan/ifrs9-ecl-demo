"""Tests for domain/usage_analytics.py — API usage tracking."""
import pytest
import pandas as pd
from unittest.mock import patch, call
from datetime import datetime


@pytest.fixture
def _patch_db():
    with patch("domain.usage_analytics.query_df") as mock_q, \
         patch("domain.usage_analytics.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


class TestEnsureUsageTable:
    def test_creates_table(self, _patch_db):
        from domain.usage_analytics import ensure_usage_table
        ensure_usage_table()
        calls = _patch_db["execute"].call_args_list
        assert len(calls) == 2  # CREATE TABLE + COMMENT
        ddl = calls[0].args[0]
        assert "CREATE TABLE IF NOT EXISTS" in ddl
        assert "app_usage_analytics" in ddl

    def test_idempotent(self, _patch_db):
        from domain.usage_analytics import ensure_usage_table
        ensure_usage_table()
        ensure_usage_table()
        # Should succeed twice without error
        assert _patch_db["execute"].call_count == 4  # 2 calls per invocation

    def test_table_has_comment(self, _patch_db):
        from domain.usage_analytics import ensure_usage_table
        ensure_usage_table()
        comment_call = _patch_db["execute"].call_args_list[1].args[0]
        assert "COMMENT ON TABLE" in comment_call
        assert "ifrs9ecl:" in comment_call

    def test_schema_columns(self, _patch_db):
        from domain.usage_analytics import ensure_usage_table
        ensure_usage_table()
        ddl = _patch_db["execute"].call_args_list[0].args[0]
        for col in ("id", "timestamp", "user_id", "method", "endpoint",
                     "status_code", "duration_ms", "request_id", "user_agent"):
            assert col in ddl, f"Column {col} missing from DDL"

    def test_uses_schema_constant(self):
        from domain.usage_analytics import USAGE_TABLE
        assert "expected_credit_loss" in USAGE_TABLE
        assert "app_usage_analytics" in USAGE_TABLE


class TestRecordRequest:
    def test_inserts_record(self, _patch_db):
        from domain.usage_analytics import record_request
        record_request("user1", "GET", "/api/projects", 200, 45.2,
                       "req-abc", "Mozilla/5.0")
        assert _patch_db["execute"].called
        sql = _patch_db["execute"].call_args.args[0]
        assert "INSERT INTO" in sql
        params = _patch_db["execute"].call_args.args[1]
        assert params == ("user1", "GET", "/api/projects", 200, 45.2,
                          "req-abc", "Mozilla/5.0")

    def test_optional_fields_none(self, _patch_db):
        from domain.usage_analytics import record_request
        record_request("user2", "POST", "/api/data", 201, 120.5)
        params = _patch_db["execute"].call_args.args[1]
        assert params[5] is None  # request_id
        assert params[6] is None  # user_agent


class TestGetUsageStats:
    def test_returns_stats_with_data(self, _patch_db):
        from domain.usage_analytics import get_usage_stats
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "total_requests": 150,
            "unique_users": 12,
            "avg_duration_ms": 85.3,
            "error_count": 5,
            "requests_today": 30,
        }])
        stats = get_usage_stats(days=7)
        assert stats["total_requests"] == 150
        assert stats["unique_users"] == 12
        assert stats["avg_duration_ms"] == 85.3
        assert stats["error_count"] == 5
        assert stats["requests_today"] == 30

    def test_returns_zeros_on_empty(self, _patch_db):
        from domain.usage_analytics import get_usage_stats
        stats = get_usage_stats(days=7)
        assert stats["total_requests"] == 0
        assert stats["unique_users"] == 0
        assert stats["avg_duration_ms"] == 0

    def test_passes_days_param(self, _patch_db):
        from domain.usage_analytics import get_usage_stats
        get_usage_stats(days=30)
        params = _patch_db["query_df"].call_args.args[1]
        assert params == (30,)

    def test_handles_none_values(self, _patch_db):
        from domain.usage_analytics import get_usage_stats
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "total_requests": 0,
            "unique_users": 0,
            "avg_duration_ms": None,
            "error_count": 0,
            "requests_today": 0,
        }])
        stats = get_usage_stats()
        assert stats["avg_duration_ms"] == 0


class TestGetRecentRequests:
    def test_returns_records(self, _patch_db):
        from domain.usage_analytics import get_recent_requests
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"id": 1, "timestamp": "2025-01-01T00:00:00", "user_id": "u1",
             "method": "GET", "endpoint": "/api/test", "status_code": 200,
             "duration_ms": 50.0, "request_id": "r1", "user_agent": "test"},
        ])
        records = get_recent_requests(limit=10)
        assert len(records) == 1
        assert records[0]["user_id"] == "u1"

    def test_returns_empty_list(self, _patch_db):
        from domain.usage_analytics import get_recent_requests
        records = get_recent_requests()
        assert records == []

    def test_passes_limit_param(self, _patch_db):
        from domain.usage_analytics import get_recent_requests
        get_recent_requests(limit=25)
        params = _patch_db["query_df"].call_args.args[1]
        assert params == (25,)

    def test_converts_timestamp_to_iso(self, _patch_db):
        from domain.usage_analytics import get_recent_requests
        ts = datetime(2025, 6, 15, 10, 30, 0)
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"id": 1, "timestamp": ts, "user_id": "u1",
             "method": "GET", "endpoint": "/api/test", "status_code": 200,
             "duration_ms": 50.0, "request_id": "r1", "user_agent": "test"},
        ])
        records = get_recent_requests()
        assert records[0]["timestamp"] == "2025-06-15T10:30:00"
