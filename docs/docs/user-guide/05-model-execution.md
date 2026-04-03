---
sidebar_position: 6
title: "Step 5: Model Execution"
---

# Step 5: Model Execution

Run the ECL calculation engine with probability-weighted macroeconomic scenarios and optional Monte Carlo simulation.

**IFRS 9 Reference:** 5.5.17 — time value of money, reasonable and supportable forward-looking information.

## What This Step Does

This is the core computation step. The ECL engine applies the calibrated satellite models across all 8 macroeconomic scenarios, computes per-loan expected credit losses using a Monte Carlo simulation, and aggregates results by product, stage, and scenario.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| Total ECL | Probability-weighted expected credit loss |
| Coverage | ECL as a percentage of GCA |
| Scenarios | Number of macro scenarios |
| Products | Number of product types |

## Simulation Configuration

Expand the **Simulation Configuration** panel to customise Monte Carlo parameters:

### Monte Carlo Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| N Simulations | 1,000 | 100–5,000 | Number of Monte Carlo paths |
| PD-LGD Correlation (ρ) | 0.30 | 0–1 | Models procyclical LGD behaviour |
| Aging Factor | 0.08 | 0–0.20 | Quarterly PD increase for Stage 2/3 |
| PD Floor | 0.001 | — | Minimum stressed PD |
| PD Cap | 0.95 | — | Maximum stressed PD |
| LGD Floor | 0.01 | — | Minimum stressed LGD |
| LGD Cap | 0.95 | — | Maximum stressed LGD |

### Scenario Weights

Adjust probability weights for each of the 8 scenarios. Weights must sum to 100%. Use **Equalize** to distribute weights evenly or **Reset to Default** to restore the configured weights.

## Running the Simulation

Two execution modes are available:

### Run In-App

Click **Run In-App** for immediate streaming results. The UI shows:

- Real-time ECL counter updating as scenarios complete
- Scenario-by-scenario checklist with progress indicators
- Phase/message status (loading → computing → aggregating)
- Progress bar and elapsed time
- Cancel button to abort mid-run

Results appear immediately. Click **Apply Results** to use the simulation output or **Discard** to revert to pre-computed results.

### Run as Databricks Job

Click **Run as Databricks Job** to submit the simulation to a Databricks compute cluster. This is recommended for larger simulations (> 2,000 paths). The UI shows the job status and provides a link to the Databricks workspace.

## Pre-Computed Results

Even without running a custom simulation, the page displays pre-computed ECL results from the pipeline:

### ECL by Product

A table showing Product, GCA, Model ECL, Coverage%, and Loans.

### Scenario Summary

Bar charts showing ECL and weighted ECL contribution for each of the 8 scenarios.

### Loss Allowance by Stage

Bar chart and table breaking down the loss allowance across Stage 1, Stage 2, and Stage 3.

### Model Assumptions & Methodology

Expandable section showing scenario definitions with macro variables (GDP, unemployment), weights, and ECL contributions per scenario displayed as coloured tiles.

### Multi-Level Drill-Downs

- **ECL by Scenario × Product** — Grouped bar charts cross-tabulating scenarios and products
- **ECL Drill-Down** — Product-level with cohort sub-drill
- **GCA Drill-Down** — Product-level with cohort sub-drill
- **Stage → Product → Cohort** — Three-level drill-down

## Simulation vs Pre-Computed Comparison

When simulation results are active, a comparison table shows the delta between simulation output and pre-computed ECL for each product, along with a grouped bar chart.

Click **Revert to Pre-computed** to restore the original results.

## Approving This Step

1. Review the ECL results across products and scenarios.
2. If running a custom simulation, verify the parameters are reasonable.
3. Add comments about methodology choices.
4. Click **Approve** or **Reject**.
