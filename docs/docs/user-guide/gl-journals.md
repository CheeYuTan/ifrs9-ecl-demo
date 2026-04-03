---
sidebar_position: 12
title: GL Journals
---

# GL Journals

Generate, post, and manage IFRS 9 ECL double-entry journal entries.

## Purpose

After ECL calculation, the application generates the accounting journal entries needed to recognise the expected credit loss provision in the General Ledger. Journals follow double-entry bookkeeping with proper debit/credit classification by product and stage.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| Total Journals | Count of draft and posted journals |
| Posted Debits | Sum of posted debit entries |
| Posted Credits | Sum of posted credit entries |
| Balance Check | Whether debits equal credits (Balanced / Imbalance) |

## Generating Journals

Click **Generate ECL Journals** to create journal entries for the current project. The system generates entries for:

- **ECL Provision** — Impairment charge to P&L
- **Write-off** — Charge-off of credit-impaired loans
- **Recovery** — Recoveries on previously written-off loans
- **Overlay** — Management overlay adjustments

## Three Tabs

### Journal Entries

A table listing all generated journals:

| Column | Description |
|--------|-------------|
| Journal ID | Unique identifier (monospace format) |
| Type | ECL Provision, Write-off, Recovery, or Overlay |
| Date | Journal date |
| Status | Draft, Posted, or Reversed |
| Debit | Total debit amount |
| Credit | Total credit amount |
| Balance Check | Debit = Credit verification |
| Lines | Number of journal lines |

Click a row to expand the **Journal Detail** showing individual debit and credit lines with account codes, account names, product types, and stages.

**Actions:**
- **Post** (draft journals) — Posts the journal to the GL with a green confirmation
- **Reverse** (posted journals) — Creates a reversing entry with a confirmation dialog

### Trial Balance

A summary table showing the net effect across all GL accounts:

| Column | Description |
|--------|-------------|
| Code | Account code |
| Account Name | GL account name |
| Type | Asset, Contra-Asset, Expense, or Income |
| Debit | Total debit balance |
| Credit | Total credit balance |
| Balance | Net balance |

A totals row and balance indicator confirm whether the trial balance is in balance.

### Chart of Accounts

A reference table listing all ECL-related GL accounts:

| Column | Description |
|--------|-------------|
| Code | Account code |
| Account Name | Name |
| Type | Account type |
| Parent Account | Hierarchical parent |
| ECL Related | Whether the account is used for ECL entries |
