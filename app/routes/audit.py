"""Audit trail API routes for IFRS 9 ECL Platform."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from domain.audit_trail import (
    get_audit_trail,
    verify_audit_chain,
    export_audit_package,
)
from domain.config_audit import get_config_audit_log, get_config_diff

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/config/changes")
def get_config_changes(section: str | None = None, limit: int = 100):
    return get_config_audit_log(section, limit)


@router.get("/config/diff")
def config_diff(start: str, end: str | None = None, section: str | None = None):
    """Get config changes between two timestamps."""
    return get_config_diff(start, end, section)


@router.get("/{project_id}")
def get_project_audit_trail(project_id: str):
    trail = get_audit_trail(project_id)
    if not trail:
        return {"project_id": project_id, "chain_verification": {"valid": True, "entries": 0}, "entries": []}
    verification = verify_audit_chain(project_id)
    return {"project_id": project_id, "chain_verification": verification, "entries": trail}


@router.get("/{project_id}/verify")
def verify_project_audit(project_id: str):
    return verify_audit_chain(project_id)


@router.get("/{project_id}/export")
def export_project_audit(project_id: str):
    try:
        package = export_audit_package(project_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to export audit package: {exc}")
    return JSONResponse(
        content=package,
        headers={"Content-Disposition": f"attachment; filename=audit_{project_id}.json"},
    )
