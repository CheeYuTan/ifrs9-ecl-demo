"""Data Mapping routes — /api/data-mapping/*

Provides endpoints for the data mapping workflow:
  1. Browse Unity Catalog (catalogs, schemas, tables)
  2. Preview source table data
  3. Auto-suggest + validate column mappings
  4. Apply mappings (ingest from UC to Lakebase)
  5. Check ingestion status
"""

import logging

from domain.data_mapper import (
    apply_mapping,
    get_mapping_status,
    get_uc_table_columns,
    list_uc_catalogs,
    list_uc_schemas,
    list_uc_tables,
    preview_uc_table,
    suggest_mappings,
    validate_mapping,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data-mapping", tags=["data-mapping"])


# ── Request models ──────────────────────────────────────────────────────────


class PreviewRequest(BaseModel):
    source_table: str = Field(min_length=1, max_length=512)
    limit: int = Field(default=10, ge=1, le=1000)


class ValidateRequest(BaseModel):
    table_key: str = Field(min_length=1, max_length=256)
    source_table: str = Field(min_length=1, max_length=512)
    mappings: dict[str, str]


class SuggestRequest(BaseModel):
    table_key: str = Field(min_length=1, max_length=256)
    source_table: str = Field(min_length=1, max_length=512)


class ApplyRequest(BaseModel):
    table_key: str = Field(min_length=1, max_length=256)
    source_table: str = Field(min_length=1, max_length=512)
    mappings: dict[str, str]
    mode: str = Field(default="overwrite", pattern=r"^(overwrite|append)$")


# ── Browse Unity Catalog ────────────────────────────────────────────────────


@router.get("/catalogs")
def get_catalogs():
    """List available Unity Catalog catalogs."""
    try:
        return list_uc_catalogs()
    except Exception as e:
        log.exception("Failed to list catalogs")
        raise HTTPException(500, f"Failed to list catalogs: {e}")


@router.get("/schemas/{catalog}")
def get_schemas(catalog: str):
    """List schemas in a catalog."""
    try:
        return list_uc_schemas(catalog)
    except Exception as e:
        log.exception("Failed to list schemas")
        raise HTTPException(500, f"Failed to list schemas: {e}")


@router.get("/tables/{catalog}/{schema}")
def get_tables(catalog: str, schema: str):
    """List tables in a catalog.schema."""
    try:
        return list_uc_tables(catalog, schema)
    except Exception as e:
        log.exception("Failed to list tables")
        raise HTTPException(500, f"Failed to list tables: {e}")


@router.get("/columns/{catalog}/{schema}/{table}")
def get_columns(catalog: str, schema: str, table: str):
    """Get column metadata for a Unity Catalog table."""
    full_name = f"{catalog}.{schema}.{table}"
    try:
        return get_uc_table_columns(full_name)
    except Exception as e:
        log.exception("Failed to get columns for %s", full_name)
        raise HTTPException(500, f"Failed to get columns: {e}")


# ── Preview ─────────────────────────────────────────────────────────────────


@router.post("/preview")
def preview_table(body: PreviewRequest):
    """Preview rows from a Unity Catalog source table."""
    try:
        result = preview_uc_table(body.source_table, limit=body.limit)
        if result.get("error"):
            raise HTTPException(400, result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to preview table")
        raise HTTPException(500, f"Preview failed: {e}")


# ── Validate ────────────────────────────────────────────────────────────────


@router.post("/validate")
def validate(body: ValidateRequest):
    """Validate a column mapping configuration."""
    try:
        return validate_mapping(body.table_key, body.source_table, body.mappings)
    except Exception as e:
        log.exception("Validation failed")
        raise HTTPException(500, f"Validation failed: {e}")


# ── Suggest ─────────────────────────────────────────────────────────────────


@router.post("/suggest")
def suggest(body: SuggestRequest):
    """Auto-suggest column mappings based on name matching."""
    try:
        return suggest_mappings(body.table_key, body.source_table)
    except Exception as e:
        log.exception("Suggestion failed")
        raise HTTPException(500, f"Suggestion failed: {e}")


# ── Apply ───────────────────────────────────────────────────────────────────


@router.post("/apply")
def apply_data_mapping(body: ApplyRequest):
    """Apply the mapping: ingest data from UC to Lakebase."""
    try:
        result = apply_mapping(
            table_key=body.table_key,
            source_table=body.source_table,
            mappings=body.mappings,
            mode=body.mode,
        )
        if result["status"] == "error":
            raise HTTPException(400, result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Apply mapping failed")
        raise HTTPException(500, f"Apply failed: {e}")


# ── Status ──────────────────────────────────────────────────────────────────


@router.get("/status")
def mapping_status():
    """Get data mapping status for all ECL tables."""
    try:
        return get_mapping_status()
    except Exception as e:
        log.exception("Failed to get mapping status")
        raise HTTPException(500, f"Failed to get status: {e}")
