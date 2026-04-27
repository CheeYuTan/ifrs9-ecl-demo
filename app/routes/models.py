"""Model registry routes — /api/models/*"""

import json

import backend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from routes._utils import DecimalEncoder

router = APIRouter(prefix="/api", tags=["models"])


class RegisterModelRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=256)
    model_type: str = Field(min_length=1, max_length=64)
    algorithm: str = Field(default="Unknown", max_length=128)
    version: int = Field(default=1, ge=1, le=9999)
    description: str = Field(default="", max_length=2000)
    product_type: str = Field(default="", max_length=128)
    cohort: str = Field(default="", max_length=128)
    parameters: dict = {}
    performance_metrics: dict = {}
    training_data_info: dict = {}
    created_by: str = Field(default="system", max_length=256)
    notes: str = Field(default="", max_length=4000)
    parent_model_id: str | None = Field(default=None, max_length=128)


class UpdateModelStatusRequest(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    user: str = Field(min_length=1, max_length=256)
    comment: str = Field(default="", max_length=2000)


class CompareModelsRequest(BaseModel):
    model_ids: list[str] = Field(min_length=2, max_length=10)


class PromoteChampionRequest(BaseModel):
    user: str = Field(min_length=1, max_length=256)


@router.get("/models")
def list_models(model_type: str | None = None, status: str | None = None):
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
