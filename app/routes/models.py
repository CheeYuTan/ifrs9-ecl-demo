"""Model registry routes — /api/models/*"""
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import backend
from routes._utils import DecimalEncoder

router = APIRouter(prefix="/api", tags=["models"])


class RegisterModelRequest(BaseModel):
    model_name: str
    model_type: str
    algorithm: str = "Unknown"
    version: int = 1
    description: str = ""
    product_type: str = ""
    cohort: str = ""
    parameters: dict = {}
    performance_metrics: dict = {}
    training_data_info: dict = {}
    created_by: str = "system"
    notes: str = ""
    parent_model_id: Optional[str] = None

class UpdateModelStatusRequest(BaseModel):
    status: str
    user: str
    comment: str = ""

class CompareModelsRequest(BaseModel):
    model_ids: list[str]

class PromoteChampionRequest(BaseModel):
    user: str


@router.get("/models")
def list_models(model_type: Optional[str] = None, status: Optional[str] = None):
    try:
        models = backend.list_models(model_type, status)
        return json.loads(json.dumps(models, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list models: {e}")

@router.get("/models/{model_id}")
def get_model(model_id: str):
    try:
        model = backend.get_model(model_id)
        if not model:
            raise HTTPException(404, "Model not found")
        return json.loads(json.dumps(model, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get model: {e}")

@router.post("/models")
def register_model(body: RegisterModelRequest):
    try:
        model = backend.register_model(body.model_dump())
        return json.loads(json.dumps(model, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to register model: {e}")

@router.put("/models/{model_id}/status")
def update_model_status(model_id: str, body: UpdateModelStatusRequest):
    try:
        model = backend.update_model_status(model_id, body.status, body.user, body.comment)
        return json.loads(json.dumps(model, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to update model status: {e}")

@router.post("/models/{model_id}/promote")
def promote_champion(model_id: str, body: PromoteChampionRequest):
    try:
        model = backend.promote_champion(model_id, body.user)
        return json.loads(json.dumps(model, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to promote champion: {e}")

@router.post("/models/compare")
def compare_models(body: CompareModelsRequest):
    try:
        models = backend.compare_models(body.model_ids)
        return json.loads(json.dumps(models, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to compare models: {e}")

@router.get("/models/{model_id}/audit")
def get_model_audit(model_id: str):
    try:
        trail = backend.get_model_audit_trail(model_id)
        return json.loads(json.dumps(trail, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to get audit trail: {e}")
