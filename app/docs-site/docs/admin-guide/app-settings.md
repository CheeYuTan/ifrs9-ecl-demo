---
sidebar_position: 4
title: "Application Settings"
description: "Managing platform configuration including organization identity, scenarios, governance, and data sources."
---

# Application Settings

Manage all platform configuration through the centralized admin settings system, including organization identity, data source bindings, scenario definitions, and governance structure.

:::info Who Should Read This
System administrators responsible for platform configuration and organizational customization.
:::

## Overview

The platform stores all configuration in four sections. Each section can be viewed and modified through the **Admin > Settings** page in the application. Changes are saved immediately and tracked in the configuration audit log.

| Section | What It Controls | See Also |
|---------|-----------------|----------|
| **Data Sources** | Unity Catalog connection, Lakebase schema, table mappings | [Data Mapping](data-mapping) |
| **Model Configuration** | Satellite models, simulation parameters, SICR thresholds, LGD assumptions | [Model Configuration](model-configuration) |
| **Jobs** | Databricks job provisioning, compute settings, script paths | [Jobs & Pipelines](jobs-pipelines) |
| **App Settings** | Organization identity, reporting, scenarios, governance | This page (below) |

On first startup, if no configuration exists, the platform automatically seeds all sections with sensible factory defaults. The platform is operational immediately — no manual configuration is required before initial exploration.

## Organization Identity

These settings control how the organization is identified in reports, disclosures, and the application header.

| Setting | Description | Example |
|---------|-------------|---------|
| **Organization Name** | Display name shown in the application header and report titles | Horizon Bank |
| **Legal Name** | Full legal entity name used in regulatory disclosure reports | Horizon Bank Berhad |
| **Logo URL** | URL to your organization's logo for report headers | `https://cdn.example.com/logo.png` |
| **Currency Code** | ISO 4217 currency code used for all monetary values | USD, EUR, MYR |
| **Currency Symbol** | Display symbol for formatting amounts | $, RM |
| **Currency Locale** | Locale for number formatting (thousands separator, decimal) | en-US, ms-MY |
| **Country** | Country of incorporation | Malaysia |

## Reporting Parameters

These settings define the current reporting context for ECL calculations.

| Setting | Description | Example |
|---------|-------------|---------|
| **Reporting Date** | The as-of date for ECL calculations (YYYY-MM-DD format) | 2025-12-31 |
| **Reporting Period** | Human-readable period label for dashboards and reports | Q4 2025 |
| **Framework** | Accounting framework identifier | IFRS 9 |
| **Regulatory Framework** | Full regulatory citation for disclosure reports | IFRS 9 Financial Instruments (IASB, 2014) |
| **Local Regulator** | Name of the local regulatory authority | Bank Negara Malaysia |
| **Local Circular** | Applicable regulatory circular or guideline | BNM/RH/PD 032-11 |

:::tip
Update the **Reporting Date** and **Reporting Period** at the start of each period-end close process. These values appear on all generated reports and disclosure documents.
:::

## Application Branding

| Setting | Description | Default |
|---------|-------------|---------|
| **App Title** | Application title shown in the header bar | IFRS 9 ECL Platform |
| **App Subtitle** | Subtitle shown below the title | Expected Credit Loss Management |
| **Model Version** | Current model version label for audit purposes | v2.1 |
| **Last Validation** | Date of last independent model validation | 2025-06-15 |

## Governance Structure

The governance section defines the organizational roles and thresholds used by the [Approval Workflow](../user-guide/approval-workflow). These names appear on attestation pages and sign-off documents.

| Setting | Description |
|---------|-------------|
| **CFO Name / Title** | Chief Financial Officer identity for sign-off attestation |
| **CRO Name / Title** | Chief Risk Officer identity |
| **Head of Credit Risk** | Head of Credit Risk — typically the primary sign-off authority |
| **Model Validator** | Independent Model Validator identity |
| **External Auditor** | External auditor firm and partner name |
| **Board Committee** | Oversight committee name (e.g., "Board Risk Committee") |
| **Approval Workflow** | Human-readable description of the approval chain |

### Governance Thresholds

| Setting | Default | Description |
|---------|---------|-------------|
| **GL Reconciliation Tolerance** | 0.50% | Maximum acceptable difference between ECL provision and GL balance before reconciliation is flagged |
| **DQ Score Threshold** | 90.0% | Minimum data quality score required to pass the data quality gate |

## Scenario Definitions

Macroeconomic scenarios are the foundation of IFRS 9's forward-looking ECL requirement. Each scenario represents a different view of how the economy might evolve, and the ECL is calculated as a probability-weighted average across all scenarios.

### How Scenarios Work

Each scenario defines:

| Property | Description |
|----------|-------------|
| **Key** | Unique identifier (must match the `scenario_name` values in your macroeconomic data) |
| **Name** | Display name shown in charts and reports |
| **Weight** | Probability weight — all scenario weights must sum to 1.0 (100%) |
| **PD Multiplier** | Factor applied to the base Probability of Default. Values above 1.0 increase PD (stress scenarios); below 1.0 decrease PD (optimistic scenarios). |
| **LGD Multiplier** | Factor applied to the base Loss Given Default. Values above 1.0 increase loss severity. |
| **Color** | Hex color code used for the scenario in charts and visualizations |

### Default Scenarios

The platform ships with eight scenarios that cover a range of economic conditions:

| Scenario | Weight | PD Multiplier | LGD Multiplier | Purpose |
|----------|--------|---------------|----------------|---------|
| **Baseline** | 40% | 1.00 | 1.00 | Central economic expectation |
| **Mild Recovery** | 10% | 0.85 | 0.90 | Moderate improvement in economic conditions |
| **Strong Growth** | 5% | 0.70 | 0.80 | Significant economic expansion |
| **Mild Downturn** | 15% | 1.30 | 1.20 | Moderate economic deterioration |
| **Adverse** | 15% | 1.80 | 1.40 | Significant economic stress |
| **Stagflation** | 5% | 1.50 | 1.30 | Low growth with high inflation |
| **Severely Adverse** | 5% | 2.50 | 1.80 | Extreme economic stress |
| **Tail Risk** | 5% | 3.00 | 2.00 | Extreme tail event |

:::warning
All scenario weights must sum to exactly 1.0 (100%). The platform validates this constraint when you save changes. If the weights do not sum to 1.0, the update will be rejected with a validation error.
:::

:::tip
Review scenario weights quarterly as part of your period-end close process. Economic conditions change, and the probability weights should reflect your institution's current economic outlook. Many institutions present scenario weight proposals to the Board Risk Committee for approval.
:::

## Audit Trail for Configuration Changes

Every configuration change is automatically recorded in an immutable audit log. The audit log captures:

- Which configuration section was changed
- The previous value (complete snapshot)
- The new value (complete snapshot)
- Who made the change (authenticated user identity)
- When the change occurred (timestamp)

Audit log entries cannot be modified or deleted. This forms part of the platform's broader hash-chained audit trail that supports regulatory compliance with IAS 8, SOX Section 302, and BCBS 239 requirements.

To review configuration change history, navigate to **Admin > System > Audit Log** in the application. See [System Administration](system-administration) for details on audit trail integrity verification.

## Resetting to Factory Defaults

If configuration becomes corrupted or you need to return to a known-good state, the platform provides a factory reset option accessible from the Admin Settings page.

:::danger
Resetting to factory defaults is a destructive operation. All custom configuration — including organization identity, data source mappings, scenario definitions, and governance settings — will be replaced with platform defaults. This action is logged in the audit trail and cannot be undone. Export your current configuration before resetting.
:::

## Configuration Initialization

On first startup, the platform automatically:

1. Creates the configuration storage table if it does not exist
2. Seeds all sections with factory default values if the table is empty
3. Loads the database schema and table prefix settings
4. Supplements any missing configuration sections with default values

This means the platform is always operational with sensible defaults, even before any administrator customization has been performed.

## What's Next?

- [Data Mapping](data-mapping) — Connect your Unity Catalog tables to the platform
- [Model Configuration](model-configuration) — Configure satellite models, SICR thresholds, and LGD assumptions
- [Jobs & Pipelines](jobs-pipelines) — Set up and run ECL calculation jobs
- [Governance](../user-guide/approval-workflow) — Understand the approval workflow that uses the governance settings defined here
