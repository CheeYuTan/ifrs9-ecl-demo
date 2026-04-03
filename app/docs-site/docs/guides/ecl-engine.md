---
sidebar_position: 5
title: ECL Engine Deep Dive
---

# ECL Engine — Monte Carlo Simulation Core

The ECL engine is the mathematical heart of the platform, implementing the IFRS 9 forward-looking Expected Credit Loss calculation using correlated Monte Carlo simulation with Cholesky decomposition.

## Overview

The engine comprises 9 modules in the `ecl/` package that work together to produce probability-weighted ECL estimates:

| Module | Purpose |
|--------|---------|
| `simulation.py` | Orchestrates the full simulation pipeline |
| `monte_carlo.py` | Core math: Cholesky-correlated PD-LGD draws, ECL calculation |
| `aggregation.py` | Result aggregation, percentiles, convergence diagnostics |
| `data_loader.py` | Loan and scenario data loading from Lakebase |
| `config.py` | Schema and prefix configuration |
| `constants.py` | Base LGD values, satellite coefficients, default weights |
| `defaults.py` | Default parameter generation |
| `helpers.py` | Convergence checking, event emission, data conversion |

![Monte Carlo Workflow](/img/guides/monte-carlo-workflow.png)
*Monte Carlo simulation page showing configuration parameters and execution controls*

## The ECL Formula

The fundamental calculation follows IFRS 9.5.5.17:

```
ECL = PD × LGD × EAD × DF
```

Where:
- **PD** (Probability of Default) — likelihood of borrower default in the relevant horizon
- **LGD** (Loss Given Default) — fraction of exposure lost if default occurs
- **EAD** (Exposure at Default) — outstanding exposure at time of default
- **DF** (Discount Factor) — present value adjustment: `DF = 1 / (1 + EIR)^t`

For probability-weighted ECL across macroeconomic scenarios:

```
ECL_weighted = Σ(w_i × ECL_i)  where Σw_i = 1.0
```

### Hand-Calculated Verification

The engine's correctness is verified against hand-calculated values with 1e-6 relative tolerance:

**Single-quarter example**:
- PD_q = 0.02, LGD = 0.45, GCA = 1,000,000, EIR = 0.05
- DF = 1 / (1.05)^0.25 = 0.9879
- ECL = 0.02 × 0.45 × 1,000,000 × 0.9879 = **8,891.06**

## Cholesky-Correlated Draws

PD and LGD are not independent in real credit portfolios — they tend to increase together during economic downturns. The engine captures this correlation using Cholesky decomposition.

### How It Works

1. **Correlation matrix** — Define the PD-LGD correlation (typically 0.2–0.5)
2. **Cholesky decomposition** — Factor the correlation matrix: `C = L × L^T`
3. **Generate independent draws** — Sample from standard normal distribution
4. **Apply correlation** — Multiply by L to produce correlated draws
5. **Transform** — Map to lognormal shocks, apply to base PD and LGD

### Properties Verified

| Property | Validation |
|----------|-----------|
| **ρ = 0** | Draws are independent (correlation within statistical tolerance) |
| **ρ = 0.5** | Empirical correlation matches ±0.02 for 100K samples |
| **ρ = -0.4** | Negative correlation correctly applied |
| **ρ = 0.99** | Near-perfect correlation without numerical instability |
| **Determinism** | Same seed produces identical results |

## Stage-Aware Calculation

IFRS 9 requires different ECL horizons depending on the credit stage:

| Stage | Horizon | ECL Type | Description |
|-------|---------|----------|-------------|
| **Stage 1** | 4 quarters (12 months) | 12-month ECL | Performing, no significant credit deterioration |
| **Stage 2** | Full remaining life | Lifetime ECL | Performing, but significant increase in credit risk |
| **Stage 3** | Full remaining life | Lifetime ECL | Credit-impaired (defaulted) |

### Stage Transfer Logic (SICR)

The engine implements Significant Increase in Credit Risk detection:
- **Stage 1 → 2**: PD exceeds SICR threshold relative to origination PD
- **Stage 2 → 3**: Borrower triggers default event
- **Stage 3 → 2 → 1**: Curing — borrower returns to performing status

### Key Behaviors

- **Stage 1** horizon capped at 4 quarters — ECL never exceeds 12-month loss
- **Stage 2/3** use full remaining life — ECL reflects lifetime expected loss
- **Aging factor** only applies to Stage 2/3 (no effect on Stage 1)
- **Stage 3 ECL > Stage 2 ECL > Stage 1 ECL** for the same loan (monotonic ordering)

## Parameter Controls

### PD and LGD Bounds

The engine clips all PD and LGD values to configurable floor/cap bounds:

| Parameter | Floor | Cap |
|-----------|-------|-----|
| PD | Configurable (default: 0.0001) | 1.0 |
| LGD | Configurable (default: 0.01) | 1.0 |

Clipping prevents extreme simulation draws from producing unrealistic results.

### Amortizing EAD

For amortizing exposures, EAD decreases over time based on prepayment assumptions:

```
EAD_t = EAD_0 × (1 - prepayment_rate)^t
```

The engine correctly reduces exposure across simulation periods.

### Scenario Weighting

Macroeconomic scenarios are weighted according to their assessed probability:

```json
{
  "base": 0.50,
  "optimistic": 0.20,
  "pessimistic": 0.30
}
```

**Validation rules**:
- Each weight must be in [0, 1]
- Weights must sum to 1.0 (with floating-point tolerance)
- Missing scenarios receive default weights from `constants.py`

## Convergence Diagnostics

The engine monitors simulation convergence using the coefficient of variation (CV):

```
CV = σ(ECL) / μ(ECL)
```

As `n_sims` increases, CV should decrease — indicating the Monte Carlo estimate is stabilizing. The convergence check verifies that increasing simulation count produces monotonically improving convergence.

![ECL Homepage](/img/guides/ecl-homepage.png)
*Platform homepage showing ECL summary metrics and portfolio overview*

## Aggregation

The aggregation module produces:

| Output | Description |
|--------|-------------|
| **Total ECL** | Probability-weighted ECL across all loans and scenarios |
| **Coverage ratio** | ECL / Total exposure (provision rate) |
| **Percentiles** | P5, P25, P50, P75, P95 of simulated ECL distribution |
| **By-stage breakdown** | ECL separated by impairment stage |
| **Cross-product** | ECL by product type × stage combination |
| **Convergence diagnostics** | CV and stability metrics |

All aggregation outputs are JSON-serializable (no NumPy types leak to API responses).

## Numerical Stability

The engine is tested for stability under extreme conditions:

| Scenario | Expected Behavior |
|----------|------------------|
| Very small PD (1e-6) | ECL ≈ 0, no NaN or overflow |
| Very large EAD (1e12) | Correct ECL proportional to exposure |
| Zero EIR | Discount factor = 1.0 (no discounting) |
| High volatility | Results bounded, no negative ECL |
| Correlation near 1.0 | Cholesky decomposition remains stable |
| Single loan portfolio | Correct ECL without division errors |
| 100-loan portfolio | Consistent per-loan and total ECL |

## Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `LAKEBASE_INSTANCE_NAME` | Lakebase instance for data loading | Required |
| `LAKEBASE_DATABASE` | Database name | `databricks_postgres` |

### Default Parameters

The `constants.py` module defines sensible defaults:

- **Base LGD values** per product type
- **Satellite model coefficients** for scenario adjustment
- **Default scenario weights** (base: 0.50, optimistic: 0.25, pessimistic: 0.25)

## Test Coverage

Sprint 5 of the QA audit added **141 tests** covering all 9 ECL engine modules:
- ECL formula verified with hand-calculated values (1e-6 relative tolerance)
- Cholesky correlation verified with 100K sample statistical tests
- Stage 1 horizon capping at 4 quarters
- Amortizing EAD with prepayment adjustment
- Quarterly discounting with exact DF calculation
- Scenario weighting with sum-to-1.0 validation
- Edge cases: PD=0, PD=1, LGD=0, LGD=1, EAD=0, single loan, 100-loan portfolio
- Numerical stability: small PD (1e-6), large EAD (1e12), high correlation, zero EIR
- All `__all__` package exports verified
