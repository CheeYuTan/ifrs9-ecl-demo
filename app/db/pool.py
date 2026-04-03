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
_config_loaded = False


def load_schema_from_config():
    """Load schema/prefix from admin_config. Called once after pool init."""
    global SCHEMA, PREFIX, _config_loaded
    if _config_loaded:
        return
    try:
        import admin_config
        cfg = admin_config.get_config()
        ds = cfg.get("data_sources", {})
        SCHEMA = ds.get("lakebase_schema", SCHEMA)
        PREFIX = ds.get("lakebase_prefix", PREFIX)
        _config_loaded = True
        log.info("Loaded schema=%s prefix=%s from admin_config", SCHEMA, PREFIX)
    except Exception:
        log.debug("Could not load schema from admin_config, using defaults")

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
            log.info("PGPASSWORD not set, generating OAuth token for user=%s host=%s", pg_user, pg_host)
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            token = w.config.authenticate()
            if isinstance(token, dict):
                oauth_token = token.get("Authorization", "").replace("Bearer ", "")
            else:
                oauth_token = getattr(token, 'token', str(token))
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2, maxconn=10,
                host=pg_host, port=pg_port, database=pg_db,
                user=pg_user, password=oauth_token, sslmode="require",
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

        from domain.workflow import ensure_workflow_table
        ensure_workflow_table()
        load_schema_from_config()

        if _refresh_thread is None or not _refresh_thread.is_alive():
            _refresh_stop.clear()
            _refresh_thread = threading.Thread(target=_token_refresh_loop, daemon=True)
            _refresh_thread.start()
            log.info("Started background token refresh thread (every %ds)", TOKEN_REFRESH_INTERVAL)


def _init_pool_via_sdk():
    global _pool
    from databricks.sdk import WorkspaceClient
    inst_name = os.environ.get("LAKEBASE_INSTANCE_NAME", "ifrs9-ecl-demo-db")

    is_app = bool(os.environ.get("DATABRICKS_APP_NAME"))
    if is_app:
        w = WorkspaceClient()
    else:
        profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "lakemeter")
        w = WorkspaceClient(profile=profile)

    inst = w.database.get_database_instance(inst_name)
    host = inst.read_write_dns
    cred = w.database.generate_database_credential(
        request_id=str(uuid.uuid4()),
        instance_names=[inst_name],
    )
    me = w.current_user.me()

    _pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=2, maxconn=10,
        host=host, port=5432, database="databricks_postgres",
        user=me.user_name, password=cred.token, sslmode="require",
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
    try:
        while not _refresh_stop.wait(TOKEN_REFRESH_INTERVAL):
            log.info("Proactive token refresh: reinitializing Lakebase pool")
            try:
                _force_reinit()
                log.info("Proactive token refresh succeeded")
            except Exception:
                log.exception("Proactive token refresh failed — will retry next cycle")
    except Exception:
        log.exception("Token refresh loop crashed unexpectedly")


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
    try:
        conn = _pool.getconn()
    except psycopg2.OperationalError as e:
        if _retry:
            log.warning("query_df getconn OperationalError (retrying): %s — %s", sql[:120], e)
            _reinit_pool()
            return query_df(sql, params, _retry=False)
        raise
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
    try:
        conn = _pool.getconn()
    except psycopg2.OperationalError as e:
        if _retry:
            log.warning("execute getconn OperationalError (retrying): %s — %s", sql[:120], e)
            _reinit_pool()
            return execute(sql, params, _retry=False)
        raise
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
