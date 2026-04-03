---
sidebar_position: 5
title: "Step 4: Satellite Models"
description: "Selecting macroeconomic models that link PD and LGD to economic conditions."
---

# Step 4: Satellite Models

Satellite models are the link between macroeconomic conditions and your portfolio's credit risk. They translate economic scenarios (such as GDP growth, unemployment rates, and interest rate movements) into adjustments to Probability of Default (PD) and Loss Given Default (LGD). IFRS 9 requires that ECL calculations incorporate "forward-looking information" — satellite models are how the platform fulfills this requirement.

:::info Prerequisites
- Completed [Step 3: Data Control](step-3-data-control)
- Satellite model pipeline configured by your administrator (see [Model Configuration](../admin-guide/model-configuration))
:::

## What You'll Do

On this page you will run the satellite model pipeline (which evaluates up to 8 model types across every product-cohort combination), review the auto-selected best models, examine model performance metrics, and approve the model selection for use in the Monte Carlo ECL calculation.

## Step-by-Step Instructions

### 1. Select and Run the Model Pipeline

At the top of the page, the **Run Satellite Model Pipeline** panel lets you choose which model types to evaluate:

| Model Type | Description |
|-----------|-------------|
| **Linear Regression** | The simplest approach — fits a straight-line relationship between economic variables and credit risk |
| **Logistic Regression** | Models the probability of default as a logistic (S-shaped) function of economic variables |
| **Polynomial (Degree 2)** | Captures curved relationships — useful when the impact of economic conditions is not purely linear |
| **Ridge Regression** | A regularized linear model that handles correlated economic variables more robustly |
| **Random Forest** | An ensemble method that combines many decision trees — captures complex, non-linear patterns |
| **Elastic Net** | Combines the strengths of Ridge and Lasso regularization for variable selection |
| **Gradient Boosting** | Builds models sequentially, with each new model correcting the errors of previous ones |
| **XGBoost** | An optimized gradient boosting implementation known for strong predictive performance |

Each model type appears as a toggle button with a color indicator. By default, all 8 are enabled.

To run the pipeline:

1. Toggle on the model types you want to evaluate (or leave all enabled for the most comprehensive comparison)
2. Click **Run N Models** (where N is the number of selected types)

The platform submits a Databricks job that runs in parallel:
- Each model type is fitted to every product-cohort combination in your portfolio
- Results are aggregated and the best model per cohort is automatically selected
- ECL is recalculated using the winning models
- Results are synced back for review

![Running the pipeline](/img/screenshots/step-4-run-pipeline.png)
*The model pipeline panel with 8 model types. Click "Run" to evaluate all selected models.*

:::tip Pipeline Progress
While the pipeline runs, a progress indicator shows the job status. The pipeline typically takes a few minutes depending on portfolio size. You will see the status update automatically — no need to refresh the page.
:::

### 2. Review Pipeline Run History

The **Recent Pipeline Runs** panel shows your last 10 pipeline executions with:

- **Status** — green dot for successful runs, red for failed, blue pulsing for currently running
- **Start Time** — when the run began
- **Duration** — how long the pipeline took (in seconds)
- **Link** — a direct link to the Databricks job run for detailed logs

If a previous run produced better results, you can restore it: click the **Run History** toggle in the header to see all historical runs, then click **Restore** on any run to reload its results.

### 3. Review the Model Selection Summary

After a successful pipeline run, the **Model Selection Summary** shows a grid of tiles indicating which model types "won" the most cohorts. This gives you an at-a-glance view of the dominant model type across your portfolio.

For example, you might see that Ridge Regression was selected for 12 cohorts, XGBoost for 8 cohorts, and Linear Regression for 3 cohorts. This diversity is normal — different portfolio segments may have different relationships with economic variables.

### 4. Explore Results by Product

Use the **Product Selector** — a row of pill-shaped buttons, one per product type — to focus on a specific product. The number in parentheses shows how many cohorts (typically grouped by vintage year) exist for that product.

For each product, you see:

**Model Distribution Chart**
A horizontal bar chart showing how many cohorts each model type won for the selected product. This helps you see whether one model dominates or if the selection is spread across types.

**Cohort Models Table**

| Column | What It Shows |
|--------|--------------|
| **Cohort** | The cohort identifier (typically the vintage year — the year loans in this group were originated) |
| **Best Model** | The auto-selected model type, with a color indicator |
| **R-squared** | How well the model explains the relationship between economic variables and credit risk (see below) |
| **RMSE** | How far off the model's predictions are on average (see below) |
| **AIC** | A measure balancing model fit against complexity (lower is better) |
| **Selection Reason** | Why this model was chosen (e.g., "Lowest AIC" or "Lowest CV-RMSE") |

Click a cohort row to see the full model comparison for that cohort.

### 5. Compare Models for a Specific Cohort

When you click a cohort, the **Model Comparison** table expands to show all evaluated models side by side:

| Column | What It Shows |
|--------|--------------|
| **Model** | The model type with color indicator |
| **R-squared** | Goodness of fit (0 to 1 — higher is better) |
| **RMSE** | Root Mean Squared Error (lower is better) |
| **AIC** | Akaike Information Criterion (lower is better) |
| **BIC** | Bayesian Information Criterion (lower is better) |
| **CV-RMSE** | Cross-validated RMSE — how well the model performs on unseen data (lower is better) |
| **Selected** | A green checkmark on the winning model |

The winning row is highlighted. The selection logic is: for parametric models (Linear, Ridge, etc.), the model with the lowest AIC is selected; for tree-based models (Random Forest, Gradient Boosting, XGBoost), the model with the lowest cross-validated RMSE is selected.

![Model comparison](/img/screenshots/step-4-model-comparison.png)
*Side-by-side model comparison for a single cohort. The winning model is highlighted in green.*

### 6. Review the Winning Model's Details

Below the comparison table, a panel shows the selected model's formula and coefficients:

- **Model type** badge
- **Formula** — the mathematical relationship the model learned (displayed as a readable equation)
- **Coefficients** — the weight assigned to each economic variable (e.g., GDP growth, unemployment rate)
- **Fit Metrics** — R-squared, RMSE, AIC, and the number of observations used

:::tip What Do These Metrics Mean?

**R-squared** measures how much of the variation in credit risk is explained by the economic variables. A value of 0.75 means the model explains 75% of the variation. For satellite models, values above 0.30 are generally considered acceptable (the platform's minimum threshold). Higher is better, but very high values (above 0.95) in economic models may indicate overfitting.

**RMSE** (Root Mean Squared Error) measures how far off the model's predictions are, in the same units as the target variable. Lower values indicate more accurate predictions. Compare RMSE across models for the same cohort — the absolute value depends on the scale of your data.

**AIC and BIC** balance accuracy against model complexity. They penalize models that use more parameters, helping prevent overfitting. When comparing models, lower AIC/BIC is better.
:::

### 7. Approve or Reject the Model Selection

When you are satisfied with the auto-selected models:

1. Review the selection across all products and cohorts
2. Optionally add a comment explaining your assessment
3. Click **Approve** to confirm the model selection

If you are not satisfied (for example, a critical product has poor model fit, or the dominant model type seems inappropriate for your portfolio):

1. Enter a comment explaining the concern (required)
2. Click **Reject** to send the step back for rework

Approval advances the project to Step 5: Model Execution. The approved models will be used in the Monte Carlo simulation.

## Understanding the Results

The satellite model selection determines how macroeconomic scenarios will be translated into PD and LGD adjustments during the Monte Carlo simulation. Key things to check:

- **Minimum R-squared threshold**: The platform flags any model with R-squared below 0.30. If the auto-selected model for a cohort has weak fit, consider whether the economic variables available are appropriate for that segment, or whether more data is needed.
- **Consistency across cohorts**: Within a product type, you would generally expect the same or similar model types to win across cohorts. If the selection is highly fragmented (every cohort picks a different model type), this may indicate noisy data or insufficient observations per cohort.
- **Historical comparison**: If you have run satellite models for prior periods, compare the winning model types and R-squared values. Significant changes may indicate structural shifts in the relationship between economic conditions and credit risk.

## Tips & Best Practices

:::tip Run All 8 Models
Unless you have a specific reason to exclude a model type, run all 8. The computational cost is modest and it ensures you are selecting the best model from the widest pool. The platform evaluates them in parallel so there is minimal time penalty.
:::

:::tip Review Low-R-Squared Cohorts
Focus your review on the cohorts with the lowest R-squared values. These are where the model has the weakest explanatory power and where ECL estimates will be most uncertain. Consider whether overlays (Step 7) may be needed to compensate for model limitations in these segments.
:::

:::warning Model Selection Is Per Cohort, Not Per Product
The platform selects the best model for each individual cohort (product-vintage combination), not for the entire product type. This is intentional — different vintage years may have different economic sensitivities. Do not be concerned if you see different model types winning within the same product.
:::

:::tip Use Run History for Comparison
If you have run the pipeline multiple times with different model selections, use the Run History feature to compare results. You can restore a previous run if it produced better overall fit.
:::

## What's Next?

Proceed to [Step 5: Model Execution](step-5-model-execution) to run the Monte Carlo simulation and compute probability-weighted Expected Credit Losses.
