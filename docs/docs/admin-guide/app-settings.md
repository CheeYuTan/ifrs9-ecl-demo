---
sidebar_position: 5
title: App Settings
---

# App Settings

Configure organization identity, governance structure, macroeconomic scenarios, and application metadata.

## Organization

| Field | Config Key | Default |
|-------|-----------|---------|
| Organization Name | `organization_name` | Horizon Bank |
| Legal Name | `organization_legal_name` | Horizon Bank, Ltd. |
| Country | `country` | United States |
| Currency | `currency_code` | USD |
| Currency Symbol | `currency_symbol` | $ |
| Currency Locale | `currency_locale` | en-US |
| Logo URL | `logo_url` | (blank) |
| Reporting Period | `reporting_period` | Q4 2025 |
| Reporting Date | `reporting_date` | 2025-12-31 |

### Supported Currencies

USD, EUR, GBP, SGD, MYR, JPY, AUD, CAD, CHF, HKD, INR, IDR, THB, PHP, ZAR, BRL, KRW, SAR, AED.

## Governance & Approvals

Sign-off personnel and governance thresholds:

| Field | Description |
|-------|-------------|
| CFO Name & Title | Preparer for sign-off |
| CRO Name & Title | Approver for sign-off |
| Head of Credit Risk Name & Title | Checker role |
| Model Validator Name & Title | Independent model validation |
| External Auditor Firm & Partner | External audit reference |
| Board Committee | Default: "Board Risk Committee" |
| Approval Workflow | Default: "Maker → Checker → Approver → Sign-Off" |
| GL Reconciliation Tolerance | Default: 0.50% |
| DQ Score Threshold | Default: 90.0% |

## Macroeconomic Scenarios

Eight probability-weighted scenarios for ECL calculation. Weights **must sum to 100%** (±1% tolerance).

| Scenario | Default Weight | PD Multiplier | LGD Multiplier |
|----------|---------------|---------------|-----------------|
| Baseline | 40% | 1.00× | 1.00× |
| Mild Recovery | 10% | 0.85× | 0.90× |
| Strong Growth | 5% | 0.70× | 0.80× |
| Mild Downturn | 15% | 1.30× | 1.15× |
| Adverse | 15% | 1.80× | 1.40× |
| Stagflation | 5% | 2.00× | 1.50× |
| Severely Adverse | 5% | 2.50× | 1.70× |
| Tail Risk | 5% | 3.50× | 2.00× |

Each scenario can be customised:

- **Name** — Display name
- **Weight** — Probability weight (0–100%)
- **PD Multiplier** — Applied to base PD under this scenario
- **LGD Multiplier** — Applied to base LGD under this scenario
- **Colour** — Chart colour for visual distinction

Use **Normalize** to auto-adjust weights to sum to exactly 100%. Scenarios can be added or removed.

## Application

| Field | Config Key | Default |
|-------|-----------|---------|
| App Title | `app_title` | IFRS 9 ECL Workspace |
| App Subtitle | `app_subtitle` | Forward-Looking Credit Loss Management |
| Framework | `framework_mode` | IFRS 9 (also: CECL, IFRS 17) |
| Model Version | `model_version` | v4.0 |
