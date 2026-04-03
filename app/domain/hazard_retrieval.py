"""Hazard model retrieval and listing from the database."""

import json as _json
import logging
import pandas as pd

from db.pool import query_df

from domain.hazard_tables import HAZARD_MODEL_TABLE, HAZARD_CURVE_TABLE

log = logging.getLogger(__name__)


def get_hazard_model(model_id: str) -> dict | None:
    """Get a hazard model with its coefficients and survival curves."""
    df = query_df(f"SELECT * FROM {HAZARD_MODEL_TABLE} WHERE model_id = %s", (model_id,))
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    for col in ("coefficients", "baseline_hazard"):
        v = row.get(col)
        if isinstance(v, str):
            try:
                row[col] = _json.loads(v)
            except Exception:
                pass

    curves_df = query_df(f"""
        SELECT curve_id, segment, time_points, survival_probs, hazard_rates
        FROM {HAZARD_CURVE_TABLE}
        WHERE model_id = %s
        ORDER BY segment
    """, (model_id,))
    curves = []
    for _, c in curves_df.iterrows():
        cd = c.to_dict()
        for col in ("time_points", "survival_probs", "hazard_rates"):
            v = cd.get(col)
            if isinstance(v, str):
                try:
                    cd[col] = _json.loads(v)
                except Exception:
                    pass
        curves.append(cd)
    row["curves"] = curves
    return row


def list_hazard_models(model_type: str | None = None, product_type: str | None = None) -> list[dict]:
    """List hazard models with optional filtering."""
    conditions = []
    params = []
    if model_type:
        conditions.append("model_type = %s")
        params.append(model_type)
    if product_type:
        conditions.append("product_type = %s")
        params.append(product_type)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    df = query_df(f"""
        SELECT model_id, model_type, estimation_date, concordance_index,
               log_likelihood, aic, bic, product_type, segment,
               n_observations, n_events, created_at
        FROM {HAZARD_MODEL_TABLE}
        {where}
        ORDER BY created_at DESC
    """, tuple(params) if params else None)
    if df.empty:
        return []
    return df.to_dict("records")
