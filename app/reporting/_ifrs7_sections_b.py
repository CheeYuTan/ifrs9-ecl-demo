"""IFRS 7 section builders -- 35K, 35L, 35M, and 36."""
import reporting.report_helpers as _h


def _build_35k(sections: dict) -> None:
    """IFRS 7.35K - Significant changes in Gross Carrying Amount."""
    try:
        df = _h.query_df(f"""
            SELECT product_type,
                   assessed_stage as stage,
                   COUNT(*) as loan_count,
                   ROUND(SUM(gross_carrying_amount)::numeric, 2) as gross_carrying_amount,
                   ROUND(AVG(gross_carrying_amount)::numeric, 2) as avg_exposure,
                   ROUND(MIN(gross_carrying_amount)::numeric, 2) as min_exposure,
                   ROUND(MAX(gross_carrying_amount)::numeric, 2) as max_exposure
            FROM {_h._t('model_ready_loans')}
            GROUP BY product_type, assessed_stage
            ORDER BY product_type, assessed_stage
        """)
        sections["ifrs7_35k"] = {
            "title": "IFRS 7.35K \u2014 Gross Carrying Amount by Product and Stage",
            "data": df.to_dict("records") if not df.empty else [],
        }
    except Exception as ex:
        _h.log.warning("IFRS 7.35K failed: %s", ex)
        sections["ifrs7_35k"] = {"title": "IFRS 7.35K \u2014 Gross Carrying Amount by Product and Stage", "data": [], "error": str(ex)}


def _build_35l(sections: dict) -> None:
    """IFRS 7.35L - Modified financial assets."""
    try:
        df = _h.query_df(f"""
            SELECT product_type,
                   COUNT(*) as total_loans,
                   SUM(CASE WHEN days_past_due > 0 AND days_past_due <= 30 THEN 1 ELSE 0 END) as modified_performing,
                   SUM(CASE WHEN assessed_stage = 2 AND days_past_due <= 30 THEN 1 ELSE 0 END) as cured_to_stage1,
                   ROUND(SUM(CASE WHEN days_past_due > 0 AND days_past_due <= 30 THEN gross_carrying_amount ELSE 0 END)::numeric, 2) as modified_gca
            FROM {_h._t('model_ready_loans')}
            GROUP BY product_type
            ORDER BY product_type
        """)
        sections["ifrs7_35l"] = {
            "title": "IFRS 7.35L \u2014 Modified Financial Assets",
            "data": df.to_dict("records") if not df.empty else [],
        }
    except Exception as ex:
        _h.log.warning("IFRS 7.35L failed: %s", ex)
        sections["ifrs7_35l"] = {"title": "IFRS 7.35L \u2014 Modified Financial Assets", "data": [], "error": str(ex)}


def _build_35m(sections: dict) -> None:
    """IFRS 7.35M - Collateral and credit enhancements."""
    try:
        df = _h.query_df(f"""
            SELECT l.product_type,
                   l.assessed_stage as stage,
                   COUNT(DISTINCT l.loan_id) as loan_count,
                   ROUND(SUM(DISTINCT l.gross_carrying_amount)::numeric, 2) as total_exposure,
                   ROUND(SUM(DISTINCT l.gross_carrying_amount * (1 - COALESCE(le.base_lgd, 0.45)))::numeric, 2) as estimated_collateral,
                   ROUND(AVG(1 - COALESCE(le.base_lgd, 0.45))::numeric, 4) as avg_recovery_rate,
                   ROUND(AVG(COALESCE(le.base_lgd, 0.45))::numeric, 4) as avg_lgd
            FROM {_h._t('model_ready_loans')} l
            LEFT JOIN (SELECT DISTINCT ON (loan_id) loan_id, base_lgd FROM {_h._t('loan_level_ecl')}) le ON l.loan_id = le.loan_id
            GROUP BY l.product_type, l.assessed_stage
            ORDER BY l.product_type, l.assessed_stage
        """)
        sections["ifrs7_35m"] = {
            "title": "IFRS 7.35M \u2014 Collateral and Credit Enhancements",
            "data": df.to_dict("records") if not df.empty else [],
        }
    except Exception as ex:
        _h.log.warning("IFRS 7.35M failed: %s", ex)
        sections["ifrs7_35m"] = {"title": "IFRS 7.35M \u2014 Collateral and Credit Enhancements", "data": [], "error": str(ex)}


def _build_36(sections: dict) -> None:
    """IFRS 7.36 - Sensitivity analysis."""
    try:
        base_ecl_df = _h.query_df(f"""
            SELECT ROUND(SUM(weighted_ecl)::numeric, 2) as base_ecl
            FROM {_h._t('loan_ecl_weighted')}
        """)
        base_ecl = float(base_ecl_df.iloc[0]["base_ecl"]) if not base_ecl_df.empty else 0

        sensitivity = []
        for shift_name, pd_mult, lgd_mult in [
            ("PD +10%", 1.10, 1.00), ("PD -10%", 0.90, 1.00),
            ("PD +20%", 1.20, 1.00), ("PD -20%", 0.80, 1.00),
            ("LGD +10%", 1.00, 1.10), ("LGD -10%", 1.00, 0.90),
            ("PD+10% & LGD+10%", 1.10, 1.10), ("PD-10% & LGD-10%", 0.90, 0.90),
        ]:
            stressed_ecl = base_ecl * pd_mult * lgd_mult
            sensitivity.append({
                "scenario": shift_name,
                "base_ecl": round(base_ecl, 2),
                "stressed_ecl": round(stressed_ecl, 2),
                "change_amount": round(stressed_ecl - base_ecl, 2),
                "change_pct": round((stressed_ecl / base_ecl - 1) * 100, 2) if base_ecl else 0,
            })
        sections["ifrs7_36"] = {
            "title": "IFRS 7.36 \u2014 Sensitivity Analysis of ECL Estimates",
            "data": sensitivity,
        }
    except Exception as ex:
        _h.log.warning("IFRS 7.36 failed: %s", ex)
        sections["ifrs7_36"] = {"title": "IFRS 7.36 \u2014 Sensitivity Analysis of ECL Estimates", "data": [], "error": str(ex)}
