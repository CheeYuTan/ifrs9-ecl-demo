"""Audit trail API routes for IFRS 9 ECL Platform."""
import re
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from domain.audit_trail import (
    get_audit_trail,
    verify_audit_chain,
    export_audit_package,
)
from domain.config_audit import get_config_audit_log, get_config_diff

router = APIRouter(prefix="/api/audit", tags=["audit"])

_PROJECT_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,128}$")


def _validate_project_id(project_id: str) -> str:
    if not _PROJECT_ID_RE.match(project_id):
        raise HTTPException(status_code=400, detail="Invalid project_id format")
    return project_id


@router.get("/config/changes")
def get_config_changes(section: str | None = None, limit: int = 100):
    return get_config_audit_log(section, limit)


@router.get("/config/diff")
def config_diff(start: str, end: str | None = None, section: str | None = None):
    """Get config changes between two timestamps."""
    return get_config_diff(start, end, section)


@router.get("/{project_id}")
def get_project_audit_trail(
    project_id: str,
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
):
    project_id = _validate_project_id(project_id)
    trail = get_audit_trail(project_id)
    if not trail:
        return {"project_id": project_id, "chain_verification": {"valid": True, "entries": 0},
                "total": 0, "offset": offset, "limit": limit, "entries": []}
    verification = verify_audit_chain(project_id)
    total = len(trail)
    page = trail[offset:offset + limit]
    return {"project_id": project_id, "chain_verification": verification,
            "total": total, "offset": offset, "limit": limit, "entries": page}


@router.get("/{project_id}/verify")
def verify_project_audit(project_id: str):
    project_id = _validate_project_id(project_id)
    return verify_audit_chain(project_id)


@router.get("/{project_id}/export")
def export_project_audit(project_id: str):
    project_id = _validate_project_id(project_id)
    try:
        package = export_audit_package(project_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to export audit package: {exc}")
    return JSONResponse(
        content=package,
        headers={"Content-Disposition": f"attachment; filename=audit_{project_id}.json"},
    )
