"""Setup wizard routes — /api/setup/*"""

import logging

import admin_config
import backend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["setup"])


class SetupCompleteRequest(BaseModel):
    user: str = Field(default="admin", max_length=256)


@router.get("/status")
def setup_status():
    try:
        return admin_config.get_setup_status()
    except Exception as e:
        log.exception("Failed to get setup status")
        raise HTTPException(500, f"Failed to get setup status: {e}")


@router.post("/validate-tables")
def setup_validate_tables():
    try:
        return admin_config.validate_required_tables()
    except Exception as e:
        log.exception("Failed to validate tables")
        raise HTTPException(500, f"Failed to validate tables: {e}")


@router.post("/seed-sample-data")
def setup_seed_sample_data():
    try:
        backend.ensure_tables()
        return {"status": "ok", "message": "Sample data seeded successfully"}
    except Exception as e:
        log.exception("Failed to seed sample data")
        raise HTTPException(500, f"Failed to seed sample data: {e}")


@router.post("/complete")
def setup_complete(body: SetupCompleteRequest | None = None):
    try:
        user = body.user if body else "admin"
        return admin_config.mark_setup_complete(user)
    except Exception as e:
        log.exception("Failed to mark setup complete")
        raise HTTPException(500, f"Failed to mark setup complete: {e}")


@router.post("/reset")
def setup_reset():
    try:
        return admin_config.mark_setup_incomplete()
    except Exception as e:
        log.exception("Failed to reset setup")
        raise HTTPException(500, f"Failed to reset setup: {e}")
