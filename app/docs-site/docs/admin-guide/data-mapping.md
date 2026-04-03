---
sidebar_position: 2
title: "Data Mapping"
description: "Ingesting data from Unity Catalog into Lakebase through the data mapping wizard."
---

# Data Mapping

Ingest your organization's loan portfolio data from Unity Catalog into the platform's Lakebase tables using the guided data mapping wizard.

:::info Who Should Read This
System administrators responsible for data integration, and data engineers preparing source tables for ECL calculation.
:::

## Overview

The data mapping workflow connects your existing Unity Catalog tables to the platform's internal schema. Rather than requiring you to restructure your data, the wizard lets you map your column names to the platform's expected schema and handles the transformation during ingestion.

Data flows in one direction: **Unity Catalog (source) --> Lakebase (target)**. The platform reads from UC via the Databricks SDK and writes to Lakebase via PostgreSQL. Source tables are never modified.

## The 5-Step Wizard

The data mapping wizard guides administrators through five sequential steps for each table:

### Step 1: Browse Unity Catalog

Navigate the three-level Unity Catalog hierarchy to locate your source tables:

```
Catalog > Schema > Table
```

The wizard displays all accessible catalogs in your workspace. Select a catalog to see its schemas, then select a schema to see the available tables. Each table listing shows the table name, type, and any comments from Unity Catalog metadata.

### Step 2: Preview Source Data

Once a source table is selected, the wizard shows a preview of the first few rows. Use this to confirm the table contains the expected loan data before proceeding. The preview also shows column names and inferred data types, which helps when setting up mappings in the next step.

### Step 3: Auto-Suggest Mappings

The platform can automatically suggest column mappings using fuzzy name matching. The auto-suggest engine compares your source column names against the expected target column names using similarity scoring. For example:

| Your Source Column | Auto-Suggested Target | Match Reason |
|---|---|---|
| `outstanding_balance` | `gross_carrying_amount` | Semantic similarity |
| `facility_id` | `loan_id` | Functional match |
| `customer_number` | `borrower_id` | Functional match |
| `product_category` | `product_type` | Near-exact match |

Suggestions are presented for your review and can be adjusted before applying. Always review auto-suggested mappings — the engine uses heuristics and may occasionally suggest incorrect matches.

:::tip
Run auto-suggest first, even if you plan to customize mappings. It provides a useful starting point and reduces manual configuration effort.
:::

### Step 4: Validate Column Mappings

After defining your column mappings (source column to target column), the wizard validates them for completeness and type compatibility. Validation checks that:

- All mandatory columns have a mapping defined
- Source column data types are compatible with target types
- All referenced source columns exist in the source table

If validation fails, the wizard highlights the specific issues so you can correct them before proceeding.

### Step 5: Apply Mapping

Once validation passes, apply the mapping to ingest data from Unity Catalog into Lakebase. Two apply modes are available:

| Mode | Behavior | When to Use |
|------|----------|-------------|
| **Overwrite** | Drop existing data and replace with new data | Initial setup and full period-end refreshes |
| **Append** | Add new rows to the existing data | Incremental loads where you are adding new records |

After applying, the wizard shows a confirmation with the number of rows ingested and any warnings.

### Checking Mapping Status

The Data Mapping page shows a status dashboard for all ECL tables, including which tables have been mapped, their current row counts, and the timestamp of the last successful ingestion.

## Required ECL Tables

The platform requires five core tables. Each must be mapped before ECL calculations can run.

### loan_tape

The primary loan-level dataset. Each row represents one active loan facility.

**Mandatory columns (14):**

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | TEXT | Unique loan identifier. Must be unique per row. |
| `borrower_id` | TEXT | Borrower identifier. Must match `borrower_master.borrower_id`. |
| `product_type` | TEXT | Loan product category. Must match products in LGD Assumptions. |
| `origination_date` | DATE | Date the loan was originated. Must be before `reporting_date`. |
| `maturity_date` | DATE | Contractual maturity date. Must be after `origination_date`. |
| `original_principal` | NUMERIC | Original disbursed principal amount. |
| `gross_carrying_amount` | NUMERIC | Current outstanding balance (Exposure at Default basis). |
| `effective_interest_rate` | NUMERIC | Annual EIR for discounting. Decimal between 0 and 1. |
| `contractual_term_months` | INT | Original loan term in months. |
| `remaining_months` | INT | Months remaining until maturity. 0 = matured. |
| `days_past_due` | INT | Days past due. 0 = current. Used for SICR staging. |
| `origination_pd` | NUMERIC | PD at origination. Decimal between 0 and 1. |
| `current_lifetime_pd` | NUMERIC | Current point-in-time lifetime PD. Decimal between 0 and 1. |
| `current_stage` | INT | Current IFRS 9 stage (1, 2, or 3). |

### borrower_master

Borrower-level demographics and risk attributes.

**Mandatory columns (2):**

| Column | Type | Description |
|--------|------|-------------|
| `borrower_id` | TEXT | Unique borrower identifier. Must match `loan_tape.borrower_id`. |
| `segment` | TEXT | Borrower segment for risk stratification (e.g., retail, corporate, sme). |

### payment_history

Monthly payment records per loan.

**Mandatory columns (4):**

| Column | Type | Description |
|--------|------|-------------|
| `loan_id` | TEXT | Loan identifier. Must match `loan_tape.loan_id`. |
| `payment_date` | DATE | Date the payment was due or made. |
| `amount_due` | NUMERIC | Contractual payment amount due. |
| `amount_paid` | NUMERIC | Actual amount paid. 0 = missed payment. |

The `payment_status` column (values: `on_time`, `late`, `partial`, `missed`) is also expected and will be treated as mandatory during validation.

### historical_defaults

Historical default events with recovery data, used for LGD calibration.

**Mandatory columns (4):**

| Column | Type | Description |
|--------|------|-------------|
| `product_type` | TEXT | Product category. Must match `loan_tape.product_type`. |
| `default_date` | DATE | Date the loan entered default status. |
| `exposure_at_default` | NUMERIC | Outstanding balance at time of default. |
| `loss_given_default` | NUMERIC | Realized loss as fraction of exposure. Decimal between 0 and 1. |

### macro_scenarios

Forward-looking macroeconomic scenario projections for satellite models.

**Mandatory columns (5):**

| Column | Type | Description |
|--------|------|-------------|
| `scenario_name` | TEXT | Scenario identifier (e.g., baseline, adverse). Must match App Settings. |
| `scenario_weight` | NUMERIC | Probability weight. All weights should sum to 1.0. |
| `quarters_ahead` | INT | Quarters into the future (1 = next quarter). |
| `unemployment_rate` | NUMERIC | Projected unemployment rate (percentage). |
| `gdp_growth_rate` | NUMERIC | Projected GDP growth rate (percentage). |

The `inflation_rate` column is also included as a mandatory satellite model feature.

## Optional Tables

These tables enhance the platform's capabilities but are not required for core ECL calculations.

| Table | Purpose |
|-------|---------|
| `general_ledger` | GL trial balance for reconciliation. Requires `account_name`, `account_type`, `gl_balance`. |
| `collateral_register` | Collateral data for secured products. Requires `loan_id`, `current_collateral_value`, `loan_to_value_ratio`. |
| `model_ready_loans` | Pre-processed model-ready data. Map this if you prepare loan data externally rather than using the platform's data processing pipeline. |

## Type Compatibility

The validation engine checks that source column types are compatible with target types. The following mappings are accepted:

| Target Type | Compatible Source Types |
|-------------|----------------------|
| `TEXT` | text, character varying, varchar, char, character, name, uuid |
| `INT` | integer, bigint, smallint, int, int4, int8, int2, numeric |
| `NUMERIC` | numeric, decimal, real, double precision, float4, float8, integer, bigint, smallint |
| `DATE` | date |
| `BOOLEAN` | boolean |

Numeric source types are accepted for INT targets because PostgreSQL can cast between them. If a type mismatch is detected, validation returns an error specifying the incompatible column pair.

## Best Practices

- **Map all required tables before running any pipeline.** The full pipeline job expects `loan_tape`, `borrower_master`, `payment_history`, `historical_defaults`, and `macro_scenarios` to contain data.
- **Use overwrite mode for initial setup** and when refreshing data for a new reporting period. Use append mode only for incremental scenarios where you are adding new records to an existing dataset.
- **Verify product_type consistency.** The `product_type` values in `loan_tape`, `historical_defaults`, and the LGD Assumptions configuration must all match exactly. Mismatched product types will cause ECL calculations to use default LGD values.
- **Run the auto-suggest step first.** Even if you plan to customize mappings, the auto-suggest provides a useful starting point and reduces manual configuration effort.
- **Check mapping status after apply.** Confirm all tables were ingested with the expected row counts on the Data Mapping status dashboard.

## What's Next?

- [Model Configuration](model-configuration) — Configure satellite models, SICR thresholds, and LGD assumptions
- [App Settings](app-settings) — Set up organization identity, scenarios, and governance
- [Jobs & Pipelines](jobs-pipelines) — Run the ECL calculation pipeline after data is mapped
