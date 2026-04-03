"""Scenario sensitivity analysis report."""
import json as _json
from datetime import datetime as _dt, timezone as _tz

import reporting.report_helpers as _h


def generate_sensitivity_report(project_id: str, user: str = "system") -> dict:
    """Scenario sensitivity analysis report."""
    proj = _h.get_project(project_id)
    if not proj:
        raise ValueError(f"Project {project_id} not found")

    report_date = proj.get("reporting_date") or _dt.now(_tz.utc).strftime("%Y-%m-%d")

    base_ecl = 0.0
    stage_ecl = {}
    try:
        df = _h.query_df(f"""
            SELECT assessed_stage as stage,
                   ROUND(SUM(weighted_ecl)::numeric, 2) as ecl
            FROM {_h._t('model_ready_loans')} l
            JOIN {_h._t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
            GROUP BY assessed_stage
            ORDER BY assessed_stage
        """)
        for _, row in df.iterrows():
            s = int(row["stage"])
            v = float(row["ecl"])
            stage_ecl[s] = v
            base_ecl += v
    except Exception:
        pass

    weights = proj.get("scenario_weights", {})
    if isinstance(weights, str):
        try:
            weights = _json.loads(weights)
        except Exception:
            weights = {}

    scenario_data = []
    try:
        df = _h.query_df(f"""
            SELECT scenario,
                   ROUND(total_ecl::numeric, 2) as total_ecl,
                   ROUND(weight::numeric, 4) as weight,
                   ROUND(weighted_contribution::numeric, 2) as weighted_contribution
            FROM {_h._t('scenario_ecl_summary')}
            ORDER BY scenario
        """)
        total_gca_df = _h.query_df(f"""
            SELECT ROUND(SUM(total_gca)::numeric, 2) as total_gca,
                   SUM(loan_count) as loan_count
            FROM {_h._t('portfolio_ecl_summary')}
        """)
        total_gca = float(total_gca_df.iloc[0]["total_gca"]) if not total_gca_df.empty else 0
        total_loan_count = int(total_gca_df.iloc[0]["loan_count"]) if not total_gca_df.empty else 0
        for _, row in df.iterrows():
            name = row["scenario"]
            ecl = float(row["total_ecl"])
            w = float(row.get("weight", weights.get(name, 0)))
            scenario_data.append({
                "scenario": name,
                "ecl": ecl,
                "weight": w,
                "weighted_ecl": round(ecl * w, 2),
                "gca": total_gca,
                "loan_count": total_loan_count,
                "coverage_ratio": round(ecl / total_gca * 100, 4) if total_gca > 0 else 0,
                "diff_from_base": round(ecl - base_ecl, 2),
                "diff_pct": round((ecl / base_ecl - 1) * 100, 2) if base_ecl else 0,
            })
    except Exception as ex:
        _h.log.warning("Scenario data query failed: %s", ex)

    sensitivity_grid = []
    for pd_shift in [-20, -10, 0, 10, 20]:
        for lgd_shift in [-20, -10, 0, 10, 20]:
            pd_mult = 1 + pd_shift / 100
            lgd_mult = 1 + lgd_shift / 100
            stressed = base_ecl * pd_mult * lgd_mult
            sensitivity_grid.append({
                "pd_shift_pct": pd_shift,
                "lgd_shift_pct": lgd_shift,
                "ecl": round(stressed, 2),
                "change_from_base": round(stressed - base_ecl, 2),
                "change_pct": round((stressed / base_ecl - 1) * 100, 2) if base_ecl else 0,
            })

    report_id = _h._report_id("sensitivity", project_id)
    report_data = {
        "report_type": "sensitivity_analysis",
        "project_id": project_id,
        "report_date": report_date,
        "sections": {
            "base_ecl": {"title": "Base ECL Summary", "data": [
                {"stage": s, "ecl": v} for s, v in sorted(stage_ecl.items())
            ] + [{"stage": "Total", "ecl": base_ecl}]},
            "scenario_analysis": {"title": "Scenario Analysis", "data": scenario_data},
            "sensitivity_grid": {"title": "PD/LGD Sensitivity Grid", "data": sensitivity_grid},
        },
        "generated_at": _dt.now(_tz.utc).isoformat(),
    }

    _h.save_report(report_id, project_id, "sensitivity_analysis", report_date, user, report_data)

    return {"report_id": report_id, "status": "draft", "report_type": "sensitivity_analysis",
            "report_date": report_date, "generated_by": user, **report_data}
