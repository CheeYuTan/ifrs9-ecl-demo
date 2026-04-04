"""Tests for routes/analytics.py — Admin analytics summary endpoint."""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


@pytest.fixture
def _patch_db():
    with patch("routes.analytics.query_df") as mock_q, \
         patch("domain.usage_analytics.query_df") as mock_uq, \
         patch("domain.usage_analytics.execute"):
        mock_q.return_value = pd.DataFrame()
        mock_uq.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "usage_query_df": mock_uq}


class TestAnalyticsSummary:
    def test_returns_all_keys(self, _patch_db):
        from routes.analytics import analytics_summary
        result = analytics_summary()
        expected_keys = {
            "total_requests_7d", "unique_users_7d", "avg_latency_ms",
            "error_count_7d", "requests_today", "total_projects",
            "active_projects", "active_models",
        }
        assert set(result.keys()) == expected_keys

    def test_empty_tables_return_zeros(self, _patch_db):
        from routes.analytics import analytics_summary
        result = analytics_summary()
        assert result["total_requests_7d"] == 0
        assert result["unique_users_7d"] == 0
        assert result["total_projects"] == 0
        assert result["active_models"] == 0

    def test_with_usage_data(self, _patch_db):
        _patch_db["usage_query_df"].return_value = pd.DataFrame([{
            "total_requests": 150,
            "unique_users": 5,
            "avg_duration_ms": 42.5,
            "error_count": 3,
            "requests_today": 20,
        }])
        from routes.analytics import analytics_summary
        result = analytics_summary()
        assert result["total_requests_7d"] == 150
        assert result["unique_users_7d"] == 5
        assert result["avg_latency_ms"] == 42.5

    def test_with_project_data(self, _patch_db):
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "total": 10, "active": 3,
        }])
        from routes.analytics import analytics_summary
        result = analytics_summary()
        assert result["total_projects"] == 10
        assert result["active_projects"] == 3


class TestProjectCounts:
    def test_empty_table(self, _patch_db):
        from routes.analytics import _get_project_counts
        result = _get_project_counts()
        assert result == {"total_projects": 0, "active_projects": 0}

    def test_with_data(self, _patch_db):
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "total": 25, "active": 8,
        }])
        from routes.analytics import _get_project_counts
        result = _get_project_counts()
        assert result["total_projects"] == 25
        assert result["active_projects"] == 8

    def test_handles_missing_table(self, _patch_db):
        _patch_db["query_df"].side_effect = Exception("relation does not exist")
        from routes.analytics import _get_project_counts
        result = _get_project_counts()
        assert result == {"total_projects": 0, "active_projects": 0}


class TestModelCount:
    def test_empty(self, _patch_db):
        from routes.analytics import _get_model_count
        assert _get_model_count() == 0

    def test_with_models(self, _patch_db):
        _patch_db["query_df"].return_value = pd.DataFrame([{"cnt": 7}])
        from routes.analytics import _get_model_count
        assert _get_model_count() == 7

    def test_handles_missing_table(self, _patch_db):
        _patch_db["query_df"].side_effect = Exception("relation does not exist")
        from routes.analytics import _get_model_count
        assert _get_model_count() == 0


class TestRecentRequests:
    def test_returns_list(self, _patch_db):
        from routes.analytics import analytics_recent_requests
        result = analytics_recent_requests(limit=10)
        assert isinstance(result, list)

    def test_caps_limit(self, _patch_db):
        from routes.analytics import analytics_recent_requests
        # Should not raise even with large limit — capped at 200
        result = analytics_recent_requests(limit=9999)
        assert isinstance(result, list)
