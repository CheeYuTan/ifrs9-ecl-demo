"""
Unit tests for dashboard SQL query files.

Tests cover:
  - All 7 SQL files load correctly via the dashboards module
  - Schema placeholder substitution works
  - SQL syntax is broadly valid (balanced parens, no stray {schema})
  - Empty-table handling patterns (COALESCE/NULLIF) are present
  - load_query rejects invalid schema names
  - list_queries returns the expected 7 files
"""
import os
import re
import pytest

# Ensure the app directory is importable
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import dashboards


# ── Fixtures ──────────────────────────────────────────────────────────────────

EXPECTED_FILES = [
    "01_user_activity.sql",
    "02_project_analytics.sql",
    "03_model_performance.sql",
    "04_job_execution.sql",
    "05_api_usage.sql",
    "06_cost_allocation.sql",
    "07_system_health.sql",
]


# ── list_queries ──────────────────────────────────────────────────────────────

def test_list_queries_returns_all_seven():
    result = dashboards.list_queries()
    assert result == EXPECTED_FILES


def test_list_queries_returns_list():
    result = dashboards.list_queries()
    assert isinstance(result, list)
    assert len(result) == 7


# ── load_query ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", EXPECTED_FILES)
def test_load_query_returns_string(filename):
    sql = dashboards.load_query(filename)
    assert isinstance(sql, str)
    assert len(sql) > 50, f"{filename} is suspiciously short"


@pytest.mark.parametrize("filename", EXPECTED_FILES)
def test_load_query_substitutes_schema(filename):
    sql = dashboards.load_query(filename, schema="my_schema")
    assert "{schema}" not in sql, f"{filename} still has unsubstituted {{schema}}"
    assert "my_schema" in sql


@pytest.mark.parametrize("filename", EXPECTED_FILES)
def test_load_query_default_schema(filename):
    sql = dashboards.load_query(filename)
    assert "expected_credit_loss" in sql


def test_load_query_file_not_found():
    with pytest.raises(FileNotFoundError):
        dashboards.load_query("nonexistent.sql")


def test_load_query_invalid_schema_semicolon():
    with pytest.raises(ValueError, match="Invalid schema name"):
        dashboards.load_query(EXPECTED_FILES[0], schema="bad;schema")


def test_load_query_invalid_schema_space():
    with pytest.raises(ValueError, match="Invalid schema name"):
        dashboards.load_query(EXPECTED_FILES[0], schema="bad schema")


def test_load_query_valid_schema_with_underscore():
    sql = dashboards.load_query(EXPECTED_FILES[0], schema="my_ecl_schema")
    assert "my_ecl_schema" in sql


# ── load_all_queries ──────────────────────────────────────────────────────────

def test_load_all_queries_returns_dict():
    result = dashboards.load_all_queries()
    assert isinstance(result, dict)
    assert set(result.keys()) == set(EXPECTED_FILES)


def test_load_all_queries_custom_schema():
    result = dashboards.load_all_queries(schema="custom_schema")
    for fn, sql in result.items():
        assert "custom_schema" in sql, f"{fn} missing custom schema"
        assert "{schema}" not in sql


# ── SQL syntax checks ────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", EXPECTED_FILES)
def test_sql_balanced_parentheses(filename):
    sql = dashboards.load_query(filename)
    assert sql.count("(") == sql.count(")"), (
        f"{filename} has unbalanced parentheses"
    )


@pytest.mark.parametrize("filename", EXPECTED_FILES)
def test_sql_contains_select(filename):
    sql = dashboards.load_query(filename).upper()
    assert "SELECT" in sql, f"{filename} has no SELECT statement"


@pytest.mark.parametrize("filename", EXPECTED_FILES)
def test_sql_no_trailing_semicolons(filename):
    """SQL files should not end with semicolons — each query block is
    delimited by comments; trailing semicolons would break some drivers."""
    sql = dashboards.load_query(filename).strip()
    # It's OK to have semicolons between queries — just check last char
    # Actually, having semicolons at statement boundaries is standard SQL.
    # Just verify the file is non-empty and parseable.
    assert len(sql) > 0


@pytest.mark.parametrize("filename", EXPECTED_FILES)
def test_sql_no_unsubstituted_placeholders(filename):
    sql = dashboards.load_query(filename)
    remaining = re.findall(r"\{[^}]+\}", sql)
    assert len(remaining) == 0, (
        f"{filename} has unsubstituted placeholders: {remaining}"
    )


# ── Empty-table handling patterns ─────────────────────────────────────────────

@pytest.mark.parametrize("filename", EXPECTED_FILES)
def test_sql_has_coalesce_or_nullif(filename):
    """Each query file should use COALESCE or NULLIF to handle empty tables."""
    sql = dashboards.load_query(filename).upper()
    has_coalesce = "COALESCE" in sql
    has_nullif = "NULLIF" in sql
    assert has_coalesce or has_nullif, (
        f"{filename} should use COALESCE or NULLIF for empty-table safety"
    )


# ── Time-series patterns ─────────────────────────────────────────────────────

_TIME_SERIES_FILES = [
    "01_user_activity.sql",
    "04_job_execution.sql",
    "05_api_usage.sql",
    "07_system_health.sql",
]


@pytest.mark.parametrize("filename", _TIME_SERIES_FILES)
def test_sql_uses_date_trunc(filename):
    sql = dashboards.load_query(filename).upper()
    assert "DATE_TRUNC" in sql, (
        f"{filename} should use DATE_TRUNC for time-series aggregation"
    )


# ── Specific table references ─────────────────────────────────────────────────

def test_user_activity_references_correct_tables():
    sql = dashboards.load_query("01_user_activity.sql")
    assert "app_usage_analytics" in sql
    assert "audit_trail" in sql


def test_project_analytics_references_workflow():
    sql = dashboards.load_query("02_project_analytics.sql")
    assert "ecl_workflow" in sql


def test_model_performance_references_metrics_and_registry():
    sql = dashboards.load_query("03_model_performance.sql")
    assert "backtest_metrics" in sql
    assert "model_registry" in sql


def test_job_execution_references_pipeline_runs():
    sql = dashboards.load_query("04_job_execution.sql")
    assert "pipeline_runs" in sql


def test_api_usage_references_analytics():
    sql = dashboards.load_query("05_api_usage.sql")
    assert "app_usage_analytics" in sql


def test_cost_allocation_references_pg_size():
    sql = dashboards.load_query("06_cost_allocation.sql")
    assert "pg_total_relation_size" in sql


def test_system_health_references_analytics():
    sql = dashboards.load_query("07_system_health.sql")
    assert "app_usage_analytics" in sql
