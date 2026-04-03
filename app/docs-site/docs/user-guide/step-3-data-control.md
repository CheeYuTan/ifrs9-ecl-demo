---
sidebar_position: 4
title: "Step 3: Data Control"
description: "Running quality checks and approving data through maker-checker review."
---

# Step 3: Data Control

Data Control is the quality gate of the ECL workflow. Before any models are run or ECL is calculated, the platform performs automated data quality checks and General Ledger reconciliation. You review the results and formally approve (or reject) the data through a maker-checker process. This step ensures that IFRS 9 calculations are built on a reliable, reconciled data foundation.

:::info Prerequisites
- Completed [Step 2: Data Processing](step-2-data-processing)
- **Analyst** or **Risk Manager** role for reviewing results
- A second authorized user may be required for maker-checker approval (depending on your organization's governance policy)
:::

## What You'll Do

On this page you will review the Data Quality (DQ) score, examine individual quality check results, verify the GL reconciliation, understand the materiality thresholds, and then approve or reject the data.

## Step-by-Step Instructions

### 1. Check the Summary KPIs

Four KPI cards at the top give you an immediate assessment:

| KPI | What It Shows | When to Investigate |
|-----|--------------|---------------------|
| **DQ Score** | The percentage of data quality checks that passed (e.g., 96%) | Red if below the configured threshold (default: 90%) |
| **GL Reconciliation** | How many product-level GL reconciliations passed | Amber if any product fails reconciliation |
| **Critical Failures** | Count of quality checks with "Critical" severity that failed | Red if any critical failure — these must be resolved before proceeding |
| **Step Status** | Current approval state of this step | Green when approved, Amber when pending |

![Data Control summary](/img/screenshots/step-3-data-control.png)
*The Data Control page showing DQ Score, GL Reconciliation status, and quality check results.*

### 2. Review the GL Reconciliation

The **GL Reconciliation** table (per IFRS 7.35I) compares the loan tape balance against the General Ledger for each product type:

| Column | What It Shows |
|--------|--------------|
| **Product** | The loan product type |
| **GL Balance** | The balance recorded in the General Ledger |
| **Loan Tape Balance** | The balance from the imported loan data |
| **Variance** | The difference in currency terms |
| **Variance %** | The difference as a percentage of the GL balance |
| **Status** | PASS if within tolerance, FAIL if variance exceeds the threshold |

A product passes reconciliation when its variance percentage falls within the configured tolerance (default: ± 0.50%). Variances beyond this threshold require Finance sign-off before the data can be approved.

:::tip Why GL Reconciliation Matters
IFRS 7.35I requires institutions to provide a reconciliation from the opening to closing balance of the loss allowance. If your loan data does not agree with the General Ledger, the ECL calculation will be based on different figures than what appears in your financial statements — a finding that auditors will flag.
:::

### 3. Review the Data Quality Checks

The **Data Quality Checks** table shows every automated check that was run:

| Column | What It Shows |
|--------|--------------|
| **Check ID** | Unique identifier for the check (e.g., D1, D2, D7) |
| **Category** | Grouping: Data Integrity, Model Reasonableness, or Domain Accuracy |
| **Description** | What the check validates |
| **Severity** | **Critical** (red), **High** (amber), or **Medium** (grey) |
| **Failures** | How many records failed this check |
| **Status** | PASS or FAIL |

Key checks to watch for:

| Check | What It Validates | Severity |
|-------|-------------------|----------|
| **Scenario Weights** | All macroeconomic scenario weights sum to 1.0 (within ± 0.001) | Critical |
| **PD Range** | Every loan's Probability of Default is between 0 and 1 | Critical |
| **LGD Range** | Every product's Loss Given Default is between 0 and 1 | Critical |
| **EIR Positive** | Every loan's Effective Interest Rate is greater than zero | Critical |
| **GCA Positive** | Gross Carrying Amount is positive for non-written-off loans | Critical |
| **Stage 3 / DPD Consistency** | Stage 3 loans have Days Past Due of 90 or more | High |
| **Stage 1 / DPD Consistency** | Stage 1 loans have Days Past Due under 30 | High |
| **Origination Before Reporting** | Every loan's origination date precedes the reporting date | Critical |

:::warning Critical Failures Block Approval
If any check with **Critical** severity has failed, the platform displays a warning banner and requires you to document a justification in the comments field before approval can proceed. Critical failures indicate fundamental data problems that could invalidate the ECL calculation.
:::

### 4. Understand the Materiality Thresholds

Three threshold tiles show the governance rules governing data approval:

| Threshold | Default Value | What It Means |
|-----------|--------------|---------------|
| **GL Reconciliation Tolerance** | ± 0.50% | Variances beyond this percentage require Finance sign-off |
| **Critical DQ Failures** | Must be zero | Any critical failure must be resolved or justified before approval |
| **Minimum DQ Score** | ≥ 90.0% | Falling below this threshold triggers a mandatory Data Governance review |

These thresholds are configurable by your administrator. If you believe a threshold needs adjustment for your portfolio, raise this with your Data Governance team.

### 5. Approve or Reject the Data

At the bottom of the page, the **Data Quality & GL Reconciliation Decision** panel allows you to take action:

**To approve:**
1. Review all checks and reconciliation results
2. Optionally add a comment (recommended — explain any observations)
3. Click **Approve Data Quality**

**To reject:**
1. Enter a comment explaining what needs to be fixed (required for rejection)
2. Click **Reject**

Rejection sends the workflow back for rework. The rejection reason and your comment are recorded in the audit trail. The data team can then correct the issue and re-run data processing.

![Approval form](/img/screenshots/step-3-approval-form.png)
*The approval/rejection panel. Comments are required for rejection and recommended for approval.*

## Understanding the Results

The DQ score and reconciliation results tell you whether the data is fit for purpose. Use the following decision framework:

**Decision 1: Are there any Critical failures?**
- If **yes** — do not approve. Critical failures (PD outside [0, 1], missing GCA, invalid origination dates) produce mathematically invalid ECL results. Work with your data team to resolve the root cause, re-run data processing, and return to this step.
- If **no** — proceed to Decision 2.

**Decision 2: Is the DQ Score at or above the threshold?**
- If **yes** (e.g., ≥ 90%) and GL reconciliation passes — the data is ready. Approve and proceed to Step 4.
- If **yes** but GL reconciliation has failures — investigate the variance. Small variances near the tolerance boundary (e.g., 0.48% against a 0.50% threshold) may be timing differences between the loan tape extract and the GL close. Large variances indicate the loan tape and GL are fundamentally out of sync. Escalate to Finance before approving.
- If **no** (DQ Score below threshold) — review which checks failed and their severity. Medium-severity failures affecting a small number of records (e.g., 3 of 79,000 loans with missing collateral values) may be acceptable with a documented justification. Systemic failures affecting many records indicate a data pipeline problem — reject and request a fix.

**Decision 3: Can you explain every failing check?**
- If **yes** — document your reasoning in the approval comment and approve. This creates an auditable record that the failures were reviewed and deemed non-material.
- If **no** — do not approve. Unexplained data quality failures are a red flag for auditors. Investigate further or escalate to your Data Governance team before proceeding.

## Tips & Best Practices

:::tip Document Your Reasoning
Even when all checks pass, add a brief comment explaining your review (e.g., "All DQ checks passed. GL reconciliation within tolerance. Stage distribution consistent with prior quarter."). This creates a clear record for auditors that the data was actively reviewed, not rubber-stamped.
:::

:::tip Review Severity Levels
Not all failures are equal. A **Medium** severity check failing on a few records (e.g., a minor data completeness issue) is very different from a **Critical** failure. Focus your investigation on Critical and High severity failures first.
:::

:::warning Maker-Checker Discipline
In many organizations, the person who processed the data (Step 2) should not be the same person who approves it (Step 3). If your organization enforces segregation of duties at this stage, ensure a second reviewer performs the approval. The platform records who approved and when.
:::

:::caution Audit Expectations
External auditors typically expect to see documented evidence that data quality was assessed before ECL calculation. The DQ score, check results, GL reconciliation, and approval comments on this page form that evidence. A blank approval comment — even when all checks pass — may prompt an auditor to ask how the review was performed.
:::

## What's Next?

Proceed to [Step 4: Satellite Models](step-4-satellite-model) to select the macroeconomic models that will link PD and LGD to forward-looking economic scenarios.
