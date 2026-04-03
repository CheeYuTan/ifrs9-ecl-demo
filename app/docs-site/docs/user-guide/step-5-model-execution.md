---
sidebar_position: 6
title: "Step 5: Model Execution"
description: "Running Monte Carlo simulations to compute probability-weighted ECL across scenarios."
---

# Step 5: Model Execution

Model Execution is where the platform computes your Expected Credit Losses. Using a Monte Carlo simulation, the system generates thousands of possible credit loss outcomes across your macroeconomic scenarios, then probability-weights them to produce your final ECL figure. This is the core calculation step — everything before it prepared the inputs, and everything after it analyzes and governs the results.

:::info Prerequisites
- Completed [Step 4: Satellite Models](step-4-satellite-model)
- Satellite models calibrated and approved
- Macroeconomic scenarios defined by your administrator
:::

## What You'll Do

On this page you will configure simulation parameters, run the Monte Carlo ECL calculation, monitor its progress in real time, and review the results — including ECL by product, by scenario, and by impairment stage. You can also compare simulation results against pre-computed values from the prior period.

## Step-by-Step Instructions

### 1. Review Pre-Computed ECL (Optional)

Before running a new simulation, the platform displays the **pre-computed ECL** from the most recent prior calculation. This gives you a baseline for comparison:

| Metric | What It Shows |
|--------|--------------|
| **Total ECL** | The aggregate Expected Credit Loss across all products and stages |
| **Coverage Ratio** | ECL as a percentage of Gross Carrying Amount — indicates how much of the portfolio is provisioned |
| **ECL by Product** | Breakdown showing which product types (mortgages, personal loans, credit cards, etc.) contribute the most to total ECL |
| **ECL by Stage** | How much ECL comes from Stage 1 (12-month), Stage 2 (lifetime), and Stage 3 (credit-impaired) loans |

This baseline is useful for validating that your new simulation produces results in a reasonable range. Significant deviations should be investigated.

### 2. Configure Simulation Parameters

The **Simulation Panel** lets you adjust the Monte Carlo parameters before running. Key settings include:

| Parameter | What It Controls | Default |
|-----------|-----------------|---------|
| **Number of Simulations** | How many random scenarios the engine generates. More simulations produce more stable results but take longer. | 1,000 |
| **PD-LGD Correlation** | The relationship between Probability of Default and Loss Given Default. Higher values mean defaults and losses tend to move together. | 0.30 (30%) |
| **Aging Factor** | How much loan seasoning affects default probability. Newer loans typically have different risk profiles than mature ones. | 0.08 |
| **PD Floor / Cap** | The minimum and maximum bounds for Probability of Default. Prevents extreme values from distorting results. | 0.1% – 95% |
| **LGD Floor / Cap** | The minimum and maximum bounds for Loss Given Default. Ensures recovery assumptions stay within realistic ranges. | 1% – 95% |
| **Random Seed** | A number that makes the simulation reproducible. Using the same seed produces identical results, useful for audit trails. | Auto-generated |

:::tip When to Increase Simulation Count
For regulatory submissions, consider running 5,000–10,000 simulations to ensure convergence. For internal management reporting, 1,000 is typically sufficient. Watch the convergence indicator — if results are still fluctuating at completion, increase the count.
:::

### 3. Adjust Scenario Weights (Optional)

If your administrator has defined multiple macroeconomic scenarios (e.g., Base, Optimistic, Adverse), you can adjust their probability weights:

- Weights are expressed as percentages and **must sum to 100%**
- The platform validates the sum before allowing execution
- Each scenario represents a different view of the economic outlook — for example, the Base case might assume moderate GDP growth, while the Adverse case models a recession

Scenario weighting is a key IFRS 9 requirement: the standard mandates that ECL be a probability-weighted outcome, not a single-scenario estimate. The weights you assign here directly affect the final ECL figure.

:::warning Scenario Weights Have Material Impact
Changing scenario weights shifts the ECL outcome. Increasing the weight of an adverse scenario increases total ECL; increasing the weight of an optimistic scenario decreases it. Ensure weights reflect your institution's genuine view of economic probabilities, as auditors will examine the rationale behind these choices.
:::

### 4. Run the Simulation

Click **Run Simulation** to start the Monte Carlo engine. The platform provides real-time feedback during execution:

- **Progress Bar** — shows percentage completion as simulations are generated
- **Elapsed Time** — how long the simulation has been running
- **Status Messages** — key milestones (e.g., "Generating scenarios", "Computing ECL by product", "Aggregating results")

For large portfolios, you can choose to run the simulation on scalable compute (a Databricks Job), which processes results faster. Your administrator configures whether this option is available.

The simulation cannot be cancelled mid-run. Once started, it will run to completion.

### 5. Review Simulation Results

When the simulation completes, the results are displayed across several panels:

**ECL by Product**

A table showing, for each product type:

| Column | What It Shows |
|--------|--------------|
| **Product** | Loan product name (e.g., Personal Loans, Mortgages) |
| **Gross Carrying Amount** | Total outstanding balance |
| **Model ECL** | The simulation-computed Expected Credit Loss |
| **Coverage Ratio** | ECL divided by GCA — the provisioning rate |
| **Loan Count** | Number of loans in this product |

![Model Execution results](/img/screenshots/step-5-results.png)
*ECL results by product showing coverage ratios after simulation.*

**ECL by Scenario**

Each macroeconomic scenario shows its individual ECL contribution:

- **Scenario Name** — the economic outlook it represents (e.g., "Base Case", "Moderate Adverse")
- **Scenario ECL** — what the total ECL would be under this scenario alone
- **Weight** — the probability assigned to this scenario
- **Weighted Contribution** — the scenario's share of the final probability-weighted ECL

**ECL by Stage**

The stage breakdown shows how ECL distributes across impairment stages:

- **Stage 1** — 12-month ECL for performing loans
- **Stage 2** — Lifetime ECL for loans with significant increase in credit risk
- **Stage 3** — Lifetime ECL for credit-impaired loans

### 6. Compare Against Pre-Computed Values

A side-by-side comparison table lets you see how the new simulation results differ from the pre-computed baseline. Look for:

- **Direction of change** — is total ECL higher or lower than the prior period?
- **Product-level shifts** — which products drove the change?
- **Stage migration** — did loans move between stages in a way that explains the ECL movement?

Large, unexplained differences warrant investigation before proceeding. The comparison helps you build a narrative for the ECL movement that will be needed at sign-off.

### 7. Advance to Stress Testing

When you are satisfied with the simulation results, the project automatically progresses. The simulation parameters and results are recorded in the audit trail.

## Understanding the Results

The Monte Carlo simulation works by generating many possible loss outcomes and averaging them. Think of it like this: instead of asking "what will our credit losses be?", the model asks "what could our credit losses be under thousands of different conditions?" and then weights the answers by how likely each condition is.

**Convergence** means that adding more simulations no longer meaningfully changes the average result. The platform tracks convergence by product — if a product's ECL is still shifting significantly as simulations are added, the convergence indicator flags it.

**Coverage ratio** (ECL / GCA) is a key metric for management and regulators. A coverage ratio of 2% means the institution is provisioning 2 cents for every dollar of outstanding exposure. Higher coverage ratios indicate greater expected losses.

## Tips & Best Practices

:::tip Document Your Parameter Choices
Record why you chose specific simulation parameters — especially the number of simulations, PD-LGD correlation, and scenario weights. Auditors will ask for the rationale behind these choices, and the parameters are recorded in the audit trail for traceability.
:::

:::tip Compare Period-over-Period
Always compare your simulation results against the prior period. The attribution waterfall in Step 8 will decompose the movement, but spotting large shifts here lets you investigate early — before the results are presented for sign-off.
:::

:::caution Do Not Adjust Parameters to Hit a Target
The simulation parameters should reflect the economic reality and your portfolio's risk characteristics, not be tuned to produce a desired ECL number. Parameter manipulation undermines the integrity of the IFRS 9 calculation and will be flagged during audit.
:::

:::warning Convergence Matters for Regulatory Submissions
If you are producing results for regulatory submission, verify that convergence is achieved for every product. A non-converged simulation means the result is unstable and could change materially with a different random seed. Increase the simulation count until convergence is confirmed.
:::

## What's Next?

Proceed to [Step 6: Stress Testing](step-6-stress-testing) to analyze how ECL responds to different conditions through sensitivity, vintage, concentration, and migration analysis.
