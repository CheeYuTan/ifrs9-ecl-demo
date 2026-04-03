---
sidebar_position: 16
title: "Markov Chains & Hazard Models"
description: "Interpreting transition matrices, survival curves, and lifetime PD term structures for credit risk analysis."
---

# Markov Chains & Hazard Models

Markov Chains and Hazard Models are the statistical engines behind two of the most important questions in credit risk: **"How likely are borrowers to move between credit states?"** and **"How long until a borrower defaults?"** The platform provides both approaches so that risk teams can estimate transition probabilities from historical data, forecast how a portfolio's credit quality will evolve over time, and derive the lifetime Probability of Default (PD) curves that feed directly into the ECL calculation. These tools transform raw migration history into the forward-looking risk measures that IFRS 9 requires.

:::info Prerequisites
- Completed data processing with stage migration history (see [Step 2: Data Processing](step-2-data-processing))
- Historical default data for hazard model estimation
- **Analyst** role or above to estimate models; all roles can view results
:::

## What You'll Do

On this page you will estimate transition matrices from historical migration data, interpret the colour-coded heatmap, run stage distribution forecasts, read lifetime PD curves, estimate hazard models (Cox Proportional Hazards, Kaplan-Meier, and discrete-time logistic), and compare models and matrices side by side.

## Part 1: Markov Chain Transition Matrices

### What Is a Transition Matrix?

A transition matrix shows the probability that a loan in one credit state at the start of a period will be in each possible state at the end of that period. The platform uses four states:

| State | Meaning |
|---|---|
| **Stage 1** | Performing — no significant increase in credit risk since origination |
| **Stage 2** | Underperforming — significant increase in credit risk (SICR triggered) |
| **Stage 3** | Credit-impaired — the borrower is in default |
| **Default** | Absorbing state — once a loan enters Default, it does not return |

The matrix is read row by row. For example, if the Stage 1 row shows [0.92, 0.06, 0.01, 0.01], it means: of all loans starting in Stage 1, 92% remain in Stage 1, 6% move to Stage 2, 1% to Stage 3, and 1% to Default.

### Step-by-Step: Estimating a Matrix

1. Navigate to **Markov Chains** from the main menu
2. The page opens to the **Transition Matrix** tab
3. Optionally filter by **Product Type** or **Segment** to estimate a matrix for a specific portfolio slice
4. Click **Estimate Matrix**
5. The platform reads the historical stage migration data and calculates transition probabilities using the cohort methodology
6. The resulting matrix appears as an interactive colour-coded heatmap

### Reading the Heatmap

The heatmap uses colour intensity to make patterns immediately visible:

| Colour | Meaning |
|---|---|
| **Blue (diagonal)** | Probability of staying in the same state — higher is better for Stages 1 and 2 |
| **Green (off-diagonal, low values)** | Small transition probability — relatively few loans moving to this state |
| **Red (off-diagonal, high values)** | Large transition probability — many loans moving to this state, indicating credit deterioration |

![Markov transition matrix heatmap](/img/screenshots/markov-heatmap.png)
*The colour-coded transition matrix showing migration probabilities between credit states. Diagonal values (blue) represent retention rates.*

Key metrics displayed alongside the heatmap:

| Metric | What It Tells You |
|---|---|
| **SICR Probability** | The probability of a Stage 1 loan moving to Stage 2 — the key trigger for lifetime ECL measurement |
| **Cure Rate** | The probability of a Stage 2 loan improving back to Stage 1 |
| **Default Probability** | The probability of a Stage 3 loan entering the absorbing Default state |
| **Stage 1 Retention** | The percentage of Stage 1 loans that remain in Stage 1 — portfolio stability indicator |

:::tip What Good Looks Like
A healthy portfolio typically shows Stage 1 retention above 90%, SICR probability below 5%, and cure rates above 30%. These benchmarks vary significantly by product type — consumer loans typically show higher migration volatility than corporate exposures.
:::

### Stage Distribution Forecast

From the Transition Matrix tab, click **Forecast** to project how the portfolio's stage composition will evolve over time:

1. The platform uses the current portfolio composition as the starting distribution
2. It applies the transition matrix repeatedly (matrix exponentiation P^n) for each future month
3. The result is a **stacked area chart** showing the projected percentage in each state over a 12- to 120-month horizon

The forecast answers: "If current migration patterns continue, what will our portfolio look like in 1 year? In 5 years?" Watch for the Default state growing over time — in any transition matrix with a non-zero default probability, the absorbing state will eventually capture all loans.

### Lifetime PD Curves

Click **Lifetime PD** to see cumulative default probability curves for each starting stage:

- **Stage 1 curve** — starts low, gradually increases over the lifetime
- **Stage 2 curve** — starts higher, reflecting the already-deteriorated credit quality
- **Stage 3 curve** — starts highest, as these loans are already credit-impaired

Three summary cards appear for each curve:

| Card | Definition |
|---|---|
| **12-Month PD** | Probability of default within the first year — this is the PD used for Stage 1 ECL |
| **Mid-Point PD** | Cumulative PD at the midpoint of the loan's remaining life |
| **Lifetime PD** | Cumulative PD at the end of the full remaining life — this is used for Stage 2 and Stage 3 ECL |

### Comparing Matrices

The **Compare** tab allows side-by-side comparison of two or more matrices — for example, comparing matrices estimated for different product types, different time periods, or different segments. Differences in migration behaviour between segments reveal where credit risk is concentrated.

## Part 2: Hazard Models

While Markov Chains model transitions between discrete states, Hazard Models focus on the **time to default** — how long a loan survives before experiencing a credit event. The platform supports three estimation methods.

### Three Model Types

| Model | Best For | What It Produces |
|---|---|---|
| **Cox Proportional Hazards** | Understanding which borrower characteristics (covariates) accelerate or delay default | Hazard ratios for each covariate, baseline hazard function, survival curves |
| **Kaplan-Meier** | Simple, non-parametric survival estimation when covariate effects are not the focus | Survival curve with confidence intervals |
| **Discrete-Time Logistic** | Period-by-period default probability when data is observed at discrete intervals (e.g., monthly) | Hazard function at each time point, cumulative PD curve |

### Step-by-Step: Estimating a Hazard Model

1. Navigate to **Hazard Models** (accessible from the Markov Chains page or from the main menu)
2. Select the **Estimation Type** from the dropdown (Cox PH, Kaplan-Meier, or Discrete-Time)
3. Click **Estimate**
4. The platform fits the model to historical default data
5. Results appear across multiple tabs

### Reading the Results

#### Survival Tab

The **Survival** tab shows the survival curve — the probability that a loan has **not** defaulted by each time point:

- The curve starts at 1.0 (100% survival at time zero) and decreases over time
- A steep drop indicates a period of high default risk
- A flattening curve indicates a period of stability
- For Kaplan-Meier, confidence intervals show the uncertainty around the estimate

#### Hazard Tab

The **Hazard** tab shows the instantaneous default rate at each time point:

- Peaks in the hazard function indicate periods when defaults are concentrated
- A flat hazard suggests constant default risk over time
- A rising hazard suggests default risk accumulates as loans age (common for unsecured consumer credit)

![Hazard model survival curves](/img/screenshots/hazard-survival.png)
*Survival curves from three hazard model types, showing the proportion of loans surviving at each time point.*

#### PD Term Structure

The **PD Term Structure** tab converts the survival function into cumulative PD at each month — the format needed for ECL calculation:

- Cumulative PD = 1 − Survival probability at time t
- The term structure shows PD at 12 months, 24 months, 36 months, and so on
- This curve is used directly by the ECL engine to determine the default probability at each future quarter

#### Coefficients Tab (Cox PH Only)

For the Cox Proportional Hazards model, the **Coefficients** tab shows which borrower characteristics influence the speed of default:

- A **positive coefficient** means the variable accelerates default (e.g., higher debt-to-income ratio)
- A **negative coefficient** means the variable delays default (e.g., longer time at current address)
- The **hazard ratio** (exp(coefficient)) shows the multiplicative effect — a hazard ratio of 1.5 means 50% faster time-to-default

### Comparing Models

Select multiple models using the checkboxes in the model list, then switch to the **Compare** tab:

- Survival curves are overlaid on the same chart for visual comparison
- Key metrics (median survival time, 12-month PD, lifetime PD) are shown side by side
- This helps you choose the most appropriate model for your portfolio

## How These Feed into the ECL Calculation

Both Markov Chains and Hazard Models produce **PD term structures** — the probability of default at each future time point. These term structures are inputs to the Monte Carlo simulation in [Step 5: Model Execution](step-5-model-execution):

- **Stage 1 loans** use the 12-month PD (from either the transition matrix or the hazard model)
- **Stage 2 and 3 loans** use the lifetime PD (the full term structure up to loan maturity)
- The ECL formula at each future quarter is: **PD × LGD × EAD × Discount Factor**

The choice between Markov Chains and Hazard Models depends on your data and regulatory preferences. Many institutions use both: Markov Chains for portfolio-level stage forecasting and reporting, and Hazard Models for loan-level PD estimation.

## Tips & Best Practices

:::tip Start with Kaplan-Meier
If you are new to hazard modelling, start with Kaplan-Meier — it requires no assumptions about the functional form and gives you a quick visual of default timing. Move to Cox PH when you want to understand which borrower characteristics drive default.
:::

:::tip Segment Your Analysis
Transition probabilities and survival curves vary dramatically by product type. A residential mortgage portfolio will show much lower migration volatility than a credit card portfolio. Always estimate separate matrices and models by product type for meaningful results.
:::

:::warning Absorbing State Interpretation
Default is modelled as an absorbing state — once a loan enters Default, it stays there in the Markov Chain framework. In reality, loans can be restructured or cured from Default. The platform handles cures separately through the [cure rate analysis](advanced-features) in Advanced Features.
:::

:::caution Data Requirements
Reliable transition matrix estimation requires at least two consecutive reporting periods with stage migration data. Hazard model estimation requires historical default data with event timestamps. If your data history is limited, the estimated probabilities will have wider confidence intervals.
:::

## What's Next?

- [Step 5: Model Execution](step-5-model-execution) — the Monte Carlo simulation uses PD term structures from these models
- [Step 4: Satellite Models](step-4-satellite-model) — satellite models provide the macroeconomic adjustment layer on top of through-the-cycle PDs
- [Advanced Features](advanced-features) — cure rate analysis complements the transition matrix by quantifying how often loans recover
- [Backtesting](backtesting) — validate model predictions against actual outcomes
