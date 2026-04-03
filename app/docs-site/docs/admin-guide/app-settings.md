---
sidebar_position: 4
title: "Application Settings"
description: "Managing platform configuration including data sources, scenarios, and general settings."
---

# Application Settings

Manage all platform configuration through the centralized admin configuration system, including organization identity, data source bindings, scenario definitions, and governance structure.

:::info Who Should Read This
System administrators responsible for platform configuration and organizational customization.
:::

## Configuration Storage

All platform configuration is persisted in the `app_config` table within the `expected_credit_loss` schema:

```sql
CREATE TABLE expected_credit_loss.app_config (
    config_key   TEXT PRIMARY KEY,
    config_value TEXT NOT NULL,      -- JSON-encoded configuration object
    updated_at   TIMESTAMP DEFAULT NOW(),
    updated_by   TEXT DEFAULT 'system'
);
```

Each row stores a configuration section as a JSON string. The `config_key` identifies the section, and `config_value` contains the full JSON payload for that section. The `updated_at` and `updated_by` columns track when and who last modified each section.

On first startup, if the `app_config` table is empty, the platform automatically seeds it with factory defaults for all sections.

## Configuration Sections

The platform organizes configuration into four top-level sections:

### data_sources

Controls where the platform reads data and how it maps to the internal schema.

| Key | Type | Description |
|-----|------|-------------|
| `catalog` | string | Unity Catalog catalog name (e.g., `lakemeter_catalog`) |
| `schema` | string | Unity Catalog schema name (e.g., `expected_credit_loss`) |
| `lakebase_schema` | string | Lakebase PostgreSQL schema (e.g., `expected_credit_loss`) |
| `lakebase_prefix` | string | Table name prefix in Lakebase (e.g., `lb_`) |
| `tables` | object | Per-table configuration including source table names, mandatory/optional columns, and column mappings |

The `tables` object contains entries for each ECL table (`loan_tape`, `borrower_master`, `payment_history`, `historical_defaults`, `macro_scenarios`, and optional tables). Each entry defines the source table name, whether it is required, and the column mapping dictionary. See [Data Mapping](data-mapping) for details.

### model_config

Controls satellite model selection, simulation parameters, SICR thresholds, and LGD assumptions. See [Model Configuration](model-configuration) for the complete reference.

### job_config

Controls Databricks job provisioning and execution. See [Jobs & Pipelines](jobs-pipelines) for the complete reference.

| Key | Type | Description |
|-----|------|-------------|
| `workspace_url` | string | Databricks workspace URL (auto-detected if blank) |
| `workspace_id` | string | Databricks workspace ID (auto-detected if blank) |
| `scripts_base_path` | string | Workspace path to pipeline scripts. Auto-detected from app source code path if blank. |
| `job_ids` | object | Persisted Databricks job IDs for each managed job key |
| `default_job_params` | object | Default notebook parameters passed to all jobs |
| `compute.use_serverless` | boolean | Whether to use serverless compute for jobs (default: `true`) |
| `compute.cluster_spec` | string | Custom cluster specification (used when `use_serverless` is `false`) |

### app_settings

Controls organization identity, reporting parameters, governance structure, and scenario definitions.

**Organization identity:**

| Key | Type | Description |
|-----|------|-------------|
| `organization_name` | string | Display name (e.g., "Horizon Bank") |
| `organization_legal_name` | string | Legal entity name for regulatory reports |
| `logo_url` | string | URL to organization logo for report headers |
| `currency_code` | string | ISO 4217 currency code (e.g., `USD`, `EUR`, `MYR`) |
| `currency_symbol` | string | Currency display symbol (e.g., `$`, `RM`) |
| `currency_locale` | string | Locale for number formatting (e.g., `en-US`) |
| `country` | string | Country of incorporation |

**Reporting parameters:**

| Key | Type | Description |
|-----|------|-------------|
| `reporting_date` | string | Current reporting date in YYYY-MM-DD format |
| `reporting_period` | string | Human-readable period label (e.g., "Q4 2025") |
| `reporting_date_format` | string | Date format string for display |
| `framework` | string | Accounting framework identifier (e.g., "IFRS 9") |
| `framework_mode` | string | Framework mode key (e.g., `ifrs9`) |
| `regulatory_framework` | string | Full regulatory citation for disclosure reports |
| `local_regulator` | string | Name of the local regulatory authority |
| `local_circular` | string | Applicable regulatory circular or guideline |

**Application branding:**

| Key | Type | Description |
|-----|------|-------------|
| `app_title` | string | Application title shown in the header |
| `app_subtitle` | string | Subtitle shown below the title |
| `model_version` | string | Current model version label |
| `last_validation` | string | Date of last model validation |

**Governance structure:**

The `governance` sub-object defines the organizational roles and thresholds for the approval workflow:

| Key | Type | Description |
|-----|------|-------------|
| `cfo_name` / `cfo_title` | string | Chief Financial Officer identity |
| `cro_name` / `cro_title` | string | Chief Risk Officer identity |
| `head_credit_risk_name` / `head_credit_risk_title` | string | Head of Credit Risk identity |
| `model_validator_name` / `model_validator_title` | string | Independent Model Validator identity |
| `external_auditor_firm` / `external_auditor_partner` | string | External auditor details |
| `board_committee` | string | Oversight committee name (e.g., "Board Risk Committee") |
| `approval_workflow` | string | Human-readable approval chain description |
| `gl_reconciliation_tolerance_pct` | number | GL reconciliation tolerance in percent (default: 0.50%) |
| `dq_score_threshold_pct` | number | Minimum data quality score to pass the DQ gate (default: 90.0%) |

**Scenario definitions:**

The `scenarios` array defines the macroeconomic scenarios used for probability-weighted ECL calculation:

```json
{
  "scenarios": [
    {
      "key": "baseline",
      "name": "Baseline",
      "weight": 0.40,
      "pd_multiplier": 1.0,
      "lgd_multiplier": 1.0,
      "color": "#10B981"
    },
    {
      "key": "adverse",
      "name": "Adverse",
      "weight": 0.15,
      "pd_multiplier": 1.80,
      "lgd_multiplier": 1.40,
      "color": "#EF4444"
    }
  ]
}
```

Each scenario has:

| Field | Description |
|-------|-------------|
| `key` | Unique identifier. Must match `scenario_name` in the `macro_scenarios` table. |
| `name` | Display name for reports and UI. |
| `weight` | Probability weight. All scenario weights must sum to 1.0. |
| `pd_multiplier` | Multiplier applied to base PD under this scenario. Values > 1.0 increase PD (stress). |
| `lgd_multiplier` | Multiplier applied to base LGD under this scenario. Values > 1.0 increase loss severity. |
| `color` | Hex color code for charts and visualizations. |

The platform ships with eight default scenarios: Baseline (40%), Mild Recovery (10%), Strong Growth (5%), Mild Downturn (15%), Adverse (15%), Stagflation (5%), Severely Adverse (5%), and Tail Risk (5%).

## API Endpoints

### Read Configuration

```
GET /api/admin/config
```

Returns the complete configuration as a JSON object with all sections.

```
GET /api/admin/config/{section}
```

Returns a single configuration section. Valid section keys: `data_sources`, `model`, `jobs`, `app_settings`.

### Write Configuration

```
PUT /api/admin/config
```

Accepts a JSON body with one or more sections to update. Sections not included in the request body are left unchanged.

```json
{
  "app_settings": {
    "organization_name": "Meridian Bank",
    "currency_code": "EUR"
  }
}
```

```
PUT /api/admin/config/{section}
```

Updates a single configuration section. The request body is the section value directly:

```json
{
  "organization_name": "Meridian Bank",
  "currency_code": "EUR"
}
```

### Seed Factory Defaults

```
POST /api/admin/seed-defaults
```

Resets all configuration to factory defaults. This operation deletes all existing configuration rows and re-inserts the default values. Use this to recover from misconfiguration or to reset a development environment.

:::danger
Seeding defaults is a destructive operation. All custom configuration including data source mappings, scenario definitions, and governance settings will be replaced with platform defaults. This action is logged in the audit trail.
:::

### Additional Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/test-connection` | POST | Test the current Lakebase connection |
| `/api/admin/available-tables` | GET | List tables in the configured Lakebase schema |
| `/api/admin/table-columns/{table}` | GET | Get column metadata for a Lakebase table |
| `/api/admin/table-preview/{table}` | GET | Preview rows from a Lakebase table (max 20 rows) |
| `/api/admin/schemas` | GET | List available PostgreSQL schemas |
| `/api/admin/auto-detect-workspace` | GET | Auto-detect workspace URL and scripts path |
| `/api/admin/discover-products` | GET | Discover product types from mapped loan data |
| `/api/admin/auto-setup-lgd` | POST | Generate LGD assumptions from historical default data |
| `/api/admin/suggest-mappings/{table_key}` | GET | Auto-suggest column mappings for a table |
| `/api/admin/validate-mapping` | POST | Validate a column mapping configuration |
| `/api/admin/validate-mapping-typed` | POST | Validate mappings with type compatibility checking |

## Audit Trail for Configuration Changes

Every configuration change is recorded in the `config_audit_log` table:

```sql
CREATE TABLE expected_credit_loss.config_audit_log (
    id          SERIAL PRIMARY KEY,
    section     TEXT NOT NULL,
    config_key  TEXT,
    old_value   JSONB,
    new_value   JSONB,
    changed_by  TEXT NOT NULL,
    changed_at  TIMESTAMP DEFAULT NOW()
);
```

The audit log captures:
- Which section was changed
- The previous value (complete JSON snapshot)
- The new value (complete JSON snapshot)
- Who made the change
- When the change occurred

Audit log entries are immutable -- they are INSERT-only, with no UPDATE or DELETE operations permitted. This forms part of the platform's broader hash-chained audit trail that supports regulatory compliance with IAS 8, SOX Section 302, and BCBS 239 requirements.

## Configuration Initialization Flow

The following sequence occurs on platform startup:

1. **Table creation**: `app_config` table is created if it does not exist
2. **Empty check**: If the table has zero rows, default configuration is seeded
3. **Schema loading**: The Lakebase schema and prefix are loaded from `data_sources` configuration
4. **Merge with defaults**: When reading configuration, any missing sections are supplemented with default values

This means the platform is always operational with sensible defaults, even before any administrator customization has been performed.
