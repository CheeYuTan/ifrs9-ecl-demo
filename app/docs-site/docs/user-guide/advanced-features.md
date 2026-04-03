---
sidebar_position: 17
title: "Advanced Features"
description: "Cure rates, credit conversion factors, collateral haircuts, and other advanced ECL parameters."
---

# Advanced Features

The Advanced Features module provides three specialised analyses that refine the ECL calculation beyond the core PD × LGD × EAD formula. **Cure Rate Analysis** measures how often distressed loans recover. **Credit Conversion Factor (CCF) Analysis** adjusts exposure for off-balance-sheet commitments like undrawn credit lines. **Collateral Haircut Analysis** determines the realistic recovery value of collateral when calculating Loss Given Default. Together, these features allow your institution to move from conservative regulatory defaults to data-driven parameters calibrated to your own portfolio history.

:::info Prerequisites
- Completed data processing with historical stage migration data (see [Step 2: Data Processing](step-2-data-processing))
- Portfolio data must include facility limits and drawn amounts for CCF analysis
- Collateral data with property types and valuations for haircut analysis
- **Analyst** role or above to run analyses; all roles can view results
:::

## What You'll Do

On this page you will run cure rate analysis to understand recovery patterns, calculate credit conversion factors for revolving facilities, and estimate collateral haircuts across different asset types. Each analysis produces parameters that can be used to refine ECL calculations.

## Cure Rate Analysis

### What Are Cure Rates?

A "cure" occurs when a loan that was classified as Stage 2 (underperforming) or Stage 3 (credit-impaired) improves in credit quality and returns to Stage 1 (performing). The cure rate is the percentage of distressed loans that recover within a given period.

Cure rates matter for ECL because they affect the expected path of a loan: a portfolio with high cure rates will have lower lifetime ECL than one where distressed loans rarely recover.

### Running the Analysis

1. Navigate to **Advanced Features** from the main menu
2. The page opens to the **Cure Rates** tab
3. Click **Compute** to run the analysis
4. The platform scans historical stage migration data for all instances where loans moved from Stage 2 or Stage 3 back to Stage 1

### Understanding the Results

Four summary cards appear at the top:

| Card | What It Shows |
|---|---|
| **Overall Cure Rate** | The portfolio-wide percentage of distressed loans that cured |
| **Average Time to Cure** | How many months it typically takes for a distressed loan to recover |
| **Total Observations** | Number of cure events in the analysis period |
| **Trend** | Whether cure rates are improving, stable, or deteriorating |

Below the cards, three breakdowns provide granular detail:

#### By Days Past Due (DPD) Bucket

| DPD Bucket | Typical Cure Rate | Interpretation |
|---|---|---|
| 1–30 days | ~72% | Most early-stage delinquencies cure — often administrative delays or temporary cash flow issues |
| 31–60 days | ~45% | Cure probability drops significantly — genuine credit stress is emerging |
| 61–90 days | ~22% | Less than one in four cures — loans at this stage are likely heading for default |
| 90+ days | ~8% | Cure is rare — most loans at this stage are credit-impaired |

:::tip DPD Buckets Drive Stage Decisions
The steep drop in cure rates from the 1–30 bucket to the 90+ bucket illustrates why IFRS 9 uses SICR (Significant Increase in Credit Risk) as the trigger for moving loans to lifetime ECL measurement. Early delinquency often self-corrects; persistent delinquency rarely does.
:::

#### By Product Type

Cure rates vary significantly across product types. Secured products (mortgages) typically show higher cure rates than unsecured products (personal loans, credit cards) because borrowers are more motivated to maintain payments when collateral is at risk.

#### By Customer Segment

The platform segments cure rates by customer type — retail, SME, and corporate. Corporate borrowers tend to have more volatile but higher cure rates (restructuring is common), while retail cures follow more predictable patterns.

![Cure rate analysis dashboard](/img/screenshots/advanced-cure-rates.png)
*The Cure Rates tab showing overall cure rate, DPD-bucket breakdown, and trend chart.*

### Cure Rate Trend

A line chart shows the monthly cure rate over the past 12 months. This trend is critical for forward-looking ECL:

- **Rising trend** — credit conditions are improving; ECL may decrease in the next period
- **Falling trend** — credit conditions are deteriorating; ECL is likely to increase
- **Stable trend** — conditions are steady; ECL changes will be driven by portfolio composition rather than cure behaviour

## Credit Conversion Factor (CCF) Analysis

### What Is CCF?

The Credit Conversion Factor converts off-balance-sheet exposure into on-balance-sheet Exposure at Default (EAD). It applies to **revolving facilities** — credit cards, overdrafts, and revolving credit lines — where the borrower has an undrawn limit that they could draw upon before defaulting.

The formula is:

**CCF = (EAD at default − Current drawn amount) ÷ (Facility limit − Current drawn amount)**

A CCF of 0.65 means that, on average, borrowers draw an additional 65% of their available limit before defaulting. This "drawdown at default" behaviour is a critical component of EAD estimation under IFRS 9.

### Running the Analysis

1. Switch to the **CCF Analysis** tab
2. Click **Compute**
3. The platform identifies all revolving facilities in the portfolio and calculates CCF from historical drawdown patterns

### Understanding the Results

#### By Product Type and Stage

The primary results table shows CCF for each combination of product type and impairment stage:

| Product Type | Stage 1 | Stage 2 | Stage 3 |
|---|---|---|---|
| Credit Card | 0.65 | 0.78 | 0.92 |
| Overdraft | 0.65 | 0.78 | 0.92 |
| Revolving Credit | 0.65 | 0.78 | 0.92 |
| Non-Revolving (term loans) | 0.95 | 0.97 | 0.99 |

CCF increases with stage because distressed borrowers tend to draw more of their available credit before defaulting. Non-revolving facilities have CCF close to 1.0 because most of the exposure is already drawn.

#### By Utilisation Band

The analysis also segments CCF by how much of the limit is already drawn:

| Utilisation Band | Typical CCF | Why |
|---|---|---|
| 0–20% drawn | Highest CCF | Lots of undrawn headroom — borrowers in stress will draw aggressively |
| 20–40% drawn | High CCF | Still significant room to draw |
| 40–60% drawn | Moderate CCF | Less room, but still potential for additional drawdown |
| 60–80% drawn | Lower CCF | Limited remaining capacity to draw |
| 80–100% drawn | Lowest CCF | Almost fully drawn — little additional exposure risk |

:::warning Non-Revolving Facilities
Non-revolving term loans have a fixed drawdown schedule. Their CCF is always close to 1.0 because the borrower has already received the full loan amount. The CCF analysis is most meaningful for revolving facilities.
:::

### How CCF Affects EAD

The platform uses CCF to calculate EAD for each facility:

**EAD = Current Drawn Amount + (CCF × Undrawn Amount)**

A higher CCF produces a higher EAD, which increases ECL. This is why CCF calibration matters — using a regulatory default of 1.0 (assuming full drawdown) is conservative but may overstate ECL for portfolios where historical drawdown behaviour is more moderate.

## Collateral Haircut Analysis

### What Are Collateral Haircuts?

When a borrower defaults, the institution may recover some losses by liquidating collateral. However, collateral rarely recovers its full appraised value — forced-sale discounts, legal costs, time delays, and market depreciation all reduce the actual recovery. The **haircut** is the percentage reduction from appraised value to realistic recovery value.

IFRS 9 (paragraph B5.5.55) requires that LGD estimates reflect the expected recovery from collateral, adjusted for costs and time-to-recovery. The Collateral Haircut Analysis provides these data-driven adjustments.

### Running the Analysis

1. Switch to the **Collateral Haircuts** tab
2. Click **Compute**
3. The platform analyses historical recovery data by collateral type

### Understanding the Results

The results table shows key metrics for each collateral type:

| Collateral Type | Haircut | Recovery Rate | Time to Recovery | Forced Sale Discount |
|---|---|---|---|---|
| Residential Property | 20% | 72% | 18 months | Applied |
| Commercial Property | 30% | 58% | 24 months | Applied |
| Vehicle | 35% | 52% | 6 months | Applied |
| Cash Deposit | 2% | 98% | 1 month | Minimal |
| Securities | 15% | 80% | 3 months | Market-based |
| Equipment | 40% | 45% | 12 months | Applied |
| Unsecured | 100% | 15% | 36 months | N/A |

:::tip Cash Is King
Cash deposits have the lowest haircut (2%) and highest recovery rate (98%) because they can be liquidated immediately with minimal friction. If your portfolio has significant cash-collateralised exposure, ensure it is correctly flagged — it materially reduces LGD.
:::

### The LGD Waterfall

The platform visualises the path from gross exposure to net LGD through a **waterfall** showing:

1. **Gross Exposure** — the full amount at risk
2. **Secured Portion** — the portion covered by collateral at appraised value
3. **Collateral Recovery** — the expected recovery after applying the haircut
4. **Haircut Applied** — the amount lost to forced-sale discounts and costs
5. **Unsecured LGD** — the loss on the unsecured portion

The summary panel shows portfolio-wide averages: **average haircut**, **average recovery rate**, **average time to recovery**, **net LGD percentage**, and **percentage of portfolio that is secured**.

![Collateral haircut analysis](/img/screenshots/advanced-collateral.png)
*The Collateral Haircuts tab showing recovery rates by collateral type and the LGD waterfall.*

### How Haircuts Affect ECL

Lower haircuts → higher recovery → lower LGD → lower ECL. The relationship is:

**LGD (secured) = 1 − (Recovery Rate × Collateral Coverage)**

For the unsecured portion, the platform uses the historical unsecured LGD rate. The blended LGD for each loan is a weighted average of the secured and unsecured components.

## Tips & Best Practices

:::tip Calibrate to Your Own Data
Regulatory defaults (e.g., 45% LGD for senior unsecured exposures) are intentionally conservative. If your institution has sufficient historical recovery data, using data-driven haircuts and CCFs will produce more accurate — and often lower — ECL estimates. Document the methodology for auditors.
:::

:::tip Review Quarterly
Cure rates, CCFs, and collateral values change with market conditions. Re-run these analyses each quarter to ensure ECL parameters reflect current conditions, not stale estimates.
:::

:::warning Unsecured Exposure
Unsecured loans have a 100% haircut by definition — there is no collateral to recover. The LGD for unsecured exposure depends entirely on the borrower's ability to pay after default. The platform uses historical recovery rates (typically 10–20%) for this segment.
:::

:::caution Sample Size Matters
If a collateral type has very few observations (e.g., fewer than 30 historical recoveries), the estimated haircut may be unreliable. The platform shows the sample size for each collateral type — be cautious about acting on estimates with small samples.
:::

## What's Next?

- [Step 5: Model Execution](step-5-model-execution) — the Monte Carlo simulation uses LGD, EAD, and PD parameters calibrated by these analyses
- [Markov Chains & Hazard Models](markov-hazard) — cure rate analysis complements the transition matrix by quantifying recovery patterns
- [Step 4: Satellite Models](step-4-satellite-model) — satellite models provide point-in-time PD adjustments that work alongside CCF-adjusted EAD
- [GL Journals](gl-journals) — ECL provisions calculated with refined parameters flow through to journal entries
