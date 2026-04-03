---
sidebar_position: 2
title: "API Reference"
description: "Complete REST API documentation for all platform endpoints."
---

# API Reference

All endpoints are served under the `/api` prefix. Responses are JSON unless otherwise noted. Structured error responses include `error`, `message`, `request_id`, and `path` fields.

Interactive documentation is also available at `/api/swagger` (Swagger UI) and `/api/redoc` (ReDoc).

## Health and Setup

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Basic health check -- verifies Lakebase connectivity |
| GET | `/api/health/detailed` | Detailed health check -- tables, config, scipy availability |
| GET | `/api/setup/status` | Get first-run setup wizard status |
| POST | `/api/setup/validate-tables` | Validate required tables exist in Lakebase |
| POST | `/api/setup/seed-sample-data` | Seed sample portfolio data |
| POST | `/api/setup/complete` | Mark setup as complete |
| POST | `/api/setup/reset` | Reset setup status to incomplete |

## Projects

Project endpoints manage the IFRS 9 workflow lifecycle. Each project tracks its state through a series of steps (data loading, model execution, review, sign-off).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List all projects |
| GET | `/api/projects/{project_id}` | Get project details |
| POST | `/api/projects` | Create a new project |
| POST | `/api/projects/{project_id}/advance` | Advance project to next workflow step |
| POST | `/api/projects/{project_id}/overlays` | Save management overlays |
| POST | `/api/projects/{project_id}/scenario-weights` | Save scenario probability weights |
| POST | `/api/projects/{project_id}/sign-off` | Sign off project (requires `sign_off_projects` permission, enforces segregation of duties) |
| GET | `/api/projects/{project_id}/verify-hash` | Verify SHA-256 hash of signed-off ECL results |
| GET | `/api/projects/{project_id}/approval-history` | Get RBAC approval history for a project |
| POST | `/api/projects/{project_id}/reset` | Reset project to initial state |

**Sign-off request body:**
```json
{
  "name": "Jane Smith",
  "attestation_data": { "role": "CFO", "date": "2025-03-31" }
}
```

## Portfolio Data

All portfolio data endpoints are under `/api/data/` and return arrays of JSON objects. These are read-only queries against the model-ready loan data and computed ECL results.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/data/portfolio-summary` | Aggregated portfolio by product and stage |
| GET | `/api/data/stage-distribution` | Loan count and GCA by IFRS 9 stage |
| GET | `/api/data/borrower-segments` | Borrower segment statistics |
| GET | `/api/data/vintage-analysis` | Vintage cohort analysis |
| GET | `/api/data/dpd-distribution` | Days past due distribution |
| GET | `/api/data/stage-by-product` | Stage distribution broken down by product type |
| GET | `/api/data/pd-distribution` | PD distribution histogram |
| GET | `/api/data/ecl-summary` | Total ECL summary |
| GET | `/api/data/ecl-by-product` | ECL aggregated by product type |
| GET | `/api/data/ecl-by-stage-product/{stage}` | ECL by product for a specific stage |
| GET | `/api/data/scenario-summary` | Scenario-weighted ECL summary |
| GET | `/api/data/ecl-by-scenario-product` | ECL by scenario and product |
| GET | `/api/data/ecl-by-scenario-product-detail?scenario=` | Detailed ECL for a specific scenario |
| GET | `/api/data/mc-distribution` | Monte Carlo ECL distribution |
| GET | `/api/data/concentration-by-segment` | Concentration risk by borrower segment |
| GET | `/api/data/concentration-by-product-stage` | Concentration by product and stage |
| GET | `/api/data/top-concentration-risk` | Highest concentration risk entities |
| GET | `/api/data/ecl-concentration` | ECL concentration analysis |
| GET | `/api/data/top-exposures?limit=20` | Top N loan exposures by GCA |
| GET | `/api/data/sensitivity` | Sensitivity analysis data |
| GET | `/api/data/scenario-comparison` | Side-by-side scenario comparison |
| GET | `/api/data/stress-by-stage` | Stress test results by stage |
| GET | `/api/data/dq-results` | Data quality rule results |
| GET | `/api/data/dq-summary` | Data quality summary statistics |
| GET | `/api/data/gl-reconciliation` | GL reconciliation data |
| GET | `/api/data/stage-migration` | Stage migration matrix |
| GET | `/api/data/credit-risk-exposure` | Credit risk exposure summary |
| GET | `/api/data/loss-allowance-by-stage` | Loss allowance by IFRS 9 stage |
| GET | `/api/data/vintage-performance` | Vintage performance metrics |
| GET | `/api/data/vintage-by-product` | Vintage analysis by product |
| GET | `/api/data/loans-by-product/{product_type}` | Individual loans for a product type |
| GET | `/api/data/loans-by-stage/{stage}` | Individual loans for a stage |

## Simulation

Monte Carlo ECL simulation endpoints. The simulation engine processes all loans across all macro scenarios using vectorized NumPy operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/simulate` | Run Monte Carlo ECL simulation (synchronous) |
| POST | `/api/simulate-stream` | Run simulation with SSE progress streaming |
| POST | `/api/simulate-job` | Run simulation as a Databricks Job |
| POST | `/api/simulate-validate` | Validate simulation parameters before running |
| GET | `/api/simulation-defaults` | Get default simulation parameters and scenarios |
| GET | `/api/simulation/compare?run_a=&run_b=` | Compare two simulation runs |

**Simulation request body:**
```json
{
  "n_simulations": 1000,
  "pd_lgd_correlation": 0.30,
  "aging_factor": 0.08,
  "pd_floor": 0.001,
  "pd_cap": 0.95,
  "lgd_floor": 0.01,
  "lgd_cap": 0.95,
  "scenario_weights": {
    "baseline": 0.30, "mild_recovery": 0.15, "strong_growth": 0.05,
    "mild_downturn": 0.15, "adverse": 0.15, "stagflation": 0.08,
    "severely_adverse": 0.07, "tail_risk": 0.05
  },
  "random_seed": 42
}
```

The `/api/simulate-stream` endpoint returns Server-Sent Events (SSE) with progress updates during the simulation. Event types include `progress` (phase, step, percentage), `result` (final ECL data), and `error`.

## Model Registry

CRUD operations for the model governance registry. Models progress through status transitions (draft, validated, champion, retired).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models?model_type=&status=` | List registered models (filterable) |
| GET | `/api/models/{model_id}` | Get model details |
| POST | `/api/models` | Register a new model |
| PUT | `/api/models/{model_id}/status` | Update model status |
| POST | `/api/models/{model_id}/promote` | Promote model to champion |
| POST | `/api/models/compare` | Compare multiple models side-by-side |
| GET | `/api/models/{model_id}/audit` | Get model audit trail |

## Markov Chain

Transition matrix estimation, stage distribution forecasting, and lifetime PD computation.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/markov/estimate` | Estimate transition matrix from historical data |
| GET | `/api/markov/matrices?product_type=` | List stored transition matrices |
| GET | `/api/markov/matrix/{matrix_id}` | Get a specific transition matrix |
| POST | `/api/markov/forecast` | Forecast stage distribution over a time horizon |
| GET | `/api/markov/lifetime-pd/{matrix_id}?max_months=60` | Compute lifetime PD from matrix powers |
| POST | `/api/markov/compare` | Compare multiple transition matrices |

**Forecast request body:**
```json
{
  "matrix_id": "mtx_residential_mortgage_2025Q1",
  "initial_distribution": [0.80, 0.12, 0.05, 0.03],
  "horizon_months": 60
}
```

## Hazard Models

Survival analysis models for PD term structure estimation.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/hazard/estimate` | Estimate a hazard model (Cox PH, Kaplan-Meier, or discrete-time logistic) |
| GET | `/api/hazard/models?model_type=&product_type=` | List stored hazard models |
| GET | `/api/hazard/model/{model_id}` | Get hazard model details |
| POST | `/api/hazard/survival-curve` | Compute survival curve for given covariates |
| GET | `/api/hazard/term-structure/{model_id}?max_months=60` | Compute PD term structure |
| POST | `/api/hazard/compare` | Compare multiple hazard models |

## Backtesting

PD model backtesting with statistical tests.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/backtest/run` | Run a backtest (PD or LGD) |
| GET | `/api/backtest/results?model_type=` | List backtest results |
| GET | `/api/backtest/trend/{model_type}` | Get backtest metric trend over time |
| GET | `/api/backtest/{backtest_id}` | Get detailed backtest results |

## Attribution

ECL waterfall attribution analysis -- decomposes ECL changes into contributing factors.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/data/attribution/{project_id}` | Get stored attribution for a project |
| POST | `/api/data/attribution/{project_id}/compute` | Compute fresh attribution analysis |
| GET | `/api/data/attribution/{project_id}/history` | Get attribution computation history |

## Satellite Models and Model Runs

Satellite model comparison data and simulation run persistence.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/data/satellite-model-comparison?run_id=` | Satellite model comparison data |
| GET | `/api/data/satellite-model-selected?run_id=` | Selected (best) satellite model data |
| GET | `/api/model-runs?run_type=` | List model runs (satellite, Monte Carlo, etc.) |
| GET | `/api/model-runs/{run_id}` | Get model run details |
| POST | `/api/model-runs` | Save a model run record |
| GET | `/api/data/cohort-summary` | Cohort summary across all products |
| GET | `/api/data/cohort-summary/{product}` | Cohort summary for a specific product |
| GET | `/api/data/drill-down-dimensions?product=` | Available drill-down dimensions |
| GET | `/api/data/ecl-by-cohort?product=&dimension=` | ECL broken down by cohort dimension |
| GET | `/api/data/stage-by-cohort?product=` | Stage distribution by cohort |
| GET | `/api/data/portfolio-by-cohort?product=&dimension=` | Portfolio data by cohort dimension |
| GET | `/api/data/ecl-by-product-drilldown` | ECL by product with drill-down data |

## Reports

Regulatory report generation, export, and finalization.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/reports/generate/{project_id}` | Generate a report (types: `ifrs7_disclosure`, `ecl_movement`, `stage_migration`, `sensitivity_analysis`, `concentration_risk`) |
| GET | `/api/reports?project_id=&report_type=` | List reports (filterable) |
| GET | `/api/reports/{report_id}` | Get report details |
| GET | `/api/reports/{report_id}/export` | Export report as CSV |
| GET | `/api/reports/{report_id}/export/pdf` | Export report as PDF |
| POST | `/api/reports/{report_id}/finalize` | Mark report as finalized |

## GL Journals

General ledger journal entry generation, posting, and reversal.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/gl/generate/{project_id}` | Generate ECL journal entries for a project |
| GET | `/api/gl/journals/{project_id}` | List journals for a project |
| GET | `/api/gl/journal/{journal_id}` | Get journal details |
| POST | `/api/gl/journal/{journal_id}/post` | Post journal to ledger |
| POST | `/api/gl/journal/{journal_id}/reverse` | Reverse a posted journal |
| GET | `/api/gl/trial-balance/{project_id}` | Get trial balance for a project |
| GET | `/api/gl/chart-of-accounts` | Get the chart of accounts |

## RBAC and Approvals

User management, role-based permissions, and multi-level approval workflows.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rbac/users?role=` | List users (filterable by role) |
| GET | `/api/rbac/users/{user_id}` | Get user details |
| GET | `/api/rbac/permissions/{user_id}` | Check user permissions |
| GET | `/api/rbac/approvals?status=&assigned_to=&type=` | List approval requests |
| POST | `/api/rbac/approvals` | Create an approval request |
| POST | `/api/rbac/approvals/{request_id}/approve` | Approve a request |
| POST | `/api/rbac/approvals/{request_id}/reject` | Reject a request |
| GET | `/api/rbac/approvals/history/{entity_id}` | Get approval history for an entity |

## Advanced ECL Features

Cure rate analysis, credit conversion factors (CCF), and collateral haircut computation.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/advanced/cure-rates/compute` | Compute cure rates (optionally by product) |
| GET | `/api/advanced/cure-rates` | List cure rate analyses |
| GET | `/api/advanced/cure-rates/{analysis_id}` | Get cure rate analysis details |
| POST | `/api/advanced/ccf/compute` | Compute credit conversion factors |
| GET | `/api/advanced/ccf` | List CCF analyses |
| GET | `/api/advanced/ccf/{analysis_id}` | Get CCF analysis details |
| POST | `/api/advanced/collateral/compute` | Compute collateral haircuts |
| GET | `/api/advanced/collateral` | List collateral analyses |
| GET | `/api/advanced/collateral/{analysis_id}` | Get collateral analysis details |

## Admin Configuration

Platform configuration management, table discovery, and column mapping validation.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/config` | Get full admin configuration |
| PUT | `/api/admin/config` | Save full admin configuration |
| GET | `/api/admin/config/{section}` | Get a configuration section |
| PUT | `/api/admin/config/{section}` | Save a configuration section |
| POST | `/api/admin/validate-mapping` | Validate a column mapping |
| POST | `/api/admin/validate-mapping-typed` | Validate mapping with type checking |
| GET | `/api/admin/available-tables` | List available Lakebase tables |
| GET | `/api/admin/table-columns/{table}` | Get columns for a table |
| GET | `/api/admin/table-preview/{table}?schema=&limit=5` | Preview rows from a table |
| GET | `/api/admin/schemas` | List available schemas |
| GET | `/api/admin/suggest-mappings/{table_key}` | Auto-suggest column mappings |
| POST | `/api/admin/test-connection` | Test Lakebase connection |
| POST | `/api/admin/seed-defaults` | Seed default configuration values |
| GET | `/api/admin/auto-detect-workspace` | Auto-detect Databricks workspace settings |
| GET | `/api/admin/discover-products` | Discover product types from loan data |
| POST | `/api/admin/auto-setup-lgd` | Auto-configure LGD assumptions from data |

## Jobs

Databricks Job orchestration for scalable compute.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/jobs/trigger` | Trigger a managed job (`satellite_ecl_sync`, `full_pipeline`, `demo_data`, `monte_carlo`) |
| GET | `/api/jobs/run/{run_id}` | Get job run status |
| GET | `/api/jobs/runs/{job_key}?limit=10` | List recent runs for a job |
| GET | `/api/jobs/config` | Get jobs configuration (available models, job IDs, workspace info) |
| POST | `/api/jobs/provision` | Create or update all managed Databricks Jobs |

## Audit Trail

Immutable, hash-chained audit trail for regulatory compliance.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit/{project_id}?offset=0&limit=100` | Get paginated audit trail with chain verification |
| GET | `/api/audit/{project_id}/verify` | Verify audit chain integrity |
| GET | `/api/audit/{project_id}/export` | Export audit package as JSON |
| GET | `/api/audit/config/changes?section=&limit=100` | Get configuration change audit log |
| GET | `/api/audit/config/diff?start=&end=&section=` | Get configuration diff between timestamps |

## Pipeline (Period-End Close)

Orchestrated period-end close pipeline with sequential step execution.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pipeline/start/{project_id}` | Start a new pipeline run |
| GET | `/api/pipeline/steps` | List all pipeline step definitions |
| GET | `/api/pipeline/run/{run_id}` | Get pipeline run status and step details |
| POST | `/api/pipeline/run/{run_id}/execute-step` | Execute a single pipeline step |
| POST | `/api/pipeline/run/{run_id}/complete` | Mark pipeline run as completed |
| GET | `/api/pipeline/health/{project_id}` | Get pipeline health summary |
| POST | `/api/pipeline/run-all/{project_id}` | Run all pipeline steps sequentially (stops on first failure) |

## Data Mapping

Unity Catalog browsing, column mapping, and data ingestion into Lakebase.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/data-mapping/catalogs` | List Unity Catalog catalogs |
| GET | `/api/data-mapping/schemas/{catalog}` | List schemas in a catalog |
| GET | `/api/data-mapping/tables/{catalog}/{schema}` | List tables in a schema |
| GET | `/api/data-mapping/columns/{catalog}/{schema}/{table}` | Get column metadata |
| POST | `/api/data-mapping/preview` | Preview rows from a source table |
| POST | `/api/data-mapping/suggest` | Auto-suggest column mappings by name matching |
| POST | `/api/data-mapping/validate` | Validate a column mapping configuration |
| POST | `/api/data-mapping/apply` | Apply mapping and ingest data from UC to Lakebase |
| GET | `/api/data-mapping/status` | Get data mapping status for all ECL tables |

## Error Responses

All endpoints return structured errors:

```json
{
  "error": "internal_server_error",
  "message": "Descriptive error message",
  "request_id": "a1b2c3d4e5f6",
  "path": "/api/simulate"
}
```

Common HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Validation error or bad request |
| 403 | Permission denied or project locked |
| 404 | Resource not found |
| 500 | Internal server error |
