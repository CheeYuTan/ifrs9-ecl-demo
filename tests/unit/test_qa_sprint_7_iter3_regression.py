"""
Sprint 7 Iteration 3: Regression tests for BUG-VQA-7-001 (backtest detail column migration)
and additional coverage for ensure_backtesting_table schema migration logic.

BUG-VQA-7-001: GET /api/backtest/{id} returned 500 because the `detail` column
did not exist in the backtest_metrics table. Root cause: CREATE TABLE IF NOT EXISTS
does not add new columns to existing tables. Fix: ALTER TABLE ADD COLUMN IF NOT EXISTS.
"""
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, call


SCHEMA = "ecl"


# ── BUG-VQA-7-001 Regression: ensure_backtesting_table migration ──────────


class TestEnsureBacktestingTableMigration:
    """Verify ALTER TABLE migration runs after CREATE TABLE statements."""

    @patch("domain.backtesting.log")
    @patch("domain.backtesting.execute")
    @patch("domain.backtesting.query_df")
    def test_alter_table_adds_detail_column(self, mock_qdf, mock_exec, mock_log):
        """BUG-VQA-7-001: ALTER TABLE ADD COLUMN IF NOT EXISTS detail JSONB runs."""
        from domain.backtesting import ensure_backtesting_table
        mock_qdf.return_value = pd.DataFrame([{"model_type": "PD"}])
        ensure_backtesting_table()
        # Collect all execute calls
        calls_sql = [str(c) for c in mock_exec.call_args_list]
        alter_found = any("ADD COLUMN IF NOT EXISTS detail JSONB" in s for s in calls_sql)
        assert alter_found, "ALTER TABLE for detail column not found in execute calls"

    @patch("domain.backtesting.log")
    @patch("domain.backtesting.execute")
    @patch("domain.backtesting.query_df")
    def test_alter_table_runs_after_create(self, mock_qdf, mock_exec, mock_log):
        """ALTER TABLE migration runs after all CREATE TABLE statements."""
        from domain.backtesting import ensure_backtesting_table
        mock_qdf.return_value = pd.DataFrame([{"model_type": "PD"}])
        ensure_backtesting_table()
        call_strs = [str(c) for c in mock_exec.call_args_list]
        create_indices = [i for i, s in enumerate(call_strs) if "CREATE TABLE" in s]
        alter_indices = [i for i, s in enumerate(call_strs) if "ADD COLUMN" in s]
        assert len(create_indices) >= 3, "Should have at least 3 CREATE TABLE calls"
        assert len(alter_indices) >= 1, "Should have at least 1 ALTER TABLE call"
        assert alter_indices[0] > max(create_indices), \
            "ALTER TABLE should run after all CREATE TABLE statements"

    @patch("domain.backtesting.log")
    @patch("domain.backtesting.execute")
    @patch("domain.backtesting.query_df")
    def test_alter_table_exception_swallowed(self, mock_qdf, mock_exec, mock_log):
        """ALTER TABLE failure is swallowed gracefully (column already exists)."""
        from domain.backtesting import ensure_backtesting_table
        mock_qdf.return_value = pd.DataFrame([{"model_type": "PD"}])
        call_count = [0]
        original_side_effects = []

        def exec_side_effect(sql, *args, **kwargs):
            call_count[0] += 1
            if "ADD COLUMN" in str(sql):
                raise Exception("column already exists")

        mock_exec.side_effect = exec_side_effect
        # Should not raise
        ensure_backtesting_table()
        assert call_count[0] >= 4, "Should have called execute at least 4 times"

    @patch("domain.backtesting.log")
    @patch("domain.backtesting.execute")
    @patch("domain.backtesting.query_df")
    def test_legacy_migration_triggers_on_missing_model_type(self, mock_qdf, mock_exec, mock_log):
        """When model_type column is missing, legacy tables are dropped and recreated."""
        from domain.backtesting import ensure_backtesting_table
        mock_qdf.side_effect = Exception("column model_type does not exist")
        ensure_backtesting_table()
        call_strs = [str(c) for c in mock_exec.call_args_list]
        drop_calls = [s for s in call_strs if "DROP TABLE" in s]
        create_calls = [s for s in call_strs if "CREATE TABLE" in s]
        assert len(drop_calls) >= 3, "Should drop 3 legacy tables"
        assert len(create_calls) >= 3, "Should create 3 tables"

    @patch("domain.backtesting.log")
    @patch("domain.backtesting.execute")
    @patch("domain.backtesting.query_df")
    def test_ensure_idempotent(self, mock_qdf, mock_exec, mock_log):
        """Calling ensure_backtesting_table twice does not fail."""
        from domain.backtesting import ensure_backtesting_table
        mock_qdf.return_value = pd.DataFrame([{"model_type": "PD"}])
        ensure_backtesting_table()
        ensure_backtesting_table()
        # Should have doubled the calls
        call_strs = [str(c) for c in mock_exec.call_args_list]
        alter_calls = [s for s in call_strs if "ADD COLUMN" in s]
        assert len(alter_calls) >= 2, "ALTER TABLE should run on each invocation"


# ── get_backtest: detail column handling ───────────────────────────────────


class TestGetBacktestDetailColumn:
    """Verify get_backtest correctly handles the detail JSONB column."""

    @patch("domain.backtesting.query_df")
    def test_get_backtest_with_detail_json_string(self, mock_qdf):
        """Detail column as JSON string is deserialized."""
        from domain.backtesting import get_backtest
        result_df = pd.DataFrame([{
            "backtest_id": "BT001", "model_id": "M1", "model_type": "PD",
            "backtest_date": "2026-01-01", "overall_traffic_light": "Green",
            "config": None,
        }])
        metrics_df = pd.DataFrame([{
            "metric_id": "MET001", "metric_name": "AUC",
            "metric_value": 0.85, "threshold_green": 0.7,
            "threshold_amber": 0.6, "pass_fail": "Green",
            "detail": json.dumps({"fpr": [0, 0.5, 1], "tpr": [0, 0.8, 1]}),
        }])
        cohort_df = pd.DataFrame()
        mock_qdf.side_effect = [result_df, metrics_df, cohort_df]
        result = get_backtest("BT001")
        assert result is not None
        assert len(result["metrics"]) == 1
        detail = result["metrics"][0]["detail"]
        assert isinstance(detail, dict), "detail should be deserialized from JSON string"
        assert detail["fpr"] == [0, 0.5, 1]

    @patch("domain.backtesting.query_df")
    def test_get_backtest_with_detail_dict(self, mock_qdf):
        """Detail column already as dict (JSONB auto-deserialized by driver)."""
        from domain.backtesting import get_backtest
        result_df = pd.DataFrame([{
            "backtest_id": "BT001", "model_id": "M1", "model_type": "PD",
            "backtest_date": "2026-01-01", "overall_traffic_light": "Green",
            "config": None,
        }])
        metrics_df = pd.DataFrame([{
            "metric_id": "MET001", "metric_name": "Gini",
            "metric_value": 0.70, "threshold_green": 0.5,
            "threshold_amber": 0.3, "pass_fail": "Green",
            "detail": {"ks_table": [1, 2, 3]},
        }])
        cohort_df = pd.DataFrame()
        mock_qdf.side_effect = [result_df, metrics_df, cohort_df]
        result = get_backtest("BT001")
        assert result["metrics"][0]["detail"]["ks_table"] == [1, 2, 3]

    @patch("domain.backtesting.query_df")
    def test_get_backtest_with_detail_none(self, mock_qdf):
        """Detail column as None is preserved."""
        from domain.backtesting import get_backtest
        result_df = pd.DataFrame([{
            "backtest_id": "BT001", "model_id": "M1", "model_type": "PD",
            "backtest_date": "2026-01-01", "overall_traffic_light": "Green",
            "config": None,
        }])
        metrics_df = pd.DataFrame([{
            "metric_id": "MET001", "metric_name": "PSI",
            "metric_value": 0.15, "threshold_green": 0.1,
            "threshold_amber": 0.25, "pass_fail": "Amber",
            "detail": None,
        }])
        cohort_df = pd.DataFrame()
        mock_qdf.side_effect = [result_df, metrics_df, cohort_df]
        result = get_backtest("BT001")
        assert result["metrics"][0]["detail"] is None

    @patch("domain.backtesting.query_df")
    def test_get_backtest_with_malformed_detail_string(self, mock_qdf):
        """Malformed JSON string in detail column doesn't crash."""
        from domain.backtesting import get_backtest
        result_df = pd.DataFrame([{
            "backtest_id": "BT001", "model_id": "M1", "model_type": "PD",
            "backtest_date": "2026-01-01", "overall_traffic_light": "Green",
            "config": None,
        }])
        metrics_df = pd.DataFrame([{
            "metric_id": "MET001", "metric_name": "Brier",
            "metric_value": 0.02, "threshold_green": 0.05,
            "threshold_amber": 0.1, "pass_fail": "Green",
            "detail": "{invalid json",
        }])
        cohort_df = pd.DataFrame()
        mock_qdf.side_effect = [result_df, metrics_df, cohort_df]
        result = get_backtest("BT001")
        # Should not crash; detail stays as string
        assert result["metrics"][0]["detail"] == "{invalid json"

    @patch("domain.backtesting.query_df")
    def test_get_backtest_multiple_metrics_with_detail(self, mock_qdf):
        """Multiple metrics each with detail column are all handled."""
        from domain.backtesting import get_backtest
        result_df = pd.DataFrame([{
            "backtest_id": "BT001", "model_id": "M1", "model_type": "PD",
            "backtest_date": "2026-01-01", "overall_traffic_light": "Amber",
            "config": None,
        }])
        metrics_df = pd.DataFrame([
            {"metric_id": "M1", "metric_name": "AUC", "metric_value": 0.85,
             "threshold_green": 0.7, "threshold_amber": 0.6, "pass_fail": "Green",
             "detail": json.dumps({"curve": "roc"})},
            {"metric_id": "M2", "metric_name": "KS", "metric_value": 0.45,
             "threshold_green": 0.3, "threshold_amber": 0.2, "pass_fail": "Green",
             "detail": None},
            {"metric_id": "M3", "metric_name": "PSI", "metric_value": 0.30,
             "threshold_green": 0.1, "threshold_amber": 0.25, "pass_fail": "Red",
             "detail": json.dumps({"bins": 10, "values": [0.03, 0.05]})},
        ])
        cohort_df = pd.DataFrame()
        mock_qdf.side_effect = [result_df, metrics_df, cohort_df]
        result = get_backtest("BT001")
        assert len(result["metrics"]) == 3
        assert result["metrics"][0]["detail"]["curve"] == "roc"
        assert result["metrics"][1]["detail"] is None
        assert result["metrics"][2]["detail"]["bins"] == 10

    @patch("domain.backtesting.query_df")
    def test_get_backtest_not_found(self, mock_qdf):
        """Non-existent backtest returns None."""
        from domain.backtesting import get_backtest
        mock_qdf.return_value = pd.DataFrame()
        result = get_backtest("NONEXISTENT")
        assert result is None

    @patch("domain.backtesting.query_df")
    def test_get_backtest_config_deserialization(self, mock_qdf):
        """Config JSONB column is deserialized from string."""
        from domain.backtesting import get_backtest
        result_df = pd.DataFrame([{
            "backtest_id": "BT001", "model_id": "M1", "model_type": "PD",
            "backtest_date": "2026-01-01", "overall_traffic_light": "Green",
            "config": json.dumps({"n_sims": 1000}),
        }])
        metrics_df = pd.DataFrame()
        cohort_df = pd.DataFrame()
        mock_qdf.side_effect = [result_df, metrics_df, cohort_df]
        result = get_backtest("BT001")
        assert isinstance(result["config"], dict)
        assert result["config"]["n_sims"] == 1000

    @patch("domain.backtesting.query_df")
    def test_get_backtest_with_cohort_results(self, mock_qdf):
        """Cohort results are included when present."""
        from domain.backtesting import get_backtest
        result_df = pd.DataFrame([{
            "backtest_id": "BT001", "model_id": "M1", "model_type": "PD",
            "backtest_date": "2026-01-01", "overall_traffic_light": "Green",
            "config": None,
        }])
        metrics_df = pd.DataFrame()
        cohort_df = pd.DataFrame([
            {"cohort_id": "C1", "cohort_name": "Grade A", "predicted_rate": 0.01,
             "actual_rate": 0.012, "count": 5000, "abs_diff": 0.002},
            {"cohort_id": "C2", "cohort_name": "Grade B", "predicted_rate": 0.05,
             "actual_rate": 0.048, "count": 3000, "abs_diff": 0.002},
        ])
        mock_qdf.side_effect = [result_df, metrics_df, cohort_df]
        result = get_backtest("BT001")
        assert len(result["cohort_results"]) == 2
        assert result["cohort_results"][0]["cohort_name"] == "Grade A"


# ── API Route: GET /api/backtest/{id} regression ───────────────────────────


class TestBacktestRouteRegression:
    """Regression tests for the backtest detail API route."""

    @patch("routes.backtesting.backend")
    def test_get_backtest_route_returns_200(self, mock_backend):
        """BUG-VQA-7-001 regression: route returns 200, not 500."""
        from fastapi.testclient import TestClient
        from routes.backtesting import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)  # router already has prefix="/api/backtest"
        client = TestClient(app)
        mock_backend.get_backtest.return_value = {
            "backtest_id": "BT001", "model_id": "M1",
            "model_type": "PD", "overall_traffic_light": "Green",
            "metrics": [{"metric_name": "AUC", "metric_value": 0.85, "detail": {"fpr": [0, 1]}}],
            "cohort_results": [],
        }
        resp = client.get("/api/backtest/BT001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["backtest_id"] == "BT001"
        assert data["metrics"][0]["detail"]["fpr"] == [0, 1]

    @patch("routes.backtesting.backend")
    def test_get_backtest_route_404_not_found(self, mock_backend):
        """Non-existent backtest returns 404."""
        from fastapi.testclient import TestClient
        from routes.backtesting import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        mock_backend.get_backtest.return_value = None
        resp = client.get("/api/backtest/NONEXISTENT")
        assert resp.status_code == 404

    @patch("routes.backtesting.backend")
    def test_get_backtest_route_500_on_exception(self, mock_backend):
        """Internal error returns 500 with message."""
        from fastapi.testclient import TestClient
        from routes.backtesting import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        mock_backend.get_backtest.side_effect = Exception("DB connection failed")
        resp = client.get("/api/backtest/BT001")
        assert resp.status_code == 500
        assert "Failed to get backtest" in resp.json()["detail"]
