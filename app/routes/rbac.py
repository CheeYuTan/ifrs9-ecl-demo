"""RBAC & approval workflow routes — /api/rbac/*"""
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import backend
from routes._utils import DecimalEncoder

router = APIRouter(prefix="/api/rbac", tags=["rbac"])


class CreateApprovalRequest(BaseModel):
    request_type: str
    entity_id: str
    entity_type: str = ""
    requested_by: str
    assigned_to: Optional[str] = None
    priority: str = "normal"
    due_date: Optional[str] = None
    comments: str = ""

class ApproveRejectRequest(BaseModel):
    user_id: str
    comment: str = ""


@router.get("/users")
def rbac_list_users(role: Optional[str] = None):
    try:
        users = backend.list_users(role)
        return json.loads(json.dumps(users, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list users: {e}")

@router.get("/users/{user_id}")
def rbac_get_user(user_id: str):
    try:
        user = backend.get_user(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        return json.loads(json.dumps(user, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get user: {e}")

@router.get("/approvals")
def rbac_list_approvals(status: Optional[str] = None, assigned_to: Optional[str] = None, type: Optional[str] = None):
    try:
        approvals = backend.list_approval_requests(status, assigned_to, type)
        return json.loads(json.dumps(approvals, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list approvals: {e}")

@router.post("/approvals")
def rbac_create_approval(body: CreateApprovalRequest):
    try:
        req = backend.create_approval_request(body.model_dump())
        return json.loads(json.dumps(req, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to create approval: {e}")

@router.post("/approvals/{request_id}/approve")
def rbac_approve(request_id: str, body: ApproveRejectRequest):
    try:
        req = backend.approve_request(request_id, body.user_id, body.comment)
        return json.loads(json.dumps(req, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to approve: {e}")

@router.post("/approvals/{request_id}/reject")
def rbac_reject(request_id: str, body: ApproveRejectRequest):
    try:
        req = backend.reject_request(request_id, body.user_id, body.comment)
        return json.loads(json.dumps(req, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to reject: {e}")

@router.get("/approvals/history/{entity_id}")
def rbac_approval_history(entity_id: str):
    try:
        history = backend.get_approval_history(entity_id)
        return json.loads(json.dumps(history, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to get approval history: {e}")

@router.get("/permissions/{user_id}")
def rbac_check_permissions(user_id: str):
    try:
        user = backend.get_user(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        return {
            "user_id": user_id,
            "role": user["role"],
            "permissions": user["permissions"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to check permissions: {e}")
