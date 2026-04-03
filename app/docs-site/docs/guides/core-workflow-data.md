---
sidebar_position: 1
title: Core Workflow & Data Endpoints
---

# Core Workflow & Data Endpoints

The platform's core is an 8-step ECL workflow with 47 API endpoints covering project lifecycle management, portfolio data queries, and initial setup.

## Overview

The core workflow guides users through a sequential process from project creation to final sign-off. Each step validates prerequisites before allowing advancement, ensuring data integrity throughout the ECL calculation pipeline.

![ECL Workflow Steps](/img/guides/workflow-steps.png)
*The 8-step ECL workflow stepper showing project progression*

## Project Lifecycle

### Creating a Project

Every ECL calculation begins with a project. Projects encapsulate a specific reporting date, portfolio scope, and calculation parameters.

**API**: `POST /api/projects`

```json
{
  "project_name": "Q4 2025 ECL",
  "reporting_date": "2025-12-31",
  "base_currency": "USD"
}
```

The project starts at Step 1 and advances through each stage as work is completed.

### Advancing Steps

Each workflow step can be advanced with a status:

**API**: `POST /api/projects/{project_id}/advance`

```json
{
  "status": "completed"
}
```

Valid statuses: `completed`, `failed`, `skipped`. The step number auto-increments. You cannot skip ahead — each step must be explicitly advanced.

### Project Reset

If a project needs to be recalculated, reset it back to a specific step:

**API**: `POST /api/projects/{project_id}/reset`

This clears all downstream data and returns the project to the target step.

## Portfolio Data Queries

The platform provides 32 data query endpoints for analyzing portfolio composition and ECL results. All endpoints accept a `project_id` parameter.

![Portfolio Dashboard](/img/guides/portfolio-dashboard.png)
*Portfolio summary with stage distribution and KPI cards*

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/data/portfolio-summary` | Total exposure, weighted-average PD, top metrics |
| `/api/data/stage-distribution` | Exposure breakdown by Stage 1/2/3 |
| `/api/data/ecl-summary` | Aggregate ECL by stage and product |
| `/api/data/ecl-by-product` | ECL drill-down by product type |
| `/api/data/scenario-summary` | ECL by macroeconomic scenario |
| `/api/data/mc-distribution` | Monte Carlo result distribution |
| `/api/data/concentration` | Portfolio concentration analysis |
| `/api/data/migration` | Rating migration matrices |
| `/api/data/sensitivity` | Sensitivity analysis results |
| `/api/data/vintage` | Vintage analysis by origination cohort |
| `/api/data/top-exposures` | Largest individual exposures (default: top 20) |

### Data Consistency

The platform enforces internal consistency:
- Stage distribution totals must equal the portfolio summary total
- ECL by product must sum to the aggregate ECL
- Scenario-weighted ECL must match the simulation output

## Setup Wizard

First-time users run the setup wizard to initialize the database:

| Step | Endpoint | Purpose |
|------|----------|---------|
| Check status | `GET /api/setup/status` | Verify if setup is needed |
| Validate tables | `POST /api/setup/validate-tables` | Check Lakebase schema |
| Seed data | `POST /api/setup/seed` | Populate reference data |
| Complete | `POST /api/setup/complete` | Mark setup as done |
| Reset | `POST /api/setup/reset` | Re-run setup from scratch |

## Sign-Off & Approval

The final workflow step locks the project with governance controls:

- **Segregation of duties**: The sign-off user cannot be the same person who executed the model
- **Hash verification**: `POST /api/projects/{project_id}/verify-hash` checks that ECL data has not been tampered with since calculation
- **Approval history**: `GET /api/projects/{project_id}/approval-history` provides a complete audit trail
- **Immutability**: Once signed off, the project cannot be modified — any attempt returns a 403 error

## Overlays & Scenario Weights

Management overlays allow post-model adjustments to ECL:

**API**: `POST /api/projects/{project_id}/overlays`

```json
{
  "overlays": [
    {"segment": "Corporate", "adjustment_pct": 5.0, "reason": "Sector downturn"}
  ],
  "comment": "Q4 management adjustment for energy sector exposure"
}
```

Scenario weights control the probability weighting of macroeconomic scenarios:

**API**: `POST /api/projects/{project_id}/scenario-weights`

```json
{
  "base": 0.5,
  "optimistic": 0.2,
  "pessimistic": 0.3
}
```

Weights must sum to 1.0.

## Test Coverage

Sprint 1 of the QA audit added **299 tests** covering all 47 endpoints across 4 test files:
- Happy paths for every endpoint
- Error cases: missing project_id, invalid advancement, unauthorized sign-off
- Edge cases: empty portfolios, single loans, reset mid-workflow
- Data consistency: stage distributions sum correctly
- Hash integrity with tampered data scenarios
