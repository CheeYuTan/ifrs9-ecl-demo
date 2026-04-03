---
sidebar_position: 1
title: Overview
---

# User Guide

The IFRS 9 ECL Workflow guides you through eight sequential steps — from project creation to final sign-off — producing auditable, probability-weighted Expected Credit Loss estimates.

## The 8-Step Workflow

| Step | Name | Purpose |
|------|------|---------|
| 1 | [Create Project](create-project) | Define the ECL run scope and reporting date |
| 2 | [Data Processing](data-processing) | Review portfolio data, stage distribution, and data quality |
| 3 | [Data Control](data-control) | Validate data quality checks and GL reconciliation |
| 4 | [Satellite Model](satellite-model) | Calibrate macro-linked models and select champions |
| 5 | [Model Execution](model-execution) | Run Monte Carlo ECL calculation across scenarios |
| 6 | [Stress Testing](stress-testing) | Analyse sensitivity, concentration, and capital impact |
| 7 | [Overlays](overlays) | Apply management post-model adjustments |
| 8 | [Sign Off](sign-off) | Attest, lock the project, and generate GL journals |

## Workflow Rules

- Steps must be completed **in order** — you cannot skip ahead.
- Each step has an **Approve / Reject** gate (except Step 1 and Step 8, which use dedicated actions).
- Approval comments are mandatory and recorded in the audit trail.
- Once Step 8 is signed off, the project is **locked** and immutable.

## Navigation

Use the left sidebar to navigate between steps. The current step is highlighted, and future steps show a lock icon until the prerequisite step is approved. You can always return to a completed step in read-only mode.

## Supporting Pages

Beyond the 8-step workflow, the application includes:

- [Model Registry](model-registry) — Govern model lifecycle (Draft → Active → Retired)
- [Backtesting](backtesting) — Validate PD/LGD model performance with traffic-light scoring
- [GL Journals](gl-journals) — Generate, post, and reverse double-entry journal entries
- [Regulatory Reports](regulatory-reports) — Produce IFRS 7 disclosure packages
- [Approval Workflow](approval-workflow) — Maker-Checker-Approver governance system
