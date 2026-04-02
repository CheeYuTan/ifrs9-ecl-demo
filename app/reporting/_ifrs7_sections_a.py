"""IFRS 7 section builders -- 35F, 35H, 35I, 35J.

Dependencies are accessed via ``reporting.report_helpers`` so that
tests can patch at a single location.
"""
import reporting.report_helpers as _h


def _build_35f(sections: dict) -> None:
    """IFRS 7.35F - Credit risk exposure by grade."""
    try:
        df = _h.query_df(f"""
            SELECT
                CASE
                    WHEN l.current_lifetime_pd < 0.01 THEN 'Investment Grade (AAA-BBB)'
                    WHEN l.current_lifetime_pd < 0.05 THEN 'Sub-Investment (BB)'
                    WHEN l.current_lifetime_pd < 0.15 THEN 'Speculative (B)'
                    WHEN l.current_lifetime_pd < 0.30 THEN 'Highly Speculative (CCC)'
                    ELSE 'Default / Near Default (D)'
                END as credit_grade,
                l.assessed_stage,
                COUNT(*) as loan_count,
                ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as gross_carrying_amount,
                ROUND(SUM(e.weighted_ecl)::numeric, 2) as ecl_amount,
                ROUND(AVG(l.current_lifetime_pd)::numeric, 6) as avg_pd
            FROM {_h._t('model_ready_loans')} l
            JOIN {_h._t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
            GROUP BY 1, l.assessed_stage
            ORDER BY l.assessed_stage, 1
        """)
        sections["ifrs7_35f"] = {
            "title": "IFRS 7.35F \u2014 Credit Risk Exposure by Internal Rating Grade",
            "data": df.to_dict("records") if not df.empty else [],
        }
    except Exception as ex:
        _h.log.warning("IFRS 7.35F failed: %s", ex)
        sections["ifrs7_35f"] = {"title": "IFRS 7.35F \u2014 Credit Risk Exposure by Internal Rating Grade", "data": [], "error": str(ex)}


def _build_35h(sections: dict, project_id: str, prior_data: list[dict]) -> None:
    """IFRS 7.35H - ECL by stage with prior-period comparatives."""
    try:
        df = _h.query_df(f"""
            SELECT l.assessed_stage as stage,
                   COUNT(DISTINCT l.loan_id) as loan_count,
                   ROUND(SUM(DISTINCT l.gross_carrying_amount)::numeric, 2) as gross_carrying_amount,
                   ROUND(SUM(e.weighted_ecl)::numeric, 2) as ecl_amount,
                   ROUND(AVG(l.current_lifetime_pd)::numeric, 6) as avg_pd,
                   ROUND(AVG(le.base_lgd)::numeric, 4) as avg_lgd,
                   CASE WHEN SUM(l.gross_carrying_amount) > 0
                        THEN ROUND((SUM(e.weighted_ecl) / SUM(DISTINCT l.gross_carrying_amount) * 100)::numeric, 4)
                        ELSE 0 END as coverage_ratio
            FROM {_h._t('model_ready_loans')} l
            JOIN {_h._t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
            LEFT JOIN (SELECT DISTINCT ON (loan_id) loan_id, base_lgd FROM {_h._t('loan_level_ecl')}) le ON l.loan_id = le.loan_id
            GROUP BY l.assessed_stage
            ORDER BY l.assessed_stage
        """)
        current_data = df.to_dict("records") if not df.empty else []
        for row in current_data:
            stage = row.get("stage")
            prior_row = next((p for p in prior_data if p.get("stage") == stage), {})
            row["prior_ecl_amount"] = prior_row.get("ecl_amount", 0)
            row["prior_gross_carrying_amount"] = prior_row.get("gross_carrying_amount", 0)
            prior_ecl = prior_row.get("ecl_amount", 0) or 0
            current_ecl = row.get("ecl_amount", 0) or 0
            row["ecl_movement"] = round(float(current_ecl) - float(prior_ecl), 2)
            row["ecl_movement_pct"] = round((float(current_ecl) / float(prior_ecl) - 1) * 100, 2) if prior_ecl else 0
        sections["ifrs7_35h"] = {
            "title": "IFRS 7.35H \u2014 Loss Allowance by Stage (with Prior-Period Comparatives)",
            "data": current_data,
            "has_prior_period": len(prior_data) > 0,
        }
    except Exception as ex:
        _h.log.warning("IFRS 7.35H failed: %s", ex)
        sections["ifrs7_35h"] = {"title": "IFRS 7.35H \u2014 Loss Allowance by Stage", "data": [], "error": str(ex)}


def _build_35i(sections: dict, project_id: str) -> None:
    """IFRS 7.35I - Loss allowance reconciliation (uses attribution)."""
    try:
        attr = _h.get_attribution(project_id) or _h.compute_attribution(project_id)
        reconciliation = []
        for component in ["opening_ecl", "new_originations", "derecognitions", "stage_transfers",
                          "remeasurement", "management_overlays", "write_offs", "closing_ecl"]:
            entry = attr.get(component, {})
            reconciliation.append({
                "component": component.replace("_", " ").title(),
                "stage1": float(entry.get("stage1", 0)),
                "stage2": float(entry.get("stage2", 0)),
                "stage3": float(entry.get("stage3", 0)),
                "total": float(entry.get("total", 0)),
            })
        sections["ifrs7_35i"] = {
            "title": "IFRS 7.35I \u2014 Loss Allowance Reconciliation",
            "data": reconciliation,
        }
    except Exception as ex:
        _h.log.warning("IFRS 7.35I failed: %s", ex)
        sections["ifrs7_35i"] = {"title": "IFRS 7.35I \u2014 Loss Allowance Reconciliation", "data": [], "error": str(ex)}


def _build_35j(sections: dict) -> None:
    """IFRS 7.35J - Write-off disclosure."""
    try:
        # Check table existence first to provide a clear message
        tbl = _h._t('historical_defaults')
        check_df = _h.query_df(f"SELECT COUNT(*) as cnt FROM {tbl}")
        wo_df = _h.query_df(f"""
            SELECT
                COALESCE(product_type, 'Unknown') as product_type,
                COUNT(*) as default_count,
                ROUND(SUM(gross_carrying_amount_at_default)::numeric, 2) as gross_writeoff,
                ROUND(SUM(total_recovery_amount)::numeric, 2) as recovery_amount,
                ROUND(SUM(gross_carrying_amount_at_default - total_recovery_amount)::numeric, 2) as net_writeoff,
                ROUND(AVG(CASE WHEN gross_carrying_amount_at_default > 0
                    THEN total_recovery_amount / gross_carrying_amount_at_default * 100
                    ELSE 0 END)::numeric, 2) as recovery_rate_pct
            FROM {tbl}
            GROUP BY product_type
            ORDER BY gross_writeoff DESC
        """)
        outstanding_df = _h.query_df(f"""
            SELECT
                COUNT(*) as total_defaults,
                ROUND(SUM(gross_carrying_amount_at_default)::numeric, 2) as total_gross,
                ROUND(SUM(total_recovery_amount)::numeric, 2) as total_recovered,
                ROUND(SUM(gross_carrying_amount_at_default - total_recovery_amount)::numeric, 2) as total_net_writeoff,
                ROUND(SUM(CASE WHEN total_recovery_amount < gross_carrying_amount_at_default
                    THEN gross_carrying_amount_at_default - total_recovery_amount
                    ELSE 0 END)::numeric, 2) as contractual_outstanding
            FROM {tbl}
        """)
        summary = outstanding_df.to_dict('records')[0] if not outstanding_df.empty else {}
        sections['ifrs7_35j'] = {
            'title': 'IFRS 7.35J \u2014 Write-off Disclosure',
            'data': wo_df.to_dict('records') if not wo_df.empty else [],
            'summary': summary,
            'note': 'Per IFRS 7.35J, amounts written off that are still subject to enforcement activity',
        }
    except Exception as ex:
        err_str = str(ex)
        if ('relation' in err_str.lower() and 'does not exist' in err_str.lower()) or \
           'undefined_table' in err_str.lower():
            msg = (f"Historical defaults table ({_h._t('historical_defaults')}) not found. "
                   "Run the data pipeline (scripts/04_sync_to_lakebase.py) or configure "
                   "the historical_defaults table in Data Mapping to enable this disclosure.")
        else:
            msg = str(ex)
        _h.log.warning('IFRS 7.35J failed: %s', ex)
        sections['ifrs7_35j'] = {'title': 'IFRS 7.35J \u2014 Write-off Disclosure', 'data': [], 'error': msg}
