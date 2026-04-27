"""
Configuration audit logging for IFRS 9 ECL Platform.

Tracks changes to admin configuration with old/new value capture
for IAS 8 change-in-estimate disclosure compliance.
"""

import json
import logging

from db.pool import SCHEMA, execute, query_df

log = logging.getLogger(__name__)

CONFIG_AUDIT_TABLE = f"{SCHEMA}.config_audit_log"


def log_config_change(section: str, key: str | None, old_value, new_value, changed_by: str = "admin"):
    execute(
        f"""
        INSERT INTO {CONFIG_AUDIT_TABLE} (section, config_key, old_value, new_value, changed_by)
        VALUES (%s, %s, %s, %s, %s)
    """,
        (section, key, json.dumps(old_value, default=str), json.dumps(new_value, default=str), changed_by),
    )


def get_config_audit_log(section: str | None = None, limit: int = 100) -> list[dict]:
    if section:
        df = query_df(
            f"""
            SELECT * FROM {CONFIG_AUDIT_TABLE}
            WHERE section = %s ORDER BY id DESC LIMIT %s
        """,
            (section, limit),
        )
    else:
        df = query_df(
            f"""
            SELECT * FROM {CONFIG_AUDIT_TABLE}
            ORDER BY id DESC LIMIT %s
        """,
            (limit,),
        )
    if df.empty:
        return []
    records = []
    for _, row in df.iterrows():
        r = row.to_dict()
        for col in ("old_value", "new_value"):
            if isinstance(r.get(col), str):
                r[col] = json.loads(r[col])
        # Convert Timestamp/datetime objects to ISO strings for JSON serialization
        for ts_col in ("changed_at",):
            if ts_col in r and hasattr(r[ts_col], "isoformat"):
                r[ts_col] = r[ts_col].isoformat()
        records.append(r)
    return records


def get_config_diff(start_time: str, end_time: str | None = None, section: str | None = None) -> list[dict]:
    """Get config changes between two timestamps.

    Returns a list of changes with section, key, old_value, new_value, changed_by,
    changed_at for the given time range. Used by risk managers to see what changed
    between two reporting dates.
    """
    params: list = [start_time]
    where = "WHERE changed_at >= %s::timestamp"
    if end_time:
        where += " AND changed_at <= %s::timestamp"
        params.append(end_time)
    if section:
        where += " AND section = %s"
        params.append(section)
    df = query_df(
        f"""
        SELECT section, config_key, old_value, new_value, changed_by, changed_at
        FROM {CONFIG_AUDIT_TABLE}
        {where}
        ORDER BY changed_at ASC
    """,
        tuple(params),
    )
    if df.empty:
        return []
    records = []
    for _, row in df.iterrows():
        r = row.to_dict()
        for col in ("old_value", "new_value"):
            if isinstance(r.get(col), str):
                try:
                    r[col] = json.loads(r[col])
                except (json.JSONDecodeError, TypeError):
                    pass
        # Convert Timestamp/datetime objects to ISO strings for JSON serialization
        for ts_col in ("changed_at",):
            if ts_col in r and hasattr(r[ts_col], "isoformat"):
                r[ts_col] = r[ts_col].isoformat()
        records.append(r)
    return records
