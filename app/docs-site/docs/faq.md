---
sidebar_position: 10
title: FAQ
---

# Frequently Asked Questions

## General

### What IFRS 9 sections does this platform implement?

The platform implements IFRS 9 Section 5.5 (Impairment) with the 3-stage ECL model, and supports IFRS 7 disclosure reporting (paragraphs 35H-35N). It covers PD, LGD, and EAD estimation, forward-looking macroeconomic scenario integration, and stage transfer logic based on Significant Increase in Credit Risk (SICR).

### Can I run multiple ECL projects simultaneously?

Yes. The platform supports multiple concurrent projects, each with its own independent lifecycle, portfolio data, and approval status. Use the project selector in the top navigation to switch between projects.

### What database does the platform use?

The platform uses Lakebase (Databricks managed PostgreSQL) for transactional data. All portfolio data, ECL calculations, model parameters, and audit trails are stored in Lakebase tables.

## Simulation

### How does the Monte Carlo simulation work?

The engine generates correlated PD-LGD draws using Cholesky decomposition of the correlation matrix. Each draw produces a scenario-specific ECL that is then probability-weighted across base, optimistic, and pessimistic macroeconomic scenarios. The final ECL is the weighted average across all scenarios.

### What are the simulation parameter limits?

- **n_sims**: 100 to 50,000 simulations
- **Scenario weights**: Must sum to 1.0 (within a small tolerance)
- **PD/LGD**: Must be in the range [0, 1]
- **EAD**: Must be >= 0

### Can I stream simulation results in real-time?

Yes. The `/api/simulate-stream` endpoint uses Server-Sent Events (SSE) to report progress during long-running simulations. The frontend shows a real-time progress bar.

## Models

### What model types are supported?

- **PD Models**: Probability of Default estimation
- **LGD Models**: Loss Given Default estimation
- **Markov Chains**: Transition matrix-based rating migration
- **Hazard Models**: Cox PH, discrete-time, and Kaplan-Meier survival analysis

### What is the model governance lifecycle?

Models follow a strict lifecycle: **Draft** → **Validated** → **Champion** → **Retired**. Invalid transitions (e.g., Draft directly to Champion) are rejected. Each transition is recorded in the audit trail with the user and timestamp.

### What backtesting metrics are available?

AUC, Gini coefficient, KS statistic, PSI (Population Stability Index), Brier score, and Hosmer-Lemeshow test. Results are classified using Basel traffic light thresholds (Green/Amber/Red).

## Deployment

### How do I deploy to Databricks Apps?

Use the Databricks CLI: `databricks apps deploy ecl-platform --source-code-path .`. The `app.yaml` file configures the Lakebase connection and environment variables automatically.

### What port does the app use?

Locally, the app defaults to port 8000. On Databricks Apps, it reads the `DATABRICKS_APP_PORT` environment variable.

## Troubleshooting

### The setup wizard shows "tables not found"

Run the seed step in the setup wizard to create and populate the required Lakebase tables. Ensure your `LAKEBASE_INSTANCE_NAME` environment variable points to a valid Lakebase instance.

### Simulation fails with "correlation matrix not positive definite"

The correlation matrix between PD and LGD must be symmetric and positive definite. Check that diagonal entries are 1.0 and off-diagonal entries are in (-1, 1).

### Sign-off is rejected with "segregation of duties"

The person signing off cannot be the same user who executed the model in the current project. This is an IFRS 9 governance requirement. Use a different user account for sign-off.

## Testing

### How do I run the backend tests?

```bash
cd app && source .venv/bin/activate && python -m pytest tests/ -q
```

The full suite (3,838 tests) completes in approximately 2-3 minutes.

### How do I run the frontend tests?

```bash
cd frontend && npx vitest run
```

All 497 tests complete in approximately 9 seconds. For verbose output, add `--reporter=verbose`.

### What validation rules does the platform enforce?

The platform has 23 validation rules organized into four categories: Data Quality (D-series, checking PD/LGD/EAD bounds), Domain Accuracy (DA-series, checking ECL consistency and scenario weights), Model Risk (M-R series, checking model governance), and Governance (G-R series, checking approval workflows). See the [Domain Logic guide](./guides/domain-logic-core) for the full rule list.

### How does the ECL attribution waterfall work?

The attribution module decomposes the total ECL change between two reporting periods into: new originations, derecognitions, stage transfers, remeasurements, model changes, and overlays. These components are guaranteed to sum to the total ECL change (IFRS 7.35I compliance). A 5% materiality threshold flags any residual difference.
