---
sidebar_position: 4
title: Jobs & Pipelines
---

# Jobs & Pipelines

Configure Databricks workspace connectivity, managed jobs, and compute settings.

## Databricks Workspace

| Field | Config Key | Default |
|-------|-----------|---------|
| Workspace URL | `jobs.workspace_url` | (blank) |
| Workspace ID | `jobs.workspace_id` | (blank) |

Click **Auto-Detect** to read values from the app's runtime environment (`GET /api/admin/auto-detect-workspace`). This works when the app is deployed on Databricks Apps.

## Managed Jobs

The application manages four Databricks jobs:

| Job Key | Job Name | Purpose |
|---------|----------|---------|
| `satellite_ecl_sync` | IFRS9 ECL - Satellite Model + ECL + Sync | Train satellite models, calculate ECL, sync to Lakebase |
| `full_pipeline` | IFRS9 ECL - Full Pipeline | End-to-end pipeline (data processing through ECL) |
| `demo_data` | IFRS9 ECL - Generate Demo Data | Generate synthetic demo data |
| `monte_carlo` | IFRS9 ECL - Monte Carlo Simulation | Run Monte Carlo simulation as a batch job |

Each job's numeric Databricks Job ID is displayed along with a direct link to the Databricks Jobs UI (when workspace URL is configured).

### Provisioning Jobs

Click **Provision Jobs** to create or update all four managed jobs in your Databricks workspace (`POST /api/jobs/provision`). This is required during initial setup.

## Default Job Parameters

Editable parameters that are passed to jobs by default:

| Parameter | Default |
|-----------|---------|
| `enabled_models` | All 8 model types (comma-separated) |

Additional parameters (n_simulations, pd_lgd_correlation, etc.) are passed per invocation from the UI.

## Compute

| Setting | Config Key | Default |
|---------|-----------|---------|
| Serverless Compute | `jobs.serverless` | Enabled |
| Cluster Spec | `jobs.cluster_spec` | (blank) |

When serverless is enabled, jobs run on Databricks Serverless compute. Disable this to specify a custom cluster configuration.

## Connection Test

Click **Test Connection** to verify connectivity to Lakebase (`POST /api/admin/test-connection`). The result shows:

- Connected / Disconnected badge
- Schema and table prefix details

## Triggering Jobs

Jobs can be triggered from two places:

1. **Step 4 (Satellite Model)** — Triggers `satellite_ecl_sync` with selected model types
2. **Step 5 (Model Execution)** — Triggers `monte_carlo` with simulation parameters

The API endpoint is `POST /api/jobs/trigger` with the job key and parameters. Job status is polled via `GET /api/jobs/run/{run_id}`.
