---
sidebar_position: 11
title: Backtesting
---

# Backtesting

Validate PD and LGD model performance using traffic-light assessment against historical outcomes.

## Purpose

Backtesting compares model predictions against realised outcomes to assess whether models remain well-calibrated. Results are classified using a **Green/Amber/Red** traffic-light system aligned with regulatory expectations.

## Running a Backtest

1. Select the **Model Type** (PD or LGD) from the dropdown.
2. Click **Run Backtest**.
3. Results appear once the backtest completes.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| Latest Result | Traffic light colour (Green/Amber/Red) |
| Total Runs | Number of backtests performed |
| Pass Rate | Breakdown of green/amber/red results |
| Latest Loans | Number of loans in the latest backtest |

## Discrimination Metrics Trend

A line chart tracking key metrics over time with reference lines for Green and Amber thresholds:

- **AUC** — Area Under the ROC Curve
- **Gini** — Gini coefficient (2 × AUC − 1)
- **KS** — Kolmogorov-Smirnov statistic

## Stability & Calibration Trend

A line chart for stability and calibration metrics:

- **PSI** — Population Stability Index (lower is better)
- **Brier Score** — Calibration accuracy (lower is better)

## Latest Backtest Metrics

A grid of metric cards showing each metric's value, threshold, and traffic-light status.

## Backtest History

A table of all past backtests with Status, Model, Date, Loan count, Pass/Amber/Fail counts, and observation/outcome windows. Click any row to see the full detail.

## Backtest Detail

The detail panel includes:

- Traffic-light badge, date, and loan count
- Observation and outcome window tiles
- All metric cards with traffic-light indicators
- **Predicted vs Actual by Cohort** — Grouped bar chart comparing predictions against outcomes
- **Calibration Plot** — Scatter chart with a 45-degree perfect-calibration reference line
- **Cohort Analysis Table** — Cohort, Predicted%, Actual%, Difference (colour-coded), and Count
