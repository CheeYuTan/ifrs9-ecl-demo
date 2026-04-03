---
sidebar_position: 4
title: "Step 3: Data Control"
---

# Step 3: Data Control

Validate data quality checks and reconcile the loan tape against the General Ledger.

**IFRS 9 Reference:** IFRS 7.35I — reconciliation of opening to closing loss allowance.

## What This Step Does

Before ECL calculation, this step ensures your data meets quality thresholds and that the loan tape balances against your GL trial balance within materiality tolerances.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| DQ Score | Percentage of data quality checks that passed |
| GL Reconciliation | Number of products that reconcile within tolerance |
| Critical Failures | Count of critical-severity DQ check failures |
| Step Status | Current approval state |

## GL Reconciliation

A table comparing the General Ledger balance against the loan tape balance for each product:

| Column | Description |
|--------|-------------|
| Product | Product type |
| GL Balance | Balance from the `general_ledger` table |
| Loan Tape Balance | Sum of GCA from `loan_tape` |
| Variance | Absolute difference |
| Variance % | Percentage difference |
| Status | PASS (within tolerance) or FAIL |

The default GL reconciliation tolerance is **0.50%** (configurable in Admin > App Settings).

## Data Quality Checks

A paginated table of all DQ checks run against the loan data:

| Column | Description |
|--------|-------------|
| Check ID | Unique identifier |
| Category | Check category (completeness, consistency, validity, etc.) |
| Description | What the check verifies |
| Severity | Critical, High, or Medium |
| Failures | Number of records that failed |
| Status | PASS or FAIL |

The table supports 20 rows per page and is exportable to CSV.

## Materiality Thresholds

Three governance thresholds are displayed:

- **GL Reconciliation Tolerance** — Default ±0.50%
- **Critical DQ Failures** — Must be zero for clean approval
- **Minimum DQ Score** — Default ≥ 90%

## Warning Banners

- **Critical failures detected** — A red warning appears if any critical-severity checks failed. You must provide documented justification in the approval comments.
- **DQ score below threshold** — An amber warning appears if the score is below the configured minimum.

## Approving This Step

1. Review the GL reconciliation results.
2. Review all data quality check results.
3. If there are critical failures, document your justification in the comment field.
4. Click **Approve Data Quality** or **Reject** with comments.

:::warning
If critical DQ failures exist, the approval still proceeds but requires documented justification. This is recorded in the audit trail for regulatory review.
:::
