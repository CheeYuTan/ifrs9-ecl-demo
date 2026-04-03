---
sidebar_position: 10
title: "Model Registry"
description: "Browse registered models, compare performance metrics, and understand the model governance lifecycle."
---

# Model Registry

The Model Registry is the platform's central catalog for all credit risk models used in ECL calculations. Every model — whether it estimates Probability of Default (PD), Loss Given Default (LGD), Exposure at Default (EAD), or stage assignment — is registered here with its performance metrics, version history, and governance status. The registry ensures that only validated, approved models are used in production ECL calculations, providing the model governance trail that regulators expect.

:::info Prerequisites
- Completed at least one ECL project through [Step 4: Satellite Models](step-4-satellite-model)
- **Risk Manager** or **Admin** role for model registration and approval
- **Analyst** role sufficient for browsing and comparison
:::

## What You'll Do

On this page you will browse the model inventory, understand the five lifecycle stages every model passes through, compare models side-by-side using performance metrics, review model cards for governance documentation, and promote validated models to champion status.

## Understanding Model Lifecycle

Every model in the registry progresses through five governance stages. This lifecycle ensures that no model enters production without proper validation and approval:

| Stage | Badge Color | What It Means |
|-------|-------------|---------------|
| **Draft** | Grey | Newly registered model. Metadata and metrics can still be edited. Not yet submitted for review. |
| **Pending Review** | Amber | Submitted for validation by the model owner. Waiting for an independent reviewer to assess. |
| **Approved** | Blue | Passed validation review. Confirmed as fit for purpose but not yet active in production. |
| **Active** | Green | Promoted to production use. This is the **champion model** for its model type and product segment. |
| **Retired** | Red | Decommissioned. Retained in the registry for audit trail purposes but no longer used in calculations. |

The allowed transitions enforce governance controls:

- **Draft** → **Pending Review** — the model owner submits the model for independent review
- **Pending Review** → **Approved** — the reviewer confirms the model meets validation standards
- **Pending Review** → **Draft** — the reviewer rejects the model with feedback; the owner can revise and resubmit
- **Approved** → **Active** — a senior risk manager promotes the model to champion status
- **Active** → **Retired** — the model is decommissioned when a successor is promoted

:::warning Segregation of Duties
The person who registers a model cannot be the same person who approves it. This separation ensures independent model validation — a governance requirement under most banking supervisory frameworks.
:::

## Step-by-Step Instructions

### 1. Browse the Model Inventory

The Model Registry landing page displays all registered models in a sortable, filterable table:

| Column | What It Shows |
|--------|---------------|
| **Model Name** | Descriptive name (e.g., "PD Corporate Term Loans v3.2") |
| **Type** | PD, LGD, EAD, or Staging |
| **Algorithm** | The modelling technique (e.g., Logistic Regression, XGBoost, Random Forest) |
| **Version** | Version number within the model lineage |
| **Status** | Current lifecycle stage with colour-coded badge |
| **Champion** | Trophy icon if this is the active production model for its segment |
| **Created** | Registration date |

Use the **filter controls** at the top to narrow the list:
- **By Type** — show only PD models, only LGD models, etc.
- **By Status** — show only Active models, only models Pending Review, etc.

![Model Registry list view](/img/screenshots/model-registry-list.png)
*The Model Registry showing registered models with status badges and champion indicators.*

### 2. View Model Details

Click any model row to open the **Model Detail** panel. This panel shows:

- **Model metadata** — name, type, algorithm, version, product type, cohort
- **Performance metrics** — AUC, Gini, KS, Accuracy, RMSE, R-squared (depending on model type)
- **Training data summary** — sample size, date range, data snapshot identifier
- **Governance trail** — who registered, reviewed, approved, and promoted the model, with timestamps
- **Audit history** — every status change recorded with the user, timestamp, and comments

### 3. Compare Models Side-by-Side

To compare two or more models:

1. Select models using the checkboxes in the model list
2. Click the **Compare** button in the toolbar
3. The comparison view opens showing models in columns with metrics in rows

The comparison includes:

| Comparison Field | What to Look For |
|-----------------|------------------|
| **AUC** | Higher is better — measures the model's ability to distinguish defaulters from non-defaulters |
| **Gini Coefficient** | Higher is better — the accuracy ratio, related to AUC by Gini = 2 × AUC - 1 |
| **KS Statistic** | Higher is better — maximum separation between cumulative default and non-default distributions |
| **RMSE** | Lower is better — prediction error magnitude |
| **R-squared** | Higher is better — proportion of variance explained |

A **radar chart** visualises the comparison across all metrics simultaneously, making it easy to spot which model excels on which dimension.

:::tip Compare Before Promoting
Always compare a candidate model against the current champion before promotion. A model should demonstrate meaningful improvement on at least the primary discrimination metric (AUC for PD models, RMSE for LGD models) to justify a champion change.
:::

### 4. Review the Model Card

Every model has an auto-generated **Model Card** — a structured governance document that summarises everything an auditor or reviewer needs:

- **Methodology** — algorithm description, key parameters, product scope, cohort definition
- **Training Data** — sample size, date range, representativeness, data quality hash
- **Performance** — all metrics with thresholds and pass/fail indicators
- **Validation** — who validated, validation methodology, findings
- **Assumptions and Limitations** — automatically extracted from model metadata
- **Governance Trail** — complete history of status changes with responsible parties

The Model Card can be exported for inclusion in model validation reports and regulatory submissions.

### 5. Register a New Model

To register a model, click **Register Model** and complete the form:

1. **Model Name** — use a descriptive naming convention (e.g., "PD Retail Mortgages v2.1")
2. **Model Type** — select PD, LGD, EAD, or Staging
3. **Algorithm** — the modelling technique used
4. **Product Type** — which portfolio segment this model covers
5. **Performance Metrics** — enter the validation results (AUC, Gini, KS, etc.)
6. **Description** — explain the model's purpose, key features, and any differences from prior versions

After saving, the model enters **Draft** status. Review the details, then click **Submit for Review** to move it to Pending Review.

### 6. Approve and Promote Models

**Approving** (Pending Review → Approved):
- Open a model in Pending Review status
- Review the performance metrics, training data summary, and model card
- Click **Approve** to confirm the model meets validation standards, or **Reject** with comments to return it to Draft

**Promoting** (Approved → Active):
- Open an Approved model
- Click **Promote to Active** — this designates it as the champion model
- The previous champion (if any) is automatically moved to Retired status

:::caution Champion Model Changes Affect ECL
When you promote a new champion model, all subsequent ECL calculations for that product segment will use the new model. Ensure the model has been thoroughly validated and backtested before promotion. See [Backtesting](backtesting) for validation guidance.
:::

## Understanding Model Types

The platform uses four categories of credit risk models:

| Model Type | What It Estimates | Key Metric |
|------------|------------------|------------|
| **PD** | Probability that a borrower will default within a given time horizon | AUC, Gini |
| **LGD** | Percentage of exposure that will be lost if default occurs | RMSE, R-squared |
| **EAD** | Outstanding exposure amount at the point of default | RMSE |
| **Staging** | Which IFRS 9 impairment stage a loan should be assigned to | Accuracy, KS |

Each model type has different primary performance metrics. The registry displays the relevant metrics for each type automatically.

## Tips & Best Practices

:::tip Maintain a Model Lineage
Use version numbers and the parent model reference to maintain a clear lineage. When you register v3.2, link it to v3.1 so the registry shows the complete evolution of each model family.
:::

:::tip Document Rejection Reasons
When rejecting a model, always provide specific feedback — which metrics fell short, what additional validation is needed, or what data quality concerns were found. This creates a governance record showing that the review was substantive, not perfunctory.
:::

:::warning Keep At Least One Active Model Per Type
The ECL calculation requires an active champion model for each model type used. If you retire a champion without promoting a successor, ECL calculations for that segment will fail. Always promote the replacement before retiring the incumbent.
:::

## What's Next?

- [Backtesting](backtesting) — validate model performance using the traffic light system before promoting to champion
- [Step 4: Satellite Models](step-4-satellite-model) — understand how models are calibrated during the ECL workflow
- [Regulatory Reports](regulatory-reports) — model information feeds into IFRS 7 disclosure reports
