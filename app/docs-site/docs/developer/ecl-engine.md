---
sidebar_position: 4
title: "ECL Engine"
description: "Monte Carlo simulation engine, Cholesky decomposition, and ECL calculation methodology."
---

# ECL Engine

The ECL engine is the core computational module of the platform. It implements a Monte Carlo simulation framework that computes Expected Credit Losses across all loans, scenarios, and simulation paths using fully vectorized NumPy operations.

## Entry Point

The simulation is orchestrated by `ecl/simulation.py`:

```python
def run_simulation(
    n_sims: int = 1000,
    pd_lgd_correlation: float = 0.30,
    aging_factor: float = 0.08,
    pd_floor: float = 0.001,
    pd_cap: float = 0.95,
    lgd_floor: float = 0.01,
    lgd_cap: float = 0.95,
    scenario_weights: dict[str, float] | None = None,
    progress_callback=None,
    random_seed: int | None = None,
) -> dict:
```

The function returns a dictionary containing `portfolio_summary`, `scenario_results`, `product_scenario`, `stage_summary`, and `run_metadata`.

## ECL Formula

The IFRS 9 ECL for each loan is computed as:

```
ECL = SUM over quarters q of:
    P(default in q) * LGD * EAD(q) * DF(q)
```

Where:
- **P(default in q)** = survival to quarter q-1 multiplied by the quarterly PD
- **LGD** = Loss Given Default (stressed by scenario)
- **EAD(q)** = Exposure at Default at quarter q (amortized, with prepayment)
- **DF(q)** = Discount factor at quarter q using the effective interest rate

The final ECL for each loan is the **probability-weighted average** across all macro scenarios:

```
ECL_final = SUM over scenarios s of:
    weight(s) * ECL(s)
```

## Four-Step Process

### Step 1: Data Loading

The engine loads data from Lakebase via `ecl/data_loader.py`:

1. **Loans**: All rows from `lb_model_ready_loans`, each with `loan_id`, `product_type`, `assessed_stage`, `gross_carrying_amount`, `effective_interest_rate`, `current_lifetime_pd`, and `remaining_months`.
2. **Scenarios**: Scenario definitions with `pd_mult`, `lgd_mult`, `pd_vol`, and `lgd_vol` per scenario.
3. **Configuration**: LGD assumptions and satellite coefficients from admin config, with fallbacks to `ecl/constants.py`.

The `prepare_loan_columns()` function in `ecl/monte_carlo.py` derives simulation-ready columns:

| Derived Column | Formula | Description |
|---------------|---------|-------------|
| `stage` | `assessed_stage` cast to int | Integer stage (1, 2, or 3) |
| `gca` | `gross_carrying_amount` as float | Gross carrying amount |
| `eir` | `effective_interest_rate` as float | Effective interest rate |
| `base_pd` | `current_lifetime_pd` as float | Annualized point-in-time PD |
| `rem_q` | `remaining_months // 3`, clipped to ≥ 1 | Remaining quarters |
| `rem_months_f` | `remaining_months` as float, clipped to ≥ 1 | Remaining months (float) |
| `base_lgd` | Mapped from product_type LGD assumptions | Base LGD by product |

### Step 2: Scenario Loop

For each macro scenario (default: 8 scenarios), the engine calls `run_scenario_sims()` which processes all `n_sims` simulations in batches.

The 8 default scenarios and their weights:

| Scenario | Weight | Description |
|----------|--------|-------------|
| `baseline` | 30% | Central economic forecast |
| `mild_recovery` | 15% | Moderate improvement |
| `strong_growth` | 5% | Optimistic expansion |
| `mild_downturn` | 15% | Moderate deterioration |
| `adverse` | 15% | Significant downturn |
| `stagflation` | 8% | High inflation with stagnation |
| `severely_adverse` | 7% | Severe recession |
| `tail_risk` | 5% | Extreme tail event |

Each scenario provides a `pd_mult` (PD multiplier), `lgd_mult` (LGD multiplier), `pd_vol` (PD shock volatility), and `lgd_vol` (LGD shock volatility).

### Step 3: Per-Loan Quarterly Recursion

Within each batch of simulations, the engine runs a quarterly recursion over the loan's remaining life. This is the core computation in `ecl/monte_carlo.py`.

#### Cholesky Decomposition for Correlated Shocks

PD and LGD shocks are correlated using a Cholesky-based approach. For each loan and simulation path:

```python
z_pd = rng.standard_normal((n_loans, batch))         # Independent PD shocks
z_lgd_indep = rng.standard_normal((n_loans, batch))   # Independent LGD shocks

# Cholesky correlation: z_lgd shares rho fraction of z_pd
z_lgd = rho * z_pd + sqrt(1 - rho^2) * z_lgd_indep
```

Where `rho` is the PD-LGD correlation (per product type, from satellite coefficients). This ensures that when PD shocks are adverse, LGD shocks tend to be adverse as well (positive correlation).

#### Lognormal Shocking

The correlated normal shocks are converted to multiplicative lognormal shocks:

```python
pd_shocks = exp(z_pd * pd_vol - 0.5 * pd_vol^2)     # Mean-preserving lognormal
lgd_shocks = exp(z_lgd * lgd_vol - 0.5 * lgd_vol^2)
```

The `-0.5 * vol^2` term is the lognormal mean correction, ensuring the expected value of the shock is 1.0. Stressed PD and LGD are then:

```python
stressed_pd  = clip(base_pd * pd_mult * pd_shocks, pd_floor, pd_cap)
stressed_lgd = clip(base_lgd * lgd_mult * lgd_shocks, lgd_floor, lgd_cap)
```

#### Quarterly Recursion

For each quarter `q` from 1 to `max_horizon`:

```python
# 1. Convert annual PD to quarterly
quarterly_base_pd = 1 - (1 - stressed_pd)^0.25

# 2. Apply aging factor for Stage 2/3 loans
aging = 1.0 + aging_factor * (q - 1)   # Only for Stage 2/3
q_pd = clip(quarterly_base_pd * aging, 0, 0.99)

# 3. Compute default probability this quarter
default_this_q = survival * q_pd

# 4. Compute EAD with amortization and prepayment
prepay_surv = (1 - quarterly_prepay)^q
amort = max(0, 1 - (q * 3) / remaining_months)
ead_q = gca * amort * prepay_surv          # Amortizing loans
ead_q = gca                                 # Bullet loans (remaining_months <= 3)

# 5. Discount factor
discount = 1 / (1 + eir/4)^q

# 6. ECL contribution this quarter
contribution = default_this_q * stressed_lgd * ead_q * discount

# 7. Update survival probability
survival *= (1 - q_pd)
```

#### Stage Handling

The `max_horizon` determines how many quarters of ECL are accumulated:

- **Stage 1**: `min(4, remaining_quarters)` -- 12-month ECL (4 quarters)
- **Stage 2 and 3**: `remaining_quarters` -- lifetime ECL over the full remaining term

#### Aging Factor

The aging factor increases the quarterly PD for Stage 2/3 loans as time progresses. With the default `aging_factor = 0.08`, a Stage 2 loan's PD increases by 8% per quarter, reflecting deteriorating credit quality for loans that have already shown signs of increased credit risk.

### Step 4: Result Aggregation

After all scenarios complete, `ecl/aggregation.py` assembles the final results:

1. **Loan-level weighted ECL**: Sum of each scenario's mean ECL weighted by scenario probability
2. **Portfolio summary**: Grouped by `product_type` and `stage`, with `loan_count`, `total_gca`, `total_ecl`, and `coverage_ratio`
3. **Scenario results**: Per-scenario `ecl_mean`, `ecl_p50`, `ecl_p75`, `ecl_p95`, `ecl_p99`
4. **Product-scenario breakdown**: ECL for each product within each scenario
5. **Stage summary**: ECL aggregated by stage
6. **Convergence diagnostics**: Per-product CI width and CV
7. **Run metadata**: Timing, parameters, seed, loan count

## Vectorization and Performance

The engine processes loans in fully vectorized NumPy batches with no per-loan Python loops:

| Parameter | Value |
|-----------|-------|
| Batch size | `min(n_sims, 200)` per batch |
| Array shape per batch | `(n_loans, batch_size)` |
| Typical performance | ~0.02 seconds per simulation for 84,000 loans |
| Memory layout | Column-oriented NumPy arrays extracted from DataFrame |

Key vectorization techniques:
- All loan attributes are extracted as 1D NumPy arrays before the simulation loop
- Broadcasting expands 1D loan arrays against 2D `(n_loans, batch)` simulation arrays
- The quarterly loop operates on full `(n_loans, batch)` matrices simultaneously
- Product-level accumulation uses boolean masking (`products == prod`)

## Convergence Diagnostics

After simulation, the engine computes convergence metrics per product type:

```python
se = std_ecl / sqrt(n_sims)       # Standard error
ci_width = 1.96 * se              # 95% confidence interval half-width
ci_pct = ci_width / mean_ecl * 100  # CI as percentage of mean
```

A well-converged simulation should have `ci_pct < 5%` for each product type. If convergence is insufficient, increase `n_simulations`.

## Markov Chain Module

The Markov chain module (`domain/markov.py`) estimates and applies discrete-time transition matrices for stage migration modeling.

### State Space

The model uses a 4-state absorbing Markov chain:

| State | Label | Absorbing |
|-------|-------|-----------|
| 0 | Stage 1 (Performing) | No |
| 1 | Stage 2 (Underperforming) | No |
| 2 | Stage 3 (Non-performing) | No |
| 3 | Default | Yes |

### Transition Matrix Estimation

Transition matrices are estimated from historical stage migration data using the cohort method. Each element `P[i,j]` represents the probability of moving from state `i` to state `j` in one period.

### Matrix Exponentiation for Forecasting

Multi-period forecasts use matrix exponentiation:

```
distribution(t) = distribution(0) * P^t
```

where `P^t` is the transition matrix raised to the power `t` (number of periods).

### Lifetime PD

The lifetime PD is derived from the forecasted stage distribution by tracking the cumulative probability of entering the Default (absorbing) state over the forecast horizon.

## Hazard Models

The platform supports three types of survival analysis models (`domain/hazard*.py`):

| Model | Module | Use Case |
|-------|--------|----------|
| **Cox Proportional Hazards** | `hazard_cox_ph.py` | Semi-parametric model with covariates; estimates relative hazard ratios |
| **Kaplan-Meier** | `hazard_nonparam.py` | Non-parametric survival curve estimation; no covariate assumptions |
| **Discrete-Time Logistic** | `hazard_estimation.py` | Logistic regression on discrete time intervals; outputs period-specific PDs |

All models produce survival curves and PD term structures that can be used for IFRS 9 lifetime PD estimation.

## Validation Rules

The platform enforces 23 domain validation rules in three categories:

### Pre-Calculation Rules (D1-D10)

Checked before simulation execution; critical failures block the run.

| Rule | Check |
|------|-------|
| D1 | Scenario weights sum to 1.0 (tolerance: 0.001) |
| D2 | PD values in [0, 1] range |
| D3 | LGD values in [0, 1] range |
| D4 | EIR values are non-negative and reasonable |
| D5 | Remaining months are positive integers |
| D6 | GCA values are positive |
| D7 | Stages are valid (1, 2, or 3) |
| D8 | Stage-DPD consistency (Stage 3 implies DPD > 90) |
| D9 | Aging factor is within acceptable range |
| D10 | No critical data completeness gaps |

### Post-Calculation Rules (M-R1-R8)

Checked after simulation; warnings indicate potential issues.

| Rule | Check |
|------|-------|
| M-R1 | Convergence CV < 5% per product |
| M-R2 | ECL coverage ratios within expected ranges |
| M-R3 | Stage 3 ECL > Stage 2 ECL > Stage 1 ECL (monotonicity) |
| M-R4 | Scenario ordering (adverse ECL > baseline ECL) |
| M-R5 | No negative ECL values |
| M-R6 | Total ECL is less than total GCA |
| M-R7 | ECL change vs. prior period within bounds |
| M-R8 | Product-level ECL reasonableness |

### Governance Rules (G-R1-G-R5)

Enforced during workflow transitions.

| Rule | Check |
|------|-------|
| G-R1 | Simulation must complete before sign-off |
| G-R2 | Segregation of duties (executor cannot sign off) |
| G-R3 | Approval required for material overlays |
| G-R4 | Audit trail completeness |
| G-R5 | ECL hash integrity at sign-off |

## Default Constants

Fallback values from `ecl/constants.py` when admin configuration is unavailable:

### Default LGD by Product Type

| Product | LGD |
|---------|-----|
| `credit_card` | 60% |
| `residential_mortgage` | 15% |
| `commercial_loan` | 25% |
| `personal_loan` | 50% |
| `auto_loan` | 35% |

### Satellite Coefficients by Product Type

| Product | PD-LGD Correlation | Annual Prepay Rate | LGD Std Dev |
|---------|--------------------|--------------------|-------------|
| `credit_card` | 0.35 | 3% | 0.15 |
| `residential_mortgage` | 0.20 | 8% | 0.08 |
| `commercial_loan` | 0.30 | 5% | 0.12 |
| `personal_loan` | 0.32 | 10% | 0.14 |
| `auto_loan` | 0.25 | 6% | 0.10 |

### Default Satellite Parameters

When product-specific coefficients are not available, the engine falls back to:

| Parameter | Value |
|-----------|-------|
| PD-LGD correlation | 0.30 |
| Annual prepay rate | 5% |
| LGD standard deviation | 0.15 |

## Random Seed Management

The simulation supports deterministic reproducibility through the `random_seed` parameter:

- If `random_seed` is provided, the simulation produces identical results for the same inputs.
- If not provided, a random seed is generated via `np.random.default_rng().integers(0, 2**31)`.
- The seed is recorded in `run_metadata` and persisted in the `model_runs` table for audit traceability.
- The `/api/simulation/compare` endpoint can compare runs with different seeds to assess Monte Carlo variance.
