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

## Triggering Jobs

Jobs are triggered from the **Jobs** page in the application. Select a job type and optionally override parameters before running.

### Available Parameters

When triggering a job, you can override these parameters for the run:

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Enabled Models** | All enabled in config | Select which satellite models to train for this run |
| **Simulation Count** | 1,000 | Number of Monte Carlo simulation paths |
| **PD-LGD Correlation** | 0.30 | Correlation between PD and LGD shocks |
| **Aging Factor** | 0.08 | Annual PD aging adjustment |
| **PD Floor / Cap** | 0.001 / 0.95 | Bounds on simulated PD values |
| **LGD Floor / Cap** | 0.01 / 0.95 | Bounds on simulated LGD values |
| **Random Seed** | None | Fix the seed for reproducible results |
| **Scenario Weights** | Config default | Override probability weights for this run |

Per-run overrides do not change the persisted configuration — they apply only to that specific run.

### Monitoring Job Runs

After triggering a job, the Jobs page shows real-time status including:

- Overall job state (Running, Succeeded, Failed)
- Per-task breakdown — each satellite model task shows its individual status
- Execution duration
- Direct link to the Databricks workspace for detailed logs

### Job Provisioning

Jobs are auto-provisioned on first trigger — the platform creates the Databricks workflow with the correct notebook paths and serverless environment. After a code redeployment, use the **Provision Jobs** button on the Jobs page to update notebook paths.

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

:::tip
For production period-end runs, increase simulations to 5,000-10,000 and set a random seed for reproducibility. For development and testing, 1,000 simulations is sufficient.
:::

## Scripts Base Path

The platform needs to know where pipeline notebook scripts are deployed in the workspace. It uses an automatic four-step detection strategy:

1. **Admin config override** — If you set the scripts base path explicitly in **Admin > Jobs Configuration**, that value is used. This is the recommended approach for production.
2. **App source code path** — Derived from the Databricks App deployment location.
3. **App info lookup** — Queried from the Databricks Apps API.
4. **Workspace convention** — Falls back to the standard user workspace path.

If auto-detection is not finding the correct path, set it explicitly in **Admin > Jobs Configuration** under the **Scripts Base Path** field.

## Compute Configuration

Jobs default to **serverless compute**, which requires no cluster management and provides fast startup times. The serverless environment automatically includes the required Python dependencies (scikit-learn, xgboost, optuna, psycopg2-binary).

If you need to use a dedicated cluster instead of serverless, change the compute setting in **Admin > Jobs Configuration** to use a cluster specification.

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

### Running the Pipeline

The period-end close pipeline is accessed from the project's workflow page. To run it:

1. Navigate to the project's workflow page
2. Click **Start Period-End Close**
3. Execute each step sequentially — the pipeline guides you through the six steps in order
4. Review the results of each step before proceeding to the next
5. Once all steps complete successfully, click **Complete Pipeline**

### Pipeline Step States

Each step transitions through the following states: **Pending** (not yet started) to **Running** (executing checks) to **Completed** (all checks passed) or **Failed** (one or more checks did not pass).

When a step fails, the pipeline shows the specific error message. Subsequent steps can still be attempted, but a pipeline with any failed step should not be used for sign-off. Investigate and resolve failures before proceeding.

### Pipeline Health Monitoring

The pipeline dashboard shows a health summary for each project, including:

- **Last run status** — Should be "Completed" after each reporting period
- **Execution duration** — Track trends to detect performance degradation
- **Total runs** — History of all pipeline executions for the project
- **Failed steps** — Any failed step requires investigation before sign-off

## Best Practices

- **Pre-provision jobs** after each deployment using `POST /api/jobs/provision` to ensure notebook paths are current.
- **Use the satellite_ecl_sync job** for routine model refreshes. Reserve the full_pipeline job for period-end runs where data processing must also execute.
- **Set a random seed** for production Monte Carlo runs to ensure reproducibility. Run without a seed during development for variety in results.
- **Monitor job completion** via the Jobs page or the Databricks workspace UI. Set up alerting on job failures for production environments.
- **Run the period-end close pipeline** sequentially through all six steps. Do not skip steps, even if you believe the data is correct. The pipeline provides an auditable record that all checks passed.

## What's Next?

- [Model Configuration](model-configuration) — Configure the satellite models and parameters used by these jobs
- [App Settings](app-settings) — Define scenarios and governance thresholds used during period-end close
- [System Administration](system-administration) — Monitor platform health and job infrastructure
- [Troubleshooting](troubleshooting) — Resolve job execution failures and script path issues
