---
sidebar_position: 3
title: Model Registry & Analytics
---

# Model Registry, Backtesting, Markov Chains & Hazard Models

The platform provides a comprehensive suite of analytical models for credit risk estimation, validation, and forecasting — all integrated into the IFRS 9 ECL workflow.

## Overview

Four interconnected model systems support ECL calculation:

1. **Model Registry** — Lifecycle management and governance for all model types
2. **Backtesting** — Validation of model predictions against actuals
3. **Markov Chains** — Rating migration and lifetime PD estimation
4. **Hazard Models** — Survival analysis for time-to-default modeling

![Model Registry](/img/guides/model-registry.png)
*Model Registry showing lifecycle status and version history*

## Model Registry

### Model Lifecycle

Every model follows a strict governance lifecycle:

```
Draft → Validated → Champion → Retired
```

**Valid transitions**:
| From | To | Description |
|------|----|-------------|
| Draft | Validated | Model passes validation criteria |
| Validated | Champion | Model promoted to production use |
| Champion | Retired | Model replaced by new champion |
| Validated | Retired | Model rejected after validation |
| Draft | Retired | Model abandoned during development |

**Invalid transitions** (rejected with 400 error):
- Draft → Champion (must validate first)
- Retired → any state (retired is terminal)
- Champion → Draft (cannot demote)
- Champion → Validated (cannot demote)

### Key Endpoints

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Register model | `/api/models` | POST |
| List models | `/api/models` | GET |
| Get model details | `/api/models/{id}` | GET |
| Update status | `/api/models/{id}/status` | PUT |
| Promote to champion | `/api/models/{id}/promote` | POST |
| Compare models | `/api/models/compare` | POST |
| Audit trail | `/api/models/{id}/audit` | GET |

### Model Comparison

Compare up to 3 models side-by-side on performance metrics, parameters, and validation results.

## Backtesting

Backtesting validates model predictions against realized outcomes using industry-standard metrics.

![Backtesting Results](/img/guides/backtesting-results.png)
*Backtesting dashboard with traffic light classification and metric trends*

### Metrics

| Metric | Description | Traffic Light Thresholds |
|--------|-------------|------------------------|
| **AUC** | Area Under ROC Curve | Green ≥ 0.7, Amber ≥ 0.6, Red < 0.6 |
| **Gini** | Gini coefficient (2×AUC - 1) | Green ≥ 0.4, Amber ≥ 0.2, Red < 0.2 |
| **KS** | Kolmogorov-Smirnov statistic | Green ≥ 0.3, Amber ≥ 0.15, Red < 0.15 |
| **PSI** | Population Stability Index | Green < 0.1, Amber < 0.25, Red ≥ 0.25 |
| **Brier** | Brier score (lower is better) | Green < 0.1, Amber < 0.2, Red ≥ 0.2 |
| **H-L** | Hosmer-Lemeshow goodness-of-fit | Green p > 0.05, Amber p > 0.01, Red p ≤ 0.01 |

Traffic light classification follows Basel Committee guidelines for model validation.

### Running a Backtest

```bash
POST /api/backtest/run
```

```json
{
  "model_id": "model-001",
  "model_type": "PD",
  "config": {"lookback_months": 12}
}
```

Returns metrics, per-cohort results, and an overall traffic light classification.

### Trend Analysis

**API**: `GET /api/backtest/trend/{model_type}`

Track metric evolution across multiple backtest runs to detect model degradation.

## Markov Chain Models

Markov chains model rating migration — how borrowers transition between credit grades over time.

### Transition Matrix Estimation

**API**: `POST /api/markov/estimate`

```json
{
  "project_id": "proj-001",
  "product": "Corporate Loans",
  "segment": "Investment Grade"
}
```

Returns a transition matrix with these guaranteed properties:
- **Row stochasticity**: Each row sums to 1.0
- **Non-negativity**: All entries ≥ 0
- **Absorbing default state**: The default state has probability 1.0 of staying in default

### Lifetime PD

**API**: `GET /api/markov/lifetime-pd/{matrix_id}?months=60`

Computes the cumulative probability of default over a given horizon using matrix exponentiation.

Properties:
- **Monotonically non-decreasing** — Lifetime PD can only increase over time
- **Starts at zero** at t=0 (no default has occurred yet)
- **Approaches 1.0** as the horizon extends (absorbing state)

### Forecasting

**API**: `POST /api/markov/forecast`

Projects the portfolio rating distribution forward using the estimated transition matrix:

```json
{
  "matrix_id": "mx-001",
  "horizon": 12,
  "initial_distribution": [0.6, 0.25, 0.1, 0.05]
}
```

The forecasted distribution sums to 100% at every time step.

## Hazard Models

Hazard models estimate time-to-default using survival analysis techniques.

### Model Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Cox PH** | Cox Proportional Hazards | Covariate-adjusted default risk |
| **Discrete-Time** | Discrete-time hazard model | Period-by-period default probability |
| **Kaplan-Meier** | Non-parametric survival estimator | Baseline survival without covariates |

### Survival Curves

**API**: `POST /api/hazard/survival-curve`

```json
{
  "model_id": "hz-001",
  "covariates": {"leverage": 0.6, "interest_coverage": 3.5}
}
```

Properties:
- **Monotonically non-increasing** — Survival probability can only decrease
- **Starts at 1.0** (all borrowers alive at t=0)
- **Risk multiplier** — Higher-risk covariates accelerate the decline

### Term Structure

**API**: `GET /api/hazard/term-structure/{model_id}?months=60`

Derives a cumulative PD term structure from the hazard model:
- Cumulative PD is **monotonically non-decreasing**
- 12-month PD is bounded in [0, 1]
- Longer horizons always have higher or equal cumulative PD

### Model Comparison

**API**: `POST /api/hazard/compare`

Compare up to 3 hazard models, including their survival curves and coefficient estimates.

## Test Coverage

Sprint 3 of the QA audit added **178 tests** across all four model systems:
- Full model governance lifecycle (5 valid + 15 invalid transitions tested parametrically)
- Markov mathematical properties: row stochasticity, non-negativity, absorbing states
- Hazard survival curve monotonicity and risk multiplier behavior
- Backtesting traffic light classification with known metric values
- Multi-model comparison for all model types
