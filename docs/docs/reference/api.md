---
sidebar_position: 2
title: API Reference
---

# API Reference

The backend exposes a RESTful API via FastAPI. Interactive documentation is available at `/api/swagger` (Swagger UI) and `/api/redoc` (ReDoc).

## Base URL

All endpoints are prefixed with `/api`. When running locally, the default URL is `http://localhost:8000/api`.

## Authentication

When deployed on Databricks Apps, authentication is handled via Databricks OAuth. All requests inherit the user's workspace identity.

## Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness check (queries `SELECT 1`) |
| `GET` | `/api/health/detailed` | Full health check across all subsystems |

## Projects

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/projects` | List all ECL projects |
| `GET` | `/api/projects/{project_id}` | Get single project |
| `POST` | `/api/projects` | Create new project |
| `POST` | `/api/projects/{project_id}/advance` | Advance workflow step |
| `POST` | `/api/projects/{project_id}/overlays` | Save management overlays |
| `POST` | `/api/projects/{project_id}/scenario-weights` | Save scenario weights |
| `POST` | `/api/projects/{project_id}/sign-off` | Sign off and lock project |
| `GET` | `/api/projects/{project_id}/verify-hash` | Verify ECL hash integrity |
| `POST` | `/api/projects/{project_id}/reset` | Reset project workflow |

## Portfolio Data

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/data/portfolio-summary` | Portfolio KPI summary |
| `GET` | `/api/data/stage-distribution` | Stage distribution (count and GCA) |
| `GET` | `/api/data/borrower-segments` | Segment-level statistics |
| `GET` | `/api/data/vintage-analysis` | Vintage cohort performance |
| `GET` | `/api/data/dpd-distribution` | DPD bucket distribution |
| `GET` | `/api/data/pd-distribution` | PD score distribution |
| `GET` | `/api/data/stage-by-product` | Stage mix per product |

## Data Quality & GL

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/data/dq-results` | Data quality check results |
| `GET` | `/api/data/dq-summary` | DQ score summary |
| `GET` | `/api/data/gl-reconciliation` | GL vs loan-tape variance |

## ECL Results

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/data/ecl-summary` | ECL totals |
| `GET` | `/api/data/ecl-by-product` | ECL by product type |
| `GET` | `/api/data/ecl-by-stage-product/{stage}` | ECL by product for a stage |
| `GET` | `/api/data/ecl-by-cohort?product=X` | ECL by cohort (drill-down) |
| `GET` | `/api/data/ecl-by-scenario-product` | ECL cross-tabulated by scenario and product |
| `GET` | `/api/data/scenario-summary` | Scenario-level ECL |
| `GET` | `/api/data/loss-allowance-by-stage` | Loss allowance by stage |
| `GET` | `/api/data/mc-distribution` | Monte Carlo ECL distribution |
| `GET` | `/api/data/top-exposures?limit=N` | Top N exposures by ECL |
| `GET` | `/api/data/credit-risk-exposure` | Credit risk grade exposure |
| `GET` | `/api/data/concentration-by-product-stage` | Concentration heatmap |

## Satellite Models

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/data/satellite-model-comparison` | All model fit metrics per cohort |
| `GET` | `/api/data/satellite-model-selected` | Best model per cohort |
| `GET` | `/api/model-runs` | List model runs |
| `POST` | `/api/model-runs` | Save model run metadata |
| `GET` | `/api/data/cohort-summary` | Cohort-level summary |
| `GET` | `/api/data/ecl-by-cohort?product=X&dimension=Y` | Cohort drill-down |

## Simulation

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/simulate` | Run Monte Carlo (synchronous) |
| `POST` | `/api/simulate-stream` | Run with SSE streaming progress |
| `POST` | `/api/simulate-job` | Run as Databricks Job |
| `POST` | `/api/simulate-validate` | Validate parameters |
| `GET` | `/api/simulation-defaults` | Get default parameters |

## Stress Testing

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/data/sensitivity` | PD/LGD sensitivity data |
| `GET` | `/api/data/scenario-comparison` | Side-by-side scenario comparison |
| `GET` | `/api/data/stress-by-stage` | ECL under stress by stage |
| `GET` | `/api/data/vintage-performance` | Vintage default rate performance |
| `GET` | `/api/data/concentration-by-product-stage` | Concentration heatmap |

## Attribution

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/data/attribution/{project_id}` | Get ECL attribution waterfall |
| `POST` | `/api/data/attribution/{project_id}/compute` | Compute attribution |

## Model Registry

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/models` | List models (filter by type/status) |
| `POST` | `/api/models` | Register new model |
| `PUT` | `/api/models/{model_id}/status` | Update lifecycle status |
| `POST` | `/api/models/{model_id}/promote` | Promote to champion |
| `POST` | `/api/models/compare` | Compare models side-by-side |

## Backtesting

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/backtest/run` | Run backtest |
| `GET` | `/api/backtest/results` | List results (filter by model type) |
| `GET` | `/api/backtest/trend/{model_type}` | Trend over time |
| `GET` | `/api/backtest/{backtest_id}` | Single result detail |

## GL Journals

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/gl/generate/{project_id}` | Generate ECL journals |
| `GET` | `/api/gl/journals/{project_id}` | List journals |
| `GET` | `/api/gl/journal/{journal_id}` | Journal detail |
| `POST` | `/api/gl/journal/{journal_id}/post` | Post to GL |
| `POST` | `/api/gl/journal/{journal_id}/reverse` | Reverse journal |
| `GET` | `/api/gl/trial-balance/{project_id}` | Trial balance |
| `GET` | `/api/gl/chart-of-accounts` | Chart of accounts |

## Reports

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/reports/generate/{project_id}` | Generate report |
| `GET` | `/api/reports` | List reports |
| `GET` | `/api/reports/{report_id}` | Get report |
| `GET` | `/api/reports/{report_id}/export` | Export as CSV |
| `POST` | `/api/reports/{report_id}/finalize` | Finalize report |

Report types: `ifrs7_disclosure`, `ecl_movement`, `stage_migration`, `sensitivity_analysis`, `concentration_risk`.

## Jobs

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/jobs/trigger` | Trigger a Databricks job |
| `GET` | `/api/jobs/run/{run_id}` | Job run status |
| `GET` | `/api/jobs/runs/{job_key}` | Recent runs for a job |
| `GET` | `/api/jobs/config` | Job configuration |
| `POST` | `/api/jobs/provision` | Provision managed jobs |

## RBAC & Approvals

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/rbac/users` | List users |
| `GET` | `/api/rbac/approvals` | List approval requests |
| `POST` | `/api/rbac/approvals` | Create request |
| `POST` | `/api/rbac/approvals/{id}/approve` | Approve |
| `POST` | `/api/rbac/approvals/{id}/reject` | Reject |

## Admin Configuration

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/config` | Get config |
| `PUT` | `/api/admin/config` | Save config |
| `POST` | `/api/admin/test-connection` | Test Lakebase connection |
| `POST` | `/api/admin/seed-defaults` | Reset to defaults |
| `GET` | `/api/admin/suggest-mappings/{table_key}` | Auto-suggest column mappings |

## Audit

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/audit/{project_id}` | Project audit trail |
| `GET` | `/api/audit/{project_id}/verify` | Verify chain integrity |
| `GET` | `/api/audit/{project_id}/export` | Export audit package |
| `GET` | `/api/audit/config/changes` | Config change log |

## Advanced Analytics

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/markov/estimate` | Estimate transition matrix |
| `POST` | `/api/markov/forecast` | Forecast stage distribution |
| `GET` | `/api/markov/lifetime-pd/{matrix_id}` | Lifetime PD from matrix |
| `POST` | `/api/hazard/estimate` | Estimate hazard model |
| `POST` | `/api/hazard/survival-curve` | Compute survival curve |
| `POST` | `/api/advanced/cure-rates/compute` | Compute cure rates |
| `POST` | `/api/advanced/ccf/compute` | Compute Credit Conversion Factors |
| `POST` | `/api/advanced/collateral/compute` | Compute collateral haircuts |
