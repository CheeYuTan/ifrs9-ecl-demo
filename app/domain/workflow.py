import json as _json
import logging
import pandas as pd
from datetime import datetime as _dt, timezone as _tz

from db.pool import query_df, execute, SCHEMA, PREFIX, _t

log = logging.getLogger(__name__)


def _audit_event(project_id, entity_type, action, user, detail=None):
    """Append to immutable audit trail (best-effort — does not block caller)."""
    try:
        from domain.audit_trail import append_audit_entry
        append_audit_entry(project_id, "workflow", entity_type, project_id, action, user, detail)
    except Exception as exc:
        log.warning("Audit trail write failed: %s", exc)

STEPS = [
    "create_project",
    "data_processing",
    "data_control",
    "satellite_model",
    "model_execution",
    "stress_testing",
    "overlays",
    "sign_off",
]

WF_TABLE = f"{SCHEMA}.ecl_workflow"


def ensure_workflow_table():
    execute(f"""
        CREATE TABLE IF NOT EXISTS {WF_TABLE} (
            project_id      TEXT PRIMARY KEY,
            project_name    TEXT,
            project_type    TEXT,
            description     TEXT,
            reporting_date  TEXT,
            current_step    INT DEFAULT 0,
            step_status     TEXT,
            audit_log       TEXT,
            overlays        TEXT,
            scenario_weights TEXT,
            signed_off_by   TEXT,
            signed_off_at   TIMESTAMP,
            created_at      TIMESTAMP DEFAULT NOW(),
            updated_at      TIMESTAMP DEFAULT NOW()
        )
    """)
    log.info("Ensured %s table exists", WF_TABLE)
    try:
        from domain.audit_trail import ensure_audit_tables
        ensure_audit_tables()
    except Exception as exc:
        log.warning("Could not create audit tables: %s", exc)
    for fn_name in ("ensure_attribution_table", "ensure_model_registry_table",
                     "ensure_backtesting_table", "ensure_gl_tables",
                     "ensure_markov_tables", "ensure_hazard_tables",
                     "ensure_rbac_tables"):
        try:
            fn = globals().get(fn_name)
            if fn:
                fn()
        except Exception:
            log.debug("Could not run %s, skipping", fn_name)


def get_project(project_id: str) -> dict | None:
    df = query_df(f"SELECT * FROM {WF_TABLE} WHERE project_id = %s", (project_id,))
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    for col in ("step_status", "overlays", "scenario_weights", "audit_log"):
        v = row.get(col)
        if isinstance(v, str):
            row[col] = _json.loads(v)
    return row


def list_projects() -> pd.DataFrame:
    return query_df(f"SELECT project_id, project_name, project_type, current_step, created_at, signed_off_by FROM {WF_TABLE} ORDER BY created_at DESC")


def create_project(project_id: str, name: str, ptype: str, desc: str, rdate: str) -> dict:
    step_status = {s: "pending" for s in STEPS}
    step_status["create_project"] = "completed"
    audit = [{"ts": _dt.now(_tz.utc).isoformat(), "user": "Current User", "action": "Project Created", "detail": f"{name} initialized", "step": "create_project"}]
    execute(f"""
        INSERT INTO {WF_TABLE} (project_id, project_name, project_type, description, reporting_date, current_step, step_status, audit_log)
        VALUES (%s, %s, %s, %s, %s, 1, %s, %s)
        ON CONFLICT (project_id) DO UPDATE SET
            project_name=EXCLUDED.project_name, project_type=EXCLUDED.project_type,
            description=EXCLUDED.description, reporting_date=EXCLUDED.reporting_date,
            current_step=EXCLUDED.current_step, step_status=EXCLUDED.step_status,
            audit_log=EXCLUDED.audit_log, updated_at=NOW()
    """, (project_id, name, ptype, desc, rdate, _json.dumps(step_status), _json.dumps(audit)))
    _audit_event(project_id, "workflow", "project_created", "Current User",
                 {"name": name, "type": ptype, "reporting_date": rdate})
    return get_project(project_id)


def advance_step(project_id: str, step_name: str, action: str, user: str, detail: str, status: str = "completed") -> dict:
    proj = get_project(project_id)
    if not proj:
        raise ValueError(f"Project {project_id} not found")
    ss = proj["step_status"]
    ss[step_name] = status
    step_idx = STEPS.index(step_name) if step_name in STEPS else proj["current_step"]
    new_step = max(proj["current_step"], step_idx + 1) if status == "completed" else proj["current_step"]
    audit = proj["audit_log"]
    audit.append({"ts": _dt.now(_tz.utc).isoformat(), "user": user, "action": action, "detail": detail, "step": step_name})
    execute(f"""
        UPDATE {WF_TABLE} SET current_step=%s, step_status=%s, audit_log=%s, updated_at=NOW()
        WHERE project_id=%s
    """, (new_step, _json.dumps(ss), _json.dumps(audit), project_id))
    _audit_event(project_id, "workflow_step", action, user,
                 {"step": step_name, "status": status, "detail": detail})
    return get_project(project_id)


def save_overlays(project_id: str, overlays: list, user: str = "analyst") -> dict:
    execute(f"UPDATE {WF_TABLE} SET overlays=%s, updated_at=NOW() WHERE project_id=%s",
            (_json.dumps(overlays), project_id))
    _audit_event(project_id, "overlays", "overlays_updated", user,
                 {"overlay_count": len(overlays)})
    return get_project(project_id)


def save_scenario_weights(project_id: str, weights: dict, user: str = "analyst") -> dict:
    execute(f"UPDATE {WF_TABLE} SET scenario_weights=%s, updated_at=NOW() WHERE project_id=%s",
            (_json.dumps(weights), project_id))
    _audit_event(project_id, "scenario_weights", "weights_updated", user,
                 {"weights": weights})
    return get_project(project_id)


def reset_project(project_id: str) -> dict:
    proj = get_project(project_id)
    if not proj:
        raise ValueError("Project not found")
    if proj.get("signed_off_by"):
        raise ValueError("Cannot reset a signed-off project")
    step_status = {s: "pending" for s in STEPS}
    step_status["create_project"] = "completed"
    audit = proj["audit_log"]
    audit.append({"ts": _dt.now(_tz.utc).isoformat(), "user": "System", "action": "Project Reset", "detail": "All steps reset to pending", "step": "create_project"})
    execute(f"""
        UPDATE {WF_TABLE} SET current_step=1, step_status=%s, audit_log=%s,
               overlays='[]'::jsonb, scenario_weights='{{}}'::jsonb, signed_off_by=NULL, signed_off_at=NULL, updated_at=NOW()
        WHERE project_id=%s
    """, (_json.dumps(step_status), _json.dumps(audit), project_id))
    return get_project(project_id)


def sign_off_project(project_id: str, user: str,
                     attestation_data: dict | None = None) -> dict:
    proj = get_project(project_id)
    if not proj:
        raise ValueError("Project not found")
    ss = proj["step_status"]
    ss["sign_off"] = "completed"
    audit = proj["audit_log"]
    audit.append({"ts": _dt.now(_tz.utc).isoformat(), "user": user,
                  "action": "ECL Measurement Sign-Off",
                  "detail": "Project signed off and locked", "step": "sign_off"})

    ecl_hash = None
    try:
        from middleware.auth import compute_ecl_hash
        ecl_hash = compute_ecl_hash({
            "project_id": project_id,
            "step_status": ss,
            "overlays": proj.get("overlays"),
            "scenario_weights": proj.get("scenario_weights"),
        })
    except Exception as exc:
        log.warning("Could not compute ECL hash at sign-off: %s", exc)

    for col, ctype in [("attestation_data", "JSONB"), ("ecl_hash", "TEXT")]:
        try:
            execute(f"ALTER TABLE {WF_TABLE} ADD COLUMN IF NOT EXISTS {col} {ctype}")
        except Exception:
            pass

    execute(f"""
        UPDATE {WF_TABLE} SET current_step={len(STEPS)}, step_status=%s, audit_log=%s,
               signed_off_by=%s, signed_off_at=NOW(),
               attestation_data=%s, ecl_hash=%s, updated_at=NOW()
        WHERE project_id=%s
    """, (_json.dumps(ss), _json.dumps(audit), user,
          _json.dumps(attestation_data) if attestation_data else None,
          ecl_hash, project_id))

    _audit_event(project_id, "sign_off", "ecl_measurement_sign_off", user, {
        "attestation_provided": attestation_data is not None,
        "ecl_hash": ecl_hash,
    })
    return get_project(project_id)
