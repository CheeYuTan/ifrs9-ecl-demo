---
sidebar_position: 2
title: Monte Carlo Simulation & Satellite Models
---

# Monte Carlo Simulation & Satellite Models

The simulation engine is the computational core of the ECL platform, generating probability-weighted loss estimates using correlated Monte Carlo draws and macroeconomic scenario modeling.

## Overview

The simulation system provides three execution modes (inline, streaming, job-based) and integrates with satellite macroeconomic models for forward-looking ECL estimation per IFRS 9 requirements.

![Monte Carlo Simulation](/img/guides/monte-carlo-panel.png)
*Monte Carlo simulation panel showing configuration and results*

## Monte Carlo Simulation

### How It Works

1. **Input**: PD term structures, LGD estimates, EAD values, correlation matrix, scenario weights
2. **Cholesky Decomposition**: The correlation matrix between PD and LGD is decomposed to generate correlated random draws
3. **Scenario Simulation**: For each macroeconomic scenario, N simulations are drawn
4. **ECL Calculation**: ECL = PD x LGD x EAD x Discount Factor for each draw
5. **Aggregation**: Results are probability-weighted across scenarios using user-defined weights

### Running a Simulation

**Inline (synchronous)**:

```bash
POST /api/simulate
```

```json
{
  "project_id": "proj-001",
  "n_sims": 10000,
  "scenario_weights": {"base": 0.5, "optimistic": 0.2, "pessimistic": 0.3},
  "correlation": {"pd_lgd": 0.3}
}
```

**Streaming (SSE)**:

```bash
POST /api/simulate-stream
```

Returns Server-Sent Events with progress updates:

```
event: progress
data: {"percent": 25, "stage": "generating_draws"}

event: progress
data: {"percent": 75, "stage": "aggregating"}

event: result
data: {"ecl_total": 1234567.89, "by_stage": {...}}
```

**Job-based (Databricks)**:

```bash
POST /api/simulate-job
```

Submits the simulation as a Databricks job for large portfolios.

### Parameter Validation

The `/api/simulate-validate` endpoint pre-checks parameters before execution:

| Parameter | Validation | Range |
|-----------|-----------|-------|
| `n_sims` | Must be positive integer | 100 – 50,000 |
| `scenario_weights` | Must sum to 1.0 (±0.01 tolerance) | Each weight in [0, 1] |
| `correlation.pd_lgd` | Must produce positive-definite matrix | (-1, 1) |

The validate endpoint also returns estimated runtime and memory usage that scale with `n_sims`.

### Comparing Simulation Runs

**API**: `GET /api/simulation/compare?run_a={id}&run_b={id}`

Returns per-metric deltas with improved/degraded classification:

```json
{
  "metrics": [
    {"name": "ecl_total", "run_a": 1200000, "run_b": 1150000, "delta": -50000, "status": "improved"},
    {"name": "coverage_ratio", "run_a": 0.025, "run_b": 0.023, "delta": -0.002, "status": "improved"}
  ],
  "improved_count": 2,
  "degraded_count": 0
}
```

![Simulation Results](/img/guides/simulation-results.png)
*Simulation results showing ECL distribution and scenario breakdown*

## Satellite Models

Satellite models link macroeconomic variables (GDP growth, unemployment, interest rates) to credit risk parameters, providing the forward-looking component required by IFRS 9.

### Model Comparison

**API**: `GET /api/data/satellite-model-comparison`

Compare multiple satellite models side-by-side to select the best-performing model for each scenario.

### Model Selection

**API**: `GET /api/data/satellite-model-selected`

Returns the currently selected model for the active project.

### Model Runs

Full CRUD for model execution records:

| Operation | Endpoint | Method |
|-----------|----------|--------|
| List runs | `/api/model-runs` | GET |
| Get run | `/api/model-runs/{run_id}` | GET |
| Create run | `/api/model-runs` | POST |

Runs can be filtered by `run_type` and include metadata like execution timestamps and configuration parameters.

### Cohort Analysis

Deep drill-down analytics by portfolio cohort:

| Endpoint | Dimension |
|----------|-----------|
| `/api/data/cohort-summary` | Overall summary |
| `/api/data/cohort-summary/{product}` | By product type |
| `/api/data/ecl-by-cohort` | ECL by risk band (default) |
| `/api/data/stage-by-cohort` | Stage distribution by cohort |
| `/api/data/portfolio-by-cohort` | Exposure by cohort |
| `/api/data/ecl-by-product-drilldown` | Product-level drill-down |
| `/api/data/drill-down-dimensions` | Available dimension list |

Cohort dimensions include: `risk_band`, `vintage_year`, `credit_grade`, `product_type`.

## Configuration

### Simulation Defaults

**API**: `GET /api/simulation-defaults`

Returns system defaults for simulation parameters:

```json
{
  "n_sims": 10000,
  "confidence_level": 0.99,
  "correlation_pd_lgd": 0.3,
  "scenarios": ["base", "optimistic", "pessimistic"]
}
```

All numeric parameters are typed as numbers. The scenarios field is always a list.

## Test Coverage

Sprint 2 of the QA audit added **150 tests** covering all 18 endpoints:
- Simulation parameter boundary testing (exact limits at 50,000/50,001)
- Scenario weight tolerance (0.999 vs 1.001 vs 0.5)
- SSE streaming response format and event sequence
- Simulation comparison with known deltas
- Cohort drill-down across all dimension types
- Internal helper functions: config validation, result transformation, pre-checks
