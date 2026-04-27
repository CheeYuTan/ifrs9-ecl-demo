"""Stage migration / transition analysis report."""

from datetime import UTC
from datetime import datetime as _dt

import reporting.report_helpers as _h


def generate_stage_migration_report(project_id: str, user: str = "system") -> dict:
    """Stage transition analysis report."""
    proj = _h.get_project(project_id)
    if not proj:
        raise ValueError(f"Project {project_id} not found")

    report_date = proj.get("reporting_date") or _dt.now(UTC).strftime("%Y-%m-%d")

    migration_matrix = []
    try:
        df = _h.query_df(f"""
            SELECT original_stage, assessed_stage,
                   SUM(loan_count) as loan_count,
                   ROUND(SUM(total_gca)::numeric, 2) as total_gca,
                   ROUND(SUM(total_ecl)::numeric, 2) as total_ecl
            FROM {_h._t("ifrs7_stage_migration")}
            GROUP BY original_stage, assessed_stage
            ORDER BY original_stage, assessed_stage
        """)
        if not df.empty:
            migration_matrix = df.to_dict("records")
    except Exception as ex:
        _h.log.warning("Stage migration query failed: %s", ex)

    transition_rates = []
    try:
        df = _h.query_df(f"""
            SELECT original_stage,
                   SUM(loan_count) as total_from_stage,
                   SUM(CASE WHEN assessed_stage = 1 THEN loan_count ELSE 0 END) as to_stage1,
                   SUM(CASE WHEN assessed_stage = 2 THEN loan_count ELSE 0 END) as to_stage2,
                   SUM(CASE WHEN assessed_stage = 3 THEN loan_count ELSE 0 END) as to_stage3
            FROM {_h._t("ifrs7_stage_migration")}
            GROUP BY original_stage
            ORDER BY original_stage
        """)
        for _, row in df.iterrows():
            total = int(row["total_from_stage"]) or 1
            transition_rates.append(
                {
                    "from_stage": int(row["original_stage"]),
                    "total_loans": total,
                    "to_stage1_pct": round(int(row["to_stage1"]) / total * 100, 2),
                    "to_stage2_pct": round(int(row["to_stage2"]) / total * 100, 2),
                    "to_stage3_pct": round(int(row["to_stage3"]) / total * 100, 2),
                }
            )
    except Exception as ex:
        _h.log.warning("Transition rates query failed: %s", ex)

    report_id = _h._report_id("stage_migration", project_id)
    report_data = {
        "report_type": "stage_migration",
        "project_id": project_id,
        "report_date": report_date,
        "sections": {
            "migration_matrix": {"title": "Stage Migration Matrix", "data": migration_matrix},
            "transition_rates": {"title": "Transition Rate Summary", "data": transition_rates},
        },
        "generated_at": _dt.now(UTC).isoformat(),
    }

    _h.save_report(report_id, project_id, "stage_migration", report_date, user, report_data)

    return {
        "report_id": report_id,
        "status": "draft",
        "report_type": "stage_migration",
        "report_date": report_date,
        "generated_by": user,
        **report_data,
    }
