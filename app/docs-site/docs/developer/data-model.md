---
sidebar_position: 3
title: "Data Model"
description: "Database schema, table definitions, and data relationships."
---

# Data Model

All platform data is stored in Databricks Lakebase (PostgreSQL wire protocol). This page documents the schema layout, table definitions, column specifications, and relationships between tables.

## Schema and Naming Conventions

| Property | Value |
|----------|-------|
| **Schema** | `expected_credit_loss` (configurable via admin config) |
| **Table prefix** | `lb_` (configurable via admin config) |
| **Table reference helper** | `backend._t(name)` resolves to `{schema}.{prefix}{name}` |

For example, `_t('model_ready_loans')` resolves to `expected_credit_loss.lb_model_ready_loans`.

Tables without the `lb_` prefix (such as `ecl_workflow`, `model_registry`, `audit_trail`) use the schema name directly (e.g., `expected_credit_loss.ecl_workflow`).

## Entity Relationship Overview

```
lb_model_ready_loans ──────────┐
  (loan_id, product_type,      │
   assessed_stage, GCA, PD)    │
                               │
lb_borrower_master ────────────┤  ── Portfolio Data
  (borrower_id, segment,       │
   risk_rating)                │
                               │
lb_historical_defaults ────────┘
  (loan_id, default_date)

lb_model_run_results ──────────┐
  (run_id, loan_id,            │
   weighted_ecl)               │  ── ECL Results
                               │
lb_mc_ecl_distribution ────────┘
  (scenario, ecl_mean, p50-p99)

ecl_workflow ──────────────────┐
  (project_id, step_status,    │
   signed_off, ecl_hash)       │
                               │
audit_trail ───────────────────┤  ── Governance
  (project_id, action,         │
   prev_hash, current_hash)    │
                               │
rbac_users ────────────────────┤
rbac_approval_requests ────────┘

model_registry ────────────────┐
model_registry_audit ──────────┘  ── Model Governance

markov_transition_matrices ────┐
markov_forecasts ──────────────┤
hazard_models ─────────────────┤  ── ECL Features
hazard_curves ─────────────────┤
backtesting_results ───────────┤
model_runs ────────────────────┤
lb_attribution ────────────────┘

reports ───────────────────────┐
gl_chart_of_accounts ──────────┤  ── Reporting
gl_journals ───────────────────┤
gl_line ───────────────────────┘

lb_dq_results ─────────────────┐  ── Data Quality
pipeline_runs ─────────────────┘

app_config ────────────────────── Configuration
```

## Portfolio Tables

### lb_model_ready_loans

The primary loan-level table consumed by the ECL simulation engine. Each row represents a single loan with its current risk parameters.

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | TEXT (PK) | Unique loan identifier |
| `borrower_id` | TEXT | Foreign key to borrower master |
| `product_type` | TEXT | Product category (e.g., `credit_card`, `residential_mortgage`, `commercial_loan`, `personal_loan`, `auto_loan`) |
| `assessed_stage` | INTEGER | IFRS 9 stage (1, 2, or 3) |
| `gross_carrying_amount` | NUMERIC | Current gross carrying amount |
| `effective_interest_rate` | NUMERIC | Annualized effective interest rate |
| `current_lifetime_pd` | NUMERIC | Annualized point-in-time PD (converted to quarterly in the engine) |
| `remaining_months` | INTEGER | Remaining contractual term in months |
| `days_past_due` | INTEGER | Current days past due |
| `origination_date` | DATE | Loan origination date |
| `maturity_date` | DATE | Contractual maturity date |
| `collateral_value` | NUMERIC | Collateral value (if secured) |
| `risk_rating` | TEXT | Internal risk rating |
| `segment` | TEXT | Borrower segment classification |

### lb_borrower_master

Borrower-level attributes for segmentation and concentration analysis.

| Column | Type | Description |
|--------|------|-------------|
| `borrower_id` | TEXT (PK) | Unique borrower identifier |
| `borrower_name` | TEXT | Borrower name |
| `segment` | TEXT | Business segment |
| `industry` | TEXT | Industry classification |
| `region` | TEXT | Geographic region |
| `risk_rating` | TEXT | Borrower-level risk rating |
| `total_exposure` | NUMERIC | Total exposure across all facilities |

### lb_historical_defaults

Historical default events used for transition matrix estimation, hazard model training, and backtesting.

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | TEXT | Loan that defaulted |
| `default_date` | DATE | Date of default event |
| `cure_date` | DATE | Date of cure (if applicable) |
| `loss_amount` | NUMERIC | Realized loss amount |
| `recovery_amount` | NUMERIC | Recovery amount |
| `product_type` | TEXT | Product type at default |
| `stage_at_default` | INTEGER | IFRS 9 stage immediately before default |

## ECL Result Tables

### lb_model_run_results

Loan-level ECL results from each simulation run.

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | TEXT | Simulation run identifier |
| `loan_id` | TEXT | Loan identifier |
| `product_type` | TEXT | Product type |
| `assessed_stage` | INTEGER | IFRS 9 stage |
| `gross_carrying_amount` | NUMERIC | GCA at time of run |
| `weighted_ecl` | NUMERIC | Scenario-weighted expected credit loss |
| `coverage_ratio` | NUMERIC | ECL / GCA as a percentage |
| `computed_at` | TIMESTAMP | When the result was computed |

### lb_mc_ecl_distribution

Scenario-level Monte Carlo distribution statistics from each simulation run.

| Column | Type | Description |
|--------|------|-------------|
| `scenario` | TEXT | Macro scenario name |
| `weight` | NUMERIC | Scenario probability weight |
| `ecl_mean` | NUMERIC | Mean ECL across simulations |
| `ecl_p50` | NUMERIC | Median (50th percentile) ECL |
| `ecl_p75` | NUMERIC | 75th percentile ECL |
| `ecl_p95` | NUMERIC | 95th percentile ECL |
| `ecl_p99` | NUMERIC | 99th percentile ECL |
| `avg_pd_multiplier` | NUMERIC | PD stress multiplier for this scenario |
| `avg_lgd_multiplier` | NUMERIC | LGD stress multiplier for this scenario |
| `pd_vol` | NUMERIC | PD volatility parameter |
| `lgd_vol` | NUMERIC | LGD volatility parameter |
| `n_simulations` | INTEGER | Number of Monte Carlo paths |

## Workflow and Governance Tables

### ecl_workflow

Project state machine. Each project tracks its progression through the IFRS 9 workflow.

| Column | Type | Description |
|--------|------|-------------|
| `project_id` | TEXT (PK) | Unique project identifier |
| `project_name` | TEXT | Human-readable project name |
| `project_type` | TEXT | Type (default: `ifrs9`) |
| `description` | TEXT | Project description |
| `reporting_date` | TEXT | Reporting period date |
| `step_status` | JSONB | Current status of each workflow step |
| `current_step` | TEXT | Active workflow step |
| `overlays` | JSONB | Management overlay adjustments |
| `scenario_weights` | JSONB | Scenario probability weights |
| `audit_log` | JSONB | Embedded audit log entries |
| `signed_off` | BOOLEAN | Whether the project is signed off (immutable) |
| `signed_off_by` | TEXT | User who signed off |
| `signed_off_at` | TIMESTAMP | Sign-off timestamp |
| `ecl_hash` | TEXT | SHA-256 hash of ECL results at sign-off |
| `created_at` | TIMESTAMP | Project creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

### audit_trail

Immutable, hash-chained audit log for regulatory compliance. Each entry includes the SHA-256 hash of the previous entry, forming a tamper-evident chain.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL (PK) | Auto-incrementing row ID |
| `project_id` | TEXT | Associated project |
| `action` | TEXT | Action performed (e.g., `sign_off`, `advance_step`, `overlay_save`) |
| `user_id` | TEXT | User who performed the action |
| `timestamp` | TIMESTAMP | When the action occurred |
| `detail` | JSONB | Action-specific metadata |
| `prev_hash` | TEXT | SHA-256 hash of the previous audit entry |
| `current_hash` | TEXT | SHA-256 hash of this entry (including prev_hash) |

### rbac_users

User accounts and role assignments.

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | TEXT (PK) | Unique user identifier (email) |
| `email` | TEXT | User email address |
| `display_name` | TEXT | Display name |
| `role` | TEXT | Role (`analyst`, `reviewer`, `approver`, `admin`) |
| `permissions` | JSONB | Explicit permission overrides |
| `created_at` | TIMESTAMP | Account creation timestamp |

### rbac_approval_requests

Multi-level approval workflow records.

| Column | Type | Description |
|--------|------|-------------|
| `request_id` | TEXT (PK) | Unique request identifier |
| `request_type` | TEXT | Type of approval (e.g., `sign_off`, `model_promotion`) |
| `entity_id` | TEXT | ID of the entity being approved |
| `entity_type` | TEXT | Type of entity |
| `requested_by` | TEXT | User who initiated the request |
| `assigned_to` | TEXT | User assigned to review |
| `status` | TEXT | Status (`pending`, `approved`, `rejected`) |
| `priority` | TEXT | Priority level |
| `due_date` | DATE | Due date for review |
| `comments` | TEXT | Request comments |
| `resolved_by` | TEXT | User who resolved the request |
| `resolved_at` | TIMESTAMP | Resolution timestamp |
| `resolution_comment` | TEXT | Resolution comment |

## Model Governance Tables

### model_registry

Central registry for all models (PD, LGD, EAD, satellite, etc.) with lifecycle status tracking.

| Column | Type | Description |
|--------|------|-------------|
| `model_id` | TEXT (PK) | Unique model identifier |
| `model_name` | TEXT | Model display name |
| `model_type` | TEXT | Model category (e.g., `PD`, `LGD`, `satellite`) |
| `algorithm` | TEXT | Algorithm name |
| `version` | INTEGER | Model version number |
| `status` | TEXT | Lifecycle status (`draft`, `validated`, `champion`, `retired`) |
| `product_type` | TEXT | Associated product type |
| `cohort` | TEXT | Training cohort |
| `parameters` | JSONB | Model hyperparameters |
| `performance_metrics` | JSONB | Validation metrics (AUC, Gini, KS, etc.) |
| `training_data_info` | JSONB | Training data metadata |
| `created_by` | TEXT | User who registered the model |
| `parent_model_id` | TEXT | Parent model (for versioning chains) |
| `notes` | TEXT | Free-text notes |
| `created_at` | TIMESTAMP | Registration timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

### model_registry_audit

Audit trail for model status changes.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL (PK) | Auto-incrementing ID |
| `model_id` | TEXT | Model that was changed |
| `action` | TEXT | Action (e.g., `status_change`, `promote_champion`) |
| `old_status` | TEXT | Previous status |
| `new_status` | TEXT | New status |
| `user_id` | TEXT | User who made the change |
| `comment` | TEXT | Change comment |
| `timestamp` | TIMESTAMP | When the change occurred |

## ECL Feature Tables

### markov_transition_matrices

Estimated stage transition matrices for Markov chain modeling.

| Column | Type | Description |
|--------|------|-------------|
| `matrix_id` | TEXT (PK) | Unique matrix identifier |
| `model_name` | TEXT | Model name |
| `estimation_date` | DATE | Date of estimation |
| `matrix_data` | JSONB | 4x4 transition matrix (Stage 1, Stage 2, Stage 3, Default) |
| `matrix_type` | TEXT | Frequency (`annual`, `quarterly`) |
| `product_type` | TEXT | Product type (or all) |
| `segment` | TEXT | Borrower segment (or all) |
| `methodology` | TEXT | Estimation methodology (`cohort`) |
| `n_observations` | INTEGER | Number of observations used |
| `computed_at` | TIMESTAMP | Computation timestamp |

### markov_forecasts

Forecasted stage distributions from matrix exponentiation.

| Column | Type | Description |
|--------|------|-------------|
| `forecast_id` | TEXT (PK) | Unique forecast identifier |
| `matrix_id` | TEXT | Source transition matrix |
| `horizon_months` | INTEGER | Forecast horizon |
| `forecast_data` | JSONB | Period-by-period stage distribution |
| `created_at` | TIMESTAMP | Creation timestamp |

### hazard_models

Fitted survival analysis models (Cox PH, Kaplan-Meier, discrete-time logistic).

| Column | Type | Description |
|--------|------|-------------|
| `model_id` | TEXT (PK) | Unique model identifier |
| `model_type` | TEXT | Type (`cox_ph`, `kaplan_meier`, `discrete_logistic`) |
| `product_type` | TEXT | Product type |
| `segment` | TEXT | Borrower segment |
| `coefficients` | JSONB | Model coefficients or parameters |
| `fit_statistics` | JSONB | Goodness-of-fit statistics |
| `n_observations` | INTEGER | Training sample size |
| `created_at` | TIMESTAMP | Creation timestamp |

### hazard_curves

Precomputed survival and hazard curves from fitted models.

| Column | Type | Description |
|--------|------|-------------|
| `curve_id` | TEXT (PK) | Unique curve identifier |
| `model_id` | TEXT | Source hazard model |
| `curve_type` | TEXT | Type (`survival`, `hazard`, `cumulative_hazard`) |
| `curve_data` | JSONB | Time-indexed curve values |
| `covariates` | JSONB | Covariates used for this curve |
| `created_at` | TIMESTAMP | Creation timestamp |

### backtesting_results

PD model backtesting results with statistical test outcomes.

| Column | Type | Description |
|--------|------|-------------|
| `backtest_id` | TEXT (PK) | Unique backtest identifier |
| `model_type` | TEXT | Model type tested (e.g., `PD`) |
| `config` | JSONB | Backtest configuration |
| `results` | JSONB | Test results (binomial, traffic light, Hosmer-Lemeshow) |
| `overall_status` | TEXT | Aggregate pass/fail status |
| `created_at` | TIMESTAMP | When the backtest ran |

### model_runs

Persisted records of simulation and satellite model runs.

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | TEXT (PK) | Unique run identifier |
| `run_type` | TEXT | Type (`monte_carlo_simulation`, `satellite_model`, etc.) |
| `models_used` | JSONB | List of model keys used |
| `products` | JSONB | Product types processed |
| `total_cohorts` | INTEGER | Number of cohorts |
| `best_model_summary` | JSONB | Summary statistics (seed, total ECL, convergence) |
| `notes` | TEXT | Run notes |
| `run_timestamp` | TIMESTAMP | Run timestamp |

### lb_attribution

ECL waterfall attribution decomposing period-over-period changes.

| Column | Type | Description |
|--------|------|-------------|
| `project_id` | TEXT | Associated project |
| `attribution_data` | JSONB | Waterfall decomposition (volume, PD, LGD, model, overlay, etc.) |
| `computed_at` | TIMESTAMP | Computation timestamp |

## Advanced Feature Tables

### cure_rates, ccf, collateral_haircuts

Tables for advanced ECL parameters, each following a similar pattern:

| Column | Type | Description |
|--------|------|-------------|
| `analysis_id` | TEXT (PK) | Unique analysis identifier |
| `product_type` | TEXT | Product type |
| `results` | JSONB | Analysis results |
| `computed_at` | TIMESTAMP | Computation timestamp |

## Reporting Tables

### reports

Generated regulatory reports (IFRS 7, ECL movement, sensitivity, concentration).

| Column | Type | Description |
|--------|------|-------------|
| `report_id` | TEXT (PK) | Unique report identifier |
| `project_id` | TEXT | Associated project |
| `report_type` | TEXT | Report type |
| `report_date` | TEXT | Reporting date |
| `report_data` | JSONB | Full report content (sections, tables, narratives) |
| `status` | TEXT | Status (`draft`, `finalized`) |
| `created_by` | TEXT | User who generated the report |
| `created_at` | TIMESTAMP | Generation timestamp |

### gl_chart_of_accounts

Chart of accounts for ECL-related GL entries.

| Column | Type | Description |
|--------|------|-------------|
| `account_code` | TEXT (PK) | GL account code |
| `account_name` | TEXT | Account name |
| `account_type` | TEXT | Type (asset, liability, expense, etc.) |
| `parent_code` | TEXT | Parent account code |

### gl_journals and gl_line

Journal headers and line items for ECL accounting entries.

**gl_journals:**

| Column | Type | Description |
|--------|------|-------------|
| `journal_id` | TEXT (PK) | Unique journal identifier |
| `project_id` | TEXT | Associated project |
| `journal_date` | DATE | Journal date |
| `status` | TEXT | Status (`draft`, `posted`, `reversed`) |
| `posted_by` | TEXT | User who posted |
| `posted_at` | TIMESTAMP | Posting timestamp |
| `reversed_by` | TEXT | User who reversed |
| `reversed_at` | TIMESTAMP | Reversal timestamp |

**gl_line:**

| Column | Type | Description |
|--------|------|-------------|
| `line_id` | SERIAL (PK) | Auto-incrementing ID |
| `journal_id` | TEXT | Parent journal |
| `account_code` | TEXT | GL account code |
| `debit` | NUMERIC | Debit amount |
| `credit` | NUMERIC | Credit amount |
| `description` | TEXT | Line description |

## Data Quality and Pipeline Tables

### lb_dq_results

Data quality rule execution results.

| Column | Type | Description |
|--------|------|-------------|
| `rule_id` | TEXT | Validation rule identifier |
| `category` | TEXT | Rule category |
| `severity` | TEXT | Severity level (`critical`, `warning`, `info`) |
| `passed` | BOOLEAN | Whether the rule passed |
| `message` | TEXT | Result message |
| `detail` | JSONB | Detailed results |
| `checked_at` | TIMESTAMP | When the check ran |

### pipeline_runs

Period-end close pipeline execution records.

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | TEXT (PK) | Unique pipeline run identifier |
| `project_id` | TEXT | Associated project |
| `status` | TEXT | Run status (`running`, `completed`, `failed`) |
| `triggered_by` | TEXT | User who started the pipeline |
| `steps` | JSONB | Step-by-step execution status and timing |
| `started_at` | TIMESTAMP | Pipeline start time |
| `completed_at` | TIMESTAMP | Pipeline completion time |
| `error_message` | TEXT | Error message (if failed) |

## Configuration Table

### app_config

Singleton configuration table storing the full admin configuration as JSONB.

| Column | Type | Description |
|--------|------|-------------|
| `config_key` | TEXT (PK) | Configuration key (typically `main`) |
| `config_data` | JSONB | Full configuration document |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `updated_by` | TEXT | User who last updated |

The configuration document contains sections for `data_sources` (schema, prefix), `model` (LGD assumptions, satellite models, default parameters), `app_settings` (scenarios, scenario weights), and `governance` (approval rules, segregation of duties).
