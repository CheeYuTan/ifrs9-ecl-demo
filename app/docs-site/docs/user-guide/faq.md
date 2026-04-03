---
sidebar_position: 18
title: "FAQ"
description: "Frequently asked questions about using the IFRS 9 ECL Platform."
---

# Frequently Asked Questions

Answers to the most common questions from business users, organised by topic. For technical questions about the API or system architecture, see the [Developer Reference](/developer/architecture).

## General

### What is IFRS 9 ECL?

IFRS 9 is the International Financial Reporting Standard for financial instruments, effective since January 2018. Section 5.5 requires institutions to measure **Expected Credit Losses (ECL)** — a forward-looking estimate of credit losses on financial assets. Unlike the previous standard (IAS 39), which recognised losses only when they occurred ("incurred loss"), IFRS 9 requires recognition of expected losses from the moment a loan is originated.

### What does this platform do?

The IFRS 9 ECL Platform automates the end-to-end ECL calculation workflow: from loading portfolio data, through statistical modelling and Monte Carlo simulation, to generating accounting journal entries and regulatory reports. It replaces spreadsheet-based approaches with an auditable, governed, and reproducible process.

### Who is this platform for?

The platform serves three primary audiences:

| Role | What They Do |
|---|---|
| **Credit Risk Analysts** | Run ECL calculations, train models, analyse results |
| **Risk Managers / Reviewers** | Review and approve models, overlays, and sign-offs |
| **Finance / Accounting** | Generate and post GL journal entries, produce IFRS 7 disclosures |

Auditors also use the platform in read-only mode to verify the governance trail.

### What are the four user roles?

| Role | Access Level |
|---|---|
| **Admin** | Full access — user management, configuration, all approvals |
| **Risk Manager** | Run calculations, review and approve models and overlays, sign off projects |
| **Analyst** | Run calculations, train models, create overlays, generate reports |
| **Auditor** | Read-only access to all data, models, approvals, and audit trails |

See [Approval Workflow](approval-workflow) for the full permissions matrix.

## The 8-Step Workflow

### What is the 8-step workflow?

The platform organises the ECL process into eight sequential steps:

1. **Create Project** — define the reporting period and portfolio scope
2. **Data Processing** — load and validate portfolio data
3. **Data Control** — quality checks and maker-checker approval of input data
4. **Satellite Models** — train and compare macroeconomic regression models
5. **Model Execution** — run Monte Carlo simulation to calculate ECL
6. **Stress Testing** — sensitivity, vintage, concentration, and migration analysis
7. **Overlays** — apply management adjustments with documented rationale
8. **Sign-Off** — final attestation with hash verification

See [Workflow Overview](workflow-overview) for a visual guide.

### Do I have to follow the steps in order?

Yes. Each step depends on the output of the previous step. You cannot run the Monte Carlo simulation (Step 5) without first processing data (Step 2) and training satellite models (Step 4). The platform enforces this sequence.

### Can I go back and change something in an earlier step?

You can re-run earlier steps, but this will invalidate all subsequent steps. For example, if you re-process data in Step 2, you will need to re-run Steps 3 through 8. The platform warns you before invalidating downstream results.

### How long does a full ECL run take?

The Monte Carlo simulation in Step 5 is the most computationally intensive step. For a portfolio of 79,000 loans with 1,000 simulation paths and 9 macroeconomic scenarios, the simulation typically completes in 2–5 minutes. The other steps are interactive and take seconds to minutes depending on portfolio size.

## Models and Simulation

### What is a satellite model?

A satellite model is a regression model that links a credit risk parameter (PD or LGD) to macroeconomic variables (GDP growth, unemployment, interest rates, etc.). The platform supports eight model types: Linear, Ridge, Lasso, ElasticNet, Random Forest, Gradient Boosting, XGBoost, and SVR. See [Step 4: Satellite Models](step-4-satellite-model).

### How does Monte Carlo simulation work?

The simulation generates thousands of possible future scenarios by sampling random shocks to PD and LGD, correlated using Cholesky decomposition. For each scenario, it calculates the ECL for every loan at every future quarter, then averages across all scenarios to produce the expected (probability-weighted) loss. See [Step 5: Model Execution](step-5-model-execution) for a business-friendly explanation.

### What are the three impairment stages?

| Stage | ECL Horizon | When It Applies |
|---|---|---|
| **Stage 1** | 12-month ECL | Performing loans — no significant deterioration since origination |
| **Stage 2** | Lifetime ECL | Loans where credit risk has significantly increased (SICR triggered) |
| **Stage 3** | Lifetime ECL (credit-impaired) | Loans in default or individually identified as impaired |

The key difference is the measurement horizon: Stage 1 uses a 12-month window, while Stages 2 and 3 use the full remaining life of the loan.

### What triggers a loan moving from Stage 1 to Stage 2?

A Significant Increase in Credit Risk (SICR) triggers the transfer. The platform evaluates SICR using quantitative criteria (e.g., PD has increased by more than a defined threshold since origination) and backstop criteria (e.g., more than 30 days past due). See [Step 3: Data Control](step-3-data-control) for details on how SICR is assessed.

### What is the difference between PD, LGD, and EAD?

| Parameter | Definition | Range |
|---|---|---|
| **PD** (Probability of Default) | The likelihood that a borrower will default within the measurement horizon | 0% to 100% |
| **LGD** (Loss Given Default) | The percentage of exposure that will be lost if default occurs, after recoveries | 0% to 100% |
| **EAD** (Exposure at Default) | The outstanding amount at the point of default, including undrawn commitments | Currency amount |

ECL = PD × LGD × EAD × Discount Factor. See [ECL Attribution](attribution) for how each parameter drives changes in the total provision.

## Results and Reporting

### How do I know if the ECL calculation is correct?

Several validation mechanisms are built into the platform:

- **Convergence diagnostics** in Step 5 show whether the Monte Carlo simulation has run enough paths to produce stable results
- **Backtesting** compares model predictions against actual outcomes using the EBA traffic light system. See [Backtesting](backtesting)
- **Reconciliation checks** in ECL Attribution verify that the movement from opening to closing ECL is fully explained. See [ECL Attribution](attribution)
- **Trial balance** in GL Journals confirms that debits equal credits. See [GL Journals](gl-journals)

### What reports does the platform generate?

The platform produces five report types for regulatory and management purposes:

1. **IFRS 7 Disclosure** — loss allowance reconciliation, gross carrying amounts by stage, ECL movement
2. **ECL Movement** — period-over-period changes in ECL by product and stage
3. **Stage Migration** — how loans moved between stages during the period
4. **Sensitivity Analysis** — ECL under different scenario weightings
5. **Concentration Risk** — ECL exposure by segment, geography, or product

See [Regulatory Reports](regulatory-reports) for details on each report and export formats.

### Can I export data?

Yes. Reports can be exported as PDF (for formal distribution) or CSV (for further analysis in Excel or other tools). The export function is available on the Regulatory Reports page.

## Overlays and Adjustments

### What is a management overlay?

A management overlay is a post-model adjustment to the ECL calculation. IFRS 9 permits (and regulators expect) institutions to apply expert judgement when the model does not fully capture known risks — for example, emerging sector-specific stress not yet reflected in macroeconomic data. See [Step 7: Overlays](step-7-overlays).

### When should I use an overlay?

Common reasons for overlays include:

- Emerging risks not captured by historical data (e.g., a new regulatory change affecting a sector)
- Known model limitations (e.g., the model does not differentiate between geographic regions)
- Sector-specific stress (e.g., energy sector downturn not reflected in the base macroeconomic scenario)
- Post-model adjustments required by management or the board

Every overlay must include a documented rationale and requires approval through the [Approval Workflow](approval-workflow).

### Can overlays be negative (reducing ECL)?

Yes, but negative overlays receive additional scrutiny. Regulators view ECL reductions with caution, so the rationale for a negative overlay must be particularly well-documented. The platform flags negative overlays with a warning indicator.

## Governance and Audit

### How does the platform maintain an audit trail?

Every action is recorded with the user identity and timestamp: who ran the calculation, who approved the model, who posted the journal, who signed off the project. The approval history is immutable — entries cannot be edited or deleted after creation.

### What is hash verification in the sign-off process?

When a project is signed off, the platform computes a cryptographic hash of the ECL results. This hash serves as a tamper-evident seal — if any underlying data or calculation is modified after sign-off, the hash will no longer match, and the platform flags the discrepancy. See [Step 8: Sign-Off](step-8-sign-off).

### Can I re-open a signed-off project?

No. Once signed off, a project is immutable. If corrections are needed, create a new project for the same reporting period. The original project and its audit trail remain permanently in the system.

## Troubleshooting

### The simulation seems stuck — what should I do?

Check the convergence monitor on the Step 5 page. The simulation may still be running (progress bar advancing) or may have encountered a convergence issue. If the coefficient of variation is not decreasing after many paths, try increasing the number of simulation paths or reviewing input data for anomalies.

### My ECL numbers seem too high (or too low) — where do I start?

1. Check **stage distribution** — are too many loans being classified as Stage 2 or 3? Review the SICR thresholds in [Step 3: Data Control](step-3-data-control)
2. Check **PD calibration** — are PDs consistent with historical default rates? Run [Backtesting](backtesting) to validate
3. Check **LGD assumptions** — are recovery rates realistic? Review [collateral haircuts](advanced-features)
4. Check **scenario weights** — is the pessimistic scenario over-weighted? Review [Step 6: Stress Testing](step-6-stress-testing)
5. Check **overlays** — are overlays increasing ECL beyond what the model suggests? Review [Step 7: Overlays](step-7-overlays)

### I cannot approve a request — the button is greyed out

You need the **Approver** or **Admin** role to approve requests. If you are a Reviewer, you can submit items for approval but cannot approve them yourself. Contact your administrator to check your role assignment.

### The build/deploy failed — what should I do?

Documentation site build issues are handled by the system administrator. See the [Admin Guide: Troubleshooting](/admin-guide/troubleshooting) for common build errors and resolutions.

## What's Next?

- [Workflow Overview](workflow-overview) — visual guide to the complete 8-step process
- [Approval Workflow](approval-workflow) — governance and segregation of duties
- [ECL Attribution](attribution) — understand what drives ECL changes
- [Regulatory Reports](regulatory-reports) — generate IFRS 7 disclosures and management reports
