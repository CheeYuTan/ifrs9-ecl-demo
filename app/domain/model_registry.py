import json as _json
import logging
import uuid
from datetime import UTC

from db.pool import SCHEMA, execute, query_df

log = logging.getLogger(__name__)


def ensure_model_registry_table():
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.model_registry (
            model_id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            model_type TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            version INT NOT NULL DEFAULT 1,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            product_type TEXT,
            cohort TEXT,
            parameters JSONB,
            performance_metrics JSONB,
            training_data_info JSONB,
            is_champion BOOLEAN DEFAULT FALSE,
            created_by TEXT DEFAULT 'system',
            created_at TIMESTAMP DEFAULT NOW(),
            approved_by TEXT,
            approved_at TIMESTAMP,
            promoted_by TEXT,
            promoted_at TIMESTAMP,
            retired_by TEXT,
            retired_at TIMESTAMP,
            notes TEXT,
            parent_model_id TEXT
        )
    """)
    try:
        execute(f"COMMENT ON TABLE {SCHEMA}.model_registry IS 'ifrs9ecl: Model governance and lifecycle tracking'")
    except Exception:
        pass
    _migrate_model_registry_columns()
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.model_registry_audit (
            audit_id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            action TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            performed_by TEXT,
            performed_at TIMESTAMP DEFAULT NOW(),
            comment TEXT
        )
    """)
    try:
        execute(f"COMMENT ON TABLE {SCHEMA}.model_registry_audit IS 'ifrs9ecl: Model status change log'")
    except Exception:
        pass
    log.info("Ensured model_registry tables exist")


def _migrate_model_registry_columns():
    """Recreate model_registry if it's missing required columns (e.g. from an older schema)."""
    try:
        cols_df = query_df(
            "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = 'model_registry'",
            (SCHEMA,),
        )
        existing_cols = set(cols_df["column_name"].tolist()) if not cols_df.empty else set()
        required = {"description", "performance_metrics", "is_champion", "approved_by", "approved_at"}
        if required - existing_cols:
            log.info("Model registry table missing columns %s — dropping and recreating", required - existing_cols)
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.model_registry")
            execute(f"""
                CREATE TABLE {SCHEMA}.model_registry (
                    model_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    version INT NOT NULL DEFAULT 1,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'draft',
                    product_type TEXT,
                    cohort TEXT,
                    parameters JSONB,
                    performance_metrics JSONB,
                    training_data_info JSONB,
                    is_champion BOOLEAN DEFAULT FALSE,
                    created_by TEXT DEFAULT 'system',
                    created_at TIMESTAMP DEFAULT NOW(),
                    approved_by TEXT,
                    approved_at TIMESTAMP,
                    promoted_by TEXT,
                    promoted_at TIMESTAMP,
                    retired_by TEXT,
                    retired_at TIMESTAMP,
                    notes TEXT,
                    parent_model_id TEXT
                )
            """)
    except Exception:
        log.debug("Model registry migration check skipped")


MODEL_REGISTRY_TABLE = f"{SCHEMA}.model_registry"
MODEL_REGISTRY_AUDIT_TABLE = f"{SCHEMA}.model_registry_audit"

VALID_MODEL_STATUSES = ("draft", "pending_review", "approved", "active", "retired")
VALID_STATUS_TRANSITIONS = {
    "draft": ["pending_review"],
    "pending_review": ["approved", "draft"],
    "approved": ["active"],
    "active": ["retired"],
    "retired": [],
}


VALID_MODEL_TYPES = {"PD", "LGD", "EAD", "Staging"}


def register_model(data: dict) -> dict:
    """Register a new model version in the registry."""
    model_id = data.get("model_id") or str(uuid.uuid4())
    model_name = data.get("model_name", "")
    model_type = data.get("model_type", "PD")
    if model_type not in VALID_MODEL_TYPES:
        raise ValueError(f"Invalid model_type '{model_type}'. Must be one of: {', '.join(sorted(VALID_MODEL_TYPES))}")
    algorithm = data.get("algorithm", "Unknown")
    version = int(data.get("version", 1))
    description = data.get("description", "")
    status = "draft"
    product_type = data.get("product_type", "")
    cohort = data.get("cohort", "")
    parameters = data.get("parameters", {})
    performance_metrics = data.get("performance_metrics", {})
    training_data_info = data.get("training_data_info", {})
    created_by = data.get("created_by", "system")
    notes = data.get("notes", "")
    parent_model_id = data.get("parent_model_id")

    execute(
        f"""
        INSERT INTO {MODEL_REGISTRY_TABLE}
            (model_id, model_name, model_type, algorithm, version, description, status,
             product_type, cohort, parameters, performance_metrics, training_data_info,
             is_champion, created_by, notes, parent_model_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, %s, %s, %s)
    """,
        (
            model_id,
            model_name,
            model_type,
            algorithm,
            version,
            description,
            status,
            product_type,
            cohort,
            _json.dumps(parameters),
            _json.dumps(performance_metrics),
            _json.dumps(training_data_info),
            created_by,
            notes,
            parent_model_id,
        ),
    )

    _log_model_audit(model_id, "registered", None, "draft", created_by, "Model registered")
    return get_model(model_id)


def list_models(model_type: str = None, status: str = None) -> list[dict]:
    """List models with optional filtering by type and status."""
    conditions = []
    params = []
    if model_type:
        conditions.append("model_type = %s")
        params.append(model_type)
    if status:
        conditions.append("status = %s")
        params.append(status)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    df = query_df(
        f"""
        SELECT model_id, model_name, model_type, algorithm, version, description,
               status, product_type, cohort, parameters, performance_metrics,
               training_data_info, is_champion, created_by, created_at, approved_by, approved_at,
               promoted_by, promoted_at, retired_by, retired_at, notes, parent_model_id
        FROM {MODEL_REGISTRY_TABLE}
        {where}
        ORDER BY created_at DESC
    """,
        tuple(params) if params else None,
    )

    if df.empty:
        return []
    return _parse_model_rows(df)


def get_model(model_id: str) -> dict | None:
    """Get a single model with full details."""
    df = query_df(
        f"""
        SELECT model_id, model_name, model_type, algorithm, version, description,
               status, product_type, cohort, parameters, performance_metrics,
               training_data_info, is_champion, created_by, created_at,
               approved_by, approved_at, promoted_by, promoted_at,
               retired_by, retired_at, notes, parent_model_id
        FROM {MODEL_REGISTRY_TABLE}
        WHERE model_id = %s
    """,
        (model_id,),
    )

    if df.empty:
        return None
    rows = _parse_model_rows(df)
    return rows[0] if rows else None


def update_model_status(model_id: str, new_status: str, user: str, comment: str = "") -> dict:
    """Governance workflow: transition a model's status with validation and audit logging."""
    model = get_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")

    old_status = model["status"]
    allowed = VALID_STATUS_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise ValueError(f"Cannot transition from '{old_status}' to '{new_status}'. Allowed: {allowed}")

    update_fields = ["status = %s"]
    update_params = [new_status]

    if new_status == "approved":
        update_fields.extend(["approved_by = %s", "approved_at = NOW()"])
        update_params.extend([user])
    elif new_status == "active":
        update_fields.extend(["promoted_by = %s", "promoted_at = NOW()"])
        update_params.extend([user])
    elif new_status == "retired":
        update_fields.extend(["retired_by = %s", "retired_at = NOW()", "is_champion = FALSE"])
        update_params.extend([user])

    update_params.append(model_id)
    execute(
        f"""
        UPDATE {MODEL_REGISTRY_TABLE}
        SET {", ".join(update_fields)}
        WHERE model_id = %s
    """,
        tuple(update_params),
    )

    action_map = {
        "pending_review": "submitted_for_review",
        "approved": "approved",
        "draft": "rejected",
        "active": "promoted_to_active",
        "retired": "retired",
    }
    _log_model_audit(model_id, action_map.get(new_status, new_status), old_status, new_status, user, comment)
    return get_model(model_id)


def promote_champion(model_id: str, user: str) -> dict:
    """Set a model as champion, unsetting the previous champion for the same model_type."""
    model = get_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")
    if model["status"] not in ("approved", "active"):
        raise ValueError(f"Only approved or active models can be promoted to champion (current: {model['status']})")

    execute(
        f"""
        UPDATE {MODEL_REGISTRY_TABLE}
        SET is_champion = FALSE
        WHERE model_type = %s AND is_champion = TRUE
    """,
        (model["model_type"],),
    )

    execute(
        f"""
        UPDATE {MODEL_REGISTRY_TABLE}
        SET is_champion = TRUE
        WHERE model_id = %s
    """,
        (model_id,),
    )

    _log_model_audit(model_id, "promoted_to_champion", None, None, user, f"Set as champion for {model['model_type']}")
    return get_model(model_id)


def compare_models(model_ids: list) -> list[dict]:
    """Return side-by-side comparison of models."""
    if not model_ids:
        return []
    placeholders = ",".join(["%s"] * len(model_ids))
    df = query_df(
        f"""
        SELECT model_id, model_name, model_type, algorithm, version, description,
               status, product_type, parameters, performance_metrics,
               is_champion, created_by, created_at
        FROM {MODEL_REGISTRY_TABLE}
        WHERE model_id IN ({placeholders})
        ORDER BY created_at DESC
    """,
        tuple(model_ids),
    )

    if df.empty:
        return []
    return _parse_model_rows(df)


def get_model_audit_trail(model_id: str) -> list[dict]:
    """Full audit history for a model."""
    df = query_df(
        f"""
        SELECT audit_id, model_id, action, old_status, new_status,
               performed_by, performed_at, comment
        FROM {MODEL_REGISTRY_AUDIT_TABLE}
        WHERE model_id = %s
        ORDER BY performed_at DESC
    """,
        (model_id,),
    )

    if df.empty:
        return []
    return df.to_dict("records")


def _log_model_audit(
    model_id: str, action: str, old_status: str | None, new_status: str | None, user: str, comment: str
):
    audit_id = str(uuid.uuid4())
    execute(
        f"""
        INSERT INTO {MODEL_REGISTRY_AUDIT_TABLE}
            (audit_id, model_id, action, old_status, new_status, performed_by, comment)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """,
        (audit_id, model_id, action, old_status, new_status, user, comment),
    )


def generate_model_card(model_id: str) -> dict:
    """Auto-generate a model card with methodology, assumptions, limitations, and validation results."""
    model = get_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")

    audit = get_model_audit_trail(model_id)
    params = model.get("parameters", {}) or {}
    metrics = model.get("performance_metrics", {}) or {}
    training_info = model.get("training_data_info", {}) or {}

    card = {
        "model_id": model_id,
        "model_name": model.get("model_name", ""),
        "model_type": model.get("model_type", ""),
        "algorithm": model.get("algorithm", ""),
        "version": model.get("version", 1),
        "status": model.get("status", "draft"),
        "is_champion": model.get("is_champion", False),
        "methodology": {
            "description": model.get("description", ""),
            "algorithm": model.get("algorithm", ""),
            "parameters": params,
            "product_type": model.get("product_type", ""),
            "cohort": model.get("cohort", ""),
        },
        "training_data": {
            "info": training_info,
            "data_hash": training_info.get("data_hash", "not_recorded"),
            "sample_size": training_info.get("sample_size", "unknown"),
            "date_range": training_info.get("date_range", "unknown"),
        },
        "performance": {
            "metrics": metrics,
            "validation_type": metrics.get("validation_type", "in_sample"),
        },
        "governance": {
            "created_by": model.get("created_by", ""),
            "created_at": str(model.get("created_at", "")),
            "approved_by": model.get("approved_by"),
            "approved_at": str(model.get("approved_at", "")) if model.get("approved_at") else None,
            "audit_trail_count": len(audit),
        },
        "assumptions": _extract_assumptions(model),
        "limitations": _extract_limitations(model),
    }
    return card


def _extract_assumptions(model: dict) -> list[str]:
    """Extract model assumptions based on model type and algorithm."""
    assumptions = []
    mt = model.get("model_type", "")
    algo = model.get("algorithm", "")

    if mt == "PD":
        assumptions.append("Default is defined as 90+ DPD or Stage 3 classification")
        assumptions.append("PD is estimated as point-in-time, adjusted for macroeconomic scenarios")
    elif mt == "LGD":
        assumptions.append("LGD is estimated from historical recovery data")
        assumptions.append("Downturn LGD adjustment applied via scenario multipliers")
    elif mt == "EAD":
        assumptions.append("EAD assumes linear amortization with prepayment adjustment")

    if "logistic" in algo.lower():
        assumptions.append("Logistic regression assumes linear relationship in log-odds space")
    elif "random_forest" in algo.lower() or "gradient" in algo.lower():
        assumptions.append("Ensemble model may overfit on small samples; cross-validation applied")

    assumptions.append("Forward-looking adjustment via satellite model linking macro variables to risk parameters")
    return assumptions


def _extract_limitations(model: dict) -> list[str]:
    """Extract model limitations based on model type and performance."""
    limitations = []
    metrics = model.get("performance_metrics", {}) or {}

    r_squared = metrics.get("r_squared") or metrics.get("r2")
    if r_squared is not None and float(r_squared) < 0.5:
        limitations.append(f"Low explanatory power (R²={r_squared}); macro variables may have weak predictive value")

    if model.get("model_type") == "PD":
        limitations.append("PD model does not capture idiosyncratic borrower risk beyond segment-level factors")
    if model.get("model_type") == "LGD":
        limitations.append("LGD model assumes static collateral values; does not model depreciation curves")

    limitations.append("Model performance may degrade under economic conditions outside the training data range")
    return limitations


def compute_sensitivity(model_id: str, perturbation_pct: float = 10.0) -> dict:
    """Compute sensitivity analysis: ECL impact of ±perturbation% changes in key parameters.

    Returns the estimated directional impact without re-running the full Monte Carlo.
    """
    model = get_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")

    params = model.get("parameters", {}) or {}
    factor = perturbation_pct / 100.0

    sensitivities = []
    key_params = [
        "intercept",
        "unemployment_coeff",
        "gdp_coeff",
        "inflation_coeff",
        "base_pd",
        "base_lgd",
        "pd_lgd_correlation",
    ]

    for param_name in key_params:
        base_value = params.get(param_name)
        if base_value is None:
            continue
        try:
            base_val = float(base_value)
        except (TypeError, ValueError):
            continue

        sensitivities.append(
            {
                "parameter": param_name,
                "base_value": round(base_val, 6),
                "perturbed_up": round(base_val * (1 + factor), 6),
                "perturbed_down": round(base_val * (1 - factor), 6),
                "perturbation_pct": perturbation_pct,
                "estimated_ecl_impact_up_pct": round(factor * 100 * abs(base_val) / max(abs(base_val), 0.01), 2),
                "estimated_ecl_impact_down_pct": round(-factor * 100 * abs(base_val) / max(abs(base_val), 0.01), 2),
            }
        )

    return {
        "model_id": model_id,
        "model_name": model.get("model_name", ""),
        "perturbation_pct": perturbation_pct,
        "sensitivities": sensitivities,
        "note": "Estimated directional impact; full re-run recommended for precise figures",
    }


def check_recalibration_due(model_id: str, max_age_days: int = 365) -> dict:
    """Check if a model is due for recalibration based on its age and last validation."""
    model = get_model(model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")

    from datetime import datetime

    now = datetime.now(UTC)
    created_at = model.get("created_at")
    approved_at = model.get("approved_at")

    reference_date = approved_at or created_at
    if reference_date:
        if isinstance(reference_date, str):
            try:
                reference_date = datetime.fromisoformat(reference_date.replace("Z", "+00:00"))
            except Exception:
                reference_date = now
        if reference_date.tzinfo is None:
            reference_date = reference_date.replace(tzinfo=UTC)
        age_days = (now - reference_date).days
    else:
        age_days = 0

    is_due = age_days > max_age_days
    return {
        "model_id": model_id,
        "model_name": model.get("model_name", ""),
        "status": model.get("status", ""),
        "age_days": age_days,
        "max_age_days": max_age_days,
        "recalibration_due": is_due,
        "last_validated": str(approved_at) if approved_at else None,
        "recommendation": "Recalibration required" if is_due else "Within policy period",
    }


def _parse_model_rows(df) -> list[dict]:
    """Parse JSONB columns in model registry DataFrame rows."""
    import pandas as _pd

    results = []
    for _, row in df.iterrows():
        d = row.to_dict()
        for k, v in list(d.items()):
            if _pd.isna(v) if not isinstance(v, (dict, list)) else False:
                d[k] = None
        for col in ("parameters", "performance_metrics", "training_data_info"):
            v = d.get(col)
            if isinstance(v, str):
                try:
                    d[col] = _json.loads(v)
                except Exception:
                    pass
            elif v is None:
                d[col] = {}
        results.append(d)
    return results
