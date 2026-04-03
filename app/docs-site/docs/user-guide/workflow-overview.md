---
sidebar_position: 1
title: "The 8-Step ECL Workflow"
description: "A visual overview of the complete IFRS 9 Expected Credit Loss workflow — from project creation through final sign-off."
---

# The 8-Step ECL Workflow

The IFRS 9 ECL Platform organizes the entire Expected Credit Loss process into eight sequential steps. Each step must be completed before advancing to the next, ensuring a disciplined, auditable approach to credit impairment calculation.

:::info Prerequisites
- An active ECL project (see [Your First ECL Project](../quick-start))
- Appropriate role permissions for each step
:::

## Workflow at a Glance

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. Create   │───▶│  2. Data     │───▶│  3. Data     │───▶│  4. Satellite│
│   Project    │    │  Processing  │    │  Control     │    │   Models     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                    │
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────▼──────┐
│  8. Sign-Off │◀───│  7. Overlays │◀───│  6. Stress   │◀───│  5. Model    │
│              │    │              │    │  Testing     │    │  Execution   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

![ECL workflow overview](/img/guides/ecl-workflow-overview.png)
*The 8-step workflow as shown in the platform's stepper interface.*

## Step-by-Step Summary

### Step 1: Create Project

**What you do**: Define the ECL project — name, reporting date, base currency, and portfolio scope.

**Why it matters**: Every ECL calculation is anchored to a specific reporting period. The project container ensures all subsequent steps, data, and results are linked to this period.

**Output**: A new project in "Active" state, ready for data processing.

[Read the full guide &#8594;](step-1-create-project)

---

### Step 2: Data Processing

**What you do**: Import and review portfolio data — loan balances, borrower attributes, and risk parameters.

**Why it matters**: The quality of your ECL depends on the quality of your input data. This step loads the portfolio and calculates key performance indicators (KPIs) including stage distribution, exposure summaries, and default rates.

**Output**: Processed portfolio with stage assignments and summary statistics.

[Read the full guide &#8594;](step-2-data-processing)

---

### Step 3: Data Control

**What you do**: Run automated quality checks and approve the data through maker-checker review.

**Why it matters**: IFRS 9 requires demonstrable data quality governance. The quality control process checks for missing values, out-of-range parameters, and inconsistent stage assignments before any calculation proceeds.

**Output**: Approved dataset with documented quality assessment.

[Read the full guide &#8594;](step-3-data-control)

---

### Step 4: Satellite Models

**What you do**: Select and configure macroeconomic models that link Probability of Default (PD) and Loss Given Default (LGD) to economic conditions.

**Why it matters**: IFRS 9 requires "forward-looking" information in ECL calculations. Satellite models translate macroeconomic scenarios (GDP growth, unemployment, interest rates) into PD and LGD adjustments, ensuring provisions reflect expected future conditions.

**Output**: Selected model configuration with performance metrics (R-squared, RMSE).

[Read the full guide &#8594;](step-4-satellite-model)

---

### Step 5: Model Execution

**What you do**: Run the Monte Carlo simulation to compute probability-weighted Expected Credit Losses.

**Why it matters**: This is the core calculation — the engine generates thousands of correlated PD-LGD scenarios, computes ECL for each, and produces a probability-weighted estimate. The result is a defensible, statistically rigorous ECL figure.

**Output**: ECL results by stage, product type, and scenario, with confidence intervals and convergence diagnostics.

[Read the full guide &#8594;](step-5-model-execution)

---

### Step 6: Stress Testing

**What you do**: Analyze how ECL responds to different conditions through sensitivity analysis, vintage analysis, concentration analysis, and migration analysis.

**Why it matters**: Regulators and senior management need to understand how robust the ECL estimate is. Stress testing reveals which portfolios, scenarios, or assumptions have the greatest impact on provisions.

**Output**: Stress test results across multiple analysis dimensions.

[Read the full guide &#8594;](step-6-stress-testing)

---

### Step 7: Overlays

**What you do**: Apply management adjustments (overlays) to the model-computed ECL, with documented rationale for each adjustment.

**Why it matters**: IFRS 9 explicitly allows post-model adjustments to account for factors the models cannot capture — such as emerging risks, sector-specific concerns, or anticipated regulatory changes. Every overlay must be justified and recorded.

**Output**: Adjusted ECL figures with documented overlay rationale.

[Read the full guide &#8594;](step-7-overlays)

---

### Step 8: Sign-Off

**What you do**: Review the final ECL summary, attest to the results, and lock the calculation.

**Why it matters**: The sign-off step enforces governance. It applies segregation of duties (the signer must differ from the executor), creates a hash-based integrity seal, and produces an immutable audit record. Once signed off, the project cannot be modified without creating a new run.

**Output**: Locked project with hash verification, approval record, and immutable audit trail.

[Read the full guide &#8594;](step-8-sign-off)

---

## After the Workflow

Once you have completed the 8-step workflow and signed off, you can:

| Action | Description |
|--------|-------------|
| [**Generate Regulatory Reports**](regulatory-reports) | Create IFRS 7 disclosure reports (35H-35N) |
| [**Create GL Journals**](gl-journals) | Generate double-entry provisioning journal entries |
| [**Run Backtesting**](backtesting) | Validate model performance against actual outcomes |
| [**Review Attribution**](attribution) | Analyze what drove ECL changes between periods |
| [**Explore Advanced Features**](advanced-features) | Cure rates, credit conversion factors, collateral haircuts |

## Tips for a Smooth Workflow

:::tip Start with Sample Data
If you are evaluating the platform, use the built-in sample portfolio (79,000 loans) to explore every step before loading production data.
:::

:::tip Review Before Advancing
Each step's results carry forward. Take time to review KPIs, model fit, and simulation results before clicking "Advance" — corrections become harder in later steps.
:::

:::warning Plan Your Roles
Because sign-off requires segregation of duties, ensure at least two authorized users are available before starting a time-sensitive ECL run.
:::

## What's Next?

Ready to dive into each step? Start with [Step 1: Create Project](step-1-create-project).
