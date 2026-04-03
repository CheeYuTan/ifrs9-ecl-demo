"""Project workflow routes — /api/projects/*"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import backend
from routes._utils import df_to_records, serialize_project
from middleware.auth import get_current_user, require_permission

router = APIRouter(prefix="/api", tags=["projects"])


class ProjectCreate(BaseModel):
    project_id: str
    project_name: str
    project_type: str = "ifrs9"
    description: str = ""
    reporting_date: str = ""

class StepAction(BaseModel):
    action: str
    user: str
    detail: str = ""
    status: str = "completed"

class OverlayItem(BaseModel):
    id: str
    product: str
    type: str
    amount: float
    reason: str
    ifrs9: str = ""

class OverlaySave(BaseModel):
    overlays: list[OverlayItem]
    comment: str = ""

class ScenarioWeights(BaseModel):
    weights: dict[str, float]

class SignOff(BaseModel):
    name: str
    attestation_data: dict | None = None


@router.get("/projects")
def list_projects():
    return df_to_records(backend.list_projects())

@router.get("/projects/{project_id}")
def get_project(project_id: str):
    p = backend.get_project(project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return serialize_project(p)

@router.post("/projects")
def create_project(body: ProjectCreate):
    p = backend.create_project(body.project_id, body.project_name, body.project_type, body.description, body.reporting_date)
    return serialize_project(p)

@router.post("/projects/{project_id}/advance")
def advance_step(project_id: str, body: StepAction):
    try:
        p = backend.advance_step(project_id, body.action, body.action, body.user, body.detail, body.status)
        return serialize_project(p)
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.post("/projects/{project_id}/overlays")
def save_overlays(project_id: str, body: OverlaySave):
    overlays = [o.model_dump() for o in body.overlays]
    p = backend.save_overlays(project_id, overlays)
    if body.comment:
        p = backend.advance_step(project_id, "overlays", "Overlays Submitted", "Credit Risk Analyst", body.comment)
    return serialize_project(p)

@router.post("/projects/{project_id}/scenario-weights")
def save_weights(project_id: str, body: ScenarioWeights):
    p = backend.save_scenario_weights(project_id, body.weights)
    return serialize_project(p)

@router.post("/projects/{project_id}/sign-off")
def sign_off(project_id: str, body: SignOff,
             user: dict = Depends(require_permission("sign_off_projects"))):
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
            403,
            f"Segregation of duties violation: user '{body.name}' executed the simulation and cannot sign off"
        )
    p = backend.sign_off_project(project_id, body.name, attestation_data=body.attestation_data)
    return serialize_project(p)


@router.get("/projects/{project_id}/verify-hash")
def verify_hash(project_id: str):
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
def approval_history(project_id: str):
    """Get approval history for a project (from RBAC approval requests)."""
    try:
        from governance.rbac import get_approval_history
        history = get_approval_history(project_id)
        return history
    except Exception as e:
        raise HTTPException(500, f"Failed to get approval history: {e}")

@router.post("/projects/{project_id}/reset")
def reset_project(project_id: str):
    try:
        p = backend.reset_project(project_id)
        return serialize_project(p)
    except Exception as e:
        raise HTTPException(400, str(e))
