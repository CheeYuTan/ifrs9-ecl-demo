import json as _json
import logging

import pandas as pd
from db.pool import PREFIX, SCHEMA, _t, execute, query_df

log = logging.getLogger(__name__)

MODEL_RUNS_TABLE = f"{SCHEMA}.model_runs"


def ensure_model_runs_table():
    execute(f"""
        CREATE TABLE IF NOT EXISTS {MODEL_RUNS_TABLE} (
            run_id          TEXT PRIMARY KEY,
            run_type        TEXT NOT NULL,
            run_timestamp   TIMESTAMP NOT NULL DEFAULT NOW(),
            models_used     TEXT,
            products        TEXT,
            total_cohorts   INT DEFAULT 0,
            best_model_summary TEXT,
            status          TEXT DEFAULT 'completed',
            notes           TEXT,
            created_by      TEXT DEFAULT 'system'
        )
    """)
    try:
        execute(f"COMMENT ON TABLE {MODEL_RUNS_TABLE} IS 'ifrs9ecl: Model execution history'")
    except Exception:
        pass


def save_model_run(
    run_id: str,
    run_type: str,
    models_used: list,
    products: list,
    total_cohorts: int,
    best_model_summary: dict,
    notes: str = "",
) -> dict:
    ensure_model_runs_table()
    execute(
        f"""
        INSERT INTO {MODEL_RUNS_TABLE} (run_id, run_type, models_used, products, total_cohorts, best_model_summary, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id) DO UPDATE SET
            models_used=EXCLUDED.models_used, products=EXCLUDED.products,
            total_cohorts=EXCLUDED.total_cohorts, best_model_summary=EXCLUDED.best_model_summary,
            notes=EXCLUDED.notes
    """,
        (
            run_id,
            run_type,
            _json.dumps(models_used),
            _json.dumps(products),
            total_cohorts,
            _json.dumps(best_model_summary),
            notes,
        ),
    )
    return get_model_run(run_id)


def get_model_run(run_id: str) -> dict | None:
    ensure_model_runs_table()
    df = query_df(f"SELECT * FROM {MODEL_RUNS_TABLE} WHERE run_id = %s", (run_id,))
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    for col in ("models_used", "products", "best_model_summary"):
        v = row.get(col)
        if isinstance(v, str):
            try:
                row[col] = _json.loads(v)
            except Exception:
                pass
    return row


def list_model_runs(run_type: str = None) -> pd.DataFrame:
    ensure_model_runs_table()
    if run_type:
        return query_df(
            f"""
            SELECT run_id, run_type, run_timestamp, models_used, products,
                   total_cohorts, best_model_summary, status, notes, created_by
            FROM {MODEL_RUNS_TABLE}
            WHERE run_type = %s
            ORDER BY run_timestamp DESC
            LIMIT 50
        """,
            (run_type,),
        )
    return query_df(f"""
        SELECT run_id, run_type, run_timestamp, models_used, products,
               total_cohorts, best_model_summary, status, notes, created_by
        FROM {MODEL_RUNS_TABLE}
        ORDER BY run_timestamp DESC
        LIMIT 50
    """)


def get_active_run_id(run_type: str = "satellite_model") -> str | None:
    """Get the run_id of the data currently in the satellite model tables (latest run_timestamp)."""
    try:
        df = query_df(f"""
            SELECT DISTINCT run_timestamp FROM {_t("satellite_model_selected")}
            ORDER BY run_timestamp DESC LIMIT 1
        """)
        if df.empty:
            return None
        return str(df.iloc[0]["run_timestamp"])
    except Exception:
        return None


def get_satellite_model_comparison(run_id: str = None) -> pd.DataFrame:
    if run_id:
        return query_df(
            f"""
            SELECT product_type, cohort_id, model_type,
                   r_squared, rmse, aic, bic, cv_rmse,
                   coefficients_json, formula, n_observations, run_timestamp
            FROM {_t("satellite_model_comparison")}
            WHERE run_timestamp = %s
            ORDER BY product_type, cohort_id, model_type
        """,
            (run_id,),
        )
    return query_df(f"""
        SELECT product_type, cohort_id, model_type,
               r_squared, rmse, aic, bic, cv_rmse,
               coefficients_json, formula, n_observations, run_timestamp
        FROM {_t("satellite_model_comparison")}
        ORDER BY product_type, cohort_id, model_type
    """)


def get_satellite_model_selected(run_id: str = None) -> pd.DataFrame:
    if run_id:
        return query_df(
            f"""
            SELECT product_type, cohort_id, model_type,
                   r_squared, rmse, aic, bic,
                   coefficients_json, formula, selection_reason, n_observations, run_timestamp
            FROM {_t("satellite_model_selected")}
            WHERE run_timestamp = %s
            ORDER BY product_type, cohort_id
        """,
            (run_id,),
        )
    return query_df(f"""
        SELECT product_type, cohort_id, model_type,
               r_squared, rmse, aic, bic,
               coefficients_json, formula, selection_reason, n_observations, run_timestamp
        FROM {_t("satellite_model_selected")}
        ORDER BY product_type, cohort_id
    """)


def get_cohort_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, vintage_year as cohort_id,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(AVG(current_lifetime_pd)::numeric, 6) as avg_pd,
               ROUND(AVG(days_past_due)::numeric, 1) as avg_dpd,
               SUM(CASE WHEN assessed_stage = 1 THEN 1 ELSE 0 END) as stage1,
               SUM(CASE WHEN assessed_stage = 2 THEN 1 ELSE 0 END) as stage2,
               SUM(CASE WHEN assessed_stage = 3 THEN 1 ELSE 0 END) as stage3
        FROM {_t("model_ready_loans")}
        GROUP BY product_type, vintage_year
        ORDER BY product_type, loan_count DESC
    """)


def get_cohort_summary_by_product(product: str) -> pd.DataFrame:
    return query_df(
        f"""
        SELECT vintage_year as cohort_id,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(AVG(current_lifetime_pd)::numeric, 6) as avg_pd,
               ROUND(AVG(days_past_due)::numeric, 1) as avg_dpd,
               SUM(CASE WHEN assessed_stage = 1 THEN 1 ELSE 0 END) as stage1,
               SUM(CASE WHEN assessed_stage = 2 THEN 1 ELSE 0 END) as stage2,
               SUM(CASE WHEN assessed_stage = 3 THEN 1 ELSE 0 END) as stage3
        FROM {_t("model_ready_loans")}
        WHERE product_type = %s
        GROUP BY vintage_year
        ORDER BY loan_count DESC
    """,
        (product,),
    )


def get_ecl_by_cohort(product: str, dimension: str = "credit_grade") -> pd.DataFrame:
    """ECL drill-down by a meaningful business dimension instead of composite cohort_id."""
    ecl_tbl = _t("loan_ecl_weighted")
    loans_tbl = _t("model_ready_loans")
    dims = _detect_available_dimensions(loans_tbl)

    if dimension == "auto" or dimension not in dims:
        dimension = dims[0] if dims else "assessed_stage"

    if dimension == "assessed_stage":
        group_expr = "'Stage ' || l.assessed_stage::text"
    elif dimension == "vintage_year":
        group_expr = "l.vintage_year::text"
    else:
        group_expr = f"COALESCE(l.{dimension}::text, 'Unknown')"

    return query_df(
        f"""
        SELECT {group_expr} as cohort_id,
               COUNT(DISTINCT e.loan_id) as loan_count,
               ROUND(SUM(e.gross_carrying_amount)::numeric
                     / (SELECT COUNT(DISTINCT scenario) FROM {_t("loan_level_ecl")}), 2) as total_gca,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(e.weighted_ecl)
                     / NULLIF(SUM(e.gross_carrying_amount)::numeric
                              / (SELECT COUNT(DISTINCT scenario) FROM {_t("loan_level_ecl")}), 0)
                     * 100)::numeric, 2) as coverage_ratio
        FROM {ecl_tbl} e
        JOIN {loans_tbl} l ON e.loan_id = l.loan_id
        WHERE e.product_type = %s
        GROUP BY {group_expr}
        ORDER BY total_ecl DESC
    """,
        (product,),
    )


def get_stage_by_cohort(product: str) -> pd.DataFrame:
    return query_df(
        f"""
        SELECT vintage_year as cohort_id, assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca
        FROM {_t("model_ready_loans")}
        WHERE product_type = %s
        GROUP BY vintage_year, assessed_stage
        ORDER BY vintage_year, assessed_stage
    """,
        (product,),
    )


def get_portfolio_by_cohort(product: str) -> pd.DataFrame:
    """Legacy endpoint — delegates to dimension-based drill-down with best available dimension."""
    return get_portfolio_by_dimension(product, "auto")


def _detect_available_dimensions(tbl: str) -> list[str]:
    """Return list of drill-down dimensions available in the table."""
    try:
        cols_df = query_df(
            "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s",
            (SCHEMA, f"{PREFIX}model_ready_loans"),
        )
        cols = set(cols_df["column_name"].tolist()) if not cols_df.empty else set()
    except Exception:
        cols = set()

    DIMENSION_PRIORITY = [
        "credit_grade",
        "risk_band",
        "delinquency_bucket",
        "region",
        "age_bucket",
        "employment_type",
        "vintage_year",
        "ltv_band",
        "industry_sector",
        "assessed_stage",
        "segment",
    ]
    available = []
    for dim in DIMENSION_PRIORITY:
        if dim in cols:
            available.append(dim)
    return available


def get_drill_down_dimensions(product: str) -> list[dict]:
    """Return available drill-down dimensions for a product."""
    tbl = _t("model_ready_loans")
    dims = _detect_available_dimensions(tbl)
    labels = {
        "credit_grade": "Credit Grade",
        "risk_band": "Risk Band",
        "delinquency_bucket": "Delinquency Bucket",
        "region": "Geography",
        "age_bucket": "Age Group",
        "employment_type": "Employment Type",
        "vintage_year": "Origination Vintage",
        "ltv_band": "LTV Band",
        "industry_sector": "Industry Sector",
        "assessed_stage": "IFRS 9 Stage",
        "segment": "Segment",
    }
    return [{"key": d, "label": labels.get(d, d)} for d in dims]


def get_portfolio_by_dimension(product: str, dimension: str = "credit_grade") -> pd.DataFrame:
    """Drill-down portfolio data by a meaningful business dimension."""
    tbl = _t("model_ready_loans")
    dims = _detect_available_dimensions(tbl)

    if dimension == "auto":
        dimension = dims[0] if dims else "assessed_stage"

    if dimension == "assessed_stage":
        group_expr = "'Stage ' || assessed_stage::text"
    elif dimension == "vintage_year":
        group_expr = "vintage_year::text"
    elif dimension in dims:
        group_expr = f"COALESCE({dimension}::text, 'Unknown')"
    else:
        group_expr = "'All'"

    return query_df(
        f"""
        SELECT {group_expr} as cohort_id,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(AVG(COALESCE(current_lifetime_pd, 0) * 100)::numeric, 2) as avg_pd_pct,
               ROUND(AVG(COALESCE(days_past_due, 0))::numeric, 1) as avg_dpd
        FROM {tbl}
        WHERE product_type = %s
        GROUP BY {group_expr}
        ORDER BY total_gca DESC
    """,
        (product,),
    )


def get_ecl_by_product_drilldown() -> pd.DataFrame:
    """ECL grouped by product for the top-level drill-down."""
    return query_df(f"""
        SELECT product_type,
               COUNT(DISTINCT loan_id) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(SUM(weighted_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(weighted_ecl) / NULLIF(SUM(gross_carrying_amount), 0) * 100)::numeric, 2) as coverage_ratio
        FROM {_t("loan_ecl_weighted")}
        GROUP BY product_type
        ORDER BY total_ecl DESC
    """)
