"""
Usage analytics tracking for IFRS 9 ECL Platform.

Records API request metrics (user, endpoint, timing, status) to support
operational dashboards, audit compliance (SOX 302, BCBS 239), and
performance monitoring.
"""
import logging
from datetime import datetime, timezone

from db.pool import query_df, execute, SCHEMA

log = logging.getLogger(__name__)

USAGE_TABLE = f"{SCHEMA}.app_usage_analytics"


def ensure_usage_table():
    """Create the usage analytics table if it does not exist (idempotent)."""
    execute(f"""
        CREATE TABLE IF NOT EXISTS {USAGE_TABLE} (
            id          SERIAL PRIMARY KEY,
            timestamp   TIMESTAMP DEFAULT NOW(),
            user_id     TEXT,
            method      TEXT,
            endpoint    TEXT,
            status_code INT,
            duration_ms FLOAT,
            request_id  TEXT,
            user_agent  TEXT
        )
    """)
    execute(
        f"COMMENT ON TABLE {USAGE_TABLE} IS "
        f"'ifrs9ecl: API request usage analytics for operational dashboards'"
    )
    log.info("Ensured %s table exists", USAGE_TABLE)


def record_request(
    user_id: str,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    request_id: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Insert a single usage analytics record."""
    execute(f"""
        INSERT INTO {USAGE_TABLE}
            (user_id, method, endpoint, status_code, duration_ms,
             request_id, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, method, endpoint, status_code, duration_ms,
          request_id, user_agent))


def get_usage_stats(days: int = 7) -> dict:
    """Return summary metrics for the last N days.

    Returns dict with: total_requests, unique_users, avg_duration_ms,
    error_count (status >= 400), requests_today.
    """
    df = query_df(f"""
        SELECT
            COUNT(*)::INT                          AS total_requests,
            COUNT(DISTINCT user_id)::INT           AS unique_users,
            COALESCE(ROUND(AVG(duration_ms)::NUMERIC, 2), 0) AS avg_duration_ms,
            COUNT(*) FILTER (WHERE status_code >= 400)::INT AS error_count,
            COUNT(*) FILTER (WHERE timestamp >= CURRENT_DATE)::INT AS requests_today
        FROM {USAGE_TABLE}
        WHERE timestamp >= NOW() - INTERVAL '%s days'
    """, (days,))
    if df.empty:
        return {
            "total_requests": 0,
            "unique_users": 0,
            "avg_duration_ms": 0,
            "error_count": 0,
            "requests_today": 0,
        }
    row = df.iloc[0].to_dict()
    return {k: (float(v) if v is not None else 0) for k, v in row.items()}


def get_recent_requests(limit: int = 50) -> list[dict]:
    """Return the most recent usage records."""
    df = query_df(f"""
        SELECT id, timestamp, user_id, method, endpoint,
               status_code, duration_ms, request_id, user_agent
        FROM {USAGE_TABLE}
        ORDER BY timestamp DESC
        LIMIT %s
    """, (limit,))
    if df.empty:
        return []
    records = df.to_dict("records")
    for r in records:
        if hasattr(r.get("timestamp"), "isoformat"):
            r["timestamp"] = r["timestamp"].isoformat()
    return records
