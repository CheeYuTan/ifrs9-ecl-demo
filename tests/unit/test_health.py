"""Tests for domain/health.py — health check module."""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from domain.health import (
    check_lakebase_connection,
    check_required_tables,
    check_config_loaded,
    check_scipy_available,
    run_health_check,
    REQUIRED_TABLES,
)


class TestCheckLakebaseConnection:
    def test_healthy_connection(self):
        with patch("domain.health.query_df", return_value=pd.DataFrame({"ok": [1]})):
            result = check_lakebase_connection()
            assert result["healthy"] is True
            assert result["status"] == "connected"

    def test_unhealthy_connection(self):
        with patch("domain.health.query_df", side_effect=Exception("Connection refused")):
            result = check_lakebase_connection()
            assert result["healthy"] is False
            assert result["status"] == "error"
            assert "Connection refused" in result["error"]

    def test_timeout_error(self):
        with patch("domain.health.query_df", side_effect=TimeoutError("query timeout")):
            result = check_lakebase_connection()
            assert result["healthy"] is False


class TestCheckRequiredTables:
    def test_all_tables_present(self):
        with patch("domain.health.query_df", return_value=pd.DataFrame({"cnt": [100]})), \
             patch("domain.health._t", side_effect=lambda t: f"schema.{t}"):
            result = check_required_tables()
            assert result["all_present"] is True
            assert result["missing"] == []
            assert len(result["tables"]) == len(REQUIRED_TABLES)
            for table in REQUIRED_TABLES:
                assert result["tables"][table]["exists"] is True
                assert result["tables"][table]["row_count"] == 100

    def test_some_tables_missing(self):
        call_count = [0]

        def mock_query(sql):
            call_count[0] += 1
            if call_count[0] <= 2:
                return pd.DataFrame({"cnt": [50]})
            raise Exception("table not found")

        with patch("domain.health.query_df", side_effect=mock_query), \
             patch("domain.health._t", side_effect=lambda t: f"schema.{t}"):
            result = check_required_tables()
            assert result["all_present"] is False
            assert len(result["missing"]) > 0

    def test_all_tables_missing(self):
        with patch("domain.health.query_df", side_effect=Exception("no table")), \
             patch("domain.health._t", side_effect=lambda t: f"schema.{t}"):
            result = check_required_tables()
            assert result["all_present"] is False
            assert len(result["missing"]) == len(REQUIRED_TABLES)

    def test_empty_table(self):
        with patch("domain.health.query_df", return_value=pd.DataFrame({"cnt": [0]})), \
             patch("domain.health._t", side_effect=lambda t: f"schema.{t}"):
            result = check_required_tables()
            assert result["all_present"] is True
            for table in REQUIRED_TABLES:
                assert result["tables"][table]["row_count"] == 0

    def test_empty_dataframe_returned(self):
        with patch("domain.health.query_df", return_value=pd.DataFrame()), \
             patch("domain.health._t", side_effect=lambda t: f"schema.{t}"):
            result = check_required_tables()
            assert result["all_present"] is True
            for table in REQUIRED_TABLES:
                assert result["tables"][table]["row_count"] == 0


class TestCheckConfigLoaded:
    def test_config_loaded(self):
        import admin_config as ac_mod
        with patch.object(ac_mod, "get_config", return_value={"general": {}, "model": {}, "display": {}}):
            result = check_config_loaded()
            assert result["loaded"] is True
            assert result["section_count"] == 3
            assert "general" in result["sections"]

    def test_config_not_loaded(self):
        import admin_config as ac_mod
        with patch.object(ac_mod, "get_config", side_effect=RuntimeError("Config not initialized")):
            result = check_config_loaded()
            assert result["loaded"] is False
            assert "error" in result


class TestCheckScipyAvailable:
    def test_scipy_available(self):
        result = check_scipy_available()
        assert result["available"] is True
        assert "version" in result

    def test_scipy_import_error(self):
        import importlib
        with patch.dict("sys.modules", {"scipy": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'scipy'")):
                result = check_scipy_available()
                assert result["available"] is False


class TestRunHealthCheck:
    def test_all_healthy(self):
        with patch("domain.health.check_lakebase_connection", return_value={"healthy": True, "status": "connected"}), \
             patch("domain.health.check_required_tables", return_value={"all_present": True, "tables": {}, "missing": []}), \
             patch("domain.health.check_config_loaded", return_value={"loaded": True, "sections": [], "section_count": 0}), \
             patch("domain.health.check_scipy_available", return_value={"available": True, "version": "1.0"}):
            result = run_health_check()
            assert result["status"] == "healthy"
            assert "lakebase" in result["services"]
            assert "tables" in result["services"]
            assert "config" in result["services"]
            assert "scipy" in result["services"]

    def test_degraded_lakebase_down(self):
        with patch("domain.health.check_lakebase_connection", return_value={"healthy": False, "status": "error", "error": "down"}), \
             patch("domain.health.check_required_tables", return_value={"all_present": True, "tables": {}, "missing": []}), \
             patch("domain.health.check_config_loaded", return_value={"loaded": True, "sections": [], "section_count": 0}), \
             patch("domain.health.check_scipy_available", return_value={"available": True, "version": "1.0"}):
            result = run_health_check()
            assert result["status"] == "degraded"

    def test_degraded_tables_missing(self):
        with patch("domain.health.check_lakebase_connection", return_value={"healthy": True, "status": "connected"}), \
             patch("domain.health.check_required_tables", return_value={"all_present": False, "tables": {}, "missing": ["ecl_workflow"]}), \
             patch("domain.health.check_config_loaded", return_value={"loaded": True, "sections": [], "section_count": 0}), \
             patch("domain.health.check_scipy_available", return_value={"available": True, "version": "1.0"}):
            result = run_health_check()
            assert result["status"] == "degraded"

    def test_degraded_config_not_loaded(self):
        with patch("domain.health.check_lakebase_connection", return_value={"healthy": True, "status": "connected"}), \
             patch("domain.health.check_required_tables", return_value={"all_present": True, "tables": {}, "missing": []}), \
             patch("domain.health.check_config_loaded", return_value={"loaded": False, "error": "init failed"}), \
             patch("domain.health.check_scipy_available", return_value={"available": True, "version": "1.0"}):
            result = run_health_check()
            assert result["status"] == "degraded"

    def test_degraded_scipy_missing(self):
        with patch("domain.health.check_lakebase_connection", return_value={"healthy": True, "status": "connected"}), \
             patch("domain.health.check_required_tables", return_value={"all_present": True, "tables": {}, "missing": []}), \
             patch("domain.health.check_config_loaded", return_value={"loaded": True, "sections": [], "section_count": 0}), \
             patch("domain.health.check_scipy_available", return_value={"available": False, "error": "no scipy"}):
            result = run_health_check()
            assert result["status"] == "degraded"

    def test_all_services_down(self):
        with patch("domain.health.check_lakebase_connection", return_value={"healthy": False, "status": "error", "error": "x"}), \
             patch("domain.health.check_required_tables", return_value={"all_present": False, "tables": {}, "missing": ["a"]}), \
             patch("domain.health.check_config_loaded", return_value={"loaded": False, "error": "x"}), \
             patch("domain.health.check_scipy_available", return_value={"available": False, "error": "x"}):
            result = run_health_check()
            assert result["status"] == "degraded"
