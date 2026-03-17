"""
Lakebase-powered backend for IFRS 9 ECL Application.
Uses auto-injected PGHOST/PGDATABASE/PGUSER/PGPASSWORD from Databricks App resource.
Falls back to SDK-based OAuth for local development.

Token refresh: OAuth tokens last ~1 hour. A background thread proactively
refreshes the connection pool every 45 minutes so queries never hit an
expired token.
"""
import os
import time
import uuid
import logging
import threading
import pandas as pd
import psycopg2
import psycopg2.pool

log = logging.getLogger(__name__)

SCHEMA = "expected_credit_loss"
PREFIX = "lb_"

TOKEN_REFRESH_INTERVAL = 45 * 60  # 45 minutes (tokens last ~60 min)

_pool = None
_pool_lock = threading.Lock()
_refresh_thread: threading.Thread | None = None
_refresh_stop = threading.Event()


def init_pool():
    global _pool, _refresh_thread
    with _pool_lock:
        if _pool is not None:
            return

        pg_host = os.environ.get("PGHOST", "")
        pg_db = os.environ.get("PGDATABASE", "databricks_postgres")
        pg_user = os.environ.get("PGUSER", "")
        pg_pass = os.environ.get("PGPASSWORD", "")
        pg_port = os.environ.get("PGPORT", "5432")

        if pg_host and pg_user and pg_pass:
            log.info("Connecting to Lakebase via auto-injected env vars: host=%s db=%s user=%s", pg_host, pg_db, pg_user)
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2, maxconn=10,
                host=pg_host, port=pg_port, database=pg_db,
                user=pg_user, password=pg_pass, sslmode="require",
            )
        elif pg_host and pg_user:
            log.info("PGPASSWORD not set, generating OAuth token via SDK for user=%s host=%s", pg_user, pg_host)
            inst_name = os.environ.get("LAKEBASE_INSTANCE_NAME", "horizon-ecl-db")
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            cred = w.database.generate_database_credential(
                request_id=str(uuid.uuid4()),
                instance_names=[inst_name],
            )
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2, maxconn=10,
                host=pg_host, port=pg_port, database=pg_db,
                user=pg_user, password=cred.token, sslmode="require",
            )
        else:
            log.info("PGHOST not set, falling back to CLI-based connection")
            _init_pool_via_sdk()

        conn = _pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                ver = cur.fetchone()
                log.info("Lakebase connected: %s", ver[0] if ver else "unknown")
        finally:
            _pool.putconn(conn)

        ensure_workflow_table()

        if _refresh_thread is None or not _refresh_thread.is_alive():
            _refresh_stop.clear()
            _refresh_thread = threading.Thread(target=_token_refresh_loop, daemon=True)
            _refresh_thread.start()
            log.info("Started background token refresh thread (every %ds)", TOKEN_REFRESH_INTERVAL)


def _init_pool_via_sdk():
    global _pool
    import subprocess, json
    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "lakemeter")
    inst_name = os.environ.get("LAKEBASE_INSTANCE_NAME", "horizon-ecl-db")

    def cli_json(args):
        r = subprocess.run(["databricks"] + args + ["-p", profile, "-o", "json"], capture_output=True, text=True)
        return json.loads(r.stdout)

    inst = cli_json(["database", "get-database-instance", inst_name])
    host = inst["read_write_dns"]
    cred = cli_json(["database", "generate-database-credential", "--json",
                      json.dumps({"request_id": str(uuid.uuid4()), "instance_names": [inst_name]})])
    me = cli_json(["current-user", "me"])

    _pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=2, maxconn=10,
        host=host, port=5432, database="databricks_postgres",
        user=me["userName"], password=cred["token"], sslmode="require",
    )


def _is_auth_error(exc):
    msg = str(exc).lower()
    return any(pattern in msg for pattern in (
        "invalid authorization",
        "password authentication failed",
        "authentication failed",
        "token expired",
        "token is expired",
        "ssl connection has been closed",
        "connection reset",
        "server closed the connection unexpectedly",
    )) or ("fatal" in msg and "login" in msg)


def _token_refresh_loop():
    """Background thread that proactively refreshes the connection pool before the OAuth token expires."""
    while not _refresh_stop.wait(TOKEN_REFRESH_INTERVAL):
        log.info("Proactive token refresh: reinitializing Lakebase pool")
        try:
            _force_reinit()
        except Exception:
            log.exception("Proactive token refresh failed — will retry next cycle")


def _force_reinit():
    """Destroy current pool and create a new one with fresh credentials."""
    global _pool
    with _pool_lock:
        try:
            if _pool is not None:
                _pool.closeall()
        except Exception:
            pass
        _pool = None
    init_pool()


def _reinit_pool():
    """Force pool re-creation with fresh credentials (called on query failure)."""
    log.warning("Reinitializing Lakebase connection pool due to connection error")
    _force_reinit()


def query_df(sql: str, params: tuple | None = None, _retry: bool = True) -> pd.DataFrame:
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    returned = False
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d.name for d in cur.description]
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=cols)
    except psycopg2.OperationalError as e:
        conn.rollback()
        _pool.putconn(conn, close=True)
        returned = True
        if _retry:
            log.warning("query_df OperationalError (retrying): %s — %s", sql[:120], e)
            _reinit_pool()
            return query_df(sql, params, _retry=False)
        log.exception("query_df failed after retry: %s", sql[:200])
        raise
    except Exception:
        log.exception("query_df failed: %s", sql[:200])
        conn.rollback()
        raise
    finally:
        if not returned:
            try:
                _pool.putconn(conn)
            except Exception:
                pass


def execute(sql: str, params: tuple | None = None, _retry: bool = True):
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    returned = False
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    except psycopg2.OperationalError as e:
        conn.rollback()
        _pool.putconn(conn, close=True)
        returned = True
        if _retry:
            log.warning("execute OperationalError (retrying): %s — %s", sql[:120], e)
            _reinit_pool()
            return execute(sql, params, _retry=False)
        log.exception("execute failed after retry: %s", sql[:200])
        raise
    except Exception:
        log.exception("execute failed: %s", sql[:200])
        conn.rollback()
        raise
    finally:
        if not returned:
            try:
                _pool.putconn(conn)
            except Exception:
                pass


def _t(name: str) -> str:
    return f"{SCHEMA}.{PREFIX}{name}"


# ─── Workflow State Management ───────────────────────────────────────────────

import json as _json
from datetime import datetime as _dt, timezone as _tz

STEPS = [
    "create_project",
    "data_processing",
    "data_control",
    "model_execution",
    "model_control",
    "stress_testing",
    "overlays",
    "sign_off",
]

WF_TABLE = f"{SCHEMA}.ecl_workflow"


def ensure_workflow_table():
    """Create the ecl_workflow table if it doesn't already exist."""
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
    return get_project(project_id)


def save_overlays(project_id: str, overlays: list) -> dict:
    execute(f"UPDATE {WF_TABLE} SET overlays=%s, updated_at=NOW() WHERE project_id=%s",
            (_json.dumps(overlays), project_id))
    return get_project(project_id)


def save_scenario_weights(project_id: str, weights: dict) -> dict:
    execute(f"UPDATE {WF_TABLE} SET scenario_weights=%s, updated_at=NOW() WHERE project_id=%s",
            (_json.dumps(weights), project_id))
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


def sign_off_project(project_id: str, user: str) -> dict:
    proj = get_project(project_id)
    if not proj:
        raise ValueError("Project not found")
    ss = proj["step_status"]
    ss["sign_off"] = "completed"
    audit = proj["audit_log"]
    audit.append({"ts": _dt.now(_tz.utc).isoformat(), "user": user, "action": "Final Sign-Off", "detail": "Project signed off and locked", "step": "sign_off"})
    execute(f"""
        UPDATE {WF_TABLE} SET current_step={len(STEPS)}, step_status=%s, audit_log=%s,
               signed_off_by=%s, signed_off_at=NOW(), updated_at=NOW()
        WHERE project_id=%s
    """, (_json.dumps(ss), _json.dumps(audit), user, project_id))
    return get_project(project_id)


# ─── Portfolio & Loan Queries ────────────────────────────────────────────────

def get_portfolio_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND((AVG(effective_interest_rate) * 100)::numeric, 2) as avg_eir_pct,
               ROUND(AVG(days_past_due)::numeric, 1) as avg_dpd,
               SUM(CASE WHEN assessed_stage = 1 THEN 1 ELSE 0 END) as stage_1_count,
               SUM(CASE WHEN assessed_stage = 2 THEN 1 ELSE 0 END) as stage_2_count,
               SUM(CASE WHEN assessed_stage = 3 THEN 1 ELSE 0 END) as stage_3_count
        FROM {_t('model_ready_loans')}
        GROUP BY product_type
        ORDER BY total_gca DESC
    """)


def get_stage_distribution() -> pd.DataFrame:
    return query_df(f"""
        SELECT assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca
        FROM {_t('model_ready_loans')}
        GROUP BY assessed_stage
        ORDER BY assessed_stage
    """)


def get_borrower_segment_stats() -> pd.DataFrame:
    return query_df(f"""
        SELECT segment,
               COUNT(DISTINCT borrower_id) as borrower_count,
               ROUND(AVG(alt_data_composite_score)::numeric, 1) as avg_alt_score,
               ROUND(AVG(monthly_income)::numeric, 2) as avg_monthly_income,
               ROUND(AVG(age)::numeric, 1) as avg_age
        FROM {_t('borrower_master')}
        GROUP BY segment
    """)


def get_vintage_analysis() -> pd.DataFrame:
    return query_df(f"""
        SELECT vintage_cohort,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               SUM(CASE WHEN assessed_stage >= 2 THEN 1 ELSE 0 END) as stage_2_3_count
        FROM {_t('model_ready_loans')}
        GROUP BY vintage_cohort
        ORDER BY vintage_cohort
    """)


def get_dpd_distribution() -> pd.DataFrame:
    return query_df(f"""
        SELECT dpd_bucket, loan_count, total_gca FROM (
            SELECT
                CASE
                    WHEN days_past_due = 0 THEN 'Current'
                    WHEN days_past_due BETWEEN 1 AND 30 THEN '1-30 DPD'
                    WHEN days_past_due BETWEEN 31 AND 60 THEN '31-60 DPD'
                    WHEN days_past_due BETWEEN 61 AND 90 THEN '61-90 DPD'
                    ELSE '90+ DPD'
                END as dpd_bucket,
                CASE
                    WHEN days_past_due = 0 THEN 1
                    WHEN days_past_due BETWEEN 1 AND 30 THEN 2
                    WHEN days_past_due BETWEEN 31 AND 60 THEN 3
                    WHEN days_past_due BETWEEN 61 AND 90 THEN 4
                    ELSE 5
                END as sort_order,
                COUNT(*) as loan_count,
                ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca
            FROM {_t('model_ready_loans')}
            GROUP BY 1, 2
        ) sub
        ORDER BY sort_order
    """)


def get_stage_by_product() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca
        FROM {_t('model_ready_loans')}
        GROUP BY product_type, assessed_stage
        ORDER BY product_type, assessed_stage
    """)


def get_pd_distribution() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               ROUND((MIN(current_lifetime_pd) * 100)::numeric, 2) as min_pd_pct,
               ROUND((MAX(current_lifetime_pd) * 100)::numeric, 2) as max_pd_pct,
               ROUND((PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY current_lifetime_pd) * 100)::numeric, 2) as p25_pd_pct,
               ROUND((PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY current_lifetime_pd) * 100)::numeric, 2) as p75_pd_pct
        FROM {_t('model_ready_loans')}
        GROUP BY product_type
        ORDER BY avg_pd_pct DESC
    """)


# ─── DQ & GL Queries ────────────────────────────────────────────────────────

def get_dq_results() -> pd.DataFrame:
    return query_df(f"""
        SELECT check_id, category, description, severity,
               failures, total_records, failure_pct, passed
        FROM {_t('dq_results')}
        ORDER BY passed ASC, severity DESC
    """)


def get_dq_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT category,
               COUNT(*) as total_checks,
               SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed_count,
               SUM(CASE WHEN NOT passed THEN 1 ELSE 0 END) as failed_count
        FROM {_t('dq_results')}
        GROUP BY category
        ORDER BY failed_count DESC
    """)


def get_gl_reconciliation() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, gl_balance, loan_tape_balance,
               variance, variance_pct, status
        FROM {_t('gl_reconciliation')}
    """)


# ─── ECL Queries ─────────────────────────────────────────────────────────────

def get_ecl_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, assessed_stage,
               loan_count, total_gca, total_ecl, coverage_ratio
        FROM {_t('portfolio_ecl_summary')}
        ORDER BY product_type, assessed_stage
    """)


def get_ecl_by_product() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type,
               SUM(loan_count) as loan_count,
               ROUND(SUM(total_gca)::numeric, 2) as total_gca,
               ROUND(SUM(total_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(total_ecl) / NULLIF(SUM(total_gca), 0) * 100)::numeric, 2) as coverage_ratio
        FROM {_t('portfolio_ecl_summary')}
        GROUP BY product_type
        ORDER BY total_ecl DESC
    """)


def get_scenario_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT scenario, weight, total_ecl,
               COALESCE(total_ecl_p95, total_ecl) as total_ecl_p95,
               COALESCE(total_ecl_p99, total_ecl) as total_ecl_p99,
               weighted_contribution as weighted
        FROM {_t('scenario_ecl_summary')}
        ORDER BY weight DESC
    """)


def get_mc_distribution() -> pd.DataFrame:
    return query_df(f"""
        SELECT scenario, weight, ecl_mean, ecl_p50, ecl_p75, ecl_p95, ecl_p99,
               avg_pd_multiplier, avg_lgd_multiplier, pd_vol, lgd_vol, n_simulations
        FROM {_t('mc_ecl_distribution')}
        ORDER BY weight DESC
    """)


def get_ecl_by_scenario_product() -> pd.DataFrame:
    return query_df(f"""
        SELECT scenario, product_type,
               ROUND(SUM(ecl_amount)::numeric, 2) as total_ecl,
               COUNT(*) as loan_count
        FROM {_t('loan_level_ecl')}
        GROUP BY scenario, product_type
        ORDER BY scenario, product_type
    """)


def get_ecl_concentration() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(weighted_ecl)::numeric, 2) as total_ecl,
               ROUND(AVG(weighted_ecl)::numeric, 2) as avg_ecl,
               ROUND(MAX(weighted_ecl)::numeric, 2) as max_ecl
        FROM {_t('loan_ecl_weighted')}
        GROUP BY product_type, assessed_stage
        ORDER BY total_ecl DESC
    """)


# ─── IFRS 7 Disclosure Queries ──────────────────────────────────────────────

def get_stage_migration() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, original_stage, assessed_stage,
               loan_count, ROUND(total_gca::numeric, 2) as total_gca
        FROM {_t('ifrs7_stage_migration')}
        ORDER BY product_type, original_stage, assessed_stage
    """)


def get_credit_risk_exposure() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, assessed_stage, credit_risk_grade,
               loan_count, ROUND(total_gca::numeric, 2) as total_gca
        FROM {_t('ifrs7_credit_risk_exposure')}
        ORDER BY product_type, assessed_stage, credit_risk_grade
    """)


def get_loss_allowance_by_stage() -> pd.DataFrame:
    return query_df(f"""
        SELECT assessed_stage,
               SUM(loan_count) as loan_count,
               ROUND(SUM(total_gca)::numeric, 2) as total_gca,
               ROUND(SUM(total_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(total_ecl) / NULLIF(SUM(total_gca), 0) * 100)::numeric, 2) as coverage_pct
        FROM {_t('portfolio_ecl_summary')}
        GROUP BY assessed_stage
        ORDER BY assessed_stage
    """)


# ─── Top Exposures ───────────────────────────────────────────────────────────

def get_top_exposures(limit: int = 20) -> pd.DataFrame:
    return query_df(f"""
        SELECT l.loan_id, l.product_type, l.assessed_stage,
               ROUND(l.gross_carrying_amount::numeric, 2) as gca,
               ROUND(e.weighted_ecl::numeric, 2) as ecl,
               ROUND((e.weighted_ecl / NULLIF(l.gross_carrying_amount, 0) * 100)::numeric, 2) as coverage_pct,
               l.days_past_due, l.segment,
               ROUND((l.current_lifetime_pd * 100)::numeric, 2) as pd_pct
        FROM {_t('model_ready_loans')} l
        JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
        ORDER BY e.weighted_ecl DESC
        LIMIT %s
    """, (limit,))


def get_loans_by_product(product_type: str) -> pd.DataFrame:
    return query_df(f"""
        SELECT l.loan_id, l.assessed_stage,
               ROUND(l.gross_carrying_amount::numeric, 2) as gca,
               l.days_past_due,
               ROUND((l.current_lifetime_pd * 100)::numeric, 2) as pd_pct,
               ROUND(e.weighted_ecl::numeric, 2) as ecl,
               l.segment
        FROM {_t('model_ready_loans')} l
        JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
        WHERE l.product_type = %s
        ORDER BY e.weighted_ecl DESC
        LIMIT 50
    """, (product_type,))


def get_loans_by_stage(stage: int) -> pd.DataFrame:
    return query_df(f"""
        SELECT l.loan_id, l.product_type, l.assessed_stage,
               ROUND(l.gross_carrying_amount::numeric, 2) as gca,
               l.days_past_due,
               ROUND((l.current_lifetime_pd * 100)::numeric, 2) as pd_pct,
               ROUND(e.weighted_ecl::numeric, 2) as ecl,
               l.segment
        FROM {_t('model_ready_loans')} l
        JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
        WHERE l.assessed_stage = %s
        ORDER BY e.weighted_ecl DESC
        LIMIT 50
    """, (stage,))


def get_scenario_ecl_by_product(scenario: str) -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(ecl_amount)::numeric, 2) as total_ecl,
               ROUND(AVG(ecl_amount)::numeric, 2) as avg_ecl
        FROM {_t('loan_level_ecl')}
        WHERE scenario = %s
        GROUP BY product_type
        ORDER BY total_ecl DESC
    """, (scenario,))


# ─── Stress Testing & Sensitivity ───────────────────────────────────────────

def get_sensitivity_data() -> pd.DataFrame:
    """Get base ECL data per product for client-side sensitivity simulation."""
    return query_df(f"""
        SELECT l.product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(AVG(l.current_lifetime_pd)::numeric, 6) as avg_pd,
               ROUND(AVG(e.weighted_ecl / NULLIF(l.gross_carrying_amount * l.current_lifetime_pd, 0))::numeric, 6) as implied_lgd,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as base_ecl
        FROM {_t('model_ready_loans')} l
        JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
        GROUP BY l.product_type
        ORDER BY base_ecl DESC
    """)


def get_scenario_comparison() -> pd.DataFrame:
    """Get ECL by scenario and product for comparison."""
    return query_df(f"""
        SELECT scenario, product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(ecl_amount)::numeric, 2) as total_ecl
        FROM {_t('loan_level_ecl')}
        GROUP BY scenario, product_type
        ORDER BY scenario, total_ecl DESC
    """)


def get_stress_by_stage() -> pd.DataFrame:
    """Get ECL and PD by stage for stress testing."""
    return query_df(f"""
        SELECT l.assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(AVG(l.current_lifetime_pd)::numeric, 6) as avg_pd,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as base_ecl
        FROM {_t('model_ready_loans')} l
        JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
        GROUP BY l.assessed_stage
        ORDER BY l.assessed_stage
    """)


# ─── Vintage Analysis ───────────────────────────────────────────────────────

def get_vintage_performance() -> pd.DataFrame:
    """Get vintage cohort performance with delinquency rates."""
    return query_df(f"""
        SELECT vintage_cohort,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               ROUND((SUM(CASE WHEN days_past_due > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as delinquency_rate,
               ROUND((SUM(CASE WHEN days_past_due > 30 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as dpd30_rate,
               ROUND((SUM(CASE WHEN days_past_due > 60 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as dpd60_rate,
               ROUND((SUM(CASE WHEN days_past_due > 90 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as dpd90_rate,
               SUM(CASE WHEN assessed_stage = 1 THEN 1 ELSE 0 END) as stage1,
               SUM(CASE WHEN assessed_stage = 2 THEN 1 ELSE 0 END) as stage2,
               SUM(CASE WHEN assessed_stage = 3 THEN 1 ELSE 0 END) as stage3
        FROM {_t('model_ready_loans')}
        GROUP BY vintage_cohort
        ORDER BY vintage_cohort
    """)


def get_vintage_by_product() -> pd.DataFrame:
    """Get vintage performance broken down by product."""
    return query_df(f"""
        SELECT vintage_cohort, product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               ROUND((SUM(CASE WHEN days_past_due > 30 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as dpd30_rate
        FROM {_t('model_ready_loans')}
        GROUP BY vintage_cohort, product_type
        ORDER BY vintage_cohort, product_type
    """)


# ─── Concentration Risk ─────────────────────────────────────────────────────

def get_concentration_by_segment() -> pd.DataFrame:
    """Get ECL concentration by borrower segment."""
    return query_df(f"""
        SELECT l.segment,
               COUNT(*) as loan_count,
               ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(e.weighted_ecl) / NULLIF(SUM(l.gross_carrying_amount), 0) * 100)::numeric, 2) as coverage_pct,
               ROUND(MAX(e.weighted_ecl)::numeric, 2) as max_single_ecl
        FROM {_t('model_ready_loans')} l
        JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
        GROUP BY l.segment
        ORDER BY total_ecl DESC
    """)


def get_concentration_by_product_stage() -> pd.DataFrame:
    """Get ECL concentration heatmap data: product x stage."""
    return query_df(f"""
        SELECT l.product_type, l.assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(e.weighted_ecl) / NULLIF(SUM(l.gross_carrying_amount), 0) * 100)::numeric, 2) as coverage_pct
        FROM {_t('model_ready_loans')} l
        JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
        GROUP BY l.product_type, l.assessed_stage
        ORDER BY l.product_type, l.assessed_stage
    """)


def get_top_concentration_risk() -> pd.DataFrame:
    """Get top single-name concentration risks."""
    return query_df(f"""
        SELECT l.loan_id, l.product_type, l.segment, l.assessed_stage,
               ROUND(l.gross_carrying_amount::numeric, 2) as gca,
               ROUND(e.weighted_ecl::numeric, 2) as ecl,
               ROUND((e.weighted_ecl / NULLIF(l.gross_carrying_amount, 0) * 100)::numeric, 2) as coverage_pct,
               l.days_past_due,
               ROUND((l.current_lifetime_pd * 100)::numeric, 2) as pd_pct
        FROM {_t('model_ready_loans')} l
        JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
        ORDER BY e.weighted_ecl DESC
        LIMIT 25
    """)
