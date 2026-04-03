---
sidebar_position: 1
title: Overview
---

# IFRS 9 ECL Platform

A comprehensive Expected Credit Loss calculation and reporting platform built on Databricks, implementing the IFRS 9 Financial Instruments standard (Section 5.5) for forward-looking credit impairment.

## What It Does

The platform provides an end-to-end workflow for computing, reviewing, and reporting Expected Credit Losses under IFRS 9:

- **3-Stage Impairment Model** — Classify exposures into Stage 1 (12-month ECL), Stage 2 (lifetime ECL, performing), and Stage 3 (lifetime ECL, credit-impaired) with automated SICR detection and stage transfer logic.
- **Monte Carlo Simulation** — Correlated PD-LGD draws using Cholesky decomposition, with configurable scenario weights, correlation matrices, and probability-weighted ECL aggregation.
- **Satellite Models** — Macroeconomic scenario modeling with model comparison, cohort analysis, and drill-down analytics by product, vintage, and credit grade.
- **Model Registry & Governance** — Full model lifecycle management (Draft → Validated → Champion → Retired) with audit trails, status transition validation, and model comparison.
- **Backtesting** — Automated model validation with AUC, Gini, KS, PSI, Brier score, and Hosmer-Lemeshow tests. Basel traffic light classification (Green/Amber/Red).
- **Markov Chains** — Transition matrix estimation, stochastic forecasting, and lifetime PD term structures with absorbing default state modeling.
- **Hazard Models** — Cox proportional hazards, discrete-time, and Kaplan-Meier survival analysis with covariate-adjusted term structures.
- **Regulatory Reporting** — IFRS 7 disclosure reports (35H-35N), GL journal generation, trial balance, and CSV/PDF export.
- **Approval Workflow** — Role-based sign-off with segregation of duties, hash-based data integrity verification, and immutable audit logs.

## Key Features

| Feature | Description |
|---------|-------------|
| 8-Step Workflow | Guided process from project creation through sign-off |
| Project Management | Multiple concurrent ECL projects with independent lifecycle |
| Data Quality Control | Automated validation, data mapping, and quality checks |
| Stress Testing | Scenario-based stress analysis with overlay management |
| Admin Console | Database configuration, table mapping, auto-discovery |
| GL Journals | Double-entry journal generation, posting, reversal, trial balance |
| Period Close | Orchestrated end-of-period pipeline with step dependencies |
| Data Mapping | Unity Catalog schema discovery with AI-suggested column mapping |
| Advanced Analytics | Cure rate estimation, credit conversion factors, collateral haircuts |
| Dark Mode | Full light/dark theme support |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript SPA (Vite) |
| API | FastAPI (Python 3.11) |
| Database | Lakebase (managed PostgreSQL on Databricks) |
| Simulation | NumPy + SciPy (Monte Carlo, Cholesky) |
| Reporting | fpdf2 (PDF generation) |
| Hosting | Databricks Apps |

## Test Coverage

The platform maintains a comprehensive automated test suite:

| Layer | Framework | Tests | Coverage |
|-------|-----------|-------|----------|
| Backend API + Domain + ECL Engine | pytest | 3,838 | 107+ endpoints, 24 domain modules, 9 ECL modules |
| Frontend Components + Pages | Vitest | 497 | 24/24 components, 19/19 pages |
| **Total** | | **4,335** | Full stack |

Key quality metrics:
- Zero regressions across 8 QA audit sprints
- ECL formula verified against hand-calculated values (1e-6 tolerance)
- All 23 domain validation rules tested with positive, negative, and boundary inputs
- 3 production bugs discovered and fixed with regression tests

## Who Is This For

- **Credit Risk Teams** — Compute and review ECL provisions
- **Model Validation** — Backtest and compare models with regulatory metrics
- **Finance / Accounting** — Generate GL journals and regulatory disclosures
- **Auditors** — Verify calculations via hash integrity and audit trails
