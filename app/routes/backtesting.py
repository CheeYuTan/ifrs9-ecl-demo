"""Backtesting routes — /api/backtest/*"""
import json, logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import backend
from routes._utils import DecimalEncoder

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtesting"])


class RunBacktestRequest(BaseModel):
    model_type: str = "PD"
    config: dict = {}


@router.post("/run")
def run_backtest(body: RunBacktestRequest):
    try:
        result = backend.run_backtest(body.model_type, body.config)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log.exception("Failed to run backtest")
        raise HTTPException(500, f"Failed to run backtest: {e}")

@router.get("/results")
def list_backtests(model_type: Optional[str] = None):
    try:
        results = backend.list_backtests(model_type)
        return json.loads(json.dumps(results, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list backtests: {e}")

@router.get("/trend/{model_type}")
def backtest_trend(model_type: str):
    try:
        trend = backend.get_backtest_trend(model_type)
        return json.loads(json.dumps(trend, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to get backtest trend: {e}")

@router.get("/{backtest_id}")
def get_backtest(backtest_id: str):
    try:
        result = backend.get_backtest(backtest_id)
        if not result:
            raise HTTPException(404, "Backtest not found")
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get backtest: {e}")
