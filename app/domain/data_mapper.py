"""
Data Mapper — Maps customer source data (Unity Catalog) to ECL schema tables.

Handles:
  - Listing catalogs/schemas/tables from Unity Catalog via Databricks SDK
  - Previewing source table data
  - Validating column mappings (completeness + type compatibility)
  - Applying mappings: read from UC, transform, write to Lakebase
"""

import logging
import re

import admin_config
import backend

log = logging.getLogger(__name__)

# ── Type compatibility map ──────────────────────────────────────────────────

TYPE_COMPAT = admin_config.TYPE_COMPAT  # reuse from admin_config

PG_TYPE_MAP = {
    "TEXT": "TEXT",
    "INT": "INTEGER",
    "NUMERIC": "NUMERIC",
    "DATE": "DATE",
    "BOOLEAN": "BOOLEAN",
}

# ── Helpers ─────────────────────────────────────────────────────────────────


def _get_workspace_client():
    """Lazy-load WorkspaceClient."""
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def _safe_identifier(name: str) -> str:
    """Validate identifier to prevent SQL injection."""
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.\-]*$", name):
        raise ValueError(f"Invalid identifier: {name}")
    return name


# ── Unity Catalog browsing ──────────────────────────────────────────────────


def list_uc_catalogs() -> list[dict]:
    """List catalogs accessible in the workspace."""
    try:
        w = _get_workspace_client()
        catalogs = list(w.catalogs.list())
        return [{"name": c.name, "comment": c.comment or ""} for c in catalogs]
    except Exception as e:
        log.warning("Failed to list UC catalogs: %s", e)
        return []


def list_uc_schemas(catalog: str) -> list[dict]:
    """List schemas in a Unity Catalog catalog."""
    try:
        w = _get_workspace_client()
        schemas = list(w.schemas.list(catalog_name=_safe_identifier(catalog)))
        return [{"name": s.name, "full_name": s.full_name, "comment": s.comment or ""} for s in schemas]
    except Exception as e:
        log.warning("Failed to list UC schemas for %s: %s", catalog, e)
        return []


def list_uc_tables(catalog: str, schema: str) -> list[dict]:
    """List tables in a Unity Catalog schema."""
    try:
        w = _get_workspace_client()
        tables = list(
            w.tables.list(
                catalog_name=_safe_identifier(catalog),
                schema_name=_safe_identifier(schema),
            )
        )
        return [
            {
                "name": t.name,
                "full_name": t.full_name,
                "table_type": str(t.table_type) if t.table_type else "UNKNOWN",
                "comment": t.comment or "",
            }
            for t in tables
        ]
    except Exception as e:
        log.warning("Failed to list UC tables for %s.%s: %s", catalog, schema, e)
        return []


def get_uc_table_columns(full_table_name: str) -> list[dict]:
    """Get column info for a Unity Catalog table."""
    try:
        w = _get_workspace_client()
        table_info = w.tables.get(full_name=full_table_name)
        if not table_info.columns:
            return []
        return [
            {
                "name": col.name,
                "type": col.type_name.value if col.type_name else "STRING",
                "comment": col.comment or "",
                "position": col.position,
            }
            for col in table_info.columns
        ]
    except Exception as e:
        log.warning("Failed to get columns for %s: %s", full_table_name, e)
        return []


# ── Preview ─────────────────────────────────────────────────────────────────


def preview_uc_table(full_table_name: str, limit: int = 10) -> dict:
    """
    Preview first N rows of a Unity Catalog table.
    Uses SQL via the Databricks SDK statement execution API.
    """
    try:
        _safe_identifier(full_table_name.replace(".", "_").replace("-", "_"))
    except ValueError:
        return {"error": f"Invalid table name: {full_table_name}", "columns": [], "rows": [], "total_rows": 0}

    try:
        w = _get_workspace_client()
        # Use statement execution to query UC table
        import os

        warehouse_id = os.environ.get("DATABRICKS_SQL_WAREHOUSE_ID", "")
        if not warehouse_id:
            # Try to find a warehouse
            warehouses = list(w.warehouses.list())
            if warehouses:
                warehouse_id = warehouses[0].id

        if not warehouse_id:
            return {
                "error": "No SQL warehouse available for preview. Set DATABRICKS_SQL_WAREHOUSE_ID.",
                "columns": [],
                "rows": [],
                "total_rows": 0,
            }

        # Get row count
        count_stmt = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=f"SELECT COUNT(*) as cnt FROM {full_table_name}",
            wait_timeout="30s",
        )
        total_rows = 0
        if count_stmt.result and count_stmt.result.data_array:
            total_rows = int(count_stmt.result.data_array[0][0])

        # Get preview rows
        preview_stmt = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=f"SELECT * FROM {full_table_name} LIMIT {int(limit)}",
            wait_timeout="30s",
        )

        columns = []
        rows = []
        if preview_stmt.manifest and preview_stmt.manifest.schema and preview_stmt.manifest.schema.columns:
            columns = [{"name": c.name, "type": c.type_text or "STRING"} for c in preview_stmt.manifest.schema.columns]

        if preview_stmt.result and preview_stmt.result.data_array:
            col_names = [c["name"] for c in columns]
            for row_arr in preview_stmt.result.data_array:
                row_dict = {}
                for i, val in enumerate(row_arr):
                    if i < len(col_names):
                        row_dict[col_names[i]] = val
                rows.append(row_dict)

        return {
            "table": full_table_name,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "total_rows": total_rows,
        }
    except Exception as e:
        log.exception("Failed to preview UC table %s", full_table_name)
        return {"error": str(e), "table": full_table_name, "columns": [], "rows": [], "total_rows": 0}


def preview_lakebase_table(table_key: str, limit: int = 10) -> dict:
    """Preview a Lakebase (target) table."""
    return admin_config.get_table_preview(table_key, limit=limit)


# ── Mapping validation ──────────────────────────────────────────────────────


def _uc_type_to_ecl_type(uc_type: str) -> str:
    """Map Unity Catalog types to ECL schema types."""
    uc_upper = uc_type.upper()
    if any(t in uc_upper for t in ("STRING", "VARCHAR", "CHAR")):
        return "TEXT"
    if any(t in uc_upper for t in ("INT", "LONG", "SHORT", "BYTE", "TINYINT", "SMALLINT", "BIGINT")):
        return "INT"
    if any(t in uc_upper for t in ("DOUBLE", "FLOAT", "DECIMAL", "NUMERIC")):
        return "NUMERIC"
    if "DATE" in uc_upper or "TIMESTAMP" in uc_upper:
        return "DATE"
    if "BOOLEAN" in uc_upper or "BOOL" in uc_upper:
        return "BOOLEAN"
    return "TEXT"


def validate_mapping(
    table_key: str,
    source_table: str,
    mappings: dict[str, str],
) -> dict:
    """
    Validate a column mapping from a UC source table to an ECL target table.

    Args:
        table_key: ECL table key (e.g., 'loan_tape')
        source_table: Full UC table name (e.g., 'catalog.schema.table')
        mappings: Dict of {ecl_column_name: source_column_name}

    Returns:
        Validation result with errors, warnings, and column details.
    """
    cfg = admin_config.get_config_section("data_sources")
    table_cfg = cfg.get("tables", {}).get(table_key)
    if not table_cfg:
        return {"valid": False, "errors": [f"Unknown ECL table: {table_key}"], "warnings": [], "columns": []}

    # Get source table columns
    source_columns = get_uc_table_columns(source_table)
    if not source_columns:
        return {
            "valid": False,
            "errors": [f"Cannot read columns from source table: {source_table}"],
            "warnings": [],
            "columns": [],
        }

    source_col_map = {c["name"]: c for c in source_columns}
    errors = []
    warnings = []
    columns = []

    # Check mandatory columns
    for col_def in table_cfg.get("mandatory_columns", []):
        ecl_name = col_def["name"]
        ecl_type = col_def.get("type", "TEXT")
        mapped_source = mappings.get(ecl_name)

        if not mapped_source:
            errors.append(f"Mandatory column '{ecl_name}' is not mapped")
            columns.append(
                {
                    "ecl_column": ecl_name,
                    "ecl_type": ecl_type,
                    "source_column": None,
                    "source_type": None,
                    "status": "unmapped",
                    "is_mandatory": True,
                    "description": col_def.get("description", ""),
                }
            )
            continue

        source_col = source_col_map.get(mapped_source)
        if not source_col:
            errors.append(f"Mandatory column '{ecl_name}' mapped to '{mapped_source}' which does not exist in source")
            columns.append(
                {
                    "ecl_column": ecl_name,
                    "ecl_type": ecl_type,
                    "source_column": mapped_source,
                    "source_type": None,
                    "status": "source_missing",
                    "is_mandatory": True,
                    "description": col_def.get("description", ""),
                }
            )
            continue

        source_type = source_col.get("type", "STRING")
        mapped_ecl_type = _uc_type_to_ecl_type(source_type)
        type_ok = mapped_ecl_type == ecl_type or ecl_type in ("TEXT",)

        # Special: NUMERIC columns accept INT source columns (safe widening)
        if ecl_type == "NUMERIC" and mapped_ecl_type == "INT":
            type_ok = True
        if ecl_type == "INT" and mapped_ecl_type == "NUMERIC":
            type_ok = True  # will truncate but acceptable

        status = "ok" if type_ok else "type_mismatch"
        if not type_ok:
            errors.append(
                f"Mandatory column '{ecl_name}': source type {source_type} ({mapped_ecl_type}) "
                f"is not compatible with expected {ecl_type}"
            )

        columns.append(
            {
                "ecl_column": ecl_name,
                "ecl_type": ecl_type,
                "source_column": mapped_source,
                "source_type": source_type,
                "status": status,
                "is_mandatory": True,
                "type_compatible": type_ok,
                "description": col_def.get("description", ""),
            }
        )

    # Check optional columns
    for col_def in table_cfg.get("optional_columns", []):
        ecl_name = col_def["name"]
        ecl_type = col_def.get("type", "TEXT")
        mapped_source = mappings.get(ecl_name)

        if not mapped_source:
            columns.append(
                {
                    "ecl_column": ecl_name,
                    "ecl_type": ecl_type,
                    "source_column": None,
                    "source_type": None,
                    "status": "unmapped_optional",
                    "is_mandatory": False,
                    "description": col_def.get("description", ""),
                    "default": col_def.get("default", "null"),
                }
            )
            continue

        source_col = source_col_map.get(mapped_source)
        if not source_col:
            warnings.append(f"Optional column '{ecl_name}' mapped to '{mapped_source}' which does not exist in source")
            columns.append(
                {
                    "ecl_column": ecl_name,
                    "ecl_type": ecl_type,
                    "source_column": mapped_source,
                    "source_type": None,
                    "status": "source_missing",
                    "is_mandatory": False,
                    "description": col_def.get("description", ""),
                }
            )
            continue

        source_type = source_col.get("type", "STRING")
        mapped_ecl_type = _uc_type_to_ecl_type(source_type)
        type_ok = mapped_ecl_type == ecl_type or ecl_type in ("TEXT",)
        if ecl_type == "NUMERIC" and mapped_ecl_type == "INT":
            type_ok = True
        if ecl_type == "INT" and mapped_ecl_type == "NUMERIC":
            type_ok = True

        status = "ok" if type_ok else "type_mismatch"
        if not type_ok:
            warnings.append(
                f"Optional column '{ecl_name}': source type {source_type} ({mapped_ecl_type}) "
                f"may not be compatible with expected {ecl_type}"
            )

        columns.append(
            {
                "ecl_column": ecl_name,
                "ecl_type": ecl_type,
                "source_column": mapped_source,
                "source_type": source_type,
                "status": status,
                "is_mandatory": False,
                "type_compatible": type_ok,
                "description": col_def.get("description", ""),
            }
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "columns": columns,
        "source_table": source_table,
        "target_table": table_key,
        "mapped_count": sum(1 for c in columns if c.get("source_column")),
        "mandatory_count": sum(1 for c in columns if c.get("is_mandatory")),
        "mandatory_mapped": sum(1 for c in columns if c.get("is_mandatory") and c.get("source_column")),
    }


def suggest_mappings(table_key: str, source_table: str) -> dict:
    """
    Auto-suggest column mappings by matching ECL column names to source columns.
    Uses exact match, case-insensitive match, and substring matching.
    """
    cfg = admin_config.get_config_section("data_sources")
    table_cfg = cfg.get("tables", {}).get(table_key)
    if not table_cfg:
        return {"suggestions": {}, "source_columns": []}

    source_columns = get_uc_table_columns(source_table)
    if not source_columns:
        return {"suggestions": {}, "source_columns": []}

    source_names = {c["name"] for c in source_columns}
    source_name_lower = {c["name"].lower(): c["name"] for c in source_columns}
    suggestions = {}

    all_cols = table_cfg.get("mandatory_columns", []) + table_cfg.get("optional_columns", [])

    for col_def in all_cols:
        ecl_name = col_def["name"]
        ecl_lower = ecl_name.lower()

        # Exact match
        if ecl_name in source_names:
            suggestions[ecl_name] = {"source_column": ecl_name, "confidence": "exact"}
            continue

        # Case-insensitive match
        if ecl_lower in source_name_lower:
            suggestions[ecl_name] = {"source_column": source_name_lower[ecl_lower], "confidence": "case_insensitive"}
            continue

        # Substring / fuzzy match
        ecl_normalized = ecl_lower.replace("_", "")
        for src_name in source_names:
            src_normalized = src_name.lower().replace("_", "")
            if ecl_normalized == src_normalized:
                suggestions[ecl_name] = {"source_column": src_name, "confidence": "normalized"}
                break
            if ecl_normalized in src_normalized or src_normalized in ecl_normalized:
                suggestions[ecl_name] = {"source_column": src_name, "confidence": "partial"}
                break

    return {
        "suggestions": suggestions,
        "source_columns": source_columns,
        "matched": len(suggestions),
        "total_ecl_columns": len(all_cols),
    }


# ── Apply mapping (ingest data) ────────────────────────────────────────────


def apply_mapping(
    table_key: str,
    source_table: str,
    mappings: dict[str, str],
    mode: str = "overwrite",
) -> dict:
    """
    Apply a column mapping: read from UC source, transform, write to Lakebase.

    Args:
        table_key: ECL table key (e.g., 'loan_tape')
        source_table: Full UC table name
        mappings: Dict of {ecl_column: source_column}
        mode: 'overwrite' or 'append'

    Returns:
        Result dict with status and row counts.
    """
    # Validate first
    validation = validate_mapping(table_key, source_table, mappings)
    if not validation["valid"]:
        return {
            "status": "error",
            "message": "Validation failed — fix errors before applying",
            "errors": validation["errors"],
            "rows_written": 0,
        }

    cfg = admin_config.get_config_section("data_sources")
    table_cfg = cfg.get("tables", {}).get(table_key)
    if not table_cfg:
        return {"status": "error", "message": f"Unknown table: {table_key}", "rows_written": 0}

    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    prefix = cfg.get("lakebase_prefix", backend.PREFIX)
    target_table = f"{schema}.{prefix}{table_cfg['source_table']}"

    try:
        # Build SELECT with column renames
        select_parts = []
        for col_info in validation["columns"]:
            ecl_col = col_info["ecl_column"]
            src_col = col_info.get("source_column")
            if src_col:
                select_parts.append(f'`{src_col}` AS "{ecl_col}"')

        if not select_parts:
            return {"status": "error", "message": "No columns mapped", "rows_written": 0}

        select_sql = f"SELECT {', '.join(select_parts)} FROM {source_table}"

        # Execute via Databricks SDK
        import os

        w = _get_workspace_client()
        warehouse_id = os.environ.get("DATABRICKS_SQL_WAREHOUSE_ID", "")
        if not warehouse_id:
            warehouses = list(w.warehouses.list())
            if warehouses:
                warehouse_id = warehouses[0].id

        if not warehouse_id:
            return {"status": "error", "message": "No SQL warehouse available", "rows_written": 0}

        # Read data from UC
        stmt = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=select_sql,
            wait_timeout="120s",
        )

        if not stmt.result or not stmt.result.data_array:
            return {"status": "warning", "message": "Source table is empty", "rows_written": 0}

        col_names = [c["ecl_column"] for c in validation["columns"] if c.get("source_column")]
        rows = stmt.result.data_array

        # Write to Lakebase
        if mode == "overwrite":
            backend.execute(f"TRUNCATE TABLE {target_table}")

        # Batch insert
        batch_size = 500
        total_written = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            placeholders = ", ".join("(" + ", ".join(["%s"] * len(col_names)) + ")" for _ in batch)
            col_list = ", ".join(f'"{c}"' for c in col_names)
            insert_sql = f"INSERT INTO {target_table} ({col_list}) VALUES {placeholders}"

            flat_values = []
            for row in batch:
                for val in row:
                    flat_values.append(val if val is not None else None)

            backend.execute(insert_sql, tuple(flat_values))
            total_written += len(batch)

        # Save the mapping config to admin_config
        cfg_tables = cfg.get("tables", {})
        if table_key in cfg_tables:
            cfg_tables[table_key]["column_mappings"] = mappings
            cfg_tables[table_key]["source_uc_table"] = source_table
            admin_config.save_config_section("data_sources", cfg)

        return {
            "status": "success",
            "message": f"Ingested {total_written} rows into {target_table}",
            "rows_written": total_written,
            "target_table": target_table,
            "source_table": source_table,
            "columns_mapped": len(col_names),
            "mode": mode,
        }

    except Exception as e:
        log.exception("Failed to apply mapping for %s", table_key)
        return {"status": "error", "message": str(e), "rows_written": 0}


def get_mapping_status() -> dict:
    """Get the current data mapping status for all ECL tables."""
    cfg = admin_config.get_config_section("data_sources")
    tables = cfg.get("tables", {})
    schema = cfg.get("lakebase_schema", backend.SCHEMA)
    prefix = cfg.get("lakebase_prefix", backend.PREFIX)

    status = {}
    for key, tbl in tables.items():
        target_table = f"{schema}.{prefix}{tbl['source_table']}"
        row_count = 0
        has_data = False
        try:
            df = backend.query_df(f"SELECT COUNT(*) as cnt FROM {target_table}")
            row_count = int(df.iloc[0]["cnt"]) if not df.empty else 0
            has_data = row_count > 0
        except Exception:
            pass

        mandatory = tbl.get("mandatory_columns", [])
        optional = tbl.get("optional_columns", [])
        mappings = tbl.get("column_mappings", {})
        source_uc = tbl.get("source_uc_table", "")

        status[key] = {
            "table_key": key,
            "target_table": target_table,
            "source_uc_table": source_uc,
            "required": tbl.get("required", False),
            "description": tbl.get("description", ""),
            "has_data": has_data,
            "row_count": row_count,
            "mandatory_columns": len(mandatory),
            "optional_columns": len(optional),
            "mapped_columns": len(mappings),
        }

    return status
