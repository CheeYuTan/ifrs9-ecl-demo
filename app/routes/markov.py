"""Markov chain routes — /api/markov/*"""

import json
import logging

import backend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from routes._utils import DecimalEncoder

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/markov", tags=["markov"])


class MarkovEstimateRequest(BaseModel):
    product_type: str | None = Field(default=None, max_length=128)
    segment: str | None = Field(default=None, max_length=128)


class MarkovForecastRequest(BaseModel):
    matrix_id: str = Field(min_length=1, max_length=128)
    initial_distribution: list[float] = Field(min_length=1, max_length=20)
    horizon_months: int = Field(default=60, ge=1, le=360)


class MarkovCompareRequest(BaseModel):
    matrix_ids: list[str] = Field(min_length=2, max_length=10)


@router.post("/estimate")
def markov_estimate(body: MarkovEstimateRequest):
    try:
        result = backend.estimate_transition_matrix(body.product_type, body.segment)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except Exception as e:
        log.exception("Failed to estimate transition matrix")
        raise HTTPException(500, f"Failed to estimate transition matrix: {e}")


@router.get("/matrices")
def markov_list_matrices(product_type: str | None = None):
    try:
        matrices = backend.list_transition_matrices(product_type)
        return json.loads(json.dumps(matrices, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list matrices: {e}")


@router.get("/matrix/{matrix_id}")
def markov_get_matrix(matrix_id: str):
    try:
        mat = backend.get_transition_matrix(matrix_id)
        if not mat:
            raise HTTPException(404, "Matrix not found")
        return json.loads(json.dumps(mat, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get matrix: {e}")


@router.post("/forecast")
def markov_forecast(body: MarkovForecastRequest):
    try:
        result = backend.forecast_stage_distribution(body.matrix_id, body.initial_distribution, body.horizon_months)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        log.exception("Failed to forecast stage distribution")
        raise HTTPException(500, f"Failed to forecast: {e}")


@router.get("/lifetime-pd/{matrix_id}")
def markov_lifetime_pd(matrix_id: str, max_months: int = 60):
    try:
        result = backend.compute_lifetime_pd(matrix_id, max_months)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        log.exception("Failed to compute lifetime PD")
        raise HTTPException(500, f"Failed to compute lifetime PD: {e}")


@router.post("/compare")
def markov_compare(body: MarkovCompareRequest):
    try:
        results = backend.compare_matrices(body.matrix_ids)
        return json.loads(json.dumps(results, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to compare matrices: {e}")
