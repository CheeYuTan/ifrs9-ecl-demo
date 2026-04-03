---
sidebar_position: 3
title: "Step 2: Data Processing"
---

# Step 2: Data Processing

Review the loan portfolio data loaded from your core banking system before ECL calculation begins.

**IFRS 9 Reference:** B5.5.49-51 — reasonable and supportable information.

## What This Step Does

This step presents a comprehensive view of your portfolio so you can verify that the data feeding the ECL engine is complete, accurate, and reasonable. No calculation happens here — it's a review gate.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| Total Loans | Count of active loan facilities |
| Gross Carrying Amount (GCA) | Total outstanding balance |
| Stage 3 Rate | Percentage of GCA classified as credit-impaired |
| Products | Number of distinct product types |

## Data Lineage

A traceability card shows the data pipeline path:

**Source System** (e.g., CBS T24) → **Lakeflow DLT** (Bronze → Silver → Gold) → **Lakebase** (PostgreSQL)

This includes the Unity Catalog location, extraction date, and pipeline completeness indicator.

## Charts and Drill-Downs

### IFRS 9 Stage Distribution

A donut chart shows GCA distribution across Stage 1 (Performing), Stage 2 (SICR), and Stage 3 (Credit-Impaired). Click any stage segment to drill down into ECL by product for that stage.

### Days Past Due Drill-Down

Interactive bar chart of DPD distribution by product. Click a product to drill down by risk band or age group.

### Portfolio by Product

A combined chart and table showing:

| Column | Description |
|--------|-------------|
| Product | Product type name |
| Loans | Number of facilities |
| GCA | Gross Carrying Amount |
| Avg PD% | Average probability of default |
| Avg EIR% | Average effective interest rate |
| Avg DPD | Average days past due |
| Stage 1/2/3 | Loan count per stage |

The table is exportable to CSV.

### Additional Drill-Downs

- **PD Drill-Down** — Average PD by product, with sub-drill by cohort
- **Loan Count Drill-Down** — Loan distribution across products
- **GCA Drill-Down** — GCA distribution with product-level breakdowns

## Completing This Step

Review the data summaries and drill-downs. When you are satisfied that the data is complete and reasonable:

1. Click **Mark Complete** at the bottom of the page.
2. The step status updates and you can proceed to Step 3.

:::tip
Aim for a data quality score above 90% (checked in Step 3). If you notice unexpected patterns — such as missing products or unusual stage distributions — investigate before proceeding.
:::
