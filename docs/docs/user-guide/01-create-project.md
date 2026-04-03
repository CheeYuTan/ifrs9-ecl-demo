---
sidebar_position: 2
title: "Step 1: Create Project"
---

# Step 1: Create Project

Define the scope of your ECL calculation run.

## What This Step Does

Every ECL calculation begins with a **project** — a container that tracks workflow state, stores scenario weights and overlays, and anchors the audit trail. Projects are identified by a unique Project ID and can be resumed across sessions.

## Page Layout

### Existing Projects

The left panel lists all prior projects with:

- **Status icon** — Clock (in-progress) or green checkmark (signed-off)
- **Step counter** — e.g., "Step 3/8"
- **Reporting date** and signed-by name (if applicable)

Click any project to load it and continue from where you left off.

### Create ECL Project Form

| Field | Description | Validation |
|-------|-------------|------------|
| Project ID | Alphanumeric + hyphens, max 50 chars | Required, unique |
| Project Name | Free text, max 200 chars | Required |
| Accounting Framework | IFRS 9 ECL, CECL (US GAAP), or Regulatory Stress Test | Required |
| Reporting Date | The "as-of" date for the ECL calculation | Cannot be > 1 year in the future |
| Description | Scope, portfolios, scenarios covered | Optional |

### Metadata Tiles

Three read-only tiles display values from admin configuration:

- **Accounting Standard** (e.g., IFRS 9)
- **Local Regulator**
- **Model Version** (e.g., v4.0)

### Audit Trail

When viewing an existing project, a scrollable log shows all actions taken on that project with timestamps and users.

## Creating a Project

1. Fill in the Project ID and Name.
2. Select the Accounting Framework.
3. Set the Reporting Date to the period-end date (e.g., 2025-12-31 for Q4 2025).
4. Optionally add a description.
5. Click **Create Project**.

The form validates all fields on blur. Character counters appear for the ID and Name fields. On success, you'll see a confirmation message and can click **Next** to proceed to Step 2.

## Resuming a Project

Click any existing project from the left panel. The workflow will resume at the last completed step.
