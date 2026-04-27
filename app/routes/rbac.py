"""RBAC & approval workflow routes — /api/rbac/*"""

import json

import backend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from routes._utils import DecimalEncoder

router = APIRouter(prefix="/api/rbac", tags=["rbac"])


class CreateApprovalRequest(BaseModel):
    request_type: str = Field(min_length=1, max_length=64)
    entity_id: str = Field(min_length=1, max_length=128)
    entity_type: str = Field(default="", max_length=64)
    requested_by: str = Field(min_length=1, max_length=256)
    assigned_to: str | None = Field(default=None, max_length=256)
    priority: str = Field(default="normal", pattern=r"^(low|normal|high|critical)$")
    due_date: str | None = Field(default=None, max_length=32)
    comments: str = Field(default="", max_length=2000)


class ApproveRejectRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=256)
    comment: str = Field(default="", max_length=2000)


@router.get("/users")
def rbac_list_users(role: str | None = None):
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
def rbac_list_approvals(status: str | None = None, assigned_to: str | None = None, type: str | None = None):
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
