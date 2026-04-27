"""Report CRUD operations -- list, get, finalize, export."""

import json as _json

import reporting.report_helpers as _h


def list_reports(project_id: str | None = None, report_type: str | None = None) -> list[dict]:
    """List regulatory reports with optional filters."""
    _h.ensure_report_tables()
    where = []
    params: list = []
    if project_id:
        where.append("project_id = %s")
        params.append(project_id)
    if report_type:
        where.append("report_type = %s")
        params.append(report_type)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    df = _h.query_df(
        f"""
        SELECT report_id, project_id, report_type, report_date, status, generated_by, created_at
        FROM {_h.REPORT_TABLE}
        {clause}
        ORDER BY created_at DESC
    """,
        tuple(params) if params else None,
    )
    return df.to_dict("records") if not df.empty else []


def get_report(report_id: str) -> dict | None:
    """Get a single report with full data."""
    _h.ensure_report_tables()
    df = _h.query_df(
        f"""
        SELECT report_id, project_id, report_type, report_date, status, generated_by, report_data, created_at
        FROM {_h.REPORT_TABLE}
        WHERE report_id = %s
    """,
        (report_id,),
    )
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    rd = row.get("report_data")
    if isinstance(rd, str):
        try:
            row["report_data"] = _json.loads(rd)
        except Exception:
            pass
    return row


def finalize_report(report_id: str) -> dict | None:
    """Mark a report as final (locks it)."""
    _h.ensure_report_tables()
    _h.execute(
        f"""
        UPDATE {_h.REPORT_TABLE} SET status = 'final' WHERE report_id = %s AND status = 'draft'
    """,
        (report_id,),
    )
    return get_report(report_id)


def export_report_csv(report_id: str) -> list[dict]:
    """Export report data as a flat list of dicts suitable for CSV."""
    report = get_report(report_id)
    if not report:
        return []
    rd = report.get("report_data", {})
    if isinstance(rd, str):
        try:
            rd = _json.loads(rd)
        except Exception:
            return []

    sections = rd.get("sections", {})
    rows = []
    for section_key, section in sections.items():
        title = section.get("title", section_key)
        for item in section.get("data", []):
            flat = {"section": title}
            flat.update({k: v for k, v in item.items()})
            rows.append(flat)
    return rows
