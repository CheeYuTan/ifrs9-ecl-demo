"""Admin config routes — /api/admin/*

All endpoints require admin RBAC role (Layer 1). Anonymous dev mode bypasses.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import admin_config
from middleware.auth import require_admin

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin())],
)


class ValidateMappingRequest(BaseModel):
    table_key: str
    mappings: dict


@router.get("/config")
def admin_get_config():
    try:
        return admin_config.get_config()
    except Exception as e:
        log.exception("Failed to load admin config")
        raise HTTPException(500, f"Failed to load config: {e}")

@router.put("/config")
def admin_save_config(body: dict):
    try:
        return admin_config.save_config(body)
    except Exception as e:
        log.exception("Failed to save admin config")
        raise HTTPException(500, f"Failed to save config: {e}")

@router.get("/config/{section}")
def admin_get_section(section: str):
    try:
        return admin_config.get_config_section(section)
    except Exception as e:
        raise HTTPException(500, f"Failed to load config section: {e}")

@router.put("/config/{section}")
def admin_save_section(section: str, body: dict):
    try:
        return admin_config.save_config_section(section, body)
    except Exception as e:
        raise HTTPException(500, f"Failed to save config section: {e}")

@router.post("/validate-mapping")
def admin_validate_mapping(body: ValidateMappingRequest):
    try:
        return admin_config.validate_column_mapping(body.table_key, body.mappings)
    except Exception as e:
        raise HTTPException(500, f"Validation failed: {e}")

@router.get("/available-tables")
def admin_available_tables():
    try:
        return admin_config.get_available_tables()
    except Exception as e:
        raise HTTPException(500, f"Failed to list tables: {e}")

@router.get("/table-columns/{table}")
def admin_table_columns(table: str):
    try:
        return admin_config.get_table_columns(table)
    except Exception as e:
        raise HTTPException(500, f"Failed to get columns: {e}")

@router.post("/test-connection")
def admin_test_connection():
    try:
        return admin_config.test_connection()
    except Exception as e:
        raise HTTPException(500, f"Connection test failed: {e}")

@router.post("/seed-defaults")
def admin_seed_defaults():
    try:
        return admin_config.seed_defaults()
    except Exception as e:
        raise HTTPException(500, f"Failed to seed defaults: {e}")

@router.get("/schemas")
def admin_schemas():
    try:
        return admin_config.get_available_schemas()
    except Exception as e:
        raise HTTPException(500, f"Failed to list schemas: {e}")

@router.get("/table-preview/{table}")
def admin_table_preview(table: str, schema: str | None = None, limit: int = 5):
    try:
        return admin_config.get_table_preview(table, schema, min(limit, 20))
    except Exception as e:
        raise HTTPException(500, f"Failed to preview table: {e}")

@router.post("/validate-mapping-typed")
def admin_validate_mapping_typed(body: ValidateMappingRequest):
    try:
        return admin_config.validate_column_mapping_with_types(body.table_key, body.mappings)
    except Exception as e:
        raise HTTPException(500, f"Validation failed: {e}")

@router.get("/suggest-mappings/{table_key}")
def admin_suggest_mappings(table_key: str):
    try:
        return admin_config.suggest_column_mappings(table_key)
    except Exception as e:
        raise HTTPException(500, f"Failed to suggest mappings: {e}")

@router.get("/auto-detect-workspace")
def admin_auto_detect_workspace():
    try:
        return admin_config.auto_detect_workspace()
    except Exception as e:
        raise HTTPException(500, f"Failed to auto-detect workspace: {e}")

@router.get("/discover-products")
def admin_discover_products():
    try:
        return admin_config.discover_products()
    except Exception as e:
        raise HTTPException(500, f"Failed to discover products: {e}")

@router.post("/auto-setup-lgd")
def admin_auto_setup_lgd():
    try:
        return admin_config.auto_setup_lgd_from_data()
    except Exception as e:
        raise HTTPException(500, f"Failed to auto-setup LGD: {e}")
