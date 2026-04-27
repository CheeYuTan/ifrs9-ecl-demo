"""IFRS 7 disclosure report -- orchestrator for sections 35F through 36."""

import json
from datetime import UTC
from datetime import datetime as _dt

import reporting.report_helpers as _h
from reporting._ifrs7_sections_a import (
    _build_35f,
    _build_35h,
    _build_35i,
    _build_35j,
)
from reporting._ifrs7_sections_b import (
    _build_35k,
    _build_35l,
    _build_35m,
    _build_36,
)


def _get_prior_period_35h(project_id: str) -> list[dict]:
    """Retrieve prior-period 35H data from the most recent finalized IFRS 7 report."""
    try:
        df = _h.query_df(
            f"""
            SELECT report_data
            FROM {_h.REPORT_TABLE}
            WHERE project_id = %s
              AND report_type = 'ifrs7_disclosure'
            ORDER BY created_at DESC
            LIMIT 1 OFFSET 1
        """,
            (project_id,),
        )
        if df.empty:
            return []
        data = df.iloc[0]["report_data"]
        if isinstance(data, str):
            data = json.loads(data)
        sections = data.get("sections", {})
        h_section = sections.get("ifrs7_35h", {})
        return h_section.get("data", [])
    except Exception:
        return []


def generate_ifrs7_disclosure(project_id: str, user: str = "system") -> dict:
    """Generate comprehensive IFRS 7 disclosure package."""
    proj = _h.get_project(project_id)
    if not proj:
        raise ValueError(f"Project {project_id} not found")

    report_date = proj.get("reporting_date") or _dt.now(UTC).strftime("%Y-%m-%d")
    sections: dict = {}

    _build_35f(sections)
    prior_data = _get_prior_period_35h(project_id)
    _build_35h(sections, project_id, prior_data)
    _build_35i(sections, project_id)
    _build_35j(sections)
    _build_35k(sections)
    _build_35l(sections)
    _build_35m(sections)
    _build_36(sections)

    report_id = _h._report_id("ifrs7_disclosure", project_id)
    report_data = {
        "report_type": "ifrs7_disclosure",
        "project_id": project_id,
        "report_date": report_date,
        "sections": sections,
        "generated_at": _dt.now(UTC).isoformat(),
    }

    _h.save_report(report_id, project_id, "ifrs7_disclosure", report_date, user, report_data)

    return {
        "report_id": report_id,
        "status": "draft",
        "report_type": "ifrs7_disclosure",
        "report_date": report_date,
        "generated_by": user,
        **report_data,
    }
