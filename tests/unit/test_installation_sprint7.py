"""Tests for Sprint 7: Installation Fixes.

Covers:
  - scipy is in requirements.txt
  - scipy is importable
  - Health check basic endpoint
  - Health check detailed endpoint
  - Individual health check functions (lakebase, tables, config, scipy)
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

HEALTH_MOD = "domain.health"

# Resolve requirements.txt path relative to this file (works from any CWD)
_REQUIREMENTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "app", "requirements.txt"
)


# ── Dependency Tests ───────────────────────────────────────────────────────

class TestDependencies:
    """Verify scipy is in requirements.txt and importable."""

    def test_scipy_in_requirements(self):
        with open(_REQUIREMENTS_PATH) as f:
            content = f.read()
        assert "scipy" in content

    def test_scipy_importable(self):
        import scipy
        assert hasattr(scipy, "__version__")

    def test_fpdf2_in_requirements(self):
        with open(_REQUIREMENTS_PATH) as f:
            content = f.read()
        assert "fpdf2" in content


# ── Basic Health Check Tests ───────────────────────────────────────────────

class TestBasicHealthCheck:
    """Tests for GET /api/health"""

    def test_health_check_healthy(self, fastapi_client, mock_db):
        mock_db["query_df"].return_value = pd.DataFrame({"ok": [1]})
        resp = fastapi_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["lakebase"] == "connected"

    def test_health_check_degraded(self, fastapi_client, mock_db):
        mock_db["query_df"].side_effect = Exception("Connection refused")
        resp = fastapi_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert "error" in data


# ── Detailed Health Check Tests ────────────────────────────────────────────

class TestDetailedHealthCheck:
    """Tests for GET /api/health/detailed"""

    def test_detailed_health_all_healthy(self, fastapi_client, mock_db):
        def qdf_side_effect(*args, **kwargs):
            q = args[0] if args else ""
            if "SELECT 1" in str(q):
                return pd.DataFrame({"ok": [1]})
            if "COUNT" in str(q):
                return pd.DataFrame({"cnt": [100]})
            return pd.DataFrame({"config_key": ["scenarios"],
                                "config_value": ['{"w": 0.5}']})

        mock_db["query_df"].side_effect = qdf_side_effect
        with patch(f"{HEALTH_MOD}.query_df", side_effect=qdf_side_effect):
            resp = fastapi_client.get("/api/health/detailed")
        assert resp.status_code == 200
        data = resp.json()
        assert "services" in data
        assert data["services"]["lakebase"]["healthy"] is True
        assert data["services"]["scipy"]["available"] is True

    def test_detailed_health_lakebase_down(self, fastapi_client, mock_db):
        with patch(f"{HEALTH_MOD}.query_df",
                   side_effect=Exception("Connection refused")):
            resp = fastapi_client.get("/api/health/detailed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["services"]["lakebase"]["healthy"] is False


# ── Individual Health Check Function Tests ─────────────────────────────────

class TestCheckLakebaseConnection:
    """Tests for check_lakebase_connection."""

    def test_connected(self):
        with patch(f"{HEALTH_MOD}.query_df",
                   return_value=pd.DataFrame({"ok": [1]})):
            from domain.health import check_lakebase_connection
            result = check_lakebase_connection()
        assert result["healthy"] is True
        assert result["status"] == "connected"

    def test_connection_error(self):
        with patch(f"{HEALTH_MOD}.query_df",
                   side_effect=Exception("timeout")):
            from domain.health import check_lakebase_connection
            result = check_lakebase_connection()
        assert result["healthy"] is False
        assert "error" in result


class TestCheckRequiredTables:
    """Tests for check_required_tables."""

    def test_all_tables_present(self):
        with patch(f"{HEALTH_MOD}.query_df",
                   return_value=pd.DataFrame({"cnt": [50]})):
            from domain.health import check_required_tables
            result = check_required_tables()
        assert result["all_present"] is True
        assert result["missing"] == []

    def test_missing_table(self):
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("table not found")
            return pd.DataFrame({"cnt": [50]})

        with patch(f"{HEALTH_MOD}.query_df", side_effect=side_effect):
            from domain.health import check_required_tables
            result = check_required_tables()
        assert result["all_present"] is False
        assert len(result["missing"]) >= 1


class TestCheckConfigLoaded:
    """Tests for check_config_loaded."""

    def test_config_loaded(self, mock_db):
        import admin_config
        admin_config._initialized = True
        mock_db["query_df"].return_value = pd.DataFrame({
            "config_key": ["scenarios"],
            "config_value": ['{"w": 0.5}'],
        })
        from domain.health import check_config_loaded
        result = check_config_loaded()
        assert result["loaded"] is True
        assert result["section_count"] >= 1


class TestCheckScipyAvailable:
    """Tests for check_scipy_available."""

    def test_scipy_available(self):
        from domain.health import check_scipy_available
        result = check_scipy_available()
        assert result["available"] is True
        assert "version" in result
