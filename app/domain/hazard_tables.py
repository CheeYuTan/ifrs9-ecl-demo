"""Hazard model database table setup and portfolio data retrieval."""

import logging
import pandas as pd

from db.pool import query_df, execute, _t, SCHEMA

log = logging.getLogger(__name__)


def ensure_hazard_tables():
    try:
        query_df(f"SELECT model_id FROM {SCHEMA}.hazard_model_results LIMIT 1")
    except Exception:
        try:
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.hazard_survival_curves CASCADE")
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.hazard_model_results CASCADE")
            log.info("Dropped legacy hazard tables for schema migration")
        except Exception:
            pass
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.hazard_model_results (
            model_id TEXT PRIMARY KEY,
            model_type TEXT NOT NULL,
            estimation_date DATE DEFAULT CURRENT_DATE,
            coefficients JSONB,
            baseline_hazard JSONB,
            concordance_index FLOAT,
            log_likelihood FLOAT,
            aic FLOAT,
            bic FLOAT,
            product_type TEXT,
            segment TEXT,
            n_observations INT DEFAULT 0,
            n_events INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.hazard_survival_curves (
            curve_id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            segment TEXT,
            time_points JSONB,
            survival_probs JSONB,
            hazard_rates JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    log.info("Ensured hazard tables exist")


HAZARD_MODEL_TABLE = f"{SCHEMA}.hazard_model_results"
HAZARD_CURVE_TABLE = f"{SCHEMA}.hazard_survival_curves"


def _get_portfolio_hazard_data(product_type: str | None = None, segment: str | None = None) -> pd.DataFrame:
    """Pull loan-level data needed for hazard model estimation."""
    conditions = []
    params = []
    if product_type:
        conditions.append("product_type = %s")
        params.append(product_type)
    if segment:
        conditions.append("segment = %s")
        params.append(segment)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query_df(f"""
        SELECT loan_id, product_type, segment, assessed_stage,
               days_past_due, current_lifetime_pd,
               gross_carrying_amount,
               COALESCE(remaining_months, 60) as remaining_term,
               vintage_cohort
        FROM {_t('model_ready_loans')}
        {where}
    """, tuple(params) if params else None)
