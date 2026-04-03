---
slug: /
sidebar_position: 1
title: Overview
---

# IFRS 9 Expected Credit Losses

An enterprise platform for calculating Expected Credit Losses (ECL) under IFRS 9, built on **Databricks Apps** with **Lakebase** (managed PostgreSQL) and **Unity Catalog**.

## What is this?

This application implements the full IFRS 9 ECL calculation workflow — from data ingestion through satellite model calibration, Monte Carlo simulation, stress testing, management overlays, and final sign-off with GL journal generation.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React SPA (Frontend)               │
│  8-Step Workflow │ Admin Panel │ Analytics Pages      │
├─────────────────────────────────────────────────────┤
│                FastAPI (Backend API)                  │
│  Projects │ Data │ Models │ Simulation │ Reports     │
├─────────────────────────────────────────────────────┤
│           Lakebase (Managed PostgreSQL)               │
│  Projects │ Config │ Model Registry │ Audit Trail    │
├─────────────────────────────────────────────────────┤
│         Unity Catalog + Delta Lake                    │
│  Loan Tape │ Macro Scenarios │ Payment History       │
├─────────────────────────────────────────────────────┤
│              Databricks Platform                      │
│  Jobs │ Compute │ OAuth │ Secrets                    │
└─────────────────────────────────────────────────────┘
```

## Key Capabilities

| Capability | Description |
|-----------|-------------|
| **8-Step ECL Workflow** | Sequential workflow from project creation to sign-off |
| **8 Satellite Models** | Linear, Logistic, Polynomial, Ridge, Random Forest, XGBoost, Elastic Net, Gradient Boosting |
| **Monte Carlo Simulation** | Up to 50,000 simulations with PD-LGD correlation |
| **8 Macro Scenarios** | Baseline through Tail Risk with configurable weights |
| **Management Overlays** | Temporary/permanent adjustments with approval workflow |
| **Model Registry** | Full lifecycle: Draft → Review → Approved → Active → Retired |
| **GL Journal Generation** | Automated debit/credit entries by product and stage |
| **IFRS 7 Reporting** | Regulatory disclosure templates |
| **Audit Trail** | Immutable log of all actions with chain verification |
| **Light & Dark Mode** | Full dual-theme support across all 72+ components and pages |

## Personas

This documentation is organized for two primary audiences:

- **Users** (Credit Risk Analysts, CFOs, CROs) — See the [User Guide](/user-guide/overview) for the 8-step ECL workflow
- **Administrators** — See the [Admin Guide](/admin-guide/overview) for configuration, data mapping, and system management

## Quick Links

- [Installation](/getting-started/installation) — Deploy on Databricks Apps
- [Quick Start](/getting-started/quick-start) — Run your first ECL calculation
- [IFRS 9 Concepts](/reference/ifrs9-concepts) — Background on ECL stages, PD/LGD/EAD
- [API Reference](/reference/api) — Backend API endpoints
- [Data Model](/reference/data-model) — Source table specifications
