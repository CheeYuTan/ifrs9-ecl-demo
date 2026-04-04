"""
Admin Configuration module for IFRS 9 ECL Application.
Stores and retrieves application config from Lakebase (PostgreSQL).
Enables plug-and-play deployment by configuring data mappings,
job parameters, and system settings through the API.

Sub-modules:
  admin_config_defaults  -- constant dicts (DATA_SOURCE_CONFIG, MODEL_CONFIG, …)
  admin_config_schema    -- schema discovery & column-mapping validation functions
  admin_config_setup     -- setup wizard functions
"""
import json
import logging
from datetime import datetime, timezone
from copy import deepcopy

import backend

# Re-export everything from sub-modules so callers can still do:
#   from admin_config import DATA_SOURCE_CONFIG, validate_column_mapping, ...
from admin_config_defaults import *          # noqa: F401, F403
from admin_config_defaults import DEFAULT_CONFIG  # explicit import needed for this module
from admin_config_schema import *            # noqa: F401, F403
from admin_config_setup import *             # noqa: F401, F403

log = logging.getLogger(__name__)

CONFIG_TABLE = f"{backend.SCHEMA}.app_config"
_initialized = False


# ── Table Management ----------------------------------------------------------

def ensure_config_table():
    backend.execute(f"""
        CREATE TABLE IF NOT EXISTS {CONFIG_TABLE} (
            config_key   TEXT PRIMARY KEY,
            config_value TEXT NOT NULL,
            updated_at   TIMESTAMP DEFAULT NOW(),
            updated_by   TEXT DEFAULT 'system'
        )
    """)
    backend.execute(f"COMMENT ON TABLE {CONFIG_TABLE} IS 'ifrs9ecl: Application configuration settings'")
    log.info("Ensured %s table exists", CONFIG_TABLE)


def _seed_defaults_if_empty():
    df = backend.query_df(f"SELECT COUNT(*) as cnt FROM {CONFIG_TABLE}")
    if df.iloc[0]["cnt"] == 0:
        log.info("Seeding default admin config")
        for section, value in DEFAULT_CONFIG.items():
            backend.execute(
                f"INSERT INTO {CONFIG_TABLE} (config_key, config_value) VALUES (%s, %s)",
                (section, json.dumps(value)),
            )


def init():
    global _initialized
    if _initialized:
        return
    ensure_config_table()
    _seed_defaults_if_empty()
    _initialized = True


# ── CRUD Functions ------------------------------------------------------------

def get_config() -> dict:
    init()
    df = backend.query_df(f"SELECT config_key, config_value FROM {CONFIG_TABLE}")
    result = {}
    for _, row in df.iterrows():
        try:
            result[row["config_key"]] = json.loads(row["config_value"])
        except (json.JSONDecodeError, TypeError):
            result[row["config_key"]] = row["config_value"]
    for section, default_val in DEFAULT_CONFIG.items():
        if section not in result:
            result[section] = deepcopy(default_val)
    return result


def save_config(config_data: dict, user: str = "admin") -> dict:
    init()
    now = datetime.now(timezone.utc).isoformat()
    for section, value in config_data.items():
        old_value = get_config_section(section)
        backend.execute(
            f"""INSERT INTO {CONFIG_TABLE} (config_key, config_value, updated_at, updated_by)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (config_key) DO UPDATE SET
                    config_value = EXCLUDED.config_value,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by""",
            (section, json.dumps(value), now, user),
        )
        try:
            from domain.audit_trail import log_config_change
            log_config_change(section, None, old_value, value, user)
        except Exception as exc:
            log.warning("Failed to log config change: %s", exc)
    return get_config()


def get_config_section(section: str) -> dict:
    init()
    df = backend.query_df(
        f"SELECT config_value FROM {CONFIG_TABLE} WHERE config_key = %s",
        (section,),
    )
    if df.empty:
        return deepcopy(DEFAULT_CONFIG.get(section, {}))
    try:
        return json.loads(df.iloc[0]["config_value"])
    except (json.JSONDecodeError, TypeError):
        return deepcopy(DEFAULT_CONFIG.get(section, {}))


def save_config_section(section: str, value: dict, user: str = "admin") -> dict:
    init()
    old_value = get_config_section(section)
    now = datetime.now(timezone.utc).isoformat()
    backend.execute(
        f"""INSERT INTO {CONFIG_TABLE} (config_key, config_value, updated_at, updated_by)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (config_key) DO UPDATE SET
                config_value = EXCLUDED.config_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by""",
        (section, json.dumps(value), now, user),
    )
    try:
        from domain.audit_trail import log_config_change
        log_config_change(section, None, old_value, value, user)
    except Exception as exc:
        logging.getLogger(__name__).warning("Failed to log config change: %s", exc)
    return get_config_section(section)


def seed_defaults() -> dict:
    """Reset all config to factory defaults."""
    global _initialized
    _initialized = False
    init()
    backend.execute(f"DELETE FROM {CONFIG_TABLE}")
    for section, value in DEFAULT_CONFIG.items():
        backend.execute(
            f"INSERT INTO {CONFIG_TABLE} (config_key, config_value) VALUES (%s, %s)",
            (section, json.dumps(value)),
        )
    log.info("Config reset to defaults")
    return get_config()
