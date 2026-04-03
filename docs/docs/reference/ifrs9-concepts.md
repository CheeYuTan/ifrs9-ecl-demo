---
sidebar_position: 1
title: IFRS 9 Concepts
---

# IFRS 9 Concepts

Background on Expected Credit Losses, staging, and the calculation methodology implemented in this application.

## What is IFRS 9?

IFRS 9 Financial Instruments (effective 1 January 2018) replaced IAS 39 with a forward-looking **Expected Credit Loss** (ECL) model. Instead of waiting for a loss event to occur, institutions must recognise expected losses from the time a financial instrument is originated.

## The Three Stages

IFRS 9 classifies financial instruments into three stages based on credit quality changes since origination:

| Stage | Name | Trigger | ECL Horizon |
|-------|------|---------|-------------|
| **Stage 1** | Performing | No significant increase in credit risk | 12-month ECL |
| **Stage 2** | SICR | Significant Increase in Credit Risk detected | Lifetime ECL |
| **Stage 3** | Credit-Impaired | Objective evidence of impairment | Lifetime ECL |

### SICR Triggers (as implemented)

A loan moves from Stage 1 to Stage 2 when **any** of these triggers fire:

1. **PD Deterioration** — Current PD exceeds origination PD by both:
   - Relative threshold: `current_pd / origination_pd > 2.0×`
   - Absolute threshold: `current_pd - origination_pd > 0.5%`
2. **DPD Backstop** — Days past due ≥ 30
3. **Forbearance** — Loan has been restructured

A loan moves to Stage 3 when **DPD ≥ 90** (credit-impaired).

All thresholds are configurable in [Admin > Model Config](/admin-guide/model-config).

## ECL Formula

The Expected Credit Loss for each loan under each scenario is:

```
ECL = Σ(q=1 to T) [ PD_q × LGD_q × EAD_q × DF_q ]
```

Where:
- **PD_q** — Marginal probability of default in quarter *q*
- **LGD_q** — Loss Given Default in quarter *q*
- **EAD_q** — Exposure at Default in quarter *q*
- **DF_q** — Discount factor at the effective interest rate
- **T** — Horizon (4 quarters for Stage 1, remaining life for Stage 2/3)

### Probability of Default (PD)

- **Source**: `current_lifetime_pd` column (annualised point-in-time PD)
- **Quarterly conversion**: `q_pd = 1 - (1 - annual_pd)^0.25`
- **Stage 1**: Constant (flat hazard) across quarters
- **Stage 2/3**: Increasing hazard — `q_pd = base_q_pd × (1 + aging_factor × (q-1))`
  - Default aging factor: 8% per quarter
- **Survival**: `survival_q = survival_(q-1) × (1 - q_pd)`

### Loss Given Default (LGD)

- Calibrated from `historical_defaults` table: `mean(loss_given_default)` per product
- Secured products: `LGD = max(0.05, 1 - collateral_value / GCA)`
- Defaults by product: Credit Card 60%, Mortgage 15%, Commercial 25%, Personal 50%, Auto 35%
- Cure rates reduce effective LGD (e.g., Mortgage 40% cure rate)

### Exposure at Default (EAD)

- **Amortising loans**: `EAD_q = GCA × (1 - q×3/remaining_months) × (1 - quarterly_prepay)^q`
- **Bullet loans** (≤ 3 months remaining): `EAD_q = GCA`

### Discounting

- `DF_q = 1 / (1 + EIR/4)^q`
- Uses the loan's **Effective Interest Rate** (EIR) for quarterly discounting

## Monte Carlo Simulation

The application uses Monte Carlo simulation to generate a distribution of ECL outcomes:

1. **Correlated PD-LGD shocks** via Cholesky decomposition:
   ```
   z_pd ~ N(0,1)
   z_lgd = ρ × z_pd + √(1-ρ²) × z_lgd_independent
   ```
2. **Lognormal stress factors**:
   ```
   pd_shock = exp(z_pd × σ_pd - 0.5 × σ_pd²)
   lgd_shock = exp(z_lgd × σ_lgd - 0.5 × σ_lgd²)
   ```
3. **Stressed parameters**: `stressed_pd = clip(base_pd × scenario_mult × pd_shock, floor, cap)`
4. **Vectorised computation**: Loans processed in batches of 200 per scenario using NumPy arrays

Default: 1,000 simulations, configurable up to 50,000.

## Scenario Weighting

IFRS 9.5.5.17 requires probability-weighted ECL across multiple forward-looking scenarios:

```
Final ECL = Σ (scenario_weight × scenario_ECL_mean)
```

The application supports 8 scenarios with configurable weights, PD multipliers, and LGD multipliers. Scenario volatility scales with stress severity:

```
σ_pd = 0.05 + |pd_multiplier - 1.0| × 0.25
```

More severe scenarios produce greater idiosyncratic dispersion in the Monte Carlo simulation.

## Satellite Models

Satellite models link macroeconomic variables to default rates:

```
default_rate = f(unemployment, GDP_growth, inflation)
```

Eight model types are available, from simple linear regression to XGBoost. Models are trained per product-cohort combination and evaluated using R², RMSE, AIC, and BIC. The best model per cohort is automatically selected as the champion.

## IFRS 7 Disclosures

The application generates disclosures required by IFRS 7:

- **35F**: Credit risk management practices
- **35H**: Reconciliation from opening to closing ECL
- **35I**: Loss allowance reconciliation by stage
- **35K**: Credit risk exposure by grade
- **35M**: Concentration of credit risk
- **35N**: Collateral and credit enhancements

## Further Reading

- [IFRS 9 Standard](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/) — Official IASB standard
- [Basel Committee IFRS 9 Guidance](https://www.bis.org/bcbs/publ/d350.htm) — Regulatory expectations
