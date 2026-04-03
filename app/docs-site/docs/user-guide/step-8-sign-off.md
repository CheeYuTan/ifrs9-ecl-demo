---
sidebar_position: 9
title: "Step 8: Sign-Off"
description: "Final attestation, hash verification, and locking of the ECL calculation."
---

# Step 8: Sign-Off

Sign-Off is the final step in the ECL workflow. Here, the authorized signatory reviews the complete ECL calculation — including model results, overlays, and supporting analysis — attests that the figures are compliant with IFRS 9, and locks the project. Once signed off, the calculation becomes immutable: no data, parameters, or overlays can be changed. This provides the audit trail integrity that regulators require.

:::info Prerequisites
- Completed [Step 7: Overlays](step-7-overlays)
- All prior steps reviewed and approved
- A different authorized user must perform sign-off (segregation of duties — the user who ran the simulation in Step 5 cannot sign off)
- **CFO**, **Head of Finance**, or equivalent authority required
:::

## What You'll Do

On this page you will review the final ECL summary, examine the ECL attribution waterfall, inspect the complete audit trail, complete a 4-point attestation, and sign off the calculation. After sign-off, you can verify data integrity via hash verification and generate disclosure reports.

## Step-by-Step Instructions

### 1. Review the ECL Disclosure Summary

The top of the page presents the final ECL figures in a disclosure-ready format:

| Column | What It Shows |
|--------|--------------|
| **Product** | Each product type in the portfolio |
| **Gross Carrying Amount** | Total outstanding balance for this product |
| **Model ECL** | ECL from the Monte Carlo simulation |
| **Overlay Adjustments** | Net management adjustments applied |
| **Final ECL** | Model ECL plus overlay adjustments — the figure that will be reported |
| **Coverage Ratio** | Final ECL as a percentage of GCA |
| **Loan Count** | Number of loans in this product |

The **Total** row at the bottom aggregates across all products. This is the headline ECL figure for the reporting period.

![Sign-off ECL summary](/img/screenshots/step-8-summary.png)
*The ECL disclosure summary table showing final provisioning by product.*

### 2. Review the Top 10 Exposures

A table of the ten largest individual loan provisions helps you verify that no single exposure disproportionately drives the total ECL:

| Column | What It Shows |
|--------|--------------|
| **Loan ID** | The individual loan identifier |
| **Product** | The loan product type |
| **GCA** | Outstanding balance for this loan |
| **ECL** | The provision for this specific loan |
| **Coverage %** | ECL as a percentage of the loan's GCA |
| **DPD** | Days Past Due — how overdue the borrower is |
| **Stage** | The IFRS 9 impairment stage |

Single-name concentrations are a key risk indicator. If one loan's ECL represents a significant share of total ECL, ensure it has been individually assessed and the provision is appropriate.

### 3. Examine the Attribution Waterfall

The **ECL Attribution Waterfall** decomposes the movement from the opening balance (prior period's ECL) to the closing balance (this period's final ECL). This is the reconciliation required by IFRS 7.35I:

| Movement | What It Represents |
|----------|-------------------|
| **Opening Balance** | ECL from the prior reporting period |
| **+ New Originations** | ECL for loans that were originated during the period |
| **- Derecognitions / Repayments** | Reduction from loans that were fully repaid or written off during the period |
| **+ Stage Transfers (net)** | Net ECL change from loans moving between Stage 1, 2, and 3 |
| **+ Model Parameter Changes** | ECL change due to updated PD, LGD, or EAD estimates |
| **+ Macro Scenario Changes** | ECL change due to updated macroeconomic forecasts or scenario weights |
| **+ Management Overlays** | Net impact of overlays added in Step 7 |
| **- Write-offs** | Loans that were written off as irrecoverable |
| **+ Unwind of Discount** | Time value of money effect on previously recognized ECL |
| **= Closing Balance** | The final ECL for this reporting period |

The waterfall is displayed as a chart and as a table with amounts broken down by Stage 1, Stage 2, Stage 3, and Total. This breakdown is required for IFRS 7 disclosure and is the primary analysis auditors use to understand ECL movements.

:::tip Prepare Your ECL Movement Narrative
Use the attribution waterfall to prepare the narrative explanation of ECL movements that accompanies financial statements. For example: "Total ECL increased by 12% quarter-over-quarter, primarily driven by stage transfers (+8%) reflecting macroeconomic deterioration in the commercial real estate sector, partially offset by derecognitions (-3%) from the sale of a performing loan portfolio."
:::

### 4. Review the Audit Trail

The **Audit Trail** panel shows every action taken on this project from creation to the current moment:

| Entry Field | What It Records |
|-------------|----------------|
| **Action** | The type of event (e.g., "Project Created", "Simulation Executed", "Overlay Added", "Step Approved") |
| **User** | Who performed the action |
| **Timestamp** | When the action occurred |
| **Detail** | Additional context (e.g., simulation parameters used, overlay rationale, approval comments) |

The audit trail is immutable — entries cannot be edited or deleted. Each entry is linked to the previous one, forming a verifiable chain. This provides the governance evidence that regulators expect: every decision in the ECL process is traceable to a specific person and time.

### 5. Complete the Attestation

The attestation is a formal declaration by the signatory that the ECL calculation meets regulatory standards. Four statements must be individually confirmed:

1. **Methodology Compliance** — "ECL model methodology is compliant with IFRS 9.5.5 and local regulatory requirements"
2. **Overlay Review** — "All management overlays have been individually reviewed and are reasonable and supportable"
3. **Scenario Review** — "Stress testing scenarios have been reviewed by the Economic Scenario Committee"
4. **Data Quality** — "Data quality checks passed and GL reconciliation is within materiality thresholds"

Check each statement to confirm. You cannot sign off until all four are checked.

**Enter the signatory name** — typically the CFO, Head of Finance, or Chief Risk Officer. This name is permanently recorded in the project record and the audit trail.

:::warning Attestation Is a Personal Declaration
By completing the attestation, the signatory is personally affirming that the ECL calculation meets regulatory standards. Ensure all supporting analysis (stress testing, overlay rationale, data quality reports) has been thoroughly reviewed before attesting.
:::

### 6. Verify Segregation of Duties

The platform enforces segregation of duties: the user who ran the Monte Carlo simulation in Step 5 cannot be the same user who signs off in Step 8. If you are the same user, the Sign-Off button will be disabled and a message will explain which other authorized users can perform the sign-off.

This separation ensures that no single individual can both compute and approve the ECL — a fundamental governance control required by most banking regulators.

### 7. Sign Off the Project

Click **Sign Off** to finalize the calculation. The platform will:

1. **Compute a SHA-256 hash** of the entire project state — including all step results, overlays, scenario weights, and parameters
2. **Lock the project** — all steps become read-only; no data, parameters, or overlays can be changed
3. **Record the sign-off** in the audit trail with the signatory name, timestamp, and computed hash
4. **Display a confirmation banner** — a green status bar confirming the project is signed off, showing the signatory, timestamp, and hash

The hash serves as a tamper-detection mechanism. At any point after sign-off, you can click **Verify Hash** to confirm that the project data has not been altered. If the computed hash matches the stored hash, the data is intact. If it does not match, the data has been modified — a serious compliance issue.

### 8. After Sign-Off

Once signed off, the project is available for:

- **Regulatory Reports** — generate IFRS 7 disclosure reports based on the locked figures (see [Regulatory Reports](regulatory-reports))
- **GL Journals** — create general ledger journal entries for the ECL provision (see [GL Journals](gl-journals))
- **Audit Export** — download the complete audit package as a structured file for external auditors

The project remains accessible in read-only mode for reference, comparison, and audit purposes. To calculate ECL for a new reporting period, create a new project in [Step 1](step-1-create-project).

## Understanding the Results

The signed-off ECL represents the institution's official estimate of credit losses for the reporting period. It has passed through eight steps of processing, analysis, and governance:

1. Project scope was defined and anchored to a reporting date
2. Portfolio data was loaded and reviewed
3. Data quality was checked and approved
4. Satellite models were calibrated to link credit risk to economic conditions
5. Monte Carlo simulation computed probability-weighted ECL across scenarios
6. Stress testing validated the robustness of results across multiple dimensions
7. Management overlays captured risks the model could not
8. The final figure was attested and locked with cryptographic verification

This chain of custody — from raw data to signed-off figure — is what distinguishes a compliant IFRS 9 process from an ad-hoc calculation.

## Tips & Best Practices

:::tip Review Everything Before Signing
The sign-off page is your last opportunity to review the complete picture. Check the attribution waterfall for unexpected movements, verify the top 10 exposures, and confirm that overlay rationale is documented. Once signed, corrections require a new project.
:::

:::tip Save the Hash for Your Records
After sign-off, record the SHA-256 hash in your governance documentation. If the hash is later challenged, you can demonstrate that the results have not been tampered with since the date of sign-off.
:::

:::caution Immutability Is Absolute
Once a project is signed off, it cannot be amended, adjusted, or corrected in place. If an error is discovered after sign-off, the institution must create a new project for the same reporting period, document the error and correction, and sign off the revised figures. This is by design — it ensures the integrity of the historical record.
:::

:::warning Segregation of Duties Is Non-Negotiable
If your institution has a small team, ensure at least two authorized users are configured with sign-off permissions. A single-person ECL process where the same individual runs the model and signs off is a governance finding that auditors will flag.
:::

## What's Next?

After sign-off, explore:
- [Regulatory Reports](regulatory-reports) — generate IFRS 7 disclosures based on the signed-off figures
- [GL Journals](gl-journals) — create the accounting entries for ECL provisioning
- [ECL Attribution](attribution) — deep-dive into what drove the ECL movement
