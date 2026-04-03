---
sidebar_position: 2
title: "Step 1: Create Project"
description: "How to create a new ECL project with reporting date, currency, and portfolio scope."
---

# Step 1: Create Project

Every ECL calculation begins with a project. A project anchors all subsequent workflow steps — data processing, model selection, simulation, and sign-off — to a specific reporting period. This ensures that results are traceable, auditable, and clearly linked to the period they represent.

:::info Prerequisites
- An active user account with **Analyst** or **Risk Manager** role
- Access to the ECL platform (see [Quick Start](../quick-start) if this is your first time)
:::

## What You'll Do

On this page you will create a new ECL project by providing a project identifier, name, accounting framework, reporting date, and optional description. You can also resume an existing project that is still in progress.

## Step-by-Step Instructions

### 1. Navigate to the Create Project Page

From the main navigation, select **Create Project**. You will see two sections:

- **Existing Projects** — a list of previously created projects you can resume
- **New Project Form** — the form to create a new ECL run

![Create Project page](/img/screenshots/step-1-create-project.png)
*The Create Project page showing existing projects and the new project form.*

### 2. Review Existing Projects (Optional)

If you have projects already in progress, they appear as cards showing:

| Information | What It Means |
|-------------|--------------|
| **Project ID** | The unique identifier you assigned |
| **Reporting Date** | The period this ECL run covers |
| **Current Step** | How far the project has progressed (e.g., "Step 3/8") |
| **Status Icon** | A green checkmark for signed-off projects, or a clock icon for projects still in progress |

Click any project card to resume the workflow from where you left off.

### 3. Fill in the New Project Form

Complete the following fields:

| Field | Description | Rules |
|-------|-------------|-------|
| **Project ID** | A unique identifier for this ECL run (e.g., `ecl-q4-2025`) | Required. Letters, numbers, and hyphens only. Maximum 50 characters. |
| **Project Name** | A descriptive name (e.g., "Q4 2025 ECL — Full Portfolio") | Required. Maximum 200 characters. |
| **Accounting Framework** | The impairment standard to apply | Choose from: IFRS 9 — Expected Credit Loss (ECL), CECL — US GAAP ASC 326, or Regulatory Stress Test. Default: IFRS 9. |
| **Reporting Date** | The cut-off date for this ECL calculation | Required. Must be a valid date and cannot be more than one year in the future. |
| **Description** | Notes about the scope, portfolios, or scenarios for this run | Optional. Free-form text. |

Validation errors appear inline below each field as you complete the form.

### 4. Review the Configuration Summary

Below the form, a read-only panel displays your organization's configuration:

- **Accounting Standard** — the full standard name (e.g., "IFRS 9 Financial Instruments (2014, amended 2022)")
- **Local Regulator** — the regulatory body overseeing your institution
- **Model Version** — the ECL engine version in use

These values are set by your administrator and cannot be changed here. If they look incorrect, contact your system administrator.

### 5. Create the Project

Click **Create Project**. The platform will:

1. Validate all fields
2. Create the project record
3. Automatically advance to **Step 2: Data Processing**
4. Record the creation in the project's audit trail

## Resuming an Existing Project

You do not need to complete the entire 8-step workflow in a single session. To resume a project:

1. Navigate to the **Create Project** page
2. Find the project in the **Existing Projects** list — projects are sorted by last-modified date
3. Click the project card to open it
4. The platform navigates you directly to the step where you left off
5. All previously completed steps remain locked and unmodifiable — you continue from the current active step

If a step was previously rejected, the project will reopen at that step with the rejection comments visible. Address the noted issues and resubmit for approval.

:::tip Common Project ID Patterns
Organizations typically standardize their project IDs for consistency. Common patterns include:
- **Period-based**: `ecl-q4-2025`, `ecl-2025-12`, `ecl-fy2025`
- **Portfolio-scoped**: `ecl-retail-q4-2025`, `ecl-corporate-q4-2025`
- **Run-type**: `ecl-regulatory-q4-2025`, `ecl-management-q4-2025`

Consistent naming makes it easier to filter, compare, and audit projects across reporting periods.
:::

## Understanding Project States

Once created, your project progresses through the 8-step workflow. Each step has one of three states:

| State | Meaning |
|-------|---------|
| **Pending** | The step has not been started yet |
| **Completed** | The step has been reviewed and approved |
| **Rejected** | The step was reviewed and sent back for rework |

The progress bar at the top of every page (the "stepper") shows which steps are complete, which is active, and which are still locked. You cannot skip steps — each must be completed in sequence.

**State transitions follow a defined flow:**

- A step starts as **Pending**. When you open a Pending step, it becomes your active step.
- After reviewing the step's results, you can mark it **Completed** — this locks the step and unlocks the next one.
- If a reviewer rejects the step, it moves to **Rejected**. The rejection reason is recorded and you must address the issues before the step can be re-approved.
- Once a rejected step is reworked and approved, it returns to **Completed** and the workflow continues.

This sequential, auditable progression ensures that every decision point in the ECL calculation is reviewed and approved before the next step begins — a core IFRS 9 governance requirement.

:::tip Understand What "Completed" Means
Marking a step as complete is an explicit approval decision. It means you have reviewed the results and are satisfied they are correct for this reporting period. This action is recorded in the audit trail.
:::

## The Audit Trail

Every action taken on a project — creation, step advances, model runs, approvals, rejections — is recorded in an immutable audit trail. You can view the audit trail on the project page. Each entry shows:

- **Action** — what was done (e.g., "Project Created", "Data Processing Completed")
- **User** — who performed the action
- **Timestamp** — when it happened
- **Detail** — any notes or comments associated with the action

The audit trail cannot be edited or deleted. It provides a complete, verifiable history of every decision made during the ECL process.

## Tips & Best Practices

:::tip Choose Meaningful Project IDs
Use a consistent naming convention that includes the reporting period, such as `ecl-q4-2025` or `ecl-2025-12`. This makes it easy to find and compare projects across periods.
:::

:::tip Add Scope Notes in the Description
Use the description field to record which portfolios are included, any scenarios you plan to test, or the purpose of this particular run (e.g., "Management Committee submission" or "Regulatory stress test"). These notes appear in the project list and help colleagues understand the context.
:::

:::warning Cannot Modify After Sign-Off
Once a project reaches Step 8 (Sign-Off) and is signed off, it becomes immutable. No data, models, or parameters can be changed. If corrections are needed, you must create a new project. This is by design — it preserves the integrity of the signed-off calculation.
:::

## What's Next?

Proceed to [Step 2: Data Processing](step-2-data-processing) to load and review your portfolio data.
