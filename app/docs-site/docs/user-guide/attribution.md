---
sidebar_position: 15
title: "ECL Attribution"
description: "ECL waterfall analysis — understanding what drives changes in provisions between reporting periods."
---

# ECL Attribution

ECL Attribution answers the question every Chief Risk Officer asks at the end of each reporting period: **"Why did our ECL provision change?"** The platform decomposes the movement in Expected Credit Loss between two periods into its individual drivers — new loans originated, old loans derecognised, borrowers moving between impairment stages, changes in model parameters, shifts in macroeconomic scenarios, management overlays, write-offs, and more. This waterfall analysis is not just a management tool; IFRS 7.35I specifically requires institutions to disclose a reconciliation of the loss allowance from opening to closing balance.

:::info Prerequisites
- At least one completed ECL project with results (see [Step 5: Model Execution](step-5-model-execution))
- For meaningful attribution, at least two reporting periods are needed (the platform estimates an opening balance for first-time runs)
- **Risk Manager** or **Analyst** role to view attribution; **Risk Manager** to trigger computation
:::

## What You'll Do

On this page you will run an ECL attribution analysis, interpret the waterfall chart that shows how ECL moved from opening to closing balance, review the stage-level breakdown table, check the reconciliation status, and compare attribution results across reporting periods.

## The Twelve Waterfall Components

The platform breaks down the ECL movement into twelve components. Each component represents a distinct driver of change:

| Component | What It Captures | Direction |
|---|---|---|
| **Opening ECL** | The ECL balance at the start of the period (prior period's closing) | Anchor |
| **New Originations** | ECL on loans that entered the portfolio during the period | Increase |
| **Derecognitions** | Release of ECL on loans that left the portfolio (repaid, sold, matured) | Decrease |
| **Stage Transfers** | ECL impact when loans move between Stage 1, 2, and 3 — the largest driver in most portfolios | Increase or Decrease |
| **Model Parameter Changes** | Impact of updated PD, LGD, or EAD parameters from recalibrated models | Increase or Decrease |
| **Macro Scenario Changes** | Impact of updated macroeconomic forecasts or changed scenario probability weights | Increase or Decrease |
| **Management Overlays** | Post-model adjustments applied in [Step 7](step-7-overlays) | Increase or Decrease |
| **Write-offs** | Loans removed from the portfolio as irrecoverable | Decrease |
| **Unwind of Discount** | The passage of time increases the present value of future expected losses | Increase |
| **FX Changes** | Currency translation effects for multi-currency portfolios | Increase or Decrease |
| **Residual** | Any unexplained difference — should be immaterial if the analysis is complete | Increase or Decrease |
| **Closing ECL** | The ECL balance at the end of the period | Anchor |

:::tip The Residual Should Be Small
The platform checks that the residual is less than 1% of total ECL movement. If the residual exceeds this threshold, the reconciliation is flagged as incomplete, and you should investigate the data gaps listed in the reconciliation panel.
:::

## Step-by-Step Instructions

### 1. Navigate to ECL Attribution

From the main navigation, select **ECL Attribution**. If an attribution has already been computed for the current project, the results load automatically.

### 2. Run the Attribution Analysis

If no results exist for the current project, or if you want to refresh the analysis after updating inputs:

1. Click **Compute Attribution**
2. The platform retrieves the current ECL results and the prior period's closing balance
3. Each of the twelve waterfall components is calculated
4. The reconciliation check runs automatically
5. Results appear within seconds

### 3. Check the Reconciliation Status

At the top of the page, a **Reconciliation Card** shows whether the attribution balances:

| Metric | What It Means |
|---|---|
| **Total Movement** | The absolute change in ECL from opening to closing |
| **Absolute Residual** | The portion of movement not explained by the eleven known drivers |
| **Residual Percentage** | Residual as a percentage of total movement — should be below 1% |
| **Status** | Pass (green badge) if within threshold; Fail (red badge) if residual exceeds 1% |

If the status shows **Fail**, the reconciliation card lists the **Data Gaps** — specific components where data was insufficient or estimated. Common data gaps include:

- Missing prior-period closing balance (estimated as equal to current closing for first-time runs)
- Insufficient default history for write-off estimation
- Macro scenario changes could not be isolated from model parameter changes

:::warning Investigate Failures
A failed reconciliation does not mean the ECL figures are wrong — it means the attribution analysis could not fully explain the movement. Review the data gaps and determine whether additional data can be sourced. For IFRS 7 disclosure purposes, the unexplained portion should be disclosed as "Other movements."
:::

### 4. Read the Waterfall Chart

The waterfall chart is the centrepiece of the attribution page. It visualises the flow from opening ECL to closing ECL:

- **Anchor bars** (indigo) mark the opening and closing ECL — these are the fixed endpoints
- **Increase bars** (green) show components that increased ECL — they extend upward from the running total
- **Decrease bars** (red) show components that decreased ECL — they extend downward
- **Change bars** (amber) show components that could go either way depending on the period

Hover over any bar to see the exact amount and the cumulative total at that point.

![ECL Attribution waterfall chart](/img/screenshots/attribution-waterfall.png)
*The waterfall chart showing the flow from opening to closing ECL, with stage transfers as the largest driver.*

### 5. Review the Stage-Level Breakdown

Below the waterfall chart, a **Breakdown Table** shows every component split by impairment stage:

| Component | Stage 1 | Stage 2 | Stage 3 | Total | Status |
|---|---|---|---|---|---|
| Opening ECL | 12.5M | 34.2M | 18.7M | 65.4M | Computed |
| New Originations | 1.2M | 0.3M | — | 1.5M | Computed |
| Stage Transfers | -3.1M | 5.8M | 2.4M | 5.1M | Computed |
| ... | ... | ... | ... | ... | ... |

Each row shows a **Status** badge:

- **Computed** — calculated from actual data
- **Estimated** — derived using an approximation (e.g., opening balance for a first-time run)
- **Unavailable** — insufficient data; treated as zero in the waterfall

The stage-level view is particularly useful for understanding stage transfer impacts. In the example above, Stage 1 ECL decreased by 3.1M due to loans transferring out, while Stage 2 absorbed 5.8M and Stage 3 absorbed 2.4M — indicating a net deterioration in portfolio credit quality.

![ECL Attribution stage breakdown](/img/screenshots/attribution-breakdown.png)
*The stage-level breakdown table showing component values across all three impairment stages.*

### 6. Compare Across Reporting Periods

If multiple attribution runs exist, a **History Selector** dropdown appears at the top of the page. Each entry shows:

- The run timestamp
- The total ECL at that point
- Whether the reconciliation passed

Select different periods to compare how the drivers have shifted. For example, if stage transfers were the dominant driver last quarter but macro scenario changes dominate this quarter, it signals a shift from idiosyncratic credit deterioration to a macro-driven increase.

## Understanding Key Drivers

### Stage Transfers — Usually the Largest Driver

When a loan moves from Stage 1 (12-month ECL) to Stage 2 (lifetime ECL), the ECL increases significantly — often by a factor of 3-5x — because the measurement horizon extends from 12 months to the full remaining life. This makes stage transfers the single largest driver of ECL movement in most portfolios.

The platform calculates the stage transfer impact as: the number of loans that migrated multiplied by the difference in average ECL between the destination and origin stages.

### Unwind of Discount

ECL is measured as a present value. As time passes, the discount unwinds — future expected losses become closer in time and therefore higher in present value. The platform approximates this as: Opening ECL × (average effective interest rate ÷ 4) per quarter.

### Macro Scenario Changes

When macroeconomic forecasts are updated (e.g., GDP growth revised downward), the probability-weighted ECL shifts. The platform isolates this by measuring the change in baseline scenario weight relative to the default assumption.

## Tips & Best Practices

:::tip Run Attribution Quarterly
For most institutions, quarterly attribution analysis aligns with IFRS 7 disclosure requirements. Running it monthly provides earlier visibility into portfolio trends but is not required.
:::

:::tip Focus on the Top Three Drivers
In any given period, two or three components typically explain 80-90% of the movement. Identify these first, understand them thoroughly, and document the explanation for senior management and auditors.
:::

:::warning First-Period Limitations
The first time you run attribution for a portfolio, the opening balance is estimated (set equal to the closing balance). This means the waterfall will show zero total movement, with all components reflecting within-period dynamics only. Meaningful period-over-period analysis begins from the second reporting period onward.
:::

:::caution Residual and Disclosure
For IFRS 7 disclosure, any residual amount should be disclosed under "Other movements" with an explanatory note. Regulators expect the residual to be immaterial — typically less than 1% of total movement. Persistent large residuals may trigger supervisory questions.
:::

## What's Next?

- [Regulatory Reports](regulatory-reports) — the IFRS 7 disclosure report uses attribution data for the loss allowance reconciliation table
- [GL Journals](gl-journals) — journal entries reflect the same ECL movements decomposed here
- [Step 6: Stress Testing](step-6-stress-testing) — stress testing results help explain the macro scenario component
- [Step 7: Overlays](step-7-overlays) — overlay impacts appear as a separate waterfall component
