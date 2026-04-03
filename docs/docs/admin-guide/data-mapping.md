---
sidebar_position: 2
title: Data Mapping
---

# Data Mapping

Map your Unity Catalog and Lakebase tables to the ECL engine's expected schema.

## Connection Settings

| Field | Config Key | Default |
|-------|-----------|---------|
| Unity Catalog | `data_sources.catalog` | `lakemeter_catalog` |
| UC Schema | `data_sources.schema` | `expected_credit_loss` |
| Lakebase Schema | `data_sources.lakebase_schema` | `expected_credit_loss` |
| Table Prefix | `data_sources.lakebase_prefix` | `lb_` |

## Source Tables

The ECL engine expects 7 source tables. Five are required, two are optional:

### Required Tables

| Table | Description | Mandatory Columns |
|-------|-------------|-------------------|
| `loan_tape` | Loan-level records | `loan_id`, `borrower_id`, `product_type`, `origination_date`, `maturity_date`, `original_principal`, `gross_carrying_amount`, `effective_interest_rate`, `contractual_term_months`, `remaining_months`, `days_past_due`, `origination_pd`, `current_lifetime_pd`, `current_stage` |
| `borrower_master` | Borrower demographics | `borrower_id`, `segment` |
| `payment_history` | Monthly payment records | `loan_id`, `payment_date`, `amount_due`, `amount_paid`, `payment_status` |
| `historical_defaults` | Default events with recovery data | `product_type`, `default_date`, `exposure_at_default`, `loss_given_default` |
| `macro_scenarios` | Forward-looking macro projections | `scenario_name`, `scenario_weight`, `quarters_ahead`, `unemployment_rate`, `gdp_growth_rate`, `inflation_rate` |

### Optional Tables

| Table | Description | Mandatory Columns |
|-------|-------------|-------------------|
| `general_ledger` | GL trial balance | `account_name`, `account_type`, `gl_balance` |
| `collateral_register` | Collateral for secured products | `loan_id`, `current_collateral_value`, `loan_to_value_ratio` |

## Column Mapping

Each table has a set of **expected columns** that the ECL engine references. If your source data uses different column names, the mapping translates between them.

For each table, you can:

- **Auto-Detect** — The system analyses your actual column names and suggests matches. Calls `GET /api/admin/suggest-mappings/{table_key}`.
- **Validate** — Checks that all mandatory columns are mapped and the data types are compatible. Calls `POST /api/admin/validate-mapping`.
- **Preview** — View up to 20 sample rows from the table. Calls `GET /api/admin/table-preview/{table}`.

## View Modes

### Table View

An accordion layout with one section per table. Expand a table to see its column mappings, validation status, and action buttons.

### Lineage View

An SVG data-flow diagram showing how source tables feed into the ECL engine components (PD, LGD, EAD, Stage Classification, Monte Carlo) and produce ECL Results and Reports. Click any node to inspect its columns. Mapped columns show a green indicator.

## Data Mapping Wizard

A separate **Data Mapping Wizard** is available at `/data-mapping` for initial data ingestion from Unity Catalog into Lakebase. This four-step wizard guides you through:

1. **Select Source** — Browse Unity Catalog (catalog → schema → table), preview data
2. **Map Columns** — Map expected columns to source columns with auto-suggest
3. **Validate** — Run validation checks
4. **Apply** — Ingest data with `overwrite` or `append` mode

## Validate All

Click **Validate All** to run validation across all 7 tables sequentially. This is recommended after any configuration change to ensure all mappings remain valid.
