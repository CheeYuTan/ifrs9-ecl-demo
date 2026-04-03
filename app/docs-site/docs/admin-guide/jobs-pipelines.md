---
sidebar_position: 5
title: "Jobs & Pipelines"
description: "Managing Databricks jobs and period-end close pipelines."
---

# Jobs & Pipelines

Manage Databricks job provisioning, trigger ECL calculation pipelines, monitor execution status, and orchestrate period-end close workflows.

:::info Who Should Read This
System administrators responsible for job orchestration, pipeline scheduling, and production ECL runs.
:::

## Overview

The platform manages two types of execution workflows:

1. **Databricks Jobs** -- Multi-task notebook workflows that run satellite models, ECL calculations, and data synchronization on Databricks serverless compute
2. **Period-End Close Pipelines** -- Sequenced validation and computation steps that verify data quality, model results, and calculation integrity before sign-off

Jobs handle the compute-intensive work (model training, Monte Carlo simulation). Pipelines handle the governance workflow (data checks, result validation, report generation).

## Managed Job Types

The platform auto-provisions and manages four Databricks jobs. Jobs are created on first trigger and updated automatically when notebook paths change.

### satellite_ecl_sync

**Purpose:** Train satellite models, calculate ECL, and sync results to Lakebase.

**Task graph:**

```
model_linear_regression ──┐
model_logistic_regression ─┤
model_polynomial_deg2 ─────┤
model_ridge_regression ────┤ (8 parallel tasks)
model_random_forest ───────┤
model_elastic_net ─────────┤
model_gradient_boosting ───┤
model_xgboost ─────────────┤
                           ▼
                  aggregate_models (ALL_DONE)
                           ▼
                   ecl_calculation (ALL_SUCCESS)
                           ▼
                  sync_to_lakebase (ALL_SUCCESS)
```

All eight satellite model tasks run in parallel. The aggregation task runs after all model tasks complete (even if some fail, to produce partial results). ECL calculation and Lakebase sync proceed sequentially only if the previous task succeeds.

### full_pipeline

**Purpose:** End-to-end pipeline from data processing through ECL calculation.

**Task graph:**

```
data_processing
      ▼
model_* (8 parallel) --> aggregate_models --> ecl_calculation --> sync_to_lakebase
```

This job adds a data processing step before the satellite model tasks. It does **not** generate synthetic data -- it processes data that has already been mapped via the Data Mapping wizard. Use this for production period-end runs.

### monte_carlo

**Purpose:** Run Monte Carlo simulations with configurable parameters.

**Task graph:**

```
monte_carlo_simulation --> sync_to_lakebase
```

A focused job that runs only the Monte Carlo simulation engine and syncs results. Use this when you need to re-run simulations with different parameters (e.g., increased simulation count for production) without re-training satellite models.

### demo_data

**Purpose:** Generate synthetic demonstration data and process it.

**Task graph:**

```
generate_data --> data_processing
```

Generates a synthetic loan portfolio with borrower data, payment histories, default events, and macroeconomic scenarios. Use this for demonstrations, testing, and development environments only. Production deployments should use the Data Mapping wizard to ingest real data.

## Job API

### Trigger a Job

```
POST /api/jobs/trigger
```

**Request body:**

```json
{
  "job_key": "satellite_ecl_sync",
  "enabled_models": ["linear_regression", "xgboost"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_key` | string | Yes | One of: `satellite_ecl_sync`, `full_pipeline`, `monte_carlo`, `demo_data` |
| `enabled_models` | string[] | No | Override enabled models for satellite jobs. Defaults to all enabled models in config. |
| `n_simulations` | int | No | Monte Carlo simulation count (default: 1000) |
| `pd_lgd_correlation` | float | No | PD-LGD correlation (default: 0.30) |
| `aging_factor` | float | No | Aging factor (default: 0.08) |
| `pd_floor` | float | No | PD floor (default: 0.001) |
| `pd_cap` | float | No | PD cap (default: 0.95) |
| `lgd_floor` | float | No | LGD floor (default: 0.01) |
| `lgd_cap` | float | No | LGD cap (default: 0.95) |
| `random_seed` | int | No | Random seed for reproducible simulations |
| `scenario_weights` | object | No | Scenario weight overrides (e.g., `{"baseline": 0.5, "adverse": 0.3, "severe": 0.2}`) |

**Response:**

```json
{
  "run_id": 123456,
  "job_id": 789,
  "models": ["linear_regression", "xgboost"],
  "parallel": true,
  "run_url": "https://workspace.databricks.com/?o=12345#job/789/run/123456"
}
```

### Get Run Status

```
GET /api/jobs/run/{run_id}
```

Returns detailed status for a specific job run, including per-task breakdown:

```json
{
  "run_id": 123456,
  "job_id": 789,
  "lifecycle_state": "RUNNING",
  "result_state": null,
  "state_message": "",
  "run_url": "https://...",
  "start_time": 1704067200000,
  "end_time": null,
  "run_duration_ms": 45000,
  "tasks": [
    {
      "task_key": "model_xgboost",
      "lifecycle_state": "RUNNING",
      "result_state": null,
      "run_url": "https://...",
      "execution_duration_ms": 30000
    },
    {
      "task_key": "model_linear_regression",
      "lifecycle_state": "TERMINATED",
      "result_state": "SUCCESS",
      "run_url": "https://...",
      "execution_duration_ms": 15000
    }
  ]
}
```

### List Job Runs

```
GET /api/jobs/runs/{job_key}?limit=10
```

Returns the most recent runs for a specific job key. Useful for monitoring job history and identifying failures.

### Get Jobs Configuration

```
GET /api/jobs/config
```

Returns the current state of all managed jobs:

```json
{
  "available_models": ["linear_regression", "logistic_regression", "..."],
  "job_ids": { "satellite_ecl_sync": 789, "full_pipeline": 790 },
  "workspace_url": "https://workspace.databricks.com",
  "workspace_id": "12345",
  "scripts_base": "/Workspace/Users/admin@company.com/ifrs9-ecl-demo/scripts",
  "jobs": {
    "satellite_ecl_sync": {
      "job_id": 789,
      "name": "IFRS9 ECL - Satellite Model + ECL + Sync",
      "task_count": 11,
      "paths_ok": true,
      "status": "ok"
    }
  }
}
```

### Provision Jobs

```
POST /api/jobs/provision
```

Force-creates or updates all four managed jobs with the correct notebook paths and serverless environment configuration. This is normally called automatically on first trigger, but you can call it explicitly to pre-provision jobs or to update notebook paths after a code redeployment.

## Monte Carlo Job Parameters

The Monte Carlo job accepts parameters that control simulation behavior. These parameters are passed as notebook base parameters and can be overridden per run via the trigger API.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_simulations` | int | 1,000 | Number of simulation paths. Production runs typically use 5,000-10,000. |
| `pd_lgd_correlation` | float | 0.30 | Correlation between PD and LGD shocks. Higher values model stronger downturn effects. |
| `aging_factor` | float | 0.08 | Annual PD aging adjustment. Models credit deterioration over time. |
| `pd_floor` / `pd_cap` | float | 0.001 / 0.95 | Bounds on simulated PD values. |
| `lgd_floor` / `lgd_cap` | float | 0.01 / 0.95 | Bounds on simulated LGD values. |
| `random_seed` | int | None | Fix the random seed for reproducible results. Omit for non-deterministic runs. |
| `scenario_weights` | JSON | Config default | Override scenario probability weights. Must be a JSON object mapping scenario keys to weights that sum to 1.0. |

Example: trigger a production Monte Carlo run with increased simulations and a fixed seed:

```json
POST /api/jobs/trigger
{
  "job_key": "monte_carlo",
  "n_simulations": 10000,
  "random_seed": 42,
  "scenario_weights": {
    "baseline": 0.40,
    "mild_downturn": 0.20,
    "adverse": 0.20,
    "severely_adverse": 0.10,
    "tail_risk": 0.10
  }
}
```

## Scripts Base Path Detection

The platform needs to know where pipeline notebook scripts are deployed in the workspace. It uses a four-step detection strategy:

1. **Admin config override**: Check `jobs.scripts_base_path` in admin configuration. If set, use this value. This is the recommended approach for production.
2. **App source code path**: Derive from `DATABRICKS_SOURCE_CODE_PATH` environment variable. The scripts folder is assumed to be a sibling of the app source code folder.
3. **App info lookup**: Query the Databricks Apps API to get the active deployment's source code path and derive the scripts folder.
4. **Workspace convention**: Fall back to `/Workspace/Users/{current_user}/ifrs9-ecl-demo/scripts`.

To set an explicit scripts base path:

```json
PUT /api/admin/config/jobs
{
  "scripts_base_path": "/Workspace/Repos/production/ifrs9-ecl/scripts"
}
```

## Compute Configuration

Jobs default to **serverless compute**, which requires no cluster management and provides fast startup times. The compute configuration is stored in the `jobs` config section:

```json
{
  "compute": {
    "use_serverless": true,
    "cluster_spec": ""
  }
}
```

All jobs specify a serverless environment with the following Python dependencies:

- `scikit-learn`
- `xgboost`
- `optuna`
- `psycopg2-binary`
- `faker`

If you need to use a dedicated cluster instead of serverless, set `use_serverless` to `false` and provide a cluster specification in `cluster_spec`.

## Job Permissions

When a job is created or updated, the platform automatically grants `CAN_MANAGE_RUN` permission to the app's service principal. This ensures the app can trigger runs and monitor their status without requiring the service principal to own the job.

If permission granting fails (e.g., due to workspace permission policies), a warning is logged but the job creation proceeds. You can manually grant permissions through the Databricks workspace UI.

## Period-End Close Pipeline

The period-end close pipeline is a governed workflow that validates data, verifies model results, and sequences the steps required for a clean period-end close.

### Pipeline Steps

| Order | Step Key | Label | What It Checks |
|:-----:|----------|-------|----------------|
| 1 | `data_freshness` | Data Freshness Check | Verifies `model_ready_loans` contains data and was updated within the configured threshold (default: 7 days). |
| 2 | `data_quality` | Data Quality Validation | Checks for negative GCA, PD values outside [0,1], and invalid stage assignments. All checks must pass. |
| 3 | `model_execution` | Model Execution | Verifies that loan-level ECL results exist in the `loan_level_ecl` table. |
| 4 | `ecl_calculation` | ECL Calculation | Verifies that weighted ECL results exist and computes the total ECL amount. |
| 5 | `report_generation` | Report Generation | Validates that report generation prerequisites are met. |
| 6 | `attribution` | Attribution Computation | Validates that ECL attribution/waterfall decomposition prerequisites are met. |

### Pipeline API

**Start a pipeline:**

```
POST /api/period-close/start
{
  "project_id": "PRJ-001",
  "triggered_by": "admin@company.com"
}
```

**Execute a step:**

```
POST /api/period-close/execute-step
{
  "run_id": "PIPE-PRJ-001-20251231120000",
  "step_key": "data_freshness"
}
```

**Complete a pipeline:**

```
POST /api/period-close/complete
{
  "run_id": "PIPE-PRJ-001-20251231120000"
}
```

**Get pipeline run:**

```
GET /api/period-close/run/{run_id}
```

### Pipeline Step States

Each step transitions through the following states:

```
pending --> running --> completed
                   \-> failed
```

When a step fails, it records the error message and duration. Subsequent steps can still be attempted, but a pipeline with any failed step should not be used for sign-off.

### Pipeline Health Monitoring

```
GET /api/period-close/health/{project_id}
```

Returns a health summary for a project's pipeline history:

```json
{
  "last_run": { "run_id": "PIPE-PRJ-001-...", "status": "completed", "..." },
  "total_runs": 3,
  "last_status": "completed",
  "last_duration": 45.2,
  "recent_runs": [ "..." ]
}
```

Use this endpoint to build monitoring dashboards and alerting rules. Key metrics to monitor:

- **last_status**: Should be `completed` after each reporting period
- **last_duration**: Track execution time trends to detect performance degradation
- **failed steps**: Any failed step requires investigation before sign-off

## Best Practices

- **Pre-provision jobs** after each deployment using `POST /api/jobs/provision` to ensure notebook paths are current.
- **Use the satellite_ecl_sync job** for routine model refreshes. Reserve the full_pipeline job for period-end runs where data processing must also execute.
- **Set a random seed** for production Monte Carlo runs to ensure reproducibility. Run without a seed during development for variety in results.
- **Monitor job completion** via the run status API or the Databricks workspace UI. Set up alerting on job failures for production environments.
- **Run the period-end close pipeline** sequentially through all six steps. Do not skip steps, even if you believe the data is correct. The pipeline provides an auditable record that all checks passed.
