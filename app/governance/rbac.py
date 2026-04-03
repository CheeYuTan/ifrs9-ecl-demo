import uuid
import logging
import pandas as pd

from db.pool import query_df, execute, SCHEMA

log = logging.getLogger(__name__)

RBAC_USERS_TABLE = f"{SCHEMA}.rbac_users"
RBAC_APPROVALS_TABLE = f"{SCHEMA}.rbac_approval_requests"

ROLE_PERMISSIONS = {
    "analyst": {
        "create_models", "run_backtests", "generate_journals", "create_overlays",
        "view_portfolio", "view_reports",
    },
    "reviewer": {
        "create_models", "run_backtests", "generate_journals", "create_overlays",
        "view_portfolio", "view_reports",
        "submit_for_approval", "review_models", "review_overlays",
    },
    "approver": {
        "create_models", "run_backtests", "generate_journals", "create_overlays",
        "view_portfolio", "view_reports",
        "submit_for_approval", "review_models", "review_overlays",
        "approve_requests", "reject_requests", "sign_off_projects", "post_journals",
    },
    "admin": {
        "create_models", "run_backtests", "generate_journals", "create_overlays",
        "view_portfolio", "view_reports",
        "submit_for_approval", "review_models", "review_overlays",
        "approve_requests", "reject_requests", "sign_off_projects", "post_journals",
        "manage_users", "manage_config", "manage_roles",
    },
}

SEED_USERS = [
    ("usr-001", "ana.reyes@bank.com", "Ana Reyes", "analyst", "Credit Risk Analytics"),
    ("usr-002", "david.kim@bank.com", "David Kim", "reviewer", "Model Validation"),
    ("usr-003", "sarah.chen@bank.com", "Sarah Chen", "approver", "Risk Committee"),
    ("usr-004", "admin@bank.com", "Admin User", "admin", "IT Administration"),
]


def ensure_rbac_tables():
    execute(f"""
        CREATE TABLE IF NOT EXISTS {RBAC_USERS_TABLE} (
            user_id       TEXT PRIMARY KEY,
            email         TEXT NOT NULL,
            display_name  TEXT NOT NULL,
            role          TEXT NOT NULL DEFAULT 'analyst',
            department    TEXT DEFAULT '',
            is_active     BOOLEAN DEFAULT TRUE,
            created_at    TIMESTAMP DEFAULT NOW()
        )
    """)
    execute(f"""
        CREATE TABLE IF NOT EXISTS {RBAC_APPROVALS_TABLE} (
            request_id      TEXT PRIMARY KEY,
            request_type    TEXT NOT NULL,
            entity_id       TEXT NOT NULL,
            entity_type     TEXT DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'pending',
            requested_by    TEXT NOT NULL,
            assigned_to     TEXT,
            approved_by     TEXT,
            approved_at     TIMESTAMP,
            rejection_reason TEXT DEFAULT '',
            comments        TEXT DEFAULT '',
            priority        TEXT DEFAULT 'normal',
            due_date        DATE,
            created_at      TIMESTAMP DEFAULT NOW()
        )
    """)
    for uid, email, name, role, dept in SEED_USERS:
        execute(f"""
            INSERT INTO {RBAC_USERS_TABLE} (user_id, email, display_name, role, department)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
        """, (uid, email, name, role, dept))
    log.info("Ensured RBAC tables and seed users")


def list_users(role: str | None = None) -> list[dict]:
    sql = f"SELECT * FROM {RBAC_USERS_TABLE} WHERE is_active = TRUE"
    params: tuple = ()
    if role:
        sql += " AND role = %s"
        params = (role,)
    sql += " ORDER BY display_name"
    df = query_df(sql, params or None)
    return df.to_dict("records")


def get_user(user_id: str) -> dict | None:
    df = query_df(f"SELECT * FROM {RBAC_USERS_TABLE} WHERE user_id = %s", (user_id,))
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    row["permissions"] = list(ROLE_PERMISSIONS.get(row.get("role", "analyst"), set()))
    return row


def check_permission(user_id: str, action: str) -> dict:
    user = get_user(user_id)
    if not user:
        return {"allowed": False, "reason": "User not found"}
    role = user.get("role", "analyst")
    perms = ROLE_PERMISSIONS.get(role, set())
    allowed = action in perms
    return {
        "allowed": allowed,
        "user_id": user_id,
        "role": role,
        "action": action,
        "reason": "" if allowed else f"Role '{role}' does not have permission '{action}'",
    }


def create_approval_request(data: dict) -> dict:
    req_id = f"apr-{uuid.uuid4().hex[:8]}"
    execute(f"""
        INSERT INTO {RBAC_APPROVALS_TABLE}
            (request_id, request_type, entity_id, entity_type, status,
             requested_by, assigned_to, priority, due_date, comments)
        VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s, %s, %s)
    """, (
        req_id,
        data.get("request_type", "model_approval"),
        data.get("entity_id", ""),
        data.get("entity_type", ""),
        data.get("requested_by", ""),
        data.get("assigned_to"),
        data.get("priority", "normal"),
        data.get("due_date"),
        data.get("comments", ""),
    ))
    return get_approval_request(req_id)


def get_approval_request(request_id: str) -> dict | None:
    df = query_df(f"""
        SELECT a.*, u1.display_name AS requested_by_name, u2.display_name AS assigned_to_name,
               u3.display_name AS approved_by_name
        FROM {RBAC_APPROVALS_TABLE} a
        LEFT JOIN {RBAC_USERS_TABLE} u1 ON a.requested_by = u1.user_id
        LEFT JOIN {RBAC_USERS_TABLE} u2 ON a.assigned_to = u2.user_id
        LEFT JOIN {RBAC_USERS_TABLE} u3 ON a.approved_by = u3.user_id
        WHERE a.request_id = %s
    """, (request_id,))
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def list_approval_requests(status: str | None = None, assigned_to: str | None = None,
                           request_type: str | None = None) -> list[dict]:
    sql = f"""
        SELECT a.*, u1.display_name AS requested_by_name, u2.display_name AS assigned_to_name,
               u3.display_name AS approved_by_name
        FROM {RBAC_APPROVALS_TABLE} a
        LEFT JOIN {RBAC_USERS_TABLE} u1 ON a.requested_by = u1.user_id
        LEFT JOIN {RBAC_USERS_TABLE} u2 ON a.assigned_to = u2.user_id
        LEFT JOIN {RBAC_USERS_TABLE} u3 ON a.approved_by = u3.user_id
        WHERE 1=1
    """
    params: list = []
    if status:
        sql += " AND a.status = %s"
        params.append(status)
    if assigned_to:
        sql += " AND a.assigned_to = %s"
        params.append(assigned_to)
    if request_type:
        sql += " AND a.request_type = %s"
        params.append(request_type)
    sql += " ORDER BY a.created_at DESC"
    df = query_df(sql, tuple(params) if params else None)
    return df.to_dict("records")


def approve_request(request_id: str, user_id: str, comment: str = "") -> dict:
    perm = check_permission(user_id, "approve_requests")
    if not perm["allowed"]:
        raise ValueError(perm["reason"])
    req = get_approval_request(request_id)
    if not req:
        raise ValueError("Approval request not found")
    if req["status"] != "pending":
        raise ValueError(f"Request is already {req['status']}")
    execute(f"""
        UPDATE {RBAC_APPROVALS_TABLE}
        SET status = 'approved', approved_by = %s, approved_at = NOW(), comments = %s
        WHERE request_id = %s
    """, (user_id, comment, request_id))
    return get_approval_request(request_id)


def reject_request(request_id: str, user_id: str, reason: str = "") -> dict:
    perm = check_permission(user_id, "reject_requests")
    if not perm["allowed"]:
        raise ValueError(perm["reason"])
    req = get_approval_request(request_id)
    if not req:
        raise ValueError("Approval request not found")
    if req["status"] != "pending":
        raise ValueError(f"Request is already {req['status']}")
    execute(f"""
        UPDATE {RBAC_APPROVALS_TABLE}
        SET status = 'rejected', approved_by = %s, approved_at = NOW(), rejection_reason = %s
        WHERE request_id = %s
    """, (user_id, reason, request_id))
    return get_approval_request(request_id)


def get_approval_history(entity_id: str) -> list[dict]:
    df = query_df(f"""
        SELECT a.*, u1.display_name AS requested_by_name, u2.display_name AS approved_by_name
        FROM {RBAC_APPROVALS_TABLE} a
        LEFT JOIN {RBAC_USERS_TABLE} u1 ON a.requested_by = u1.user_id
        LEFT JOIN {RBAC_USERS_TABLE} u2 ON a.approved_by = u2.user_id
        WHERE a.entity_id = %s
        ORDER BY a.created_at DESC
    """, (entity_id,))
    return df.to_dict("records")
