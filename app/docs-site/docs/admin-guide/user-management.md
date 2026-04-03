---
sidebar_position: 8
title: "User Management"
description: "Managing users, roles, permissions, and approval workflows."
---

# User Management

The IFRS 9 ECL Platform includes a role-based access control (RBAC) system that governs who can create models, submit results for review, approve ECL calculations, and manage platform configuration. This page covers the role hierarchy, permission model, approval workflows, authentication flow, and data integrity controls.

:::info Who Should Read This
System administrators responsible for managing user accounts, assigning roles, and understanding the platform's access control model.
:::

## Role Hierarchy

The platform defines four roles, each building on the permissions of the previous one. Every user is assigned exactly one role.

### Analyst

The base role for day-to-day ECL work. Analysts can create and run models but cannot submit results for formal review or approval.

**Permissions:**
- `create_models` -- Create and configure PD, LGD, and EAD models
- `run_backtests` -- Execute backtesting against historical data
- `generate_journals` -- Generate accounting journal entries
- `create_overlays` -- Create management overlays and post-model adjustments
- `view_portfolio` -- View portfolio data and loan-level details
- `view_reports` -- Access dashboards and reporting outputs

### Reviewer

Reviewers have all analyst permissions plus the ability to submit work for approval and perform model validation reviews.

**Additional permissions:**
- `submit_for_approval` -- Submit models, overlays, or ECL results into the approval workflow
- `review_models` -- Perform independent model validation reviews
- `review_overlays` -- Review and comment on management overlays

### Approver

Approvers have all reviewer permissions plus the authority to approve or reject requests, sign off on projects, and post journal entries to the general ledger.

**Additional permissions:**
- `approve_requests` -- Approve pending approval requests
- `reject_requests` -- Reject pending approval requests with a reason
- `sign_off_projects` -- Lock a project as signed off (making it immutable)
- `post_journals` -- Post finalized journal entries

### Admin

Admins have all approver permissions plus full platform management capabilities.

**Additional permissions:**
- `manage_users` -- Create, modify, and deactivate user accounts
- `manage_config` -- Modify platform configuration settings
- `manage_roles` -- Change user role assignments

## Complete Permission Matrix

| Permission | Analyst | Reviewer | Approver | Admin |
|-----------|---------|----------|----------|-------|
| `create_models` | Yes | Yes | Yes | Yes |
| `run_backtests` | Yes | Yes | Yes | Yes |
| `generate_journals` | Yes | Yes | Yes | Yes |
| `create_overlays` | Yes | Yes | Yes | Yes |
| `view_portfolio` | Yes | Yes | Yes | Yes |
| `view_reports` | Yes | Yes | Yes | Yes |
| `submit_for_approval` | -- | Yes | Yes | Yes |
| `review_models` | -- | Yes | Yes | Yes |
| `review_overlays` | -- | Yes | Yes | Yes |
| `approve_requests` | -- | -- | Yes | Yes |
| `reject_requests` | -- | -- | Yes | Yes |
| `sign_off_projects` | -- | -- | Yes | Yes |
| `post_journals` | -- | -- | Yes | Yes |
| `manage_users` | -- | -- | -- | Yes |
| `manage_config` | -- | -- | -- | Yes |
| `manage_roles` | -- | -- | -- | Yes |

## Seed Users

The platform initializes with four seed users that represent one user per role. These are created automatically when the RBAC tables are first initialized.

| User ID | Name | Email | Role | Department |
|---------|------|-------|------|------------|
| `usr-001` | Ana Reyes | ana.reyes@bank.com | analyst | Credit Risk Analytics |
| `usr-002` | David Kim | david.kim@bank.com | reviewer | Model Validation |
| `usr-003` | Sarah Chen | sarah.chen@bank.com | approver | Risk Committee |
| `usr-004` | Admin User | admin@bank.com | admin | IT Administration |

Seed users are inserted with `ON CONFLICT DO NOTHING`, so re-running initialization never overwrites modified accounts.

:::tip
In production, replace the seed users with real accounts that map to your organization's identity provider. The seed users are intended for initial setup and demonstration only.
:::

## RBAC Database Tables

### `rbac_users`

Stores all user accounts. Each user has a unique `user_id` that is used as the identity key throughout the platform.

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | TEXT (PK) | Unique user identifier (e.g., `usr-001`). |
| `email` | TEXT | User's email address. |
| `display_name` | TEXT | Human-readable name shown in the UI and audit logs. |
| `role` | TEXT | One of: `analyst`, `reviewer`, `approver`, `admin`. Default: `analyst`. |
| `department` | TEXT | Organizational department. Used for display and filtering. |
| `is_active` | BOOLEAN | Soft-delete flag. Inactive users cannot authenticate. Default: `TRUE`. |
| `created_at` | TIMESTAMP | Account creation timestamp. |

### `rbac_approval_requests`

Tracks all approval workflow requests from creation through resolution.

| Column | Type | Description |
|--------|------|-------------|
| `request_id` | TEXT (PK) | Auto-generated ID (format: `apr-{8-char-hex}`). |
| `request_type` | TEXT | Type of approval (e.g., `model_approval`, `overlay_approval`, `ecl_sign_off`). |
| `entity_id` | TEXT | The ID of the entity being approved (model ID, project ID, etc.). |
| `entity_type` | TEXT | The type of entity (e.g., `model`, `overlay`, `project`). |
| `status` | TEXT | Current status: `pending`, `approved`, or `rejected`. |
| `requested_by` | TEXT | User ID of the person who submitted the request. |
| `assigned_to` | TEXT | User ID of the designated reviewer/approver. |
| `approved_by` | TEXT | User ID of the person who approved or rejected. |
| `approved_at` | TIMESTAMP | When the approval decision was made. |
| `rejection_reason` | TEXT | Reason provided when rejecting a request. |
| `comments` | TEXT | General comments attached to the request. |
| `priority` | TEXT | Request priority: `low`, `normal`, `high`, `critical`. Default: `normal`. |
| `due_date` | DATE | Optional deadline for the approval decision. |
| `created_at` | TIMESTAMP | Request creation timestamp. |

## Approval Workflow

The approval workflow follows a linear lifecycle from creation to resolution.

### Workflow States

```
  pending ──────► approved
     │
     └──────────► rejected
```

1. **Create** -- A reviewer or approver submits a request via `POST /api/rbac/approvals`. The request is created with `status: pending`.
2. **Approve** -- An approver (or admin) calls `POST /api/rbac/approvals/{request_id}/approve`. The platform verifies the user has `approve_requests` permission before updating the status.
3. **Reject** -- An approver (or admin) calls `POST /api/rbac/approvals/{request_id}/reject` with a `reason`. The platform verifies the user has `reject_requests` permission.

Requests that are already approved or rejected cannot be modified. Attempting to approve or reject a non-pending request returns an error.

### Querying Approval Requests

```
GET /api/rbac/approvals
```

Query parameters:
- `status` -- Filter by `pending`, `approved`, or `rejected`
- `assigned_to` -- Filter by the assigned reviewer's user ID
- `request_type` -- Filter by approval type

Results include joined display names for `requested_by`, `assigned_to`, and `approved_by` fields.

## Authentication Middleware

The platform supports two authentication methods, selected automatically based on the request headers present.

### Databricks Apps OAuth (Production)

When deployed as a Databricks App, the OAuth proxy injects an `X-Forwarded-User` header into every authenticated request. The middleware extracts this value and resolves it against the `rbac_users` table.

```
X-Forwarded-User: usr-003
```

### Development Header (Local Testing)

For local development and testing without Databricks OAuth, the `X-User-Id` header simulates authentication:

```
X-User-Id: usr-001
```

### Anonymous Fallback

If no authentication header is present, the user is treated as anonymous with the `analyst` role. This allows unauthenticated access during development while enforcing RBAC in production where the OAuth proxy guarantees a user header is present.

```json
{
  "user_id": "anonymous",
  "email": "anonymous@local",
  "display_name": "Anonymous User",
  "role": "analyst",
  "permissions": []
}
```

:::warning
In production, ensure the Databricks Apps OAuth proxy is correctly configured so that every request includes the `X-Forwarded-User` header. Without it, all users are treated as anonymous analysts and RBAC is effectively bypassed.
:::

## Permission Check Dependency

Route handlers that require specific permissions use the `require_permission` FastAPI dependency:

```python
from middleware.auth import require_permission

@router.post("/approvals/{request_id}/approve")
def approve(request_id: str, user=Depends(require_permission("approve_requests"))):
    return rbac.approve_request(request_id, user["user_id"])
```

When the dependency fires:

1. It checks for an authentication header (`X-Forwarded-User` or `X-User-Id`).
2. If no header is present, it returns the anonymous user (RBAC bypass for development).
3. If a header is present, it resolves the user from the database and checks their role's permission set.
4. If the user's role does not include the required permission, an HTTP 403 is returned:

```json
{
  "detail": "Permission denied: role 'analyst' does not have 'approve_requests' permission"
}
```

## Segregation of Duties

### Project Lock Protection

The `require_project_not_locked` dependency prevents modifications to signed-off projects:

```python
from middleware.auth import require_project_not_locked

@router.put("/projects/{project_id}/models")
def update_model(project_id: str, _=Depends(require_project_not_locked())):
    ...
```

If the project has been signed off, any mutation attempt returns:

```json
{
  "detail": "Project proj-abc123 is signed off and immutable. No modifications allowed."
}
```

This enforces the IFRS 9 requirement that finalized ECL calculations cannot be retroactively altered.

## ECL Data Integrity

### Hash-Based Verification

The platform provides two functions for verifying that ECL results have not been modified after sign-off:

**`compute_ecl_hash(ecl_data: dict) -> str`**

Computes a SHA-256 hash of the ECL results dictionary. The data is serialized to JSON with sorted keys to ensure deterministic hashing.

**`verify_ecl_hash(ecl_data: dict, expected_hash: str) -> bool`**

Recomputes the hash of the current ECL data and compares it against the hash stored at sign-off time. Returns `True` if the data is unmodified, `False` if any value has changed.

```python
from middleware.auth import compute_ecl_hash, verify_ecl_hash

# At sign-off time
hash_value = compute_ecl_hash(ecl_results)
# Store hash_value alongside the signed-off project

# At verification time
is_valid = verify_ecl_hash(ecl_results, stored_hash)
```

This mechanism ensures that auditors can independently verify that the ECL numbers presented in financial statements match the numbers that were approved during the sign-off process.

## Managing Users via API

### List Users

```
GET /api/rbac/users
GET /api/rbac/users?role=approver
```

### Get User Details

```
GET /api/rbac/users/{user_id}
```

Returns the user record with their full permission set resolved from their role.

### Check Permission

```
GET /api/rbac/check-permission?user_id=usr-001&action=approve_requests
```

Returns:

```json
{
  "allowed": false,
  "user_id": "usr-001",
  "role": "analyst",
  "action": "approve_requests",
  "reason": "Role 'analyst' does not have permission 'approve_requests'"
}
```

## Best Practices

1. **Principle of least privilege** -- Assign users the minimum role required for their responsibilities. Most users should be analysts.
2. **Separate approvers from modelers** -- The person who creates an ECL model should not be the same person who approves it. Use the reviewer and approver roles to enforce this separation.
3. **Deactivate rather than delete** -- Set `is_active = FALSE` for departed users rather than deleting their records. This preserves the audit trail's referential integrity.
4. **Audit role changes** -- All role modifications are recorded in the audit trail. Review the audit log periodically to verify that role assignments follow your organization's access control policy.
5. **Test with seed users** -- Use the four seed users during development to verify that RBAC enforcement works correctly across all roles before deploying to production.
