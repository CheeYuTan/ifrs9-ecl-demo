"""
Schema discovery and column-mapping validation for IFRS 9 ECL Application.
These functions query Lakebase to validate data source configuration.
They use local imports from admin_config to avoid circular imports and to
share the same backend reference (important for test mocking).
"""

import logging
import re

from admin_config_defaults import TYPE_COMPAT

log = logging.getLogger(__name__)


def _backend():
    """Return the backend module via admin_config to share the same reference."""
    import admin_config

    return admin_config.backend


def validate_column_mapping(table_key: str, mappings: dict) -> dict:
    """Validate that mapped columns exist in the actual Lakebase table."""
    import admin_config

    backend = _backend()
    cfg = admin_config.get_config_section("data_sources")
    table_cfg = cfg.get("tables", {}).get(table_key)
    if not table_cfg:
        return {"valid": False, "errors": [f"Unknown table: {table_key}"], "warnings": []}

    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    prefix = cfg.get("lakebase_prefix", backend.PREFIX)
    full_table = f"{schema}.{prefix}{table_cfg['source_table']}"

    errors = []
    warnings = []
    valid_columns = []

    try:
        df = backend.query_df(
            """SELECT column_name FROM information_schema.columns
               WHERE table_schema = %s AND table_name = %s""",
            (schema, f"{prefix}{table_cfg['source_table']}"),
        )
        actual_cols = set(df["column_name"].tolist())
    except Exception as e:
        return {"valid": False, "errors": [f"Cannot read table schema: {e}"], "warnings": []}

    for col_def in table_cfg.get("mandatory_columns", []):
        expected = col_def["name"]
        mapped = mappings.get(expected, expected)
        if mapped in actual_cols:
            valid_columns.append({"expected": expected, "mapped": mapped, "status": "ok"})
        else:
            errors.append(f"Mandatory column '{expected}' mapped to '{mapped}' -- not found in {full_table}")
            valid_columns.append({"expected": expected, "mapped": mapped, "status": "missing"})

    for col_def in table_cfg.get("optional_columns", []):
        expected = col_def["name"]
        mapped = mappings.get(expected, expected)
        if mapped in actual_cols:
            valid_columns.append({"expected": expected, "mapped": mapped, "status": "ok"})
        else:
            warnings.append(f"Optional column '{expected}' mapped to '{mapped}' -- not found, will use default")
            valid_columns.append({"expected": expected, "mapped": mapped, "status": "default"})

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "columns": valid_columns,
        "actual_columns": sorted(actual_cols),
    }


def get_available_tables() -> list:
    """List tables in the configured Lakebase schema."""
    import admin_config

    backend = _backend()
    cfg = admin_config.get_config_section("data_sources")
    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    try:
        df = backend.query_df(
            """SELECT table_name, table_type
               FROM information_schema.tables
               WHERE table_schema = %s
               ORDER BY table_name""",
            (schema,),
        )
        return df.to_dict("records")
    except Exception as e:
        log.warning("Failed to list tables: %s", e)
        return []


def get_table_columns(table_name: str) -> list:
    """Get columns of a specific table."""
    import admin_config

    backend = _backend()
    cfg = admin_config.get_config_section("data_sources")
    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    try:
        df = backend.query_df(
            """SELECT column_name, data_type, is_nullable, column_default
               FROM information_schema.columns
               WHERE table_schema = %s AND table_name = %s
               ORDER BY ordinal_position""",
            (schema, table_name),
        )
        return df.to_dict("records")
    except Exception as e:
        log.warning("Failed to get columns for %s: %s", table_name, e)
        return []


def get_available_schemas() -> list:
    """List available schemas in Lakebase."""
    backend = _backend()
    try:
        df = backend.query_df(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast') "
            "ORDER BY schema_name"
        )
        return df["schema_name"].tolist()
    except Exception as e:
        log.warning("Failed to list schemas: %s", e)
        return []


def get_table_preview(table_name: str, schema=None, limit: int = 5) -> dict:
    """Preview rows from a Lakebase table."""
    import admin_config

    backend = _backend()
    cfg = admin_config.get_config_section("data_sources")
    schema = schema or cfg.get("lakebase_schema", backend.SCHEMA)
    prefix = cfg.get("lakebase_prefix", backend.PREFIX)

    raw_name = table_name if table_name.startswith(prefix) else f"{prefix}{table_name}"
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", raw_name):
        return {
            "table": raw_name,
            "error": "Invalid table name",
            "row_count": 0,
            "total_rows": 0,
            "columns": [],
            "rows": [],
        }
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", schema):
        return {
            "table": raw_name,
            "error": "Invalid schema name",
            "row_count": 0,
            "total_rows": 0,
            "columns": [],
            "rows": [],
        }

    available = get_available_tables()
    valid_names = {t["table_name"] for t in available}
    if raw_name not in valid_names:
        return {
            "table": f"{schema}.{raw_name}",
            "error": f"Table '{raw_name}' not found in schema",
            "row_count": 0,
            "total_rows": 0,
            "columns": [],
            "rows": [],
        }

    full_name = f"{schema}.{raw_name}"
    try:
        count_df = backend.query_df(f"SELECT COUNT(*) as cnt FROM {full_name}")
        total_rows = int(count_df.iloc[0]["cnt"]) if not count_df.empty else 0

        df = backend.query_df(f"SELECT * FROM {full_name} LIMIT %s", (limit,))
        columns = []
        for col in df.columns:
            columns.append(
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "sample": str(df[col].iloc[0]) if len(df) > 0 else None,
                }
            )
        return {
            "table": full_name,
            "row_count": len(df),
            "total_rows": total_rows,
            "columns": columns,
            "rows": df.fillna("").to_dict("records"),
        }
    except Exception as e:
        return {"table": full_name, "error": str(e), "row_count": 0, "total_rows": 0, "columns": [], "rows": []}


def validate_column_mapping_with_types(table_key: str, mappings: dict) -> dict:
    """Validate column mappings including data type compatibility."""
    import admin_config

    backend = _backend()
    cfg = admin_config.get_config_section("data_sources")
    table_cfg = cfg.get("tables", {}).get(table_key)
    if not table_cfg:
        return {"valid": False, "errors": [f"Unknown table: {table_key}"], "warnings": [], "columns": []}

    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    prefix = cfg.get("lakebase_prefix", backend.PREFIX)
    full_table = f"{schema}.{prefix}{table_cfg['source_table']}"

    errors = []
    warnings = []
    valid_columns = []

    try:
        df = backend.query_df(
            """SELECT column_name, data_type FROM information_schema.columns
               WHERE table_schema = %s AND table_name = %s""",
            (schema, f"{prefix}{table_cfg['source_table']}"),
        )
        actual_cols = {row["column_name"]: row["data_type"] for _, row in df.iterrows()}
    except Exception as e:
        return {"valid": False, "errors": [f"Cannot read table schema: {e}"], "warnings": [], "columns": []}

    for col_def in table_cfg.get("mandatory_columns", []) + table_cfg.get("optional_columns", []):
        expected = col_def["name"]
        expected_type = col_def.get("type", "TEXT")
        is_mandatory = col_def in table_cfg.get("mandatory_columns", [])
        mapped = mappings.get(expected, expected)

        if mapped in actual_cols:
            actual_type = actual_cols[mapped]
            compatible_types = TYPE_COMPAT.get(expected_type, set())
            type_ok = actual_type.lower() in compatible_types or not compatible_types

            entry = {
                "expected": expected,
                "mapped": mapped,
                "status": "ok",
                "expected_type": expected_type,
                "actual_type": actual_type,
                "type_compatible": type_ok,
                "is_mandatory": is_mandatory,
            }
            if not type_ok:
                entry["status"] = "type_mismatch"
                warnings.append(f"Column '{mapped}' is {actual_type}, expected {expected_type}-compatible")
            valid_columns.append(entry)
        else:
            if is_mandatory:
                errors.append(f"Mandatory column '{expected}' mapped to '{mapped}' -- not found in {full_table}")
                valid_columns.append(
                    {
                        "expected": expected,
                        "mapped": mapped,
                        "status": "missing",
                        "expected_type": expected_type,
                        "actual_type": None,
                        "type_compatible": False,
                        "is_mandatory": True,
                    }
                )
            else:
                warnings.append(f"Optional column '{expected}' mapped to '{mapped}' -- not found, will use default")
                valid_columns.append(
                    {
                        "expected": expected,
                        "mapped": mapped,
                        "status": "default",
                        "expected_type": expected_type,
                        "actual_type": None,
                        "type_compatible": True,
                        "is_mandatory": False,
                    }
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "columns": valid_columns,
        "actual_columns": sorted(actual_cols.keys()),
        "actual_column_types": actual_cols,
    }


def suggest_column_mappings(table_key: str) -> dict:
    """Suggest column mappings by matching expected column names to actual columns."""
    import admin_config

    backend = _backend()
    cfg = admin_config.get_config_section("data_sources")
    table_cfg = cfg.get("tables", {}).get(table_key)
    if not table_cfg:
        return {"suggestions": {}, "actual_columns": []}

    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    prefix = cfg.get("lakebase_prefix", backend.PREFIX)

    try:
        df = backend.query_df(
            """SELECT column_name, data_type FROM information_schema.columns
               WHERE table_schema = %s AND table_name = %s""",
            (schema, f"{prefix}{table_cfg['source_table']}"),
        )
        actual_cols = {row["column_name"]: row["data_type"] for _, row in df.iterrows()}
    except Exception:
        return {"suggestions": {}, "actual_columns": []}

    suggestions = {}
    all_cols = table_cfg.get("mandatory_columns", []) + table_cfg.get("optional_columns", [])
    actual_names = set(actual_cols.keys())

    for col_def in all_cols:
        expected = col_def["name"]
        if expected in actual_names:
            suggestions[expected] = {"mapped": expected, "confidence": "exact", "actual_type": actual_cols[expected]}
            continue
        for actual in actual_names:
            if actual.lower() == expected.lower():
                suggestions[expected] = {
                    "mapped": actual,
                    "confidence": "case_insensitive",
                    "actual_type": actual_cols[actual],
                }
                break
        if expected in suggestions:
            continue
        for actual in actual_names:
            if expected.replace("_", "") in actual.replace("_", "") or actual.replace("_", "") in expected.replace(
                "_", ""
            ):
                suggestions[expected] = {"mapped": actual, "confidence": "partial", "actual_type": actual_cols[actual]}
                break

    return {
        "suggestions": suggestions,
        "actual_columns": [{"name": k, "type": v} for k, v in sorted(actual_cols.items())],
    }


def test_connection() -> dict:
    """Test the Lakebase connection and return status."""
    backend = _backend()
    try:
        df = backend.query_df("SELECT version() as version, NOW() as server_time")
        row = df.iloc[0]
        return {
            "connected": True,
            "version": str(row["version"]),
            "server_time": str(row["server_time"]),
            "schema": backend.SCHEMA,
            "prefix": backend.PREFIX,
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


def auto_detect_workspace() -> dict:
    """Auto-detect workspace URL and ID from Databricks App environment."""
    import os

    workspace_url = os.environ.get("DATABRICKS_HOST", "")
    workspace_id = os.environ.get("DATABRICKS_WORKSPACE_ID", "")
    if not workspace_url:
        try:
            from databricks.sdk import WorkspaceClient

            w = WorkspaceClient()
            workspace_url = w.config.host or ""
        except Exception:
            pass
    return {
        "workspace_url": workspace_url.rstrip("/"),
        "workspace_id": workspace_id,
        "detected": bool(workspace_url),
    }


def discover_products() -> list:
    """Discover product types from the actual data in Lakebase."""
    import admin_config

    backend = _backend()
    cfg = admin_config.get_config_section("data_sources")
    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    prefix = cfg.get("lakebase_prefix", backend.PREFIX)
    products = []
    try:
        df = backend.query_df(
            f"""SELECT product_type,
                       COUNT(*) as loan_count,
                       COALESCE(SUM(gross_carrying_amount), 0) as total_gca,
                       COALESCE(AVG(current_lifetime_pd), 0) as avg_pd
                FROM {schema}.{prefix}loan_tape
                GROUP BY product_type
                ORDER BY loan_count DESC"""
        )
        for _, row in df.iterrows():
            products.append(
                {
                    "product_type": row["product_type"],
                    "loan_count": int(row["loan_count"]),
                    "total_gca": float(row["total_gca"]),
                    "avg_pd": float(row["avg_pd"]),
                }
            )
    except Exception as e:
        log.warning("Failed to discover products: %s", e)
    return products


def auto_setup_lgd_from_data() -> dict:
    """Auto-populate LGD assumptions from discovered products."""
    products = discover_products()
    lgd = {}
    for p in products:
        pt = p["product_type"]
        avg_pd = p.get("avg_pd", 0.04)
        estimated_lgd = min(max(round(avg_pd * 8, 2), 0.15), 0.75)
        estimated_cure = min(max(round(1.0 - estimated_lgd, 2), 0.05), 0.50)
        lgd[pt] = {"lgd": estimated_lgd, "cure_rate": estimated_cure}
    return lgd
