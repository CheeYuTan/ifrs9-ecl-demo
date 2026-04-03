---
sidebar_position: 14
title: "Approval Workflow"
description: "Maker-checker pattern, role-based approval chains, and audit trail for ECL governance."
---

# Approval Workflow

The Approval Workflow enforces a maker-checker governance pattern across every critical action in the ECL platform. No model can be promoted, no overlay can take effect, no journal can be posted, and no project can be signed off without an independent approval by an authorised reviewer. This segregation of duties is a cornerstone of IFRS 9 governance — it ensures that the person who creates a calculation is never the same person who approves it for use in financial statements.

:::info Prerequisites
- Active user account with an assigned role
- At least one pending request to review (for approvers)
- **Analyst** role can create requests; **Reviewer** role can submit for approval; **Approver** role can approve or reject; **Admin** role has full access
:::

## What You'll Do

On this page you will understand the four types of approval requests, learn how the role-based permission model works, navigate the approval dashboard, review and act on pending requests, and access the full approval history for audit purposes.

## Understanding the Approval Model

### The Maker-Checker Principle

Every governance action in the platform follows a two-person rule:

1. **The Maker** creates the item — trains a model, defines an overlay, generates journals, or prepares a sign-off
2. **The Checker** independently reviews the item and either approves it (allowing it to take effect) or rejects it (with a documented reason)

This principle is not optional. The platform enforces it technically — a user cannot approve their own request, and the system records the identity of both maker and checker in the permanent audit trail.

### Four Types of Approval Request

| Request Type | What It Governs | Who Initiates | Who Approves |
|---|---|---|---|
| **Model Approval** | Promoting a satellite model from Draft to Active status | Analyst or Reviewer who trained the model | Approver or Admin |
| **Overlay Approval** | Applying a management overlay that adjusts ECL beyond the model output | Analyst or Reviewer who created the overlay | Approver or Admin |
| **Journal Posting** | Posting ECL journal entries to the general ledger | Reviewer who reviewed the journals | Approver or Admin |
| **Sign-Off** | Final attestation that the ECL calculation is complete and correct | Reviewer who verified the results | Approver or Admin |

Each request type follows the same lifecycle: **Created → Pending → Approved** or **Rejected**.

### Role Permissions

The platform defines four roles with cumulative permissions — each role inherits everything from the roles below it:

| Permission | Analyst | Reviewer | Approver | Admin |
|---|:---:|:---:|:---:|:---:|
| View portfolio data and reports | ✓ | ✓ | ✓ | ✓ |
| Create models and run backtests | ✓ | ✓ | ✓ | ✓ |
| Generate journals and create overlays | ✓ | ✓ | ✓ | ✓ |
| Submit items for approval | — | ✓ | ✓ | ✓ |
| Review models and overlays | — | ✓ | ✓ | ✓ |
| Approve or reject requests | — | — | ✓ | ✓ |
| Sign off projects and post journals | — | — | ✓ | ✓ |
| Manage users, roles, and configuration | — | — | — | ✓ |

:::warning Segregation of Duties
The platform enforces segregation at the system level. An Analyst who trains a model cannot also be the Approver who promotes it. If your team is small, ensure that at least two people hold different roles in the approval chain.
:::

## Step-by-Step Instructions

### 1. Navigate to the Approval Workflow

From the main navigation, select **Approval Workflow**. The page opens to the **Dashboard** tab, which provides an at-a-glance view of governance activity.

### 2. Review the Dashboard

The dashboard displays four summary cards at the top:

| Card | What It Shows |
|---|---|
| **Pending** | Number of requests awaiting review — the most important number for approvers |
| **Approved Today** | Requests approved in the current session or day |
| **Rejected** | Requests rejected and requiring rework by the maker |
| **Overdue** | Requests that have passed their due date without action |

Below the cards, two panels provide quick context:

- **Recent Pending Requests** — the newest requests waiting for action, with request type, entity, priority, and who submitted them
- **User Directory** — quick reference of team members, their roles, and departments

At the bottom, an **Approval Pipeline** shows the count of requests at each status, helping managers spot bottlenecks.

![Approval workflow dashboard](/img/screenshots/approval-dashboard.png)
*The Approval Workflow dashboard showing pending counts, recent requests, and the approval pipeline.*

### 3. Work the Pending Queue

Switch to the **Pending Queue** tab to see all requests awaiting action. The queue is a sortable table with:

| Column | What It Shows |
|---|---|
| **Request Type** | Model Approval, Overlay Approval, Journal Posting, or Sign-Off |
| **Entity** | The specific item under review (model name, overlay description, etc.) |
| **Requested By** | Who created the request |
| **Priority** | Normal or Urgent — urgent requests should be reviewed first |
| **Due Date** | The deadline for action, if set |
| **Created** | When the request was submitted |

Click **Review** on any row to open the request detail.

![Approval pending queue](/img/screenshots/approval-queue.png)
*The Pending Queue tab showing requests sorted by priority with Review buttons.*

### 4. Review and Act on a Request

When you open a request for review, the detail panel shows:

- **Full context** — the entity being approved, who created it, when, and why
- **Supporting information** — for model approvals, this includes model performance metrics; for overlays, the rationale and impact amount
- **Comments** — any notes from the maker explaining the request

To take action:

1. Read the supporting information carefully
2. If additional context is needed, add a comment requesting clarification (the request stays in Pending status)
3. When ready, select your action:
   - **Approve** — the item takes effect immediately (model becomes Active, overlay is applied, journal is posted, or project is signed off)
   - **Reject** — the item is returned to the maker with your rejection reason (mandatory)
4. Add a comment explaining your decision (recommended for audit trail completeness)
5. Click **Submit**

:::tip Document Your Reasoning
Even when approving, add a brief comment such as "Reviewed model performance metrics — AUC and Gini within acceptable thresholds" or "Overlay rationale is consistent with observed portfolio trends." This creates a richer audit trail for internal and external auditors.
:::

### 5. Review Approval History

Switch to the **History** tab to see all past approval actions. The history is filterable by:

- **Request type** — narrow to just model approvals, just overlays, etc.
- **Status** — filter to see only approved, only rejected, or all

Each history entry shows the complete lifecycle: who created the request, who acted on it, when each action occurred, and all comments exchanged. This is the primary audit record for governance reviews.

:::caution Immutable History
Approval history cannot be edited or deleted. Every action — creation, approval, rejection, and every comment — is permanently recorded with timestamps and user identities. This is by design for regulatory compliance.
:::

### 6. Review the User Directory and Permissions

The **Users** tab provides a complete view of:

- All registered users with their roles and departments
- A **Role Permissions Matrix** showing exactly which permissions each role grants (the same matrix shown in the table above, rendered visually with checkmarks)

This is useful for administrators setting up new users and for auditors verifying that segregation of duties is maintained.

## Understanding Priority and Due Dates

When creating an approval request, the maker can set:

- **Priority**: Normal or Urgent — urgent requests appear at the top of the pending queue with a visual indicator
- **Due Date**: An optional deadline — requests past their due date appear in the "Overdue" count on the dashboard

These fields help teams manage quarter-end and year-end reporting deadlines, when multiple approvals may be in flight simultaneously.

## Tips & Best Practices

:::tip Establish a Review Cadence
For ongoing ECL reporting, establish a regular review cadence — such as reviewing all pending requests every morning. This prevents bottlenecks at month-end when multiple projects may need sign-off simultaneously.
:::

:::tip Use Priority Wisely
Reserve "Urgent" priority for genuine time-sensitive requests (e.g., regulatory deadlines). If everything is marked urgent, nothing is.
:::

:::warning Plan for Absences
If your institution has only one Approver, ensure a backup is designated with the Approver role. A pending request that cannot be approved because the sole approver is unavailable can delay financial reporting.
:::

:::caution Rejection Requires Rework
When a request is rejected, the maker must address the issues and submit a new request. The original rejected request remains in history for audit purposes. There is no "resubmit" — it is always a new request, creating a clear chain of corrections.
:::

## What's Next?

- [Step 8: Sign-Off](step-8-sign-off) — the sign-off process that generates the final approval request
- [GL Journals](gl-journals) — journal posting requires an approved request before entries become permanent
- [Model Registry](model-registry) — model promotion follows the approval workflow before a model becomes the active champion
- [Step 7: Overlays](step-7-overlays) — management overlays require approval before they affect ECL figures
