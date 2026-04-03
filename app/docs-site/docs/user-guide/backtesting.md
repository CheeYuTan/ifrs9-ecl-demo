---
sidebar_position: 11
title: "Backtesting"
description: "Traffic light system for model validation, performance metrics, and guidance on when to retrain models."
---

# Backtesting

Backtesting is the process of comparing a model's predictions against actual outcomes to verify that the model remains fit for purpose. The platform implements the **traffic light system** aligned with European Banking Authority guidelines (EBA/GL/2017/16), giving you an immediate visual assessment of model health: green means acceptable, amber means investigate, red means recalibrate. Regular backtesting is a regulatory expectation — models that are not periodically validated are a governance finding.

:::info Prerequisites
- At least one registered model in the [Model Registry](model-registry) with historical prediction data
- Actual default outcomes available for the observation period
- **Risk Manager** or **Admin** role to run backtests
- **Analyst** role sufficient for viewing results
:::

## What You'll Do

On this page you will run backtests against registered PD and LGD models, interpret the traffic light results for each metric, understand what the discrimination and calibration metrics mean in plain language, review per-cohort performance, and decide whether a model needs retraining.

## The Traffic Light System

The traffic light system provides an at-a-glance assessment of model performance. Each metric receives its own traffic light, and an overall rating is derived from the combination:

| Light | Meaning | Action Required |
|-------|---------|-----------------|
| **Green** | Model performance is within acceptable thresholds | Continue using the model. Schedule next periodic backtest. |
| **Amber** | Performance is borderline — not failing, but deteriorating | Investigate the cause. Document your finding and whether remediation is needed. Consider enhanced monitoring. |
| **Red** | Model is underperforming and may produce unreliable ECL estimates | Initiate model recalibration or replacement. Do not rely on this model for regulatory reporting without documented management override. |

The **overall traffic light** follows a conservative rule:
- If **any metric is red** → overall is **red**
- If **any metric is amber** (and none red) → overall is **amber**
- Only if **all metrics are green** → overall is **green**

![Backtesting traffic light summary](/img/screenshots/backtesting-traffic-light.png)
*The backtesting dashboard showing the overall traffic light and individual metric results.*

## Step-by-Step Instructions

### 1. Select a Model to Backtest

From the Backtesting page, select the model type:

- **PD Models** — tests discrimination (can the model rank borrowers?) and calibration (are predicted default rates accurate?)
- **LGD Models** — tests prediction accuracy (are estimated loss rates close to actual losses?)

Then select the specific model from the dropdown. The platform shows the model's current status, version, and when it was last backtested.

### 2. Configure the Backtest

Set the parameters for the backtest:

| Parameter | What It Controls |
|-----------|-----------------|
| **Observation Window** | The period during which predictions were made (e.g., January 2024 to December 2024) |
| **Outcome Window** | The period during which actual defaults are observed (must follow the observation window) |

The observation and outcome windows determine which loans are included and what actual outcomes are measured against the model's predictions.

### 3. Run the Backtest

Click **Run Backtest**. The platform will:

1. Retrieve the model's predictions for loans in the observation window
2. Match predictions against actual outcomes in the outcome window
3. Compute all discrimination, calibration, and stability metrics
4. Assign traffic lights to each metric based on regulatory thresholds
5. Generate per-cohort breakdowns

### 4. Read the Results — PD Models

For PD models, the backtesting results are organised into three categories:

#### Discrimination Metrics (Can the model rank borrowers?)

These metrics test whether the model correctly assigns higher default probabilities to borrowers who actually defaulted:

| Metric | What It Measures | Green | Amber |
|--------|-----------------|-------|-------|
| **AUC** | Area Under the ROC Curve — the probability that the model ranks a random defaulter higher than a random non-defaulter | 0.70 or above | 0.60 – 0.69 |
| **Gini Coefficient** | Accuracy Ratio — a rescaled version of AUC that ranges from 0 (random) to 1 (perfect) | 0.40 or above | 0.20 – 0.39 |
| **KS Statistic** | Maximum separation between the cumulative distributions of defaulters and non-defaulters | 0.30 or above | 0.15 – 0.29 |

In plain language: if AUC is 0.85, it means that 85% of the time, the model correctly identifies which of two borrowers is more likely to default. An AUC below 0.60 means the model is barely better than guessing.

#### Calibration Metrics (Are predicted rates accurate?)

These metrics test whether predicted default rates match actual default rates:

| Metric | What It Measures | Green | Amber |
|--------|-----------------|-------|-------|
| **Hosmer-Lemeshow** | Whether predicted and actual default rates agree across deciles of the portfolio | p-value 0.05 or above | p-value 0.01 – 0.04 |
| **Binomial Test** | Whether the number of actual defaults per rating grade falls within the model's confidence interval | Pass rate 80% or above | Pass rate 60% – 79% |

In plain language: calibration checks whether a model that predicts "5% of these borrowers will default" actually sees roughly 5% default. A failing Hosmer-Lemeshow test means the model systematically over- or under-predicts.

#### Stability Metrics (Has the portfolio changed?)

These metrics test whether the current portfolio's characteristics are consistent with the data the model was trained on:

| Metric | What It Measures | Green | Amber |
|--------|-----------------|-------|-------|
| **PSI** | Population Stability Index — measures how much the distribution of predicted probabilities has shifted since training | 0.10 or below | 0.11 – 0.25 |
| **Brier Score** | Overall prediction accuracy combining discrimination and calibration | 0.15 or below | 0.16 – 0.25 |

In plain language: PSI detects "population drift." If your mortgage portfolio shifts from mostly prime borrowers to mostly subprime borrowers, PSI will flag that the model is being applied to a different population than it was built for. Above 0.25 means the model urgently needs retraining on current data.

### 5. Read the Results — LGD Models

For LGD models, the metrics focus on prediction accuracy:

| Metric | What It Measures | Green | Amber |
|--------|-----------------|-------|-------|
| **MAE** | Mean Absolute Error — average difference between predicted and actual loss rates | 0.10 or below | 0.11 – 0.20 |
| **RMSE** | Root Mean Squared Error — like MAE but penalises large errors more heavily | 0.15 or below | 0.16 – 0.25 |
| **Mean Bias** | Whether the model systematically over- or under-predicts losses | 0.05 or below | 0.06 – 0.10 |

A positive mean bias means the model is **conservative** (predicting higher losses than actually occur). While conservatism is generally acceptable, excessive conservatism inflates ECL provisions unnecessarily.

### 6. Review Per-Cohort Performance

Below the metric cards, the **Cohort Analysis** section breaks down predicted versus actual rates by:

- **Rating Grade** — how does each internal credit grade perform?
- **Product Type** — do some product types validate better than others?
- **Vintage** — are recent originations behaving differently from older ones?

A bar chart shows predicted rates alongside actual rates for each cohort. Large gaps between predicted and actual in specific cohorts indicate where the model is weakest.

![Backtesting cohort comparison](/img/screenshots/backtesting-cohort.png)
*Predicted versus actual default rates by cohort, highlighting segments where the model diverges.*

### 7. Review Historical Trends

The **Trend Analysis** tab shows how each metric has evolved across multiple backtests over time. This helps identify gradual model degradation that a single backtest might not reveal:

- A declining AUC trend suggests the model's discriminatory power is eroding
- A rising PSI trend indicates the portfolio is drifting from the training data
- A persistent amber on calibration metrics suggests systematic bias

:::tip Track Trends, Not Just Snapshots
A single backtest can be influenced by unusual events (e.g., a pandemic). The trend across multiple backtests gives a more reliable picture of model health. Schedule backtests quarterly and compare results over at least four quarters before making retraining decisions.
:::

## When to Retrain a Model

Use these guidelines to decide what action to take based on backtesting results:

| Situation | Recommended Action |
|-----------|--------------------|
| All green, stable trend | No action. Schedule next periodic backtest. |
| One or two amber metrics, stable | Document the finding. Monitor at next backtest. Consider if a known event caused the result. |
| Multiple amber metrics or worsening trend | Initiate model review. Consider whether current economic conditions differ from training data. Prepare a retraining plan. |
| Any red metric | Escalate to model governance committee. Begin retraining immediately. Document a management override if the model must continue in use while the replacement is developed. |
| PSI above 0.25 | The portfolio has materially changed. Retrain on current data regardless of other metric results. |

:::warning Red Does Not Mean Stop
A red traffic light does not automatically invalidate the current ECL calculation. It means the model needs urgent attention. While the replacement model is being developed, document a management override explaining why the current model is still the best available estimate. This override should be reviewed and approved by the model governance committee.
:::

## Tips & Best Practices

:::tip Minimum Sample Sizes Matter
Backtesting requires sufficient data to produce statistically meaningful results. The platform requires at least 30 loans in the backtest sample and at least 5 observed defaults per rating grade for the binomial test. Smaller portfolios may need to extend the observation window to accumulate enough defaults.
:::

:::caution Backtesting Is Not Model Validation
Backtesting (comparing predictions to outcomes) is one component of model validation, but not the whole story. A comprehensive model validation also includes conceptual soundness review, sensitivity analysis, and benchmarking against alternative approaches. The Model Registry tracks the full validation history.
:::

## What's Next?

- [Model Registry](model-registry) — promote validated models or retire underperforming ones based on backtest results
- [Step 6: Stress Testing](step-6-stress-testing) — understand how models behave under adverse scenarios
- [Step 4: Satellite Models](step-4-satellite-model) — review model calibration before running a new backtest
