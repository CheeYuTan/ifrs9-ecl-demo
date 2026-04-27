"""Hazard model estimation orchestrator — dispatches to individual estimators."""

import json as _json
import logging
import uuid
from datetime import UTC
from datetime import datetime as _dt

from db.pool import execute

from domain.hazard_cox_ph import _estimate_cox_ph
from domain.hazard_nonparam import _estimate_discrete_time, _estimate_kaplan_meier
from domain.hazard_tables import (
    HAZARD_CURVE_TABLE,
    HAZARD_MODEL_TABLE,
    _get_portfolio_hazard_data,
)

log = logging.getLogger(__name__)


def estimate_hazard_model(model_type: str, product_type: str | None = None, segment: str | None = None) -> dict:
    """Estimate a hazard model from portfolio data.

    model_type: 'cox_ph', 'discrete_time', or 'kaplan_meier'
    """
    from domain.hazard_retrieval import get_hazard_model

    df = _get_portfolio_hazard_data(product_type, segment)
    if df.empty:
        raise ValueError("No portfolio data available for hazard estimation")

    n_obs = len(df)
    n_events = int((df["assessed_stage"] >= 3).sum()) or max(1, int(n_obs * 0.05))

    if model_type == "cox_ph":
        result = _estimate_cox_ph(df, n_obs, n_events)
    elif model_type == "discrete_time":
        result = _estimate_discrete_time(df, n_obs, n_events)
    elif model_type == "kaplan_meier":
        result = _estimate_kaplan_meier(df, n_obs, n_events)
    else:
        raise ValueError(f"Unknown model type: {model_type}. Use cox_ph, discrete_time, or kaplan_meier")

    model_id = f"haz_{model_type}_{_dt.now(UTC).strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}"

    execute(
        f"""
        INSERT INTO {HAZARD_MODEL_TABLE}
            (model_id, model_type, coefficients, baseline_hazard,
             concordance_index, log_likelihood, aic, bic,
             product_type, segment, n_observations, n_events)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
        (
            model_id,
            model_type,
            _json.dumps(result["coefficients"]),
            _json.dumps(result["baseline_hazard"]),
            result["concordance_index"],
            result["log_likelihood"],
            result["aic"],
            result["bic"],
            product_type,
            segment,
            n_obs,
            n_events,
        ),
    )

    curves = result.get("curves", [])
    for curve in curves:
        curve_id = f"crv_{model_id}_{curve.get('segment', 'all')}_{str(uuid.uuid4())[:6]}"
        execute(
            f"""
            INSERT INTO {HAZARD_CURVE_TABLE}
                (curve_id, model_id, segment, time_points, survival_probs, hazard_rates)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                curve_id,
                model_id,
                curve.get("segment", "all"),
                _json.dumps(curve["time_points"]),
                _json.dumps(curve["survival_probs"]),
                _json.dumps(curve["hazard_rates"]),
            ),
        )

    return get_hazard_model(model_id)
