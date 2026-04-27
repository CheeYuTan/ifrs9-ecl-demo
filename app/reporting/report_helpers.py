"""Shared helpers, constants, and imports for reporting sub-modules.

Sub-modules should ``import reporting.report_helpers as _h`` and reference
dependencies as ``_h.query_df``, ``_h.get_project``, etc.  This keeps a
single patchable location for tests that mock DB / domain calls.
"""

import json as _json
import logging
from datetime import UTC
from datetime import datetime as _dt

from db.pool import SCHEMA, _t, execute, query_df  # noqa: F401 — re-exported for sub-modules
from domain.attribution import compute_attribution, get_attribution  # noqa: F401
from domain.workflow import get_project  # noqa: F401

log = logging.getLogger(__name__)

REPORT_TABLE = f"{SCHEMA}.regulatory_reports"


def ensure_report_tables():
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.regulatory_reports (
            report_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            report_type TEXT NOT NULL,
            report_date DATE NOT NULL DEFAULT CURRENT_DATE,
            status TEXT NOT NULL DEFAULT 'draft',
            generated_by TEXT DEFAULT 'system',
            report_data JSONB DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    log.info("Ensured regulatory_reports table exists")


def _report_id(report_type: str, project_id: str) -> str:
    ts = _dt.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"RPT-{report_type[:4].upper()}-{project_id}-{ts}"


def save_report(
    report_id: str, project_id: str, report_type: str, report_date: str, user: str, report_data: dict
) -> None:
    """Persist a report row into the regulatory_reports table."""
    ensure_report_tables()
    execute(
        f"""
        INSERT INTO {REPORT_TABLE} (report_id, project_id, report_type, report_date, status, generated_by, report_data)
        VALUES (%s, %s, %s, %s, 'draft', %s, %s::jsonb)
    """,
        (report_id, project_id, report_type, report_date, user, _json.dumps(report_data, default=str)),
    )
