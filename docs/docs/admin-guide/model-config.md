---
sidebar_position: 3
title: Model Config
---

# Model Config

Configure satellite models, Monte Carlo parameters, SICR thresholds, and LGD assumptions.

## Satellite Models

Toggle which of the 8 model types are enabled for training:

| Key | Model | Default |
|-----|-------|---------|
| `linear_regression` | Linear Regression | Enabled |
| `logistic_regression` | Logistic Regression | Enabled |
| `polynomial_deg2` | Polynomial (Degree 2) | Enabled |
| `ridge_regression` | Ridge Regression | Enabled |
| `random_forest` | Random Forest | Enabled |
| `elastic_net` | Elastic Net | Enabled |
| `gradient_boosting` | Gradient Boosting | Enabled |
| `xgboost` | XGBoost | Enabled |

Disabled models are skipped during satellite model training in Step 4.

## Monte Carlo Simulation Parameters

Default values used when users run simulations without customising:

| Parameter | Config Key | Default | Description |
|-----------|-----------|---------|-------------|
| N Simulations | `n_simulations` | 1,000 | Number of Monte Carlo paths (max 50,000) |
| PD-LGD Correlation | `pd_lgd_correlation` | 0.30 | Models procyclical LGD |
| Aging Factor | `aging_factor` | 0.08 | Quarterly PD increase for Stage 2/3 |
| PD Floor | `pd_floor` | 0.001 | Minimum stressed PD |
| PD Cap | `pd_cap` | 0.95 | Maximum stressed PD |
| LGD Floor | `lgd_floor` | 0.01 | Minimum stressed LGD |
| LGD Cap | `lgd_cap` | 0.95 | Maximum stressed LGD |

## SICR Thresholds

These control the Significant Increase in Credit Risk staging logic. They are hidden by default in the UI (expand "SICR Thresholds" to view).

| Threshold | Config Key | Default | Description |
|-----------|-----------|---------|-------------|
| Stage 1 Max DPD | `stage_1_max_dpd` | 30 | Max days past due for Stage 1 |
| Stage 2 Max DPD | `stage_2_max_dpd` | 90 | Max DPD for Stage 2 |
| Stage 3 Min DPD | `stage_3_min_dpd` | 90 | Min DPD for Stage 3 (credit-impaired) |
| PD Relative Threshold | `pd_relative_threshold` | 2.0 | PD must exceed 2× origination PD |
| PD Absolute Threshold | `pd_absolute_threshold` | 0.005 | PD must increase by ≥ 0.5% absolute |

### Staging Logic

A loan is classified as:

- **Stage 3** if `DPD ≥ 90`
- **Stage 2** if any of:
  - PD deterioration: `current_pd / origination_pd > relative_threshold` AND `current_pd - origination_pd > absolute_threshold`
  - DPD backstop: `DPD ≥ 30`
  - Forbearance: loan has been restructured
- **Stage 1** otherwise

## LGD Assumptions

Per-product LGD (Loss Given Default) and cure rate assumptions:

| Product | Default LGD | Default Cure Rate |
|---------|-------------|-------------------|
| Credit Card | 0.60 | 0.15 |
| Residential Mortgage | 0.15 | 0.40 |
| Commercial Loan | 0.25 | 0.30 |
| Personal Loan | 0.50 | 0.20 |
| Auto Loan | 0.35 | 0.25 |

You can add new products, remove existing ones, or modify the LGD and cure rate values. Both must be between 0 and 1.

### Auto-Discover from Data

Click **Auto-Discover from Data** to scan the `loan_tape` table for distinct product types and automatically populate the LGD table with default assumptions. This calls:

1. `GET /api/admin/discover-products` — finds product types
2. `POST /api/admin/auto-setup-lgd` — creates entries with default LGD/cure rates
