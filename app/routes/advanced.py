"""Advanced ECL feature routes — /api/advanced/*"""

import json
import logging

import backend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from routes._utils import DecimalEncoder

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advanced", tags=["advanced"])


class ComputeCureRatesRequest(BaseModel):
    product_type: str | None = Field(default=None, max_length=128)


class ComputeCCFRequest(BaseModel):
    product_type: str | None = Field(default=None, max_length=128)


class ComputeCollateralRequest(BaseModel):
    product_type: str | None = Field(default=None, max_length=128)


@router.post("/cure-rates/compute")
def compute_cure_rates(body: ComputeCureRatesRequest):
    try:
        result = backend.compute_cure_rates(body.product_type)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except Exception as e:
        log.exception("Failed to compute cure rates")
        raise HTTPException(500, f"Failed to compute cure rates: {e}")


@router.get("/cure-rates")
def list_cure_analyses():
    try:
        return json.loads(json.dumps(backend.list_cure_analyses(), cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list cure analyses: {e}")


@router.get("/cure-rates/{analysis_id}")
def get_cure_analysis(analysis_id: str):
    try:
        result = backend.get_cure_analysis(analysis_id)
        if not result:
            raise HTTPException(404, "Cure rate analysis not found")
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get cure analysis: {e}")


@router.post("/ccf/compute")
def compute_ccf(body: ComputeCCFRequest):
    try:
        result = backend.compute_ccf(body.product_type)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except Exception as e:
        log.exception("Failed to compute CCF")
        raise HTTPException(500, f"Failed to compute CCF: {e}")


@router.get("/ccf")
def list_ccf_analyses():
    try:
        return json.loads(json.dumps(backend.list_ccf_analyses(), cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list CCF analyses: {e}")


@router.get("/ccf/{analysis_id}")
def get_ccf_analysis(analysis_id: str):
    try:
        result = backend.get_ccf_analysis(analysis_id)
        if not result:
            raise HTTPException(404, "CCF analysis not found")
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get CCF analysis: {e}")


@router.post("/collateral/compute")
def compute_collateral(body: ComputeCollateralRequest):
    try:
        result = backend.compute_collateral_haircuts(body.product_type)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except Exception as e:
        log.exception("Failed to compute collateral haircuts")
        raise HTTPException(500, f"Failed to compute collateral haircuts: {e}")


@router.get("/collateral")
def list_collateral_analyses():
    try:
        return json.loads(json.dumps(backend.list_collateral_analyses(), cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list collateral analyses: {e}")


@router.get("/collateral/{analysis_id}")
def get_collateral_analysis(analysis_id: str):
    try:
        result = backend.get_collateral_analysis(analysis_id)
        if not result:
            raise HTTPException(404, "Collateral analysis not found")
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get collateral analysis: {e}")
