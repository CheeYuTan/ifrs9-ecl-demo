"""Hazard model routes — /api/hazard/*"""

import json
import logging

import backend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from routes._utils import DecimalEncoder

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hazard", tags=["hazard"])


class EstimateHazardRequest(BaseModel):
    model_type: str = Field(min_length=1, max_length=64)
    product_type: str | None = Field(default=None, max_length=128)
    segment: str | None = Field(default=None, max_length=128)


class SurvivalCurveRequest(BaseModel):
    model_id: str = Field(min_length=1, max_length=128)
    covariates: dict | None = None


class CompareHazardRequest(BaseModel):
    model_ids: list[str] = Field(min_length=2, max_length=10)


@router.post("/estimate")
def hazard_estimate(body: EstimateHazardRequest):
    try:
        result = backend.estimate_hazard_model(body.model_type, body.product_type, body.segment)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log.exception("Failed to estimate hazard model")
        raise HTTPException(500, f"Failed to estimate hazard model: {e}")


@router.get("/models")
def hazard_list_models(model_type: str | None = None, product_type: str | None = None):
    try:
        models = backend.list_hazard_models(model_type, product_type)
        return json.loads(json.dumps(models, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list hazard models: {e}")


@router.get("/model/{model_id}")
def hazard_get_model(model_id: str):
    try:
        model = backend.get_hazard_model(model_id)
        if not model:
            raise HTTPException(404, "Hazard model not found")
        return json.loads(json.dumps(model, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get hazard model: {e}")


@router.post("/survival-curve")
def hazard_survival_curve(body: SurvivalCurveRequest):
    try:
        result = backend.compute_survival_curve(body.model_id, body.covariates)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to compute survival curve: {e}")


@router.get("/term-structure/{model_id}")
def hazard_term_structure(model_id: str, max_months: int = 60):
    try:
        result = backend.compute_term_structure_pd(model_id, max_months)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to compute term structure: {e}")


@router.post("/compare")
def hazard_compare(body: CompareHazardRequest):
    try:
        result = backend.compare_hazard_models(body.model_ids)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to compare hazard models: {e}")
