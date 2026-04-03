"""Hazard model module — re-exports from sub-modules for backward compatibility.

Sub-modules:
  hazard_tables      — DB table setup, constants, portfolio data retrieval
  hazard_cox_ph      — Cox Proportional Hazards estimator + segment curves
  hazard_nonparam    — Discrete-time logistic and Kaplan-Meier estimators
  hazard_estimation  — Orchestrator that dispatches to estimators and persists results
  hazard_retrieval   — Model get/list from database
  hazard_analysis    — Survival curves, PD term structures, model comparison
"""

# ── hazard_tables: DB setup, constants, data retrieval ────────────────────
from domain.hazard_tables import (  # noqa: F401
    ensure_hazard_tables,
    HAZARD_MODEL_TABLE,
    HAZARD_CURVE_TABLE,
    _get_portfolio_hazard_data,
)

# ── hazard_cox_ph: Cox PH estimator + segment curve builder ──────────────
from domain.hazard_cox_ph import (  # noqa: F401
    _estimate_cox_ph,
    _build_segment_curves,
)

# ── hazard_nonparam: discrete-time + Kaplan-Meier estimators ─────────────
from domain.hazard_nonparam import (  # noqa: F401
    _estimate_discrete_time,
    _estimate_kaplan_meier,
)

# ── hazard_estimation: orchestrator ──────────────────────────────────────
from domain.hazard_estimation import (  # noqa: F401
    estimate_hazard_model,
)

# ── hazard_retrieval: model get / list ───────────────────────────────────
from domain.hazard_retrieval import (  # noqa: F401
    get_hazard_model,
    list_hazard_models,
)

# ── hazard_analysis: survival curves, PD term structures, comparison ─────
from domain.hazard_analysis import (  # noqa: F401
    compute_survival_curve,
    compute_term_structure_pd,
    compare_hazard_models,
)
