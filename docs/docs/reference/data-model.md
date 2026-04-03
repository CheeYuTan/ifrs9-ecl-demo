---
sidebar_position: 3
title: Data Model
---

# Data Model

Specifications for the 7 source tables required by the ECL engine.

## Overview

The ECL engine reads from 7 source tables stored in Unity Catalog / Lakebase. Five tables are required; two are optional. The default location is `lakemeter_catalog.expected_credit_loss` (configurable in [Admin > Data Mapping](/admin-guide/data-mapping)).

| Table | Required | Description |
|-------|----------|-------------|
| `loan_tape` | Yes | Loan-level facility records |
| `borrower_master` | Yes | Borrower demographics |
| `payment_history` | Yes | Monthly payment records |
| `historical_defaults` | Yes | Default events with recovery data |
| `macro_scenarios` | Yes | Forward-looking macro projections |
| `general_ledger` | No | GL trial balance for reconciliation |
| `collateral_register` | No | Collateral for secured products |

## loan_tape

One row per active loan facility. This is the primary input for ECL calculation.

### Mandatory Columns

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | TEXT | Unique loan identifier (PK) |
| `borrower_id` | TEXT | FK to `borrower_master` |
| `product_type` | TEXT | Must match LGD assumptions and `historical_defaults` |
| `origination_date` | DATE | Must be before reporting date |
| `maturity_date` | DATE | Must be after origination date |
| `original_principal` | NUMERIC | Original disbursed amount |
| `gross_carrying_amount` | NUMERIC | Current outstanding balance (EAD basis) |
| `effective_interest_rate` | NUMERIC | Annual EIR for discounting (decimal, e.g., 0.085) |
| `contractual_term_months` | INT | Original loan term in months |
| `remaining_months` | INT | Months to maturity from reporting date |
| `days_past_due` | INT | Days past due — used for SICR staging |
| `origination_pd` | NUMERIC | PD at origination (for SICR PD-ratio trigger) |
| `current_lifetime_pd` | NUMERIC | Current point-in-time lifetime PD (annualised) |
| `current_stage` | INT | Bank's current IFRS 9 stage (1, 2, or 3) |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `months_on_book` | INT | Months since origination |
| `prior_stage` | INT | Previous reporting period stage |
| `is_restructured` | BOOLEAN | Forbearance flag (triggers SICR) |
| `is_write_off` | BOOLEAN | Write-off flag (excluded from SICR) |
| `currency` | TEXT | Loan currency code |
| `reporting_date` | DATE | As-of date for this record |
| `origination_alt_score` | NUMERIC | Alternative credit score at origination |
| `current_alt_score` | NUMERIC | Current alternative credit score |
| `cohort_id` | TEXT | Cohort identifier |
| `vintage_year` | INT | Origination year |
| `risk_band` | TEXT | Risk classification band |

---

## borrower_master

Borrower demographics and risk attributes. One row per borrower.

### Mandatory Columns

| Column | Type | Description |
|--------|------|-------------|
| `borrower_id` | TEXT | Unique borrower identifier (PK, FK from `loan_tape`) |
| `segment` | TEXT | Borrower segment classification |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `age` | INT | Borrower age |
| `monthly_income` | NUMERIC | Monthly income |
| `income_source` | TEXT | Income source type |
| `employment_tenure_months` | INT | Employment duration |
| `education_level` | TEXT | Education level |
| `formal_credit_score` | NUMERIC | Traditional credit score |
| `alt_data_composite_score` | NUMERIC | Alternative data score |
| `country` | TEXT | Country of residence |
| `region` | TEXT | Region/state |
| `dependents` | INT | Number of dependents |

---

## payment_history

Monthly payment records per loan.

### Mandatory Columns

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | TEXT | FK to `loan_tape` |
| `payment_date` | DATE | Date of payment |
| `amount_due` | NUMERIC | Scheduled payment amount |
| `amount_paid` | NUMERIC | Actual amount paid |
| `payment_status` | TEXT | `on_time`, `late`, `partial`, or `missed` |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `days_late` | INT | Days late (if applicable) |
| `payment_period` | TEXT | Period identifier (e.g., 2025-Q4) |
| `payment_method` | TEXT | Payment channel |

---

## historical_defaults

Historical default events with realised recovery data. Used for LGD calibration.

### Mandatory Columns

| Column | Type | Description |
|--------|------|-------------|
| `product_type` | TEXT | Product type (must match `loan_tape`) |
| `default_date` | DATE | Date of default event |
| `exposure_at_default` | NUMERIC | Outstanding amount at default |
| `loss_given_default` | NUMERIC | Realised LGD (decimal 0–1) |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `recovery_amount` | NUMERIC | Amount recovered post-default |
| `recovery_date` | DATE | Date recovery was realised |
| `loss_amount` | NUMERIC | Net loss amount |
| `default_reason` | TEXT | Reason for default |
| `quarter` | TEXT | Quarter identifier |
| `was_restructured_before_default` | BOOLEAN | Whether loan was restructured before default |
| `months_to_default` | INT | Months from origination to default |

---

## macro_scenarios

Forward-looking macroeconomic projections for probability-weighted ECL.

### Mandatory Columns

| Column | Type | Description |
|--------|------|-------------|
| `scenario_name` | TEXT | Must match scenario keys in App Settings |
| `scenario_weight` | NUMERIC | Probability weight (decimal, e.g., 0.40) |
| `quarters_ahead` | INT | Forecast horizon in quarters |
| `unemployment_rate` | NUMERIC | Projected unemployment rate |
| `gdp_growth_rate` | NUMERIC | Projected GDP growth rate |
| `inflation_rate` | NUMERIC | Projected inflation rate |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `forecast_date` | DATE | Date forecast was made |
| `forecast_quarter` | TEXT | Target quarter |
| `scenario_description` | TEXT | Narrative description |
| `policy_interest_rate` | NUMERIC | Central bank policy rate |
| `consumer_confidence_index` | NUMERIC | Consumer confidence metric |

---

## general_ledger (Optional)

GL trial balance for loan-related accounts. Used for GL reconciliation in Step 3.

### Mandatory Columns

| Column | Type | Description |
|--------|------|-------------|
| `account_name` | TEXT | Must contain product type for matching |
| `account_type` | TEXT | `asset` or `contra_asset` |
| `gl_balance` | NUMERIC | GL account balance |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `account_code` | TEXT | GL account code |
| `as_of_date` | DATE | Balance date |
| `currency` | TEXT | Account currency |

---

## collateral_register (Optional)

Collateral information for secured loan products.

### Mandatory Columns

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | TEXT | FK to `loan_tape` |
| `current_collateral_value` | NUMERIC | Current market value |
| `loan_to_value_ratio` | NUMERIC | LTV ratio |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `collateral_type` | TEXT | Type of collateral (property, vehicle, etc.) |
| `original_collateral_value` | NUMERIC | Value at origination |
| `last_valuation_date` | DATE | Date of last valuation |
| `collateral_status` | TEXT | Status (active, released, etc.) |

---

## Output Tables

The ECL pipeline produces the following tables (written to Unity Catalog):

| Table | Produced By | Description |
|-------|-------------|-------------|
| `model_ready_loans` | Data Processing | SICR-staged, enriched loan records |
| `dq_results` | Data Processing | Data quality check results |
| `gl_reconciliation` | Data Processing | GL vs loan-tape variance |
| `quarterly_default_rates` | Data Generation | Historical quarterly DR by product/cohort |
| `loan_level_ecl` | ECL Calculation | Per-loan per-scenario ECL |
| `loan_ecl_weighted` | ECL Calculation | Probability-weighted ECL per loan |
| `portfolio_ecl_summary` | ECL Calculation | Summary by product and stage |
| `scenario_ecl_summary` | ECL Calculation | ECL statistics by scenario |
| `mc_ecl_distribution` | ECL Calculation | Monte Carlo distribution |
| `satellite_model_comparison` | Satellite Model | All model metrics per cohort |
| `satellite_model_selected` | Satellite Model | Best model per cohort |
| `satellite_model_metadata` | ECL Calculation | Regression coefficients and audit trail |
