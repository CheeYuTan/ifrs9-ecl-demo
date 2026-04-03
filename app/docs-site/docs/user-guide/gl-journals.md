---
sidebar_position: 13
title: "GL Journals"
description: "Double-entry ECL provisioning journal entries, trial balance review, and posting to the general ledger."
---

# GL Journals

GL Journals translate ECL calculations into the accounting entries that flow into your institution's general ledger. Every ECL provision, management overlay, and write-off generates a balanced double-entry journal: a debit to an expense account and a credit to a contra-asset provision account. The platform ensures that every journal balances to the penny, maintains a complete audit trail, and follows the posting workflow that Finance teams expect — draft, review, post.

:::info Prerequisites
- Completed and signed-off ECL project (see [Step 8: Sign-Off](step-8-sign-off))
- **Risk Manager** or **Admin** role to generate and post journals
- **Analyst** role sufficient for viewing journals and trial balance
- **Auditor** role provides read-only access to all posted journals
:::

## What You'll Do

On this page you will generate journal entries from a signed-off ECL project, review the entries line by line, understand the chart of accounts, post journals to the general ledger, review the trial balance, and reverse journals if corrections are needed.

## The Chart of Accounts

The platform uses a dedicated chart of accounts for ECL provisioning. These accounts are pre-configured and map to your institution's general ledger:

| Account Code | Account Name | Type | Purpose |
|--------------|-------------|------|---------|
| **1200** | Loans and Advances | Asset | The portfolio's gross carrying amount — the total outstanding balance |
| **1210** | Stage 1 ECL Provision | Contra-Asset | Allowance for performing loans (12-month ECL) |
| **1220** | Stage 2 ECL Provision | Contra-Asset | Allowance for underperforming loans (lifetime ECL) |
| **1230** | Stage 3 ECL Provision | Contra-Asset | Allowance for defaulted loans (credit-impaired lifetime ECL) |
| **1240** | Management Overlay Provision | Contra-Asset | Allowance for management adjustments beyond the model |
| **4100** | ECL Impairment Charge | Expense | Income statement charge for ECL provisions |
| **4110** | ECL Recovery Income | Income | Reversal of prior provisions when credit quality improves |
| **4120** | Write-off Expense | Expense | Income statement charge for irrecoverable loans |
| **4130** | Overlay Adjustment Expense | Expense | Income statement charge for management overlays |

The contra-asset accounts (1210–1240) reduce the carrying amount of loans on the balance sheet. The net carrying amount reported in financial statements is: Loans and Advances (1200) minus the sum of all provision accounts.

:::tip Mapping to Your GL
The account codes shown here are the platform's internal codes. Your Finance team will need to map these to your institution's actual chart of accounts. The account code structure (12xx for balance sheet, 41xx for income statement) follows a common pattern, but your institution's codes will differ.
:::

## Step-by-Step Instructions

### 1. Navigate to GL Journals

From the main navigation, select **GL Journals**. The page has three tabs:

- **Journals** — view, generate, post, and reverse journal entries
- **Trial Balance** — aggregated view of all posted journals
- **Chart of Accounts** — the GL master list

### 2. Generate Journal Entries

Click **Generate Journals** on the Journals tab. The platform will:

1. Read the signed-off ECL calculations for each product type and stage
2. Read any management overlays applied in [Step 7](step-7-overlays)
3. Identify any loans qualifying for write-off (Stage 3, 180+ days past due)
4. Create balanced double-entry journal entries for each category
5. Save all entries in **Draft** status

The generated journals appear in the journal list below.

![GL Journals list view](/img/screenshots/gl-journals-list.png)
*The GL Journals page showing generated journal entries with status badges and balance indicators.*

### 3. Understand the Journal Types

The platform generates three types of journal entries:

#### ECL Provision Journals

One journal entry for each product type and stage combination. For example, if your portfolio has three product types across three stages, up to nine provision journals are created:

| Debit | Credit | Amount |
|-------|--------|--------|
| 4100 — ECL Impairment Charge | 1210 — Stage 1 ECL Provision | Total Stage 1 ECL for this product |
| 4100 — ECL Impairment Charge | 1220 — Stage 2 ECL Provision | Total Stage 2 ECL for this product |
| 4100 — ECL Impairment Charge | 1230 — Stage 3 ECL Provision | Total Stage 3 ECL for this product |

The debit increases the impairment expense on the income statement. The credit increases the provision (contra-asset) on the balance sheet, reducing the net carrying amount of loans.

#### Management Overlay Journals

One journal entry for each overlay applied in Step 7:

| Debit | Credit | Amount |
|-------|--------|--------|
| 4130 — Overlay Adjustment Expense | 1240 — Management Overlay Provision | Overlay amount |

#### Write-off Journals

One journal for loans identified for write-off:

| Debit | Credit | Amount |
|-------|--------|--------|
| 4120 — Write-off Expense | 1230 — Stage 3 ECL Provision | Write-off amount |

Write-offs debit the expense account and credit (reduce) the Stage 3 provision, because the provision is no longer needed — the loss has been realised.

### 4. Review Journal Details

Click any journal entry to expand its detail view. Each journal shows:

| Field | What It Shows |
|-------|---------------|
| **Journal ID** | Unique identifier for audit reference |
| **Date** | The journal date (typically the reporting date of the ECL project) |
| **Type** | ECL Provision, Overlay, or Write-off |
| **Status** | Draft, Posted, or Reversed |
| **Balance Check** | Green checkmark if debits equal credits; red warning if imbalanced |
| **Line Items** | Each debit and credit line with account code, account name, amount, product type, and stage |

:::warning Always Verify Balance
Every journal must balance — total debits must equal total credits. The platform validates this automatically, but review the balance indicator before posting. An imbalanced journal cannot be posted.
:::

### 5. Post Journals to the General Ledger

Posting moves a journal from Draft to Posted status, making it part of the official accounting record:

1. Review the journal detail to confirm all line items are correct
2. Click **Post** on the journal entry
3. The platform validates that debits equal credits
4. If balanced, the status changes to **Posted** and the journal is locked — it can no longer be edited
5. The posting is recorded in the audit trail with the user and timestamp

Only posted journals contribute to the trial balance. Draft journals are working documents that can still be regenerated or deleted.

:::caution Posting Is One-Way
Once posted, a journal cannot be edited or deleted. If a correction is needed, you must **reverse** the journal (creating an offsetting entry) and then generate corrected entries. This preserves the audit trail — every original entry and every correction is permanently recorded.
:::

### 6. Review the Trial Balance

Switch to the **Trial Balance** tab to see the aggregated effect of all posted journals:

| Column | What It Shows |
|--------|---------------|
| **Account Code** | The GL account identifier |
| **Account Name** | Descriptive name |
| **Account Type** | Asset, Contra-Asset, Expense, or Income |
| **Total Debits** | Sum of all debit entries to this account across all posted journals |
| **Total Credits** | Sum of all credit entries to this account across all posted journals |
| **Balance** | Net position (debits minus credits) |

The trial balance should satisfy these checks:

- **Total debits = Total credits** across all accounts (the fundamental accounting equation)
- **Contra-asset balances** (1210–1240) should be negative (credits exceed debits), representing the provision held against the loan portfolio
- **Expense balances** (4100–4130) should be positive (debits exceed credits), representing the income statement charge

![GL trial balance view](/img/screenshots/gl-trial-balance.png)
*The trial balance showing account balances across all posted ECL journals.*

:::tip Reconcile to the ECL Summary
The sum of accounts 1210 + 1220 + 1230 + 1240 should equal the total ECL (including overlays) from the [Step 8: Sign-Off](step-8-sign-off) summary. If these figures do not match, investigate before proceeding.
:::

### 7. Reverse a Journal (Corrections)

If a posted journal needs to be corrected:

1. Find the journal in the Journals tab
2. Click **Reverse** — the platform creates a new journal with all debits and credits swapped
3. The reversal journal is automatically posted
4. The original journal's status changes to **Reversed**
5. Both the original and reversal remain in the audit trail

After reversing, generate corrected journal entries from the updated ECL calculation.

### 8. Review the Chart of Accounts

The **Chart of Accounts** tab displays the complete GL master list:

- All accounts with their codes, names, types, and parent relationships
- ECL-related accounts are highlighted for easy identification
- The hierarchy shows how accounts roll up (e.g., 1210, 1220, 1230, 1240 are children of 1200)

## Understanding Double-Entry Accounting for ECL

For readers less familiar with accounting mechanics, here is how ECL provisioning works in the general ledger:

**When ECL is first recognised** (e.g., $1 million Stage 1 provision):
- The **income statement** shows a $1 million impairment charge (account 4100) — this reduces profit
- The **balance sheet** shows a $1 million provision (account 1210) — this reduces the carrying amount of loans

**When ECL increases** (e.g., loans migrate from Stage 1 to Stage 2):
- Additional impairment charge is debited to 4100
- The Stage 2 provision (1220) is credited with the increased amount
- Simultaneously, the Stage 1 provision (1210) may be reduced if those loans no longer need a Stage 1 allowance

**When ECL decreases** (e.g., credit quality improves and loans cure back to Stage 1):
- Recovery income is credited to 4110
- The relevant provision account is debited (reduced)

**When a loan is written off** (irrecoverable):
- Write-off expense is debited to 4120
- The Stage 3 provision (1230) is credited — the provision is released because the loss is now realised, not estimated

## Tips & Best Practices

:::tip Generate Before the Reporting Deadline
Generate journals as soon as the ECL project is signed off. This gives your Finance team time to review, reconcile with the GL, and post before the month-end or quarter-end close.
:::

:::tip Align Journal Dates with the Reporting Period
The journal date defaults to the ECL project's reporting date. Ensure this aligns with your institution's accounting period. Journals dated outside the current accounting period may require special handling in your GL system.
:::

:::warning Reconcile Every Period
The ECL provision balances on the trial balance must reconcile to: (a) the ECL figures on the sign-off page, (b) the IFRS 7 disclosure report, and (c) the general ledger in your core banking system. Any discrepancy must be investigated and resolved before financial statements are finalised.
:::

:::caution Write-off Thresholds
The platform automatically identifies Stage 3 loans with 180+ days past due for write-off journals. Your institution's write-off policy may use different thresholds. Review the write-off journals to confirm they align with your policy before posting.
:::

## What's Next?

- [Regulatory Reports](regulatory-reports) — the IFRS 7 disclosure report references the same ECL figures as the GL journals
- [Step 8: Sign-Off](step-8-sign-off) — verify that journal amounts reconcile to the signed-off ECL summary
- [ECL Attribution](attribution) — understand the drivers behind the ECL movements posted in journals
