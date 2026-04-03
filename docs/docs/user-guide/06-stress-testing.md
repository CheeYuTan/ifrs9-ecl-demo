---
sidebar_position: 7
title: "Step 6: Stress Testing"
---

# Step 6: Stress Testing

Analyse ECL sensitivity, concentration risk, vintage performance, stage migration, and capital impact under stressed conditions.

## What This Step Does

Stress testing goes beyond the base ECL calculation to examine how the portfolio behaves under adverse conditions. This step provides six analysis tabs covering different dimensions of risk.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| Baseline ECL | ECL under the probability-weighted base case |
| Severe Stress ECL | ECL under the severely adverse scenario |
| ECL Uplift | Percentage increase from baseline to severe stress |
| Stage 3 Rate | Percentage of portfolio that is credit-impaired |

## Analysis Tabs

### Monte Carlo

Visualises the full distribution of ECL outcomes from the Monte Carlo simulation:

- **ECL Distribution Histogram** — Shows the spread of simulated ECL values
- **VaR / CVaR Statistics** — Value at Risk and Conditional VaR at key percentiles
- **Percentile Analysis** — P50, P75, P90, P95, P99 ECL values

### Sensitivity

Test how ECL responds to shocks in key risk parameters:

- **PD Shock Slider** — Increase/decrease portfolio PD
- **LGD Shock Slider** — Increase/decrease Loss Given Default
- **EAD Shock Slider** — Increase/decrease Exposure at Default
- **Tornado Chart** (quick mode) — Shows relative impact of each parameter
- **Full Simulation Mode** — Runs a stressed Monte Carlo simulation and compares to baseline

### Vintage

Analyse historical default rate performance by loan origination cohort:

- **Vintage Performance Chart** — Default rates over time grouped by origination quarter
- Helps identify whether newer vintages are performing better or worse than historical norms

### Concentration

Evaluate portfolio concentration risk:

- **Concentration by Product × Stage** — Heatmap of exposure distribution
- **Herfindahl-Hirschman Index (HHI)** — Quantitative measure of concentration
- **Top Concentrations** — Largest single-name and product exposures

### Migration

Simulate the impact of stage migration on ECL:

- **S1 → S2 Migration % Slider** — Adjust the percentage of Stage 1 loans that migrate to Stage 2
- **Real-Time ECL Bar Chart** — Shows base vs. adjusted ECL by stage as you move the slider
- Useful for "what-if" analysis of credit deterioration

### Capital Impact

Calculate regulatory capital implications under stressed scenarios:

- Capital requirements under stress
- Capital buffer adequacy assessment

## Approving This Step

1. Review each analysis tab relevant to your portfolio.
2. Pay particular attention to the sensitivity and concentration analyses.
3. Document any findings or concerns in the approval comments.
4. Click **Approve** or **Reject**.
