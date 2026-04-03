---
sidebar_position: 7
title: Domain Logic — Analytical Engines
---

# Domain Logic: Registry, Backtesting, Markov, Hazard & Advanced

The second half of the domain logic layer implements the analytical engines that power model governance, statistical validation, stochastic forecasting, survival analysis, and advanced credit risk features.

## Overview

Ten domain modules (plus sub-modules) provide the computational backbone for model-driven ECL estimation:

| Module | Purpose | Tests |
|--------|---------|-------|
| `domain/model_registry.py` | Model version management, champion/challenger lifecycle | 49 |
| `domain/backtesting.py` | Backtest orchestration, metric aggregation, traffic lights | 67 |
| `domain/backtesting_stats.py` | AUC, Gini, KS, PSI, Brier score, H-L computation | (included above) |
| `domain/backtesting_traffic.py` | Basel traffic light classification | (included above) |
| `domain/markov.py` | Transition matrix estimation, state forecasting | 19 |
| `domain/hazard.py` + 6 sub-modules | Survival analysis: Cox PH, discrete-time, Kaplan-Meier | 24 |
| `domain/advanced.py` | Cure rates, CCF, collateral haircuts | 28 |
| `domain/period_close.py` | End-of-period pipeline orchestration | 21 |
| `domain/health.py` | System and config health checks | 13 |

![Model Registry](/img/guides/model-registry.png)
*Model Registry showing version history and governance status*

## Model Registry

The `model_registry.py` module manages the full lifecycle of credit risk models.

### Version Management

Each model registration creates a new version. The registry tracks:
- **Version incrementing**: Automatic version bumps on re-registration
- **Champion replacement**: When a new model is promoted, the current champion is automatically retired
- **Audit trail**: Every status change is logged with user, timestamp, and reason

### Lifecycle Transitions

```
Draft → Validated → Champion → Retired
```

The registry enforces valid transitions and rejects invalid ones (e.g., Draft → Champion directly). See the [Model Analytics guide](./model-analytics) for the full transition matrix.

## Backtesting Engine

The backtesting engine validates model predictions against realized outcomes using six industry-standard metrics.

### Metric Computation

| Metric | Formula | Interpretation |
|--------|---------|---------------|
| **AUC** | Area under ROC curve | Discrimination power (0.5 = random, 1.0 = perfect) |
| **Gini** | `2 × AUC - 1` | Concentration measure (0 = no power, 1 = perfect) |
| **KS** | Max separation of cumulative distributions | Maximum discriminatory power at a single threshold |
| **PSI** | `Σ (actual_i - expected_i) × ln(actual_i / expected_i)` | Population stability between development and validation samples |
| **Brier** | `(1/N) × Σ (forecast - outcome)²` | Calibration accuracy (lower is better) |
| **H-L** | Hosmer-Lemeshow chi-square test | Goodness-of-fit across decile groups |

### Traffic Light Classification

Metrics are classified using Basel Committee thresholds:

| Zone | AUC | PSI | KS | Brier |
|------|-----|-----|-----|-------|
| **Green** | ≥ 0.7 | < 0.1 | ≥ 0.3 | < 0.1 |
| **Amber** | ≥ 0.6 | < 0.25 | ≥ 0.15 | < 0.2 |
| **Red** | < 0.6 | ≥ 0.25 | < 0.15 | ≥ 0.2 |

![Backtesting Results](/img/guides/backtesting-results.png)
*Backtesting dashboard with traffic light classification and metric history*

### Bug Fixes (Sprint 7)

Three bugs were discovered and fixed during testing:

1. **BUG-7-001**: NumPy types (`np.float64`, `np.int64`) were not JSON-serializable in backtest result output. Fixed by adding a `_json_default()` helper that converts NumPy scalars to native Python types.

2. **BUG-VQA-7-001**: The `backtest_metrics` table was missing a `detail` column added in a later schema revision. Fixed by adding an `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` migration in the backtest setup path.

3. **BUG-S7-1/BUG-S7-2**: `ensure_workflow_table()` used `globals().get()` to look up ensure functions, which silently returned `None` for functions that were never imported (like `ensure_backtesting_table`). Fixed by replacing the `globals()` pattern with explicit lazy imports inside the function body.

## Markov Chain Engine

The `markov.py` module estimates transition matrices from observed rating migrations and uses them for stochastic forecasting.

### Transition Matrix Properties

Every estimated transition matrix is guaranteed to satisfy:

| Property | Description | Validation |
|----------|-------------|------------|
| **Row stochasticity** | Each row sums to 1.0 | Verified within floating-point tolerance |
| **Non-negativity** | All entries ≥ 0 | No negative transition probabilities |
| **Absorbing default** | Default state has P(default→default) = 1.0 | Cannot exit default |

### Lifetime PD Computation

Lifetime PD is derived from matrix exponentiation:

```
P(default by time t) = 1 - Σ(non-default states at time t)
```

Properties verified by tests:
- **Monotonically non-decreasing** — cumulative PD can only increase over time
- **Starts at 0** at t = 0
- **Approaches 1.0** as the horizon extends (absorbing state)

### State Forecasting

The forecast function projects the portfolio rating distribution forward:

```python
distribution_t = initial_distribution × M^t
```

Where `M^t` is the t-step transition matrix computed via matrix power. The forecasted distribution sums to 100% at every time step.

## Hazard Model Engine

The hazard module implements three survival analysis methods across 7 files.

### Cox Proportional Hazards

The Cox PH model estimates the effect of covariates on the hazard rate:

```
h(t|X) = h₀(t) × exp(β₁X₁ + β₂X₂ + ... + βₖXₖ)
```

Where:
- `h₀(t)` is the baseline hazard
- `β` are the estimated coefficients
- `X` are the covariate values (leverage, interest coverage, etc.)

### Survival Curves

Survival curves computed from hazard models have these properties:
- **Monotonically non-increasing** — S(t) can only decrease
- **S(0) = 1.0** — all borrowers alive at time zero
- **Risk multiplier** — higher-risk covariates accelerate the decline

### Kaplan-Meier Estimation

The non-parametric Kaplan-Meier estimator provides a baseline survival curve without assuming any covariate structure. Useful for visualization and comparison.

### Term Structure Derivation

Hazard models produce cumulative PD term structures:
- Cumulative PD is monotonically non-decreasing
- 12-month PD is bounded in [0, 1]
- Longer horizons always have higher or equal cumulative PD

## Advanced Analytics

The `advanced.py` module provides three specialized credit risk computations.

### Cure Rates

Cure rates measure the probability of a defaulted borrower (Stage 3) returning to performing status:

- Transition from Stage 3 → Stage 2 or Stage 1
- Values bounded in [0, 1]
- Used to adjust lifetime ECL for curing probability

### Credit Conversion Factors (CCF)

CCF estimates the proportion of undrawn credit that will be drawn at default:

```
EAD = Drawn + CCF × Undrawn
```

- CCF values bounded in [0, 1]
- Higher CCF means more undrawn exposure will be used before default
- Essential for revolving credit facilities (credit cards, credit lines)

### Collateral Haircuts

Collateral analysis adjusts LGD based on the value of collateral held:

```
LGD_adjusted = LGD × (1 - collateral_coverage × (1 - haircut))
```

- Haircut reflects potential decline in collateral value during liquidation
- Different collateral types have different haircut percentages

## Period Close Pipeline

The `period_close.py` module orchestrates the end-of-period ECL calculation workflow.

### Pipeline Characteristics

- **Step ordering**: Steps execute in a defined sequence with dependency management
- **Failure handling**: If a step fails, the pipeline stops — it does not skip failed steps
- **Parallel-safe steps**: Some steps can execute in parallel where no dependency exists
- **Health monitoring**: Real-time health check during pipeline execution

## Health Checks

The `health.py` module provides system and configuration health monitoring:

- **Config loaded check**: Verifies that all required configuration is present
- **Database connectivity**: Tests Lakebase connection
- **Table existence**: Validates that required tables exist
- **Module availability**: Checks that all domain modules can be imported

## Test Coverage

Sprint 7 of the QA audit added **230 tests** across 4 iterations:

- Model registry: version management, champion replacement, lifecycle transitions (49 tests)
- Backtesting: all 6 metrics with known inputs, traffic light classification (67 tests)
- Markov: row stochasticity, non-negativity, absorbing states, lifetime PD monotonicity (19 tests)
- Hazard: Cox PH coefficients, survival curve monotonicity, term structure derivation (24 tests)
- Advanced: cure rates, CCF estimation, collateral haircuts (28 tests)
- Period close: step ordering, failure handling, parallel safety (21 tests)
- Health: config checks, connectivity, module availability (13 tests)
- 3 bug fixes with 31 regression tests
