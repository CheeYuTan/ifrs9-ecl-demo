"""ECL movement report -- period-over-period analysis."""

from datetime import UTC
from datetime import datetime as _dt

import reporting.report_helpers as _h


def generate_ecl_movement_report(project_id: str, user: str = "system") -> dict:
    """Period-over-period ECL movement report."""
    proj = _h.get_project(project_id)
    if not proj:
        raise ValueError(f"Project {project_id} not found")

    report_date = proj.get("reporting_date") or _dt.now(UTC).strftime("%Y-%m-%d")

    movement_data = []
    try:
        df = _h.query_df(f"""
            SELECT product_type,
                   assessed_stage as stage,
                   ROUND(SUM(gross_carrying_amount)::numeric, 2) as gca,
                   ROUND(SUM(weighted_ecl)::numeric, 2) as ecl,
                   COUNT(*) as loan_count,
                   ROUND(AVG(pd_lifetime)::numeric, 6) as avg_pd,
                   ROUND(AVG(lgd)::numeric, 4) as avg_lgd
            FROM {_h._t("model_ready_loans")} l
            JOIN {_h._t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
            GROUP BY product_type, assessed_stage
            ORDER BY product_type, assessed_stage
        """)
        if not df.empty:
            movement_data = df.to_dict("records")
    except Exception as ex:
        _h.log.warning("ECL movement query failed: %s", ex)

    attr = None
    try:
        attr = _h.get_attribution(project_id) or _h.compute_attribution(project_id)
    except Exception:
        pass

    waterfall = []
    if attr:
        for key in [
            "opening_ecl",
            "new_originations",
            "derecognitions",
            "stage_transfers",
            "remeasurement",
            "management_overlays",
            "write_offs",
            "closing_ecl",
        ]:
            entry = attr.get(key, {})
            waterfall.append(
                {
                    "component": key.replace("_", " ").title(),
                    "total": float(entry.get("total", 0)),
                    "stage1": float(entry.get("stage1", 0)),
                    "stage2": float(entry.get("stage2", 0)),
                    "stage3": float(entry.get("stage3", 0)),
                }
            )

    report_id = _h._report_id("ecl_movement", project_id)
    report_data = {
        "report_type": "ecl_movement",
        "project_id": project_id,
        "report_date": report_date,
        "sections": {
            "ecl_by_product_stage": {"title": "ECL by Product and Stage", "data": movement_data},
            "waterfall": {"title": "ECL Movement Waterfall", "data": waterfall},
        },
        "generated_at": _dt.now(UTC).isoformat(),
    }

    _h.save_report(report_id, project_id, "ecl_movement", report_date, user, report_data)

    return {
        "report_id": report_id,
        "status": "draft",
        "report_type": "ecl_movement",
        "report_date": report_date,
        "generated_by": user,
        **report_data,
    }
