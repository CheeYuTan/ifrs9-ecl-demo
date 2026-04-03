---
sidebar_position: 5
title: "Step 4: Satellite Model"
---

# Step 4: Satellite Model

Calibrate macroeconomic satellite models that link forward-looking scenarios to credit risk parameters.

**IFRS 9 Reference:** 5.5.17(b) — forward-looking information requirements.

## What This Step Does

Satellite models regress observed default rates against macroeconomic variables (unemployment, GDP growth, inflation) for each product-cohort combination. The system trains up to **8 model types**, compares their performance, and selects the best-performing model per cohort.

## Model Types

| Model | Algorithm | Tuning |
|-------|-----------|--------|
| Linear Regression | OLS | None |
| Logistic Regression | Logit-space OLS | None |
| Polynomial (Degree 2) | Polynomial features + OLS | None |
| Ridge Regression | Ridge with Optuna-tuned alpha | Optuna TPE |
| Elastic Net | ElasticNet with Optuna-tuned alpha/L1 ratio | Optuna TPE |
| Random Forest | RandomForestRegressor with Optuna HPO | Optuna TPE |
| Gradient Boosting | GradientBoostingRegressor with Optuna HPO | Optuna TPE |
| XGBoost | XGBRegressor with Optuna HPO | Optuna TPE |

All models use a **train/validation/test split** (70/15/15 for Optuna models, 80/20 for simple models). Minimum 5 observations per cohort required.

## Running the Pipeline

1. **Select models** — Toggle which of the 8 model types to train. Use "Select All" for a comprehensive comparison.
2. Click **Run N Models** — This triggers a Databricks job that trains, evaluates, and selects the best model per product-cohort.
3. The pipeline label shows: **Satellite Model → ECL Calculation → Sync to Lakebase**.
4. Monitor progress via the job status indicator and recent pipeline runs list.

## Reviewing Results

### Model Selection Summary

A grid showing how many cohorts each model type won (was selected as champion).

### Product Selection

Pill buttons for each product type. Click a product to see its cohort-level results.

### Cohort Models Table

For the selected product, a table showing:

| Column | Description |
|--------|-------------|
| Cohort | Cohort identifier |
| Best Model | Selected champion model (with colour indicator) |
| R² | Coefficient of determination |
| RMSE | Root Mean Squared Error |
| AIC | Akaike Information Criterion |
| Selection Reason | Why this model was chosen |

Click any row to see the full model comparison.

### Model Comparison

When you click a cohort, a detailed table shows all evaluated models with R², RMSE, AIC, BIC, and test RMSE. The selected champion is marked with a checkmark.

### Selected Model Formula

Displays the winning model's regression formula, coefficients, and fit statistics.

## Run History

Click **Run History** in the header to see past pipeline runs. Each entry shows the timestamp, model count, cohort count, and notes. Click **Restore** to view historical results without re-running.

## Approving This Step

1. Review the model selection across all products and cohorts.
2. Verify that R² and RMSE values are reasonable.
3. Add comments about any model overrides or concerns.
4. Click **Approve** or **Reject**.
