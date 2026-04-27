"""Attribution / waterfall routes — /api/data/attribution/*"""

import json
import logging

import backend
from fastapi import APIRouter, HTTPException

from routes._utils import DecimalEncoder

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["attribution"])


@router.get("/attribution/{project_id}")
def get_attribution(project_id: str):
    try:
        attr = backend.get_attribution(project_id)
        if attr is None:
            return None
        return json.loads(json.dumps(attr, cls=DecimalEncoder))
    except Exception as e:
        log.exception("Failed to get attribution")
        raise HTTPException(500, f"Failed to get attribution: {e}")


@router.post("/attribution/{project_id}/compute")
def compute_attribution(project_id: str):
    try:
        attr = backend.compute_attribution(project_id)
        return json.loads(json.dumps(attr, cls=DecimalEncoder))
    except Exception as e:
        log.exception("Failed to compute attribution")
        raise HTTPException(500, f"Failed to compute attribution: {e}")


@router.get("/attribution/{project_id}/history")
def attribution_history(project_id: str):
    try:
        history = backend.get_attribution_history(project_id)
        return json.loads(json.dumps(history, cls=DecimalEncoder))
    except Exception as e:
        log.exception("Failed to get attribution history")
        raise HTTPException(500, f"Failed to get attribution history: {e}")
