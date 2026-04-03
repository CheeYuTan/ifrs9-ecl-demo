---
sidebar_position: 3
title: "Step 2: Data Processing"
description: "Loading portfolio data, reviewing KPIs, and understanding stage distribution."
---

# Step 2: Data Processing

Data Processing is where you import and review the loan portfolio that will be used for ECL calculation. The platform loads data from your core banking system, calculates key performance indicators, and presents stage distributions — giving you a complete picture of your portfolio's credit risk profile before any models are applied.

:::info Prerequisites
- Completed [Step 1: Create Project](step-1-create-project)
- Portfolio data loaded into the data pipeline (coordinated by your administrator)
:::

## What You'll Do

On this page you will review the processed portfolio data, examine key metrics (total loans, gross carrying amount, stage distribution), explore drill-down charts by product and cohort, and confirm the data is ready for quality control.

## Step-by-Step Instructions

### 1. Review Data Lineage

At the top of the page, a **Data Lineage & Source Traceability** panel shows exactly where your data came from:

| Field | What It Shows |
|-------|--------------|
| **Source System** | The core banking system that originated the loan data |
| **Extraction Date** | The close-of-business date the data was extracted (matches your project's reporting date) |
| **Pipeline** | The data pipeline path from source to the platform (e.g., Bronze to Silver to Gold layers) |
| **Completeness** | How many loans were loaded versus expected — aim for 100% coverage |
| **Unity Catalog Reference** | The governed data catalog location |

This traceability is important for IFRS 9 compliance — auditors need to know that data used in ECL calculations can be traced back to its source system without gaps.

### 2. Check the Key Performance Indicators

Four KPI cards at the top of the page summarize the portfolio:

| KPI | What It Measures | Why It Matters |
|-----|-----------------|----------------|
| **Total Loans** | The number of individual loans in the portfolio | Confirms the full portfolio was loaded |
| **Gross Carrying Amount (GCA)** | The total outstanding balance across all loans | This is the exposure base for your ECL calculation |
| **Stage 3 Rate** | The percentage of loans classified as credit-impaired (Stage 3) | A high Stage 3 rate signals elevated credit risk in the portfolio |
| **Products** | The number of distinct product types (e.g., term loans, mortgages, revolving credit) | Confirms product diversity is as expected |

:::tip What Is Gross Carrying Amount?
Under IFRS 9, the Gross Carrying Amount (GCA) is the amortized cost of a financial asset before deducting the loss allowance. It represents the total exposure the institution carries on its balance sheet.
:::

### 3. Examine the Stage Distribution

The **IFRS 9 Stage Distribution** chart shows how the Gross Carrying Amount is split across the three impairment stages:

| Stage | Name | What It Means |
|:-----:|------|--------------|
| **1** | 12-month ECL | Performing loans with no significant credit deterioration since origination. Only 12 months of expected losses are provisioned. |
| **2** | Lifetime ECL | Loans where credit risk has significantly increased since origination (SICR triggered), but the borrower has not yet defaulted. Lifetime expected losses are provisioned. |
| **3** | Credit-impaired | Loans where the borrower is in default or individually assessed as impaired. Lifetime expected losses are provisioned using credit-adjusted rates. |

![Stage distribution chart](/img/screenshots/step-2-stage-distribution.png)
*The stage distribution donut chart. Click any segment to drill down into product-level detail.*

**Drill-down**: Click a stage segment in the chart to see how ECL is distributed across product types within that stage. This helps identify which products drive the most exposure in each stage.

### 4. Review the Portfolio by Product

The **Portfolio by Product** section shows a detailed breakdown of your portfolio:

| Column | What It Shows |
|--------|--------------|
| **Product** | The loan product type (e.g., Personal Loans, Mortgages, Credit Cards) |
| **Loans** | Number of loans in this product |
| **GCA** | Total gross carrying amount for this product |
| **Avg PD** | Average Probability of Default across loans in this product |
| **Avg EIR** | Average Effective Interest Rate (used for discounting future cash flows) |
| **Avg DPD** | Average Days Past Due — how overdue payments are on average |
| **Stage 1 / 2 / 3** | Count of loans in each impairment stage for this product |

![Portfolio dashboard](/img/guides/portfolio-dashboard.png)
*The portfolio breakdown table with product-level KPIs and stage counts.*

:::tip Use the Export Feature
Click the export button to download the portfolio table as a CSV file. This is useful for offline analysis or for sharing with colleagues who need to review the data outside the platform.
:::

### 5. Explore Drill-Down Charts

Below the summary, several interactive charts let you explore the data in more detail:

- **Days Past Due by Product** — Average DPD per product type. Click a product to drill down by risk band, vintage year, or other dimensions.
- **PD Distribution by Product** — Average Probability of Default per product, showing which product types carry the highest default risk.
- **Loan Count and GCA Distribution** — Side-by-side charts showing where the portfolio is concentrated by count and by value.

Each chart supports multi-level drill-down: click a bar to see the next level of detail. Use these to spot anomalies — for example, a product type with unusually high average DPD or an unexpected concentration of Stage 2 loans in a specific vintage.

### 6. Reading the Charts

The drill-down charts on this page are interactive and designed to help you spot patterns and anomalies before proceeding:

- **Bar heights** represent magnitude — taller bars mean higher values (more loans, larger GCA, higher average PD). Compare bars within the same chart to identify which products or stages dominate.
- **Color coding** maps to impairment stages: typically green for Stage 1, amber for Stage 2, and red for Stage 3. A chart that is predominantly green indicates a healthy portfolio; increasing amber or red warrants investigation.
- **Click to drill down** — clicking any bar or segment opens a sub-view with the next level of detail. For example, clicking a product bar in the PD Distribution chart shows the PD spread by vintage year within that product.
- **Hover for values** — hovering over any chart element displays the exact numeric value, percentage, and count.
- **Anomaly patterns to look for**:
  - A product with average DPD significantly higher than peers may indicate a systemic collection issue
  - A vintage cohort with an unusually high Stage 2 concentration may signal deteriorating underwriting standards from that period
  - A sudden drop in loan count for a product that should be stable may indicate a data pipeline issue rather than a genuine portfolio change

Use these drill-downs to build confidence that the data is complete and reasonable before advancing. If anything looks unexpected, investigate before marking the step complete — it is much easier to catch data issues now than after models have been run.

### 7. Mark the Step as Complete

When you are satisfied that the data has loaded correctly and the KPIs look reasonable:

1. Scroll to the **"Ready to proceed?"** panel at the bottom of the page
2. Click **Mark Complete**

This advances the project to Step 3: Data Control. The completion is recorded in the audit trail.

## Understanding the Results

The metrics on this page are descriptive — they summarize what is in the portfolio, not what the ECL will be. Use them to answer:

- **Is the full portfolio loaded?** Compare the total loan count and GCA against your expectations.
- **Is the stage distribution reasonable?** Most loans should be in Stage 1. If Stage 2 or 3 is unusually high, investigate whether this reflects genuine credit deterioration or a data issue.
- **Are risk parameters populated?** Check that PD, EIR, and DPD values are present and in expected ranges. Missing or zero values will cause problems in later steps.

## Tips & Best Practices

:::tip Bookmark Key Observations
As you review charts and tables, note any findings you want to reference later — for example, "Stage 2 concentration in mortgages is 12%, up from 8% last quarter." These observations will inform your Data Control review in the next step and provide useful context during sign-off.
:::

:::tip Compare Against Prior Periods
If this is not your first ECL run, compare the current portfolio KPIs against the previous reporting date. Significant changes in total GCA, stage distribution, or product mix should be understood before proceeding.
:::

:::warning Watch for Data Gaps
If the completeness indicator shows less than 100%, or if a product type you expect is missing, do not proceed. Contact your administrator to investigate the data pipeline before advancing to Data Control.
:::

:::tip Understand Stage Assignments
At this point, stage assignments are based on the data as loaded (typically using Days Past Due rules: 0-30 DPD = Stage 1, 30+ DPD with SICR = Stage 2, 90+ DPD = Stage 3). These are initial classifications — the satellite models in Step 4 may refine credit risk estimates.
:::

:::caution Zero or Missing Values
If you see PD = 0.00 or EIR = 0.00 for any product, this typically indicates missing data rather than genuinely zero risk. Zero PD means the model treats those loans as having no default probability — which would exclude them from ECL entirely. Similarly, a zero EIR prevents proper discounting of future cash shortfalls. Investigate with your data team before proceeding.
:::

## What's Next?

Proceed to [Step 3: Data Control](step-3-data-control) to run quality checks and approve the data through the maker-checker review process.
