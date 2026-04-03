"""Concentration risk analysis report."""
from datetime import datetime as _dt, timezone as _tz

import reporting.report_helpers as _h


def generate_concentration_report(project_id: str, user: str = "system") -> dict:
    """Concentration risk analysis report."""
    proj = _h.get_project(project_id)
    if not proj:
        raise ValueError(f"Project {project_id} not found")

    report_date = proj.get("reporting_date") or _dt.now(_tz.utc).strftime("%Y-%m-%d")

    by_product = []
    try:
        df = _h.query_df(f"""
            SELECT product_type,
                   COUNT(*) as loan_count,
                   ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
                   ROUND(SUM(weighted_ecl)::numeric, 2) as total_ecl,
                   ROUND(AVG(pd_lifetime)::numeric, 6) as avg_pd,
                   ROUND(AVG(lgd)::numeric, 4) as avg_lgd
            FROM {_h._t('model_ready_loans')} l
            JOIN {_h._t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
            GROUP BY product_type
            ORDER BY SUM(gross_carrying_amount) DESC
        """)
        total_gca = float(df["total_gca"].sum()) if not df.empty else 1
        for _, row in df.iterrows():
            gca = float(row["total_gca"])
            by_product.append({
                **row.to_dict(),
                "concentration_pct": round(gca / total_gca * 100, 2) if total_gca else 0,
            })
    except Exception as ex:
        _h.log.warning("Concentration by product failed: %s", ex)

    by_segment = []
    try:
        df = _h.query_df(f"""
            SELECT borrower_segment as segment,
                   COUNT(*) as loan_count,
                   ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
                   ROUND(SUM(weighted_ecl)::numeric, 2) as total_ecl,
                   ROUND(AVG(pd_lifetime)::numeric, 6) as avg_pd
            FROM {_h._t('model_ready_loans')} l
            JOIN {_h._t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
            GROUP BY borrower_segment
            ORDER BY SUM(gross_carrying_amount) DESC
        """)
        total_gca = float(df["total_gca"].sum()) if not df.empty else 1
        for _, row in df.iterrows():
            gca = float(row["total_gca"])
            by_segment.append({
                **row.to_dict(),
                "concentration_pct": round(gca / total_gca * 100, 2) if total_gca else 0,
            })
    except Exception as ex:
        _h.log.warning("Concentration by segment failed: %s", ex)

    top_exposures = []
    try:
        df = _h.query_df(f"""
            SELECT l.loan_id, l.product_type, l.borrower_segment,
                   l.gross_carrying_amount, l.assessed_stage,
                   l.pd_lifetime, e.weighted_ecl as ecl,
                   l.days_past_due
            FROM {_h._t('model_ready_loans')} l
            JOIN {_h._t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
            ORDER BY l.gross_carrying_amount DESC
            LIMIT 20
        """)
        if not df.empty:
            top_exposures = df.to_dict("records")
    except Exception as ex:
        _h.log.warning("Top exposures query failed: %s", ex)

    report_id = _h._report_id("concentration", project_id)
    report_data = {
        "report_type": "concentration_risk",
        "project_id": project_id,
        "report_date": report_date,
        "sections": {
            "by_product": {"title": "Concentration by Product Type", "data": by_product},
            "by_segment": {"title": "Concentration by Borrower Segment", "data": by_segment},
            "top_exposures": {"title": "Top 20 Single-Name Exposures", "data": top_exposures},
        },
        "generated_at": _dt.now(_tz.utc).isoformat(),
    }

    _h.save_report(report_id, project_id, "concentration_risk", report_date, user, report_data)

    return {"report_id": report_id, "status": "draft", "report_type": "concentration_risk",
            "report_date": report_date, "generated_by": user, **report_data}
