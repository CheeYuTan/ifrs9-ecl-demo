---
sidebar_position: 7
title: "Step 6: Stress Testing"
description: "Sensitivity, vintage, concentration, and migration analysis for ECL robustness."
---

# Step 6: Stress Testing

Stress Testing lets you probe the robustness of your ECL results. After the Monte Carlo simulation in Step 5 produced your base ECL figure, this step asks: "How would the ECL change if conditions were different?" The platform provides five analysis dimensions — Monte Carlo Distribution, Sensitivity Analysis, Vintage Analysis, Concentration Analysis, and Stage Migration — each revealing different aspects of portfolio risk.

:::info Prerequisites
- Completed [Step 5: Model Execution](step-5-model-execution)
- Simulation results available for the current project
:::

## What You'll Do

On this page you will explore five analysis tabs, each providing a different lens on your ECL results. You can assess how sensitive ECL is to parameter changes, identify risky origination cohorts, spot concentration risks, examine the statistical distribution of outcomes, and model the impact of stage migrations.

## Step-by-Step Instructions

### 1. Monte Carlo Distribution Tab

This tab shows the full range of outcomes from your Monte Carlo simulation — not just the average, but the entire distribution of possible credit losses.

**Key metrics displayed for each scenario:**

| Metric | What It Means |
|--------|--------------|
| **Mean ECL** | The average expected loss across all simulations — this is your base ECL figure |
| **P50 (Median)** | The midpoint — half of simulations produced losses above this, half below |
| **P75** | 75th percentile — only 25% of simulations produced losses higher than this |
| **P95** | 95th percentile — a near-worst-case outcome. Often used for stress testing capital adequacy |
| **P99** | 99th percentile — an extreme tail scenario. Useful for understanding maximum potential exposure |

The distribution view helps answer: "What is our ECL in a reasonable worst case?" If the gap between the Mean and P95 is large, the portfolio has high uncertainty — a signal to investigate which products or cohorts drive the tail risk.

**Drill-down**: Click any scenario to see the distribution broken down by product type, and then by origination cohort within each product. This reveals which segments contribute the most to tail risk.

:::tip Use P95 for Capital Planning
Regulators often expect institutions to hold capital against adverse scenarios. The P95 metric provides a defensible "stress ECL" figure — the loss you would expect to exceed only 5% of the time.
:::

### 2. Sensitivity Analysis Tab

Sensitivity Analysis shows how ECL changes when you adjust the three key risk parameters: Probability of Default (PD), Loss Given Default (LGD), and Exposure at Default (EAD).

**Using the sensitivity controls:**

1. **Choose a mode** — Quick Mode gives instant results using a mathematical approximation; Full Simulation Mode re-runs the stochastic engine with stressed parameters for more accurate results
2. **Adjust the shock sliders** — each slider lets you increase or decrease a parameter from -50% to +100%
3. **Use preset scenarios** — three built-in presets save time:

| Preset | PD Shock | LGD Shock | EAD Shock | Scenario |
|--------|---------|-----------|-----------|----------|
| **Adverse** | +20% | +10% | +5% | Moderate economic downturn |
| **Severe** | +50% | +25% | +15% | Significant recession |
| **Extreme** | +100% | +50% | +30% | Financial crisis |

**Reading the sensitivity waterfall:**

The waterfall chart decomposes the total ECL change into contributions from each parameter. For example, if you applied the Adverse preset and ECL increased by 100,000:

- The PD component might contribute 60,000 (defaults are more likely)
- The LGD component might contribute 30,000 (recoveries are lower)
- The EAD component might contribute 10,000 (exposures are higher)

This decomposition tells you which parameter your portfolio is most sensitive to — critical information for risk management.

**Drill-down**: Click any product in the results table to see the base versus stressed ECL at the cohort level.

### 3. Vintage Analysis Tab

Vintage Analysis tracks loan performance by origination cohort — revealing whether loans originated in certain periods perform better or worse than others.

**Available views:**

| View | What It Shows |
|------|--------------|
| **Delinquency Curves** | How quickly loans from each vintage become overdue. Choose the delinquency threshold: Any DPD, 30+ DPD, 60+ DPD, or 90+ DPD |
| **Vintage PD Trends** | Average Probability of Default for each origination cohort over time |
| **Cohort Performance Table** | Loan count, GCA, average PD, delinquency rate, and stage distribution for each vintage |

**What to look for:**

- **Rising delinquency curves** for recent vintages may signal deteriorating underwriting standards
- **A single vintage with unusually high Stage 2/3 concentration** may indicate a one-time event (e.g., a product launch with different risk criteria)
- **Converging curves** suggest portfolio credit quality is stabilizing
- **Diverging curves** suggest conditions are worsening for newer originations

:::warning Vintage Deterioration Requires Action
If recent vintages show significantly higher delinquency than older ones, this may indicate a systemic change in borrower quality. Document this finding — it may warrant a management overlay in Step 7 or a discussion with the credit committee.
:::

### 4. Concentration Analysis Tab

Concentration Analysis identifies where ECL risk is clustered in your portfolio — by product, by stage, and by individual exposure.

**ECL Concentration Heatmap:**

A grid showing ECL coverage rates (ECL as a percentage of GCA) across products and stages. Cells are color-coded:
- **Green** — low coverage, low relative risk
- **Amber** — moderate coverage, worth monitoring
- **Red** — high coverage, concentrated risk

This heatmap quickly reveals where the highest ECL density sits. For example, if Stage 3 Credit Cards show a 45% coverage rate while Stage 3 Mortgages show 12%, credit card losses are proportionally much higher — likely due to being unsecured.

**Single-Name Concentration:**

A summary of your largest individual exposures, showing:
- The number of loans that individually exceed a materiality threshold
- The total GCA of concentrated exposures
- Their stage distribution

High single-name concentration is a risk because a single default can materially move your ECL figure. IFRS 9 requires institutions to consider concentration risk in their impairment assessments.

**Drill-down**: Click any cell in the heatmap to see the underlying loans by cohort, with individual exposure details.

### 5. Stage Migration Analysis Tab

Stage Migration simulates what would happen if a portion of your Stage 1 loans migrated to Stage 2 — for example, due to a macroeconomic deterioration that triggers the Significant Increase in Credit Risk (SICR) threshold.

**Using the migration simulator:**

1. **Set the migration percentage** — use the slider to choose how many Stage 1 loans (by GCA) migrate to Stage 2 (range: 0–30%)
2. **Review the impact KPIs** — the platform instantly calculates:

| KPI | What It Shows |
|-----|--------------|
| **Additional ECL** | The increase in total ECL caused by the migration |
| **Migrated Loan Count** | How many loans would move from Stage 1 to Stage 2 |
| **New Total ECL** | The combined ECL after accounting for the migration |
| **ECL Increase %** | The percentage change from the base ECL |

3. **Compare base vs. simulated** — a side-by-side view shows ECL by stage before and after the simulated migration

**Why this matters:** When loans move from Stage 1 to Stage 2, their ECL changes from 12-month to lifetime — often a 3–5x increase in provisioning. Even a small percentage migration can significantly increase total ECL. This analysis helps you understand your portfolio's vulnerability to stage transfers.

**Drill-down**: Click any stage in the comparison to see which products and cohorts would be most affected by the migration.

:::tip Model Multiple Migration Scenarios
Try several migration percentages to build a picture of the ECL sensitivity to stage transfers. For example: 5% (mild deterioration), 10% (moderate), 20% (severe). Present these as scenarios to the credit committee alongside the sensitivity analysis results.
:::

## Understanding the Results

Each stress testing tab answers a different question:

| Tab | Question It Answers |
|-----|-------------------|
| **Monte Carlo Distribution** | "What is the range of possible outcomes, including worst cases?" |
| **Sensitivity** | "Which risk parameter has the biggest impact on our ECL?" |
| **Vintage** | "Are newer loans performing worse than older ones?" |
| **Concentration** | "Where is our ECL risk most concentrated?" |
| **Migration** | "How much would ECL increase if credit conditions deteriorated?" |

Together, these analyses build a comprehensive picture of portfolio risk that goes far beyond the single ECL number from Step 5. They provide the evidence base for management overlays (Step 7) and the supporting analysis for sign-off (Step 8).

## Tips & Best Practices

:::tip Document Key Findings for Sign-Off
As you review each tab, note the key findings — especially any risks, anomalies, or surprises. These findings will be referenced during the sign-off attestation in Step 8 and may need to be disclosed in IFRS 7 reports.
:::

:::tip Run Sensitivity Before Adding Overlays
Understanding which parameters most affect your ECL helps you design more targeted management overlays. If ECL is most sensitive to PD, an overlay that adjusts PD for a specific sector may be more appropriate than a blanket LGD adjustment.
:::

:::caution Stress Testing Is Not Optional
IFRS 9 requires forward-looking information in ECL estimates. Stress testing demonstrates that you have considered multiple economic conditions and understood the portfolio's risk profile. Skipping or superficially reviewing these analyses is a governance gap that auditors will note.
:::

:::warning Stage Migration Sensitivity Is Often Underestimated
The jump from 12-month ECL (Stage 1) to lifetime ECL (Stage 2) is typically the largest single driver of ECL volatility. A migration of just 10% of Stage 1 GCA can increase total ECL by 20% or more, depending on the portfolio's maturity profile. Always present migration sensitivity to the risk committee.
:::

## What's Next?

Proceed to [Step 7: Overlays](step-7-overlays) to apply management adjustments to the model-computed ECL, with documented rationale and governance controls.
