---
sidebar_position: 1
title: "What is IFRS 9 ECL?"
description: "An introduction to the IFRS 9 Expected Credit Loss platform — what it does, who it's for, and how it helps your organization achieve compliance."
---

# What is IFRS 9 ECL?

The IFRS 9 ECL Platform is a complete Expected Credit Loss calculation and reporting solution built on Databricks. It helps credit risk teams compute, review, and report impairment provisions under the IFRS 9 Financial Instruments standard.

:::info Who Should Read This
This page is for anyone new to the platform — credit risk analysts, risk managers, finance teams, auditors, and administrators. No technical knowledge required.
:::

## The Problem It Solves

IFRS 9 (Section 5.5) requires financial institutions to recognize credit losses based on forward-looking estimates rather than waiting for losses to occur. This means banks and lenders must:

- Classify every loan into one of **three impairment stages** based on credit risk changes since origination
- Calculate **Expected Credit Losses** using probability-weighted macroeconomic scenarios
- Produce **regulatory disclosures** (IFRS 7) showing how loss allowances changed and why
- Maintain **auditable records** of every model, assumption, and approval decision

Doing this manually or with spreadsheets is error-prone, slow, and difficult to audit. This platform automates the entire process in a governed, transparent workflow.

## How It Works

The platform guides you through an **8-step workflow** — from project creation to final sign-off:

| Step | Name | What Happens |
|:----:|------|-------------|
| 1 | **Create Project** | Define the reporting date, currency, and portfolio scope |
| 2 | **Data Processing** | Import portfolio data and review key performance indicators |
| 3 | **Data Control** | Run quality checks and approve data through maker-checker review |
| 4 | **Satellite Models** | Select macroeconomic models that link PD/LGD to economic conditions |
| 5 | **Model Execution** | Run Monte Carlo simulations to compute probability-weighted ECL |
| 6 | **Stress Testing** | Analyze sensitivity, vintage performance, and concentration risk |
| 7 | **Overlays** | Apply management adjustments with documented rationale |
| 8 | **Sign-Off** | Attest to results, lock the calculation, and generate audit trail |

Each step builds on the previous one, ensuring nothing is skipped and every decision is recorded.

## Key Capabilities

### Three-Stage Impairment Model
Loans are automatically classified into Stage 1 (12-month ECL), Stage 2 (lifetime ECL), or Stage 3 (credit-impaired) based on changes in credit risk since origination. The platform detects Significant Increase in Credit Risk (SICR) and manages stage transfers.

### Forward-Looking Scenarios
ECL calculations incorporate multiple macroeconomic scenarios — base case, optimistic, and pessimistic — each with configurable probability weights. This ensures provisions reflect expected future conditions, not just historical experience.

### Model Governance
Every model follows a controlled lifecycle from Draft through Validation to Champion status. Backtesting with industry-standard metrics (AUC, Gini, KS, PSI) helps ensure models remain fit for purpose.

### Regulatory Reporting
Generate IFRS 7 disclosure reports (paragraphs 35H through 35N), GL journal entries for provisioning, and comprehensive audit trails — all in formats your auditors expect.

### Approval Workflow
A maker-checker process with segregation of duties ensures that the person who runs the model is not the same person who signs off on results. Every approval is hash-verified and immutably logged.

### ECL Attribution
A waterfall analysis decomposes ECL movements between reporting periods into individual drivers — new originations, derecognitions, stage transfers, parameter changes, scenario shifts, overlays, and write-offs — satisfying the IFRS 7.35I reconciliation requirement.

### Markov Chains & Hazard Models
Transition matrices and survival models estimate how borrowers move between credit states over time. These forward-looking tools produce the lifetime PD term structures that feed directly into the ECL calculation.

### Advanced Risk Parameters
Data-driven cure rate analysis, credit conversion factors (CCF) for off-balance-sheet exposures, and collateral haircut estimation replace conservative regulatory defaults with parameters calibrated to your portfolio history.

## Who Uses This Platform

| Role | How They Use It |
|------|----------------|
| **Credit Risk Analysts** | Run the 8-step workflow, review results, apply overlays |
| **Risk Managers** | Approve calculations, review model performance, sign off |
| **Finance / Accounting** | Generate GL journals and regulatory disclosures |
| **Auditors** | Verify calculations via hash integrity checks and audit trails |
| **Administrators** | Configure data sources, manage users, set up models |

## Platform at a Glance

- **79,000+** sample loans across 5 product types
- **8** satellite model types for macroeconomic linking
- **9** configurable scenarios with probability weighting
- **162** API endpoints across 8 functional domains
- **4** user roles with granular permissions (Admin, Risk Manager, Analyst, Auditor)
- Full **light and dark mode** support

## What's Next?

- **New to the platform?** Start with the [Quick Start Guide](quick-start) to create your first ECL project
- **Want the full workflow?** Read the [8-Step ECL Workflow Overview](user-guide/workflow-overview)
- **Setting up the system?** See the [Admin Guide](admin-guide/setup-installation) for installation and configuration
- **Common questions?** Browse the [FAQ](user-guide/faq) for answers organized by topic
