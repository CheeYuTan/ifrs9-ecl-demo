---
sidebar_position: 3
title: "Model Configuration"
description: "Configuring satellite models, SICR thresholds, LGD assumptions, and Monte Carlo parameters."
---

# Model Configuration

Configure the ECL calculation engine: satellite model selection, default simulation parameters, SICR staging thresholds, and product-level LGD assumptions.

:::info Who Should Read This
System administrators and risk managers responsible for model parameterization and governance.
:::

## Overview

Model configuration is stored in the `model` section of the platform's admin configuration. It controls four areas:

1. **Satellite models** -- which algorithms are enabled for macroeconomic linking
2. **Default parameters** -- Monte Carlo simulation settings, PD/LGD floors and caps
3. **SICR thresholds** -- criteria for classifying loans into IFRS 9 stages
4. **LGD assumptions** -- product-level Loss Given Default and cure rate estimates

All model configuration is persisted in the `app_config` table under the `model` key. Changes are tracked in the configuration audit log.

## Satellite Models

Satellite models link macroeconomic variables (GDP growth, unemployment, inflation) to credit risk parameters (PD, LGD). The platform supports eight algorithms, each of which can be independently enabled or disabled.

| Algorithm | Key | Description |
|-----------|-----|-------------|
| **Linear Regression** | `linear_regression` | Ordinary least squares. Fast, interpretable baseline. |
| **Logistic Regression** | `logistic_regression` | Binary classification model. Suitable for PD estimation with bounded output. |
| **Polynomial (Degree 2)** | `polynomial_deg2` | Quadratic feature expansion + linear regression. Captures non-linear macro-PD relationships. |
| **Ridge Regression** | `ridge_regression` | L2-regularized linear regression. Reduces overfitting with correlated macro features. |
| **Random Forest** | `random_forest` | Ensemble of decision trees. Handles non-linearity and feature interactions. |
| **Elastic Net** | `elastic_net` | Combined L1+L2 regularization. Balances feature selection with coefficient shrinkage. |
| **Gradient Boosting** | `gradient_boosting` | Sequential boosted trees. Strong predictive performance on tabular data. |
| **XGBoost** | `xgboost` | Optimized gradient boosting with built-in regularization. Typically the strongest performer. |

### Enabling and Disabling Models

Each model has an enabled/disabled toggle on the Model Configuration page. When a satellite model job runs, only enabled models are trained and evaluated.

Disabling models that are not relevant to your portfolio reduces job execution time without affecting the accuracy of enabled models. The aggregation step combines results only from models that completed successfully.

:::tip
For initial development and testing, enable only 2-3 models (e.g., Linear Regression, Ridge Regression, XGBoost) to reduce job runtime. Enable the full suite for production period-end calculations.
:::

### Model Selection During Job Execution

When triggering a satellite model job from the Jobs page, you can override the enabled model list for that specific run. This override applies only to that run — the persisted configuration is not changed. See [Jobs & Pipelines](jobs-pipelines) for details.

## Default Parameters

Default parameters govern Monte Carlo simulation behavior and PD/LGD bounds. These values are used when a job is triggered without explicit parameter overrides.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `n_simulations` | 1,000 | Number of Monte Carlo simulation paths per loan. Higher values improve convergence at the cost of runtime. |
| `max_simulations` | 50,000 | Upper limit on simulations per run. Prevents accidental resource exhaustion. |
| `pd_lgd_correlation` | 0.30 | Assumed correlation between PD and LGD in the simulation. Models downturn LGD: when PDs rise, LGDs tend to increase too. |
| `aging_factor` | 0.08 | Annual aging adjustment applied to forward PD term structures. Models the tendency of PD to increase with time on book. |
| `pd_floor` | 0.001 | Minimum PD value (0.1%). Prevents zero-PD assignments that would eliminate ECL. |
| `pd_cap` | 0.95 | Maximum PD value (95%). Prevents PD from reaching 1.0, which would imply certain default. |
| `lgd_floor` | 0.01 | Minimum LGD value (1%). Ensures a non-zero loss estimate even for fully secured loans. |
| `lgd_cap` | 0.95 | Maximum LGD value (95%). Prevents total-loss assumptions that may overstate provisions. |

### Adjusting Parameters

Update default parameters through the **Admin > Model Configuration** page. Changes are saved immediately and recorded in the configuration audit log.

:::caution
Increasing `n_simulations` significantly (above 10,000) will increase Monte Carlo job runtime proportionally. For initial development and testing, 1,000 simulations provides reasonable accuracy. For production period-end reporting, 5,000-10,000 simulations is typical.
:::

## SICR Thresholds

Significant Increase in Credit Risk (SICR) thresholds determine how loans are classified into the three IFRS 9 impairment stages. The platform evaluates multiple triggers and assigns each loan to the highest applicable stage.

### Stage Classification Rules

| Stage | Criteria |
|-------|----------|
| **Stage 1** (12-month ECL) | DPD ≤ `stage_1_max_dpd` AND no PD-based trigger AND no qualitative trigger |
| **Stage 2** (Lifetime ECL) | DPD &gt; `stage_1_max_dpd` AND DPD ≤ `stage_2_max_dpd`, OR PD relative increase ≥ `pd_relative_threshold`, OR PD absolute increase ≥ `pd_absolute_threshold`, OR loan is restructured |
| **Stage 3** (Credit-impaired) | DPD &gt; `stage_2_max_dpd`, OR loan is in default |

### Threshold Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `stage_1_max_dpd` | 30 | Maximum days past due for Stage 1. Loans exceeding this move to Stage 2. |
| `stage_2_max_dpd` | 90 | Maximum days past due for Stage 2. Loans exceeding this move to Stage 3. |
| `stage_3_min_dpd` | 90 | Minimum DPD for automatic Stage 3 classification. Aligns with the IFRS 9 rebuttable presumption. |
| `pd_relative_threshold` | 2.0 | If `current_lifetime_pd / origination_pd ≥ 2.0`, the loan transfers to Stage 2 regardless of DPD. This captures credit deterioration that has not yet resulted in delinquency. |
| `pd_absolute_threshold` | 0.005 | If `current_lifetime_pd - origination_pd ≥ 0.005` (0.5 percentage points), the loan transfers to Stage 2. This catches low-PD loans where the relative threshold alone would be insensitive. |

### Customizing Thresholds

SICR thresholds should reflect your institution's credit risk appetite and historical experience. Common adjustments:

- **Emerging market portfolios**: Lower `stage_1_max_dpd` to 15-20 days to catch deterioration earlier
- **Mortgage portfolios**: Increase `pd_relative_threshold` to 2.5-3.0 because mortgage PDs are naturally low and volatile
- **Microfinance portfolios**: Lower `pd_absolute_threshold` to 0.003 for greater sensitivity to small PD changes

Update SICR thresholds through the **Admin > Model Configuration** page under the SICR Thresholds section. Changes are tracked in the configuration audit log and take effect on the next model run.

## LGD Assumptions

Loss Given Default assumptions are configured per product type. Each product has a base LGD estimate and a cure rate representing the probability that a defaulted loan returns to performing status.

### Default LGD Values

| Product Type | LGD | Cure Rate | Rationale |
|-------------|-----|-----------|-----------|
| `credit_card` | 0.60 (60%) | 0.15 (15%) | Unsecured revolving facility. High loss severity, low cure probability. |
| `residential_mortgage` | 0.15 (15%) | 0.40 (40%) | Secured by property. Low LGD due to collateral, higher cure rate from restructuring. |
| `commercial_loan` | 0.25 (25%) | 0.30 (30%) | Partially secured. Moderate loss severity with reasonable recovery prospects. |
| `personal_loan` | 0.50 (50%) | 0.20 (20%) | Unsecured term loan. High loss severity, limited recovery options. |
| `auto_loan` | 0.35 (35%) | 0.25 (25%) | Secured by depreciating asset. Moderate LGD, vehicle repossession partially offsets loss. |

### Adding Custom Products

If your portfolio contains product types not listed above, add them through the **Admin > Model Configuration** page under the LGD Assumptions section. For each new product type, provide a base LGD estimate and a cure rate.

:::warning
Product type keys in the LGD assumptions must exactly match the `product_type` values in your `loan_tape` data. If a loan has a `product_type` that is not found in the LGD assumptions, the platform will use a fallback LGD of 0.45 (45%), which may not reflect your portfolio's actual risk profile.
:::

### Auto-Setup from Data

The platform can automatically discover product types from your mapped data and propose LGD assumptions. Navigate to **Admin > Model Configuration** and click **Auto-Setup LGD**. The platform scans your historical default data to identify distinct product types and calculates empirical LGD values from observed loss data. The results are presented as suggestions that require manual review and approval before being applied.

## Model Lifecycle

Each satellite model follows a governance lifecycle that ensures only validated and approved models are used in production ECL calculations.

| Status | Description |
|--------|-------------|
| `draft` | Initial state. Model has been trained but not yet reviewed. |
| `pending_review` | Model submitted for independent validation. Awaiting review by a model validator. |
| `approved` | Model passed validation. Eligible for promotion to active. |
| `active` | Model is the current champion used in ECL calculations. Only one model per type can be active. |
| `retired` | Model has been superseded by a newer version. Retained for audit trail purposes. |

### Valid Status Transitions

A model progresses through the lifecycle as follows: **Draft** (newly trained) to **Pending Review** (submitted for validation) to **Approved** (passed validation) to **Active** (promoted as the current champion) to **Retired** (superseded by a newer version). A model can also be sent back from Pending Review to Draft if rejected.

Model status changes are recorded in the model registry audit table with the user who performed the action, a timestamp, and any review comments. See the [User Guide](../user-guide/workflow-overview) for details on the model selection and validation workflow.

## What's Next?

- [App Settings](app-settings) — Configure organization identity, scenarios, and governance thresholds
- [Jobs & Pipelines](jobs-pipelines) — Trigger satellite model jobs using the configuration defined here
- [Data Mapping](data-mapping) — Ensure your source data is mapped before running models
