---
sidebar_position: 14
title: Approval Workflow
---

# Approval Workflow

Maker-Checker-Approver governance system for model approvals, overlay approvals, journal postings, and sign-offs.

## Purpose

The approval workflow enforces segregation of duties across four roles: Analyst, Reviewer, Approver, and Admin. All approval actions are recorded in the audit trail.

## Roles and Permissions

| Permission | Analyst | Reviewer | Approver | Admin |
|-----------|---------|----------|----------|-------|
| Create projects | Yes | Yes | Yes | Yes |
| Submit for review | Yes | Yes | Yes | Yes |
| Review and comment | No | Yes | Yes | Yes |
| Approve/reject | No | No | Yes | Yes |
| Sign off projects | No | No | Yes | Yes |
| Manage users | No | No | No | Yes |
| Configure system | No | No | No | Yes |

## Request Types

| Type | Description |
|------|-------------|
| Model Approval | New or updated model requiring validation |
| Overlay Approval | Management overlay requiring sign-off |
| Journal Posting | GL journal entry requiring authorisation |
| Sign Off | Final project sign-off |

## Four Tabs

### Dashboard

Overview of the approval pipeline:

- **KPI Row** — Pending, Approved Today, Rejected, Overdue counts
- **Recent Pending** — Up to 5 pending items requiring action
- **User Directory** — Team members with roles and departments
- **Approval Pipeline** — Four columns showing Pending, Approved, Rejected, and Escalated counts

### Pending Queue

A table of all items awaiting action, showing Type, Entity, Requested By, Assigned To, Priority (Urgent/Normal), Due Date, and a Review button.

### History

Filterable table of all past approvals with Type, Entity, Status, Requested By, Actioned By, Priority, and timestamps.

### Users

User directory with roles, departments, and active/inactive status. Includes a **Role Permissions Matrix** table showing all 13 permissions across the 4 roles.

## Creating an Approval Request

Click **Create Request** and fill in:

| Field | Description |
|-------|-------------|
| Request Type | Model Approval, Overlay Approval, Journal Posting, or Sign Off |
| Priority | Urgent or Normal |
| Entity ID | The item being approved (e.g., model ID, overlay ID) |
| Entity Type | Type of entity |
| Requested By | Dropdown of users |
| Assigned To | Dropdown of approvers/admins (or auto-assign) |
| Due Date | When the approval is needed |
| Comments | Context for the reviewer |

## Acting on a Request

Open a pending request to see its full detail, then:

- Select the **Action By** user
- Add a comment
- Click **Approve** or **Reject**

The action is recorded with timestamp and user, and the requestor is notified.
