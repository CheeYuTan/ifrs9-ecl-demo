---
sidebar_position: 9
title: "Step 8: Sign Off"
---

# Step 8: Sign Off

Final review, attestation, and irreversible project lock.

**IFRS 9 Reference:** IFRS 7.35F-35N — credit risk disclosures.

## What This Step Does

This is the final step where an authorised signatory reviews the complete ECL calculation, attests to its compliance with IFRS 9, and locks the project. Once signed off, the project is immutable — all data, overlays, and configurations are frozen.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| Final ECL | Total Expected Credit Loss after overlays |
| Net Carrying Amount | GCA minus ECL |
| Coverage % | ECL as a percentage of GCA |
| Overlay % | Overlay impact as a percentage of Model ECL |

## Review Sections

### Applied Management Overlays

Lists all overlays from Step 7 with uplift/reduction badges and the net overlay total.

### ECL Attribution Waterfall

A decomposition chart showing what drove the ECL movement:

- Opening balance → New originations → Derecognitions → Stage transfers → Model changes → Macro changes → Overlays → Write-offs → Discount unwind → **Closing balance**

Click **Recompute** to recalculate the attribution from the underlying data.

### IFRS 7.35I Loss Allowance Reconciliation

A regulatory disclosure table showing the movement analysis across Stage 1, 2, and 3:

| Movement | Stage 1 | Stage 2 | Stage 3 | Total |
|----------|---------|---------|---------|-------|
| Opening balance | ... | ... | ... | ... |
| New originations | ... | ... | ... | ... |
| Derecognitions/repayments | ... | ... | ... | ... |
| Stage transfers | ... | ... | ... | ... |
| Model parameter changes | ... | ... | ... | ... |
| Management overlays | ... | ... | ... | ... |
| Write-offs | ... | ... | ... | ... |
| Closing balance | ... | ... | ... | ... |

### IFRS 7 Disclosure Summary

Product-level table with GCA, Model ECL, Coverage%, and Loan count.

### Loss Allowance by Stage

Stage-level table with Loans, GCA, Loss Allowance, and Coverage%.

### Credit Risk Exposure by Grade

Cross-tabulation of Product, Stage, and Risk Grade with exposure amounts.

### Top 10 Exposures by ECL

The largest individual loan exposures ranked by ECL amount, showing Loan ID, Product, Stage, GCA, ECL, Coverage%, DPD, and Segment.

### Complete Audit Trail

A scrollable log of every action taken on this project, including user, timestamp, and detail.

## Sign-Off Process

1. Review all sections above.
2. Check all **4 attestation boxes**:
   - IFRS 9.5.5 methodology compliance
   - Management overlays reviewed and reasonable
   - Stress testing scenarios reviewed by Economic Scenario Committee
   - DQ checks passed and GL reconciliation within materiality
3. Enter the **Prepared By** name (CFO / Head of Finance).
4. Click **Sign Off & Lock Project**.
5. Confirm in the dialog: "This action cannot be undone."

## After Sign-Off

- The project is **locked** and displayed with a green "Signed Off" badge.
- A **SHA-256 hash** is computed over the project state for tamper detection.
- **GL journal entries** are auto-generated and available for posting (see [GL Journals](gl-journals)).
- The hash can be verified at any time via the status banner.

:::warning
Sign-off is irreversible. Once locked, no data, overlays, or configurations can be modified. Ensure all reviews are complete before signing off.
:::
