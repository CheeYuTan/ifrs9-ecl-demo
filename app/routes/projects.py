"""Project workflow routes — /api/projects/*

Protected with two-layer permission model:
  - Layer 1 (RBAC): Global role via require_permission
  - Layer 2 (Project): Per-project role via require_project_access
"""

import backend
from fastapi import APIRouter, Depends, HTTPException, Request
from middleware.auth import (
    get_current_user,
    require_permission,
    require_project_access,
)
from pydantic import BaseModel, Field

from routes._utils import df_to_records, serialize_project

router = APIRouter(prefix="/api", tags=["projects"])


class ProjectCreate(BaseModel):
    project_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_\-]+$")
    project_name: str = Field(min_length=1, max_length=256)
    project_type: str = Field(default="ifrs9", max_length=64)
    description: str = Field(default="", max_length=2000)
    reporting_date: str = Field(default="", max_length=32)


class StepAction(BaseModel):
    action: str = Field(min_length=1, max_length=128)
    user: str = Field(min_length=1, max_length=256)
    detail: str = Field(default="", max_length=2000)
    status: str = Field(default="completed", max_length=32)


class OverlayItem(BaseModel):
    id: str = Field(max_length=128)
    product: str = Field(max_length=128)
    type: str = Field(max_length=64)
    amount: float
    reason: str = Field(max_length=2000)
    ifrs9: str = Field(default="", max_length=128)


class OverlaySave(BaseModel):
    overlays: list[OverlayItem] = Field(max_length=1000)
    comment: str = Field(default="", max_length=2000)


class ScenarioWeights(BaseModel):
    weights: dict[str, float]


class SignOff(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    attestation_data: dict | None = None


@router.get("/projects")
def list_projects(request: Request):
    """List projects filtered by user access.

    Anonymous / admin: see all projects.
    Authenticated non-admin: see only projects where user is owner or member.
    """
    has_auth = bool(
        request.headers.get("X-Forwarded-User") or request.headers.get("X-User-Id") or request.headers.get("x-user-id")
    )
    all_projects = df_to_records(backend.list_projects())
    if not has_auth:
        return all_projects

    user = get_current_user(request)
    if user.get("role") == "admin":
        return all_projects

    # Filter to projects the user can access
    from governance.project_permissions import get_effective_role

    return [p for p in all_projects if get_effective_role(user["user_id"], p["project_id"]) is not None]


@router.get("/projects/{project_id}")
def get_project(
    project_id: str,
    user: dict = Depends(require_project_access("viewer")),
):
    p = backend.get_project(project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return serialize_project(p)


@router.post("/projects")
def create_project(body: ProjectCreate, request: Request):
    user = get_current_user(request)
    owner_id = user["user_id"] if user["user_id"] != "anonymous" else "usr-004"
    p = backend.create_project(
        body.project_id,
        body.project_name,
        body.project_type,
        body.description,
        body.reporting_date,
        owner_id=owner_id,
    )
    return serialize_project(p)


@router.post("/projects/{project_id}/advance")
def advance_step(
    project_id: str,
    body: StepAction,
    user: dict = Depends(require_project_access("editor")),
):
    try:
        p = backend.advance_step(project_id, body.action, body.action, body.user, body.detail, body.status)
        return serialize_project(p)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/projects/{project_id}/overlays")
def save_overlays(
    project_id: str,
    body: OverlaySave,
    user: dict = Depends(require_project_access("editor")),
):
    overlays = [o.model_dump() for o in body.overlays]
    p = backend.save_overlays(project_id, overlays)
    if body.comment:
        p = backend.advance_step(project_id, "overlays", "Overlays Submitted", "Credit Risk Analyst", body.comment)
    return serialize_project(p)


@router.post("/projects/{project_id}/scenario-weights")
def save_weights(
    project_id: str,
    body: ScenarioWeights,
    user: dict = Depends(require_project_access("editor")),
):
    p = backend.save_scenario_weights(project_id, body.weights)
    return serialize_project(p)


@router.post("/projects/{project_id}/sign-off")
def sign_off(
    project_id: str,
    body: SignOff,
    rbac_user: dict = Depends(require_permission("sign_off_projects")),
    proj_user: dict = Depends(require_project_access("owner")),
):
    """Dual-gate: requires both RBAC sign_off_projects AND project owner role."""
    proj = backend.get_project(project_id)
    if proj and proj.get("signed_off"):
        raise HTTPException(403, "Project already signed off and immutable")
    audit_log = proj.get("audit_log", []) if proj else []
    if isinstance(audit_log, str):
        import json

        try:
            audit_log = json.loads(audit_log)
        except Exception:
            audit_log = []
    executor = None
    for entry in reversed(audit_log):
        if isinstance(entry, dict) and entry.get("step") == "model_execution":
            executor = entry.get("user")
            break
    if executor and executor == body.name:
        raise HTTPException(
            403, f"Segregation of duties violation: user '{body.name}' executed the simulation and cannot sign off"
        )
    p = backend.sign_off_project(project_id, body.name, attestation_data=body.attestation_data)
    return serialize_project(p)


@router.get("/projects/{project_id}/verify-hash")
def verify_hash(
    project_id: str,
    user: dict = Depends(require_project_access("viewer")),
):
    """Verify the ECL hash for a signed-off project."""
    proj = backend.get_project(project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    stored_hash = proj.get("ecl_hash")
    if not stored_hash:
        return {"status": "not_computed", "message": "No ECL hash stored for this project"}
    from middleware.auth import compute_ecl_hash, verify_ecl_hash

    ecl_data = {
        "project_id": proj.get("project_id"),
        "step_status": proj.get("step_status"),
        "overlays": proj.get("overlays"),
        "scenario_weights": proj.get("scenario_weights"),
    }
    is_valid = verify_ecl_hash(ecl_data, stored_hash)
    return {
        "status": "valid" if is_valid else "invalid",
        "stored_hash": stored_hash,
        "computed_hash": compute_ecl_hash(ecl_data),
        "match": is_valid,
        "signed_off_by": proj.get("signed_off_by"),
        "signed_off_at": str(proj.get("signed_off_at", "")),
    }


@router.get("/projects/{project_id}/approval-history")
def approval_history(
    project_id: str,
    user: dict = Depends(require_project_access("viewer")),
):
    """Get approval history for a project (from RBAC approval requests)."""
    try:
        from governance.rbac import get_approval_history

        history = get_approval_history(project_id)
        return history
    except Exception as e:
        raise HTTPException(500, f"Failed to get approval history: {e}")


@router.post("/projects/{project_id}/reset")
def reset_project(
    project_id: str,
    user: dict = Depends(require_project_access("manager")),
):
    try:
        p = backend.reset_project(project_id)
        return serialize_project(p)
    except Exception as e:
        raise HTTPException(400, str(e))
