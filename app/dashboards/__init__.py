"""
Dashboard SQL query utilities for IFRS 9 ECL Platform.

Provides helpers to load, list, and parameterise the 7 Lakeview
dashboard SQL files shipped in this package.
"""
import os
import re
from pathlib import Path

_DIR = Path(__file__).resolve().parent

# Ordered list of dashboard SQL files
QUERY_FILES = [
    "01_user_activity.sql",
    "02_project_analytics.sql",
    "03_model_performance.sql",
    "04_job_execution.sql",
    "05_api_usage.sql",
    "06_cost_allocation.sql",
    "07_system_health.sql",
]


def list_queries() -> list[str]:
    """Return the ordered list of dashboard query filenames."""
    return list(QUERY_FILES)


def load_query(filename: str, schema: str = "expected_credit_loss") -> str:
    """Load a SQL file and substitute the ``{schema}`` placeholder.

    Parameters
    ----------
    filename:
        One of the filenames from :pydata:`QUERY_FILES`.
    schema:
        The Lakebase schema name (default ``expected_credit_loss``).

    Returns
    -------
    str
        The SQL text with ``{schema}`` replaced.

    Raises
    ------
    FileNotFoundError
        If *filename* does not exist in the dashboards directory.
    ValueError
        If *schema* contains characters that are not safe for SQL identifiers.
    """
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", schema):
        raise ValueError(f"Invalid schema name: {schema!r}")
    path = _DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Dashboard SQL file not found: {path}")
    sql = path.read_text(encoding="utf-8")
    return sql.replace("{schema}", schema)


def load_all_queries(schema: str = "expected_credit_loss") -> dict[str, str]:
    """Load every dashboard SQL file, keyed by filename."""
    return {fn: load_query(fn, schema) for fn in QUERY_FILES}
