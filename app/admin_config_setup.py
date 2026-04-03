"""
Setup wizard functions for IFRS 9 ECL Application.
These functions check table presence, connection health, and project state
to drive the first-run setup wizard in the UI.
"""
import logging
from datetime import datetime, timezone

from admin_config_defaults import REQUIRED_INPUT_TABLES, REQUIRED_PROCESSED_TABLES

log = logging.getLogger(__name__)


def _backend():
    """Return the backend module via admin_config to share the same reference."""
    import admin_config
    return admin_config.backend


def validate_required_tables() -> dict:
    """Check which required tables exist in the configured schema."""
    import admin_config
    from admin_config_schema import get_available_tables

    backend = _backend()
    cfg = admin_config.get_config_section("data_sources")
    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    prefix = cfg.get("lakebase_prefix", backend.PREFIX)

    available = get_available_tables()
    available_names = {t["table_name"] for t in available}

    found = []
    missing = []

    for tbl in REQUIRED_INPUT_TABLES:
        prefixed = f"{prefix}{tbl}"
        if prefixed in available_names:
            try:
                count_df = backend.query_df(f"SELECT COUNT(*) as cnt FROM {schema}.{prefixed}")
                row_count = int(count_df.iloc[0]["cnt"]) if not count_df.empty else 0
            except Exception:
                row_count = 0
            found.append({"table": tbl, "prefixed_name": prefixed, "exists": True, "row_count": row_count})
        else:
            missing.append({"table": tbl, "prefixed_name": prefixed, "exists": False, "row_count": 0})

    processed_found = []
    for tbl in REQUIRED_PROCESSED_TABLES:
        prefixed = f"{prefix}{tbl}"
        if prefixed in available_names:
            try:
                count_df = backend.query_df(f"SELECT COUNT(*) as cnt FROM {schema}.{prefixed}")
                row_count = int(count_df.iloc[0]["cnt"]) if not count_df.empty else 0
            except Exception:
                row_count = 0
            processed_found.append({"table": tbl, "prefixed_name": prefixed, "exists": True, "row_count": row_count})
        else:
            processed_found.append({"table": tbl, "prefixed_name": prefixed, "exists": False, "row_count": 0})

    total_input = len(REQUIRED_INPUT_TABLES)
    found_input = len(found)

    return {
        "schema": schema,
        "prefix": prefix,
        "input_tables": found + missing,
        "processed_tables": processed_found,
        "input_found": found_input,
        "input_total": total_input,
        "all_input_present": found_input == total_input,
        "processed_found": sum(1 for t in processed_found if t["exists"]),
        "processed_total": len(REQUIRED_PROCESSED_TABLES),
    }


def get_setup_status() -> dict:
    """Return the overall setup completion status for the wizard."""
    import admin_config
    from admin_config_schema import test_connection

    backend = _backend()
    admin_config.init()

    # Step 1: Data connection
    conn = test_connection()
    data_connection = {
        "complete": conn.get("connected", False),
        "detail": (
            f"Connected to {conn.get('schema', 'unknown')} schema"
            if conn.get("connected")
            else conn.get("error", "Not connected")
        ),
    }

    # Step 2: Data tables
    try:
        tables = validate_required_tables()
        tables_complete = tables["input_found"] >= 3
        data_tables = {
            "complete": tables_complete,
            "detail": f"{tables['input_found']}/{tables['input_total']} required input tables found",
            "tables": tables,
        }
    except Exception as e:
        data_tables = {"complete": False, "detail": f"Error checking tables: {e}"}

    # Step 3: Organisation
    app_settings = admin_config.get_config_section("app_settings")
    org_name = app_settings.get("organization_name", "")
    org_configured = bool(org_name and org_name != "Horizon Bank")
    organization = {
        "complete": org_configured,
        "detail": (
            f"{org_name} configured"
            if org_configured
            else "Default organization -- not yet customized"
        ),
    }

    # Step 4: First project
    try:
        projects_df = backend.list_projects()
        has_project = len(projects_df) > 0
        if has_project:
            first = projects_df.iloc[0]
            first_project = {
                "complete": True,
                "detail": f"{first.get('project_name', first.get('project_id', 'Unknown'))} exists",
            }
        else:
            first_project = {"complete": False, "detail": "No projects created yet"}
    except Exception:
        first_project = {"complete": False, "detail": "Could not check projects"}

    # Check if setup was explicitly marked complete
    try:
        setup_cfg = admin_config.get_config_section("setup")
        explicitly_complete = setup_cfg.get("completed", False)
    except Exception:
        explicitly_complete = False

    steps = {
        "data_connection": data_connection,
        "data_tables": data_tables,
        "organization": organization,
        "first_project": first_project,
    }

    all_complete = all(s.get("complete", False) for s in steps.values())

    return {
        "is_configured": explicitly_complete or all_complete,
        "steps": steps,
    }


def mark_setup_complete(user: str = "admin") -> dict:
    """Mark the setup wizard as complete."""
    import admin_config
    admin_config.save_config_section("setup", {
        "completed": True,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "completed_by": user,
    }, user)
    return get_setup_status()


def mark_setup_incomplete() -> dict:
    """Reset setup status so the wizard shows again."""
    import admin_config
    admin_config.save_config_section("setup", {"completed": False})
    return get_setup_status()
