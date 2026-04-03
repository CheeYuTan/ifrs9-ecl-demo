---
sidebar_position: 8
title: "User Management"
description: "Managing users, roles, permissions, and approval workflows."
---

# User Management

The IFRS 9 ECL Platform includes a role-based access control (RBAC) system that governs who can create models, submit results for review, approve ECL calculations, and manage platform configuration. This page covers the role hierarchy, permission model, approval workflows, authentication, and data integrity controls.

:::info Who Should Read This
System administrators responsible for managing user accounts, assigning roles, and configuring the platform's access control model.
:::

## Role Hierarchy

The platform defines four roles, each building on the permissions of the previous one. Every user is assigned exactly one role.

### Analyst

The base role for day-to-day ECL work. Analysts can create and run models but cannot submit results for formal review or approval.

**Permissions:** Create models, run backtests, generate journal entries, create overlays, view portfolio data, and access reports.

### Reviewer

Reviewers have all analyst permissions plus the ability to submit work for approval and perform model validation reviews.

**Additional permissions:** Submit items for approval, review models, and review overlays.

### Approver

Approvers have all reviewer permissions plus the authority to approve or reject requests, sign off on projects, and post journal entries to the general ledger.

**Additional permissions:** Approve or reject requests, sign off projects (making them immutable), and post journal entries.

### Admin

Admins have all approver permissions plus full platform management capabilities.

**Additional permissions:** Manage user accounts, modify platform configuration, and change role assignments.

## Complete Permission Matrix

| Permission | Analyst | Reviewer | Approver | Admin |
|-----------|:-------:|:--------:|:--------:|:-----:|
| Create models and run backtests | Yes | Yes | Yes | Yes |
| Generate journals and create overlays | Yes | Yes | Yes | Yes |
| View portfolio data and reports | Yes | Yes | Yes | Yes |
| Submit items for approval | -- | Yes | Yes | Yes |
| Review models and overlays | -- | Yes | Yes | Yes |
| Approve or reject requests | -- | -- | Yes | Yes |
| Sign off projects and post journals | -- | -- | Yes | Yes |
| Manage users, roles, and configuration | -- | -- | -- | Yes |

## Seed Users

The platform initializes with four seed users — one per role — created automatically on first startup. These are intended for initial setup and demonstration.

| User ID | Name | Email | Role | Department |
|---------|------|-------|------|------------|
| usr-001 | Ana Reyes | ana.reyes@bank.com | Analyst | Credit Risk Analytics |
| usr-002 | David Kim | david.kim@bank.com | Reviewer | Model Validation |
| usr-003 | Sarah Chen | sarah.chen@bank.com | Approver | Risk Committee |
| usr-004 | Admin User | admin@bank.com | Admin | IT Administration |

Re-running initialization never overwrites accounts that have been modified — seed users are only created if they do not already exist.

:::tip
In production, replace the seed users with real accounts that map to your organization's identity provider. The seed users are intended for initial setup and demonstration only.
:::

## User Account Fields

Each user account contains the following information:

| Field | Description |
|-------|-------------|
| **User ID** | Unique identifier (e.g., `usr-001`). Used throughout the platform for audit trail and permission checks. |
| **Email** | User's email address. |
| **Display Name** | Human-readable name shown in the UI, reports, and audit logs. |
| **Role** | One of: Analyst, Reviewer, Approver, Admin. Determines the user's permission set. |
| **Department** | Organizational department. Used for display and filtering. |
| **Active Status** | Whether the account is active. Inactive users cannot authenticate. |
| **Created At** | Timestamp of account creation. |

## Managing Users

Navigate to **Admin > User Management** to view, create, and modify user accounts.

### Creating a New User

1. Navigate to the User Management page
2. Click **Add User**
3. Fill in the user ID, email, display name, department, and role
4. Click **Save**

The new user can immediately authenticate and access the platform with the permissions defined by their assigned role.

### Deactivating a User

To remove a user's access without deleting their records:

1. Navigate to the user's profile on the User Management page
2. Set the **Active** status to **Inactive**
3. Click **Save**

:::warning
Always deactivate users rather than deleting them. Deactivation preserves the audit trail's referential integrity — the user's name will still appear correctly in historical audit entries and approval records.
:::

### Changing a User's Role

1. Navigate to the user's profile on the User Management page
2. Change the **Role** dropdown to the new role
3. Click **Save**

Role changes take effect immediately. The change is recorded in the audit trail with the administrator's identity and timestamp.

## Approval Workflow

The approval workflow follows a maker-checker pattern. For full details on how the approval workflow operates from a user's perspective, see [Approval Workflow](../user-guide/approval-workflow).

### Workflow Lifecycle

Every approval request follows a simple lifecycle:

1. **Created** — A reviewer or approver submits a request. The request enters **Pending** status.
2. **Approved** — An approver (or admin) reviews and approves the request. The associated action (model promotion, journal posting, sign-off) is executed.
3. **Rejected** — An approver (or admin) reviews and rejects the request with a documented reason. The associated action is not executed.

Requests that are already approved or rejected cannot be modified. This ensures a clean, auditable decision trail.

### Filtering Approval Requests

The approval dashboard allows filtering by:

- **Status**: Pending, Approved, or Rejected
- **Assigned To**: Filter by the designated reviewer or approver
- **Request Type**: Model approval, overlay approval, journal posting, or sign-off

## Authentication

### Production (Databricks Apps)

When deployed as a Databricks App, the platform uses Databricks OAuth for authentication. The OAuth proxy automatically identifies each user via the `X-Forwarded-User` header and resolves their permissions from the user database.

No additional authentication configuration is required — Databricks Apps handles this automatically.

### Local Development

For local development without Databricks OAuth, the platform supports a development header (`X-User-Id`) that simulates authentication. Without any authentication header, the platform treats the user as anonymous with analyst-level access.

:::warning
In production, ensure the Databricks Apps OAuth proxy is correctly configured. Without it, all users are treated as anonymous and RBAC is effectively bypassed. See [Setup & Installation](setup-installation) for deployment configuration.
:::

## Segregation of Duties

The platform enforces two key segregation controls:

### Maker-Checker Separation

The person who creates a model, overlay, or journal entry cannot be the same person who approves it. The approval workflow enforces this by requiring different user identities for the maker and checker roles.

### Project Lock Protection

Once a project is signed off, it becomes immutable — no modifications are permitted to any of its data, models, overlays, or results. Any attempt to modify a signed-off project is rejected with a clear error message.

This enforces the IFRS 9 requirement that finalized ECL calculations cannot be retroactively altered.

## ECL Data Integrity

### Hash-Based Verification

At sign-off time, the platform computes a SHA-256 hash of the ECL results. This hash is stored alongside the signed-off project. At any later point, the hash can be recomputed from the current data and compared to the stored value to verify that nothing has changed.

This mechanism ensures that auditors can independently verify that the ECL numbers presented in financial statements match the numbers that were approved during the sign-off process. See [Sign-Off](../user-guide/step-8-sign-off) for the user-facing sign-off workflow.

## Best Practices

1. **Principle of least privilege** — Assign users the minimum role required for their responsibilities. Most users should be Analysts.
2. **Separate approvers from modelers** — The person who creates an ECL model should not be the same person who approves it. Use the Reviewer and Approver roles to enforce this separation.
3. **Deactivate rather than delete** — Set departing users to Inactive rather than deleting their records. This preserves the audit trail's referential integrity.
4. **Audit role changes** — All role modifications are recorded in the audit trail. Review the audit log periodically to verify that role assignments follow your organization's access control policy.
5. **Test with seed users** — Use the four seed users during development to verify that RBAC enforcement works correctly across all roles before deploying to production.

## What's Next?

- [Approval Workflow](../user-guide/approval-workflow) — Understand the end-user approval experience
- [System Administration](system-administration) — Monitor audit trail integrity and system health
- [Troubleshooting](troubleshooting) — Resolve permission denied errors and authentication issues
