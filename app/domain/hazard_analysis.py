"""Survival curve computation, PD term structures, and model comparison."""

import logging
import math as _math

from domain.hazard_retrieval import get_hazard_model

log = logging.getLogger(__name__)


def compute_survival_curve(model_id: str, covariate_values: dict | None = None) -> dict:
    """Generate a survival curve for given covariate values using a fitted model."""
    model = get_hazard_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")

    baseline = model.get("baseline_hazard", {})
    coefficients = model.get("coefficients", {})
    max_t = max(int(k) for k in baseline) if baseline else 60

    risk_mult = 1.0
    if covariate_values and coefficients.get("covariates"):
        risk_score = 0.0
        for cov in coefficients["covariates"]:
            name = cov["name"]
            beta = cov.get("coefficient", 0)
            x_val = covariate_values.get(name, 0)
            risk_score += beta * x_val
        risk_mult = _math.exp(risk_score)

    time_points = list(range(1, max_t + 1))
    hazard_rates = []
    survival_probs = []
    cum_hazard = 0.0

    for t in time_points:
        h0 = baseline.get(str(t), 0)
        h = h0 * risk_mult
        h = min(h, 0.99)
        hazard_rates.append(round(h, 6))
        cum_hazard += h
        survival_probs.append(round(_math.exp(-cum_hazard), 6))

    pd_12m = round(1 - (survival_probs[11] if len(survival_probs) > 11 else survival_probs[-1]), 6)

    return {
        "model_id": model_id,
        "covariate_values": covariate_values,
        "time_points": time_points,
        "survival_probs": survival_probs,
        "hazard_rates": hazard_rates,
        "pd_12_month": pd_12m,
        "risk_multiplier": round(risk_mult, 4),
    }


def compute_term_structure_pd(model_id: str, max_months: int = 60) -> dict:
    """Convert hazard rates to a term structure of PD (marginal and cumulative)."""
    model = get_hazard_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")

    baseline = model.get("baseline_hazard", {})
    time_points = list(range(1, max_months + 1))
    marginal_pd = []
    cumulative_pd = []
    forward_pd = []
    cum_survival = 1.0

    for t in time_points:
        h = baseline.get(str(t), 0)
        marg = cum_survival * h
        marginal_pd.append(round(marg, 6))
        cum_survival *= 1 - h
        cumulative_pd.append(round(1 - cum_survival, 6))

    for i in range(len(time_points)):
        if i < 12:
            forward_pd.append(round(cumulative_pd[i], 6))
        else:
            s_prev = 1 - cumulative_pd[i - 12]
            s_curr = 1 - cumulative_pd[i]
            fwd = (s_prev - s_curr) / max(s_prev, 0.001)
            forward_pd.append(round(fwd, 6))

    pd_12m = cumulative_pd[11] if len(cumulative_pd) > 11 else cumulative_pd[-1]
    pd_lifetime = cumulative_pd[-1] if cumulative_pd else 0

    return {
        "model_id": model_id,
        "model_type": model.get("model_type"),
        "time_points": time_points,
        "marginal_pd": marginal_pd,
        "cumulative_pd": cumulative_pd,
        "forward_pd": forward_pd,
        "pd_12_month": round(pd_12m, 6),
        "pd_lifetime": round(pd_lifetime, 6),
    }


def compare_hazard_models(model_ids: list) -> dict:
    """Compare multiple hazard models side by side."""
    if not model_ids:
        return {"models": [], "curves": []}

    models = []
    all_curves = []
    for mid in model_ids:
        m = get_hazard_model(mid)
        if m:
            models.append(
                {
                    "model_id": m["model_id"],
                    "model_type": m["model_type"],
                    "concordance_index": m.get("concordance_index"),
                    "log_likelihood": m.get("log_likelihood"),
                    "aic": m.get("aic"),
                    "bic": m.get("bic"),
                    "n_observations": m.get("n_observations"),
                    "n_events": m.get("n_events"),
                    "product_type": m.get("product_type"),
                    "segment": m.get("segment"),
                    "estimation_date": m.get("estimation_date"),
                }
            )
            for curve in m.get("curves", []):
                if curve.get("segment") == "all":
                    all_curves.append(
                        {
                            "model_id": m["model_id"],
                            "model_type": m["model_type"],
                            "time_points": curve["time_points"],
                            "survival_probs": curve["survival_probs"],
                            "hazard_rates": curve["hazard_rates"],
                        }
                    )

    return {"models": models, "curves": all_curves}
