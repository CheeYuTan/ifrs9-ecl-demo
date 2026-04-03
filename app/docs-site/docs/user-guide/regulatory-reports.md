---
sidebar_position: 12
title: "Regulatory Reports"
description: "Generate IFRS 7 disclosure reports, review section-by-section content, and export for regulators and auditors."
---

# Regulatory Reports

Regulatory Reports generate the disclosure tables and narratives required by IFRS 7 (Financial Instruments: Disclosures). After an ECL project is signed off, the platform can produce a complete set of IFRS 7 disclosure sections — from credit risk exposure breakdowns to sensitivity analyses — ready for inclusion in financial statements. Reports can be reviewed on-screen, exported as PDF for formal submissions, or downloaded as CSV for further analysis in spreadsheets.

:::info Prerequisites
- Completed and signed-off ECL project (see [Step 8: Sign-Off](step-8-sign-off))
- **Risk Manager** or **Admin** role to generate and finalise reports
- **Analyst** role sufficient for viewing generated reports
- **Auditor** role provides read-only access to all reports
:::

## What You'll Do

On this page you will generate IFRS 7 disclosure reports from a signed-off ECL project, review each disclosure section, understand what each IFRS 7 paragraph requires, export reports in PDF and CSV format, and finalise reports for regulatory submission.

## IFRS 7 Disclosure Sections

The platform generates eight disclosure sections, each mapped to a specific paragraph of IFRS 7. Together, they provide the complete picture regulators and auditors expect:

| IFRS 7 Paragraph | Section Title | What It Discloses |
|-------------------|---------------|-------------------|
| **35F** | Credit Risk Exposure by Grade | Portfolio breakdown by internal credit rating: loan count, gross carrying amount, ECL, and average PD per grade |
| **35H** | Loss Allowance by Stage | ECL and gross carrying amount by IFRS 9 stage (1, 2, 3) with prior-period comparatives and coverage ratios |
| **35I** | Loss Allowance Reconciliation | Waterfall showing how ECL moved from opening to closing balance — the same attribution analysis from [Step 8](step-8-sign-off) |
| **35J** | Collateral and LGD | LGD assumptions by product type, collateral values, and expected recovery rates |
| **35K** | Gross Carrying Amount Changes | Movement in gross carrying amount by product and stage, including originations, derecognitions, and transfers |
| **35L** | Modified Financial Assets | Performing versus non-performing modified assets, stage cures, and modification counts |
| **35M** | Collateral and Credit Enhancements | Recovery rates and estimated collateral coverage by stage and product type |
| **36** | Sensitivity Analysis | Impact on ECL of changes in key assumptions: PD, LGD, EAD, and macroeconomic scenario weights |

:::tip What Auditors Look For
Auditors typically focus on three sections first: **35H** (are the stage balances consistent with prior periods?), **35I** (can management explain every material movement in ECL?), and **36** (how sensitive is ECL to assumption changes?). Ensure these three sections are thoroughly reviewed before finalising.
:::

## Step-by-Step Instructions

### 1. Navigate to Regulatory Reports

From the main navigation, select **Regulatory Reports**. The page displays:

- **Report Type Cards** — five report categories, each with a description and colour-coded icon
- **Generated Reports** — a list of previously generated reports with status badges

### 2. Select a Report Type

The platform supports five report categories:

| Report Type | What It Contains |
|-------------|-----------------|
| **IFRS 7 Disclosure** | The complete set of eight IFRS 7 sections (35F through 36) — this is the primary regulatory report |
| **ECL Movement** | Detailed waterfall of ECL changes by driver (originations, derecognitions, stage transfers, parameter changes, scenarios, overlays, write-offs) |
| **Stage Migration** | Transition matrices showing how loans moved between stages during the reporting period, with migration rates |
| **Sensitivity Analysis** | Standalone sensitivity grids showing ECL impact of ±1% changes in PD, LGD, and EAD |
| **Concentration Risk** | Top exposures by product type, industry segment, and geography — highlights single-name and sector concentrations |

For regulatory filing, generate the **IFRS 7 Disclosure** report. The other four are supporting analyses that provide deeper insight into specific areas.

### 3. Generate the Report

Click **Generate** on the desired report type card. The platform will:

1. Read the signed-off ECL calculations for the selected project
2. Retrieve prior-period data from the most recent finalised report (for comparatives in 35H)
3. Compute all required breakdowns, aggregations, and derived metrics
4. Assemble the sections into a structured report
5. Save the report in **Draft** status

Generation typically completes within a few seconds. The new report appears in the **Generated Reports** list below.

![Regulatory Reports generation page](/img/screenshots/regulatory-reports-generate.png)
*The report generation page showing available report types and previously generated reports.*

### 4. Review the IFRS 7 Disclosure Report

Click a generated report to open the **Report Viewer**. Each IFRS 7 section is displayed as an expandable panel with interactive tables.

#### Section 35F: Credit Risk Exposure by Grade

This table shows how credit risk is distributed across your internal rating scale:

| Column | What It Shows |
|--------|---------------|
| **Credit Grade** | Your internal rating (e.g., AAA, AA, A, BBB, BB, B, CCC, Default) |
| **Loan Count** | Number of loans in this grade |
| **Gross Carrying Amount** | Total outstanding balance |
| **ECL** | Expected credit loss for this grade |
| **Average PD** | Mean probability of default across loans in this grade |

Higher grades should have lower PDs and lower ECL. If a high-grade bucket shows elevated ECL, investigate whether the grading model needs recalibration (see [Backtesting](backtesting)).

#### Section 35H: Loss Allowance by Stage

The core disclosure table showing ECL by IFRS 9 impairment stage:

| Column | What It Shows |
|--------|---------------|
| **Stage** | Stage 1 (12-month ECL), Stage 2 (lifetime ECL), Stage 3 (credit-impaired) |
| **Gross Carrying Amount** | Total exposure in this stage |
| **Loss Allowance (ECL)** | Total ECL provision for this stage |
| **Coverage Ratio** | ECL as a percentage of gross carrying amount |
| **Prior Period ECL** | ECL from the previous reporting period |
| **ECL Movement** | Change in ECL (amount and percentage) |

The coverage ratio is a key indicator: Stage 1 coverage is typically 0.1%–1%, Stage 2 is 2%–10%, and Stage 3 can be 30%–100%. Ratios outside these ranges warrant explanation.

#### Section 35I: Loss Allowance Reconciliation

The waterfall showing what drove ECL changes from opening to closing balance. This is identical to the attribution analysis in [Step 8: Sign-Off](step-8-sign-off) but formatted for disclosure:

- Opening balance → New originations → Derecognitions → Stage transfers → Parameter changes → Scenario changes → Overlays → Write-offs → Unwind of discount → Closing balance

Each line is broken down by Stage 1, Stage 2, Stage 3, and Total.

#### Section 35J: Collateral and LGD

Shows LGD assumptions and collateral coverage by product type. Auditors use this to verify that LGD assumptions are reasonable given the collateral held.

#### Sections 35K–35M: Additional Disclosures

- **35K** — movement in gross carrying amount by product and stage
- **35L** — modified financial assets and their stage distribution
- **35M** — collateral and credit enhancement coverage ratios

#### Section 36: Sensitivity Analysis

Shows how ECL would change if key assumptions were adjusted:

| Scenario | ECL Impact |
|----------|-----------|
| PD increased by 1 percentage point | +$X million |
| PD decreased by 1 percentage point | -$X million |
| LGD increased by 1 percentage point | +$X million |
| LGD decreased by 1 percentage point | -$X million |
| EAD increased by 1 percentage point | +$X million |
| EAD decreased by 1 percentage point | -$X million |

This helps stakeholders understand how robust the ECL figure is to assumption uncertainty.

### 5. Export the Report

Two export formats are available:

- **PDF** — a formatted document with all sections, tables, and charts suitable for regulatory filing or board presentation. Click the **Export PDF** button in the report viewer toolbar.
- **CSV** — tabular data for each section, suitable for loading into spreadsheets for further analysis or reconciliation. Click **Export CSV** to download.

:::tip Use CSV for Reconciliation
Export the CSV and reconcile key figures (total ECL, gross carrying amount by stage) against your general ledger and financial statement working papers. Any discrepancies should be investigated before finalising.
:::

### 6. Finalise the Report

Once the report has been reviewed and is ready for submission:

1. Click **Finalise** — this locks the report. No further edits or regeneration are possible.
2. The status changes from **Draft** to **Final**.
3. The finalisation is recorded in the audit trail with the user and timestamp.

After finalisation, the report can be marked as **Submitted** when it has been formally filed with the regulator.

:::warning Finalisation Is Irreversible
Once finalised, the report cannot be modified. If an error is discovered after finalisation, generate a new report from the same project and finalise the corrected version. The original report remains in the system for audit trail purposes.
:::

## Understanding the Results

The IFRS 7 disclosure report is not just a compliance artefact — it tells the story of your institution's credit risk:

- **35F** shows where credit risk lives across your rating scale
- **35H** shows how much provision you hold against each stage of impairment
- **35I** explains what changed and why — the narrative backbone of your ECL disclosure
- **36** demonstrates that you understand the sensitivity of your estimates

A well-prepared IFRS 7 disclosure should enable a reader to understand the institution's credit risk profile, the adequacy of provisions, and the key uncertainties without needing to ask additional questions.

## Tips & Best Practices

:::tip Generate Early, Review Often
Generate a draft report as soon as the ECL calculation is signed off. Review it with stakeholders (Finance, Risk, Audit) before finalising. Early generation allows time to investigate any unexpected figures.
:::

:::tip Prepare the Narrative Alongside the Numbers
IFRS 7 disclosures are most useful when accompanied by a narrative explaining the key movements. Use the 35I reconciliation to draft explanations such as: "ECL increased by 15% due to stage migration driven by deterioration in the commercial real estate sector."
:::

:::caution Prior-Period Comparatives
The 35H section automatically retrieves prior-period data from the most recent finalised IFRS 7 report for the same portfolio. If this is the first reporting period, prior-period columns will show as zero. Ensure at least one finalised report exists for meaningful comparatives.
:::

## What's Next?

- [GL Journals](gl-journals) — create the accounting entries for the ECL provision disclosed in the report
- [ECL Attribution](attribution) — deeper analysis of what drove ECL movements
- [Step 8: Sign-Off](step-8-sign-off) — revisit the sign-off page to verify the figures match
