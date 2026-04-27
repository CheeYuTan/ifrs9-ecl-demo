"""
ECL Engine -- data loading from Lakebase.
"""

import backend
import pandas as pd

from ecl.config import _t


def _load_loans() -> pd.DataFrame:
    return backend.query_df(f"""
        SELECT loan_id, product_type, assessed_stage,
               gross_carrying_amount, effective_interest_rate,
               current_lifetime_pd, remaining_months
        FROM {_t("model_ready_loans")}
    """)


def _load_scenarios() -> pd.DataFrame:
    df = backend.query_df(f"""
        SELECT * FROM {_t("mc_ecl_distribution")}
    """)
    defaults = {
        "avg_pd_multiplier": 1.0,
        "avg_lgd_multiplier": 1.0,
        "pd_vol": 0.05,
        "lgd_vol": 0.03,
    }
    for col, default_val in defaults.items():
        if col not in df.columns:
            df[col] = default_val
    return df
