---
sidebar_position: 10
title: Model Registry
---

# Model Registry

Central inventory for all IFRS 9 model versions with full lifecycle management and governance.

## Purpose

The Model Registry tracks every PD, LGD, EAD, and Staging model through its lifecycle — from initial draft through review, approval, production deployment, and eventual retirement. It enforces maker-checker governance and maintains a complete audit trail.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| Total Models | All registered models across all statuses |
| Active Models | Models currently in production use |
| Champions | Models designated as the primary model for their type |
| Pending Review | Models awaiting approval |

## Model Lifecycle

```
Draft → Pending Review → Approved → Active → Retired
```

| Status | Meaning |
|--------|---------|
| Draft | Initial registration, under development |
| Pending Review | Submitted for review by a validator |
| Approved | Validated and approved, ready for deployment |
| Active | Currently deployed in production |
| Retired | No longer in active use, retained for audit |

## Registering a Model

Click **Register Model** in the header to expand the registration form:

| Field | Description |
|-------|-------------|
| Model Name | Descriptive name (e.g., "PD Logistic v2.1") |
| Model Type | PD, LGD, EAD, or Staging |
| Algorithm | Model algorithm (e.g., Logistic Regression, XGBoost) |
| Version | Numeric version |
| Product Type | Which product this model covers |
| Created By | Model developer name |
| Description | Model purpose and methodology |
| Performance Metrics | AUC, Gini, KS, Accuracy, RMSE, R² (optional) |

## Model Comparison

Select 2–3 models using the checkboxes in the inventory table to enable side-by-side comparison:

- **Metric Comparison Table** — All performance metrics with the best value highlighted
- **Radar Chart** — Visual comparison across 3+ metrics

## Model Inventory

The main table lists all registered models with filtering by Type and Status. Columns include Model Name, Type, Version, Algorithm, Status, AUC, Gini, and Created date.

Click any row to open the **Detail Panel** showing:

- Full metadata and performance metrics
- Model parameters (JSON)
- Training data information
- Lifecycle action buttons (Submit, Approve, Reject, Promote, Retire)
- **Set as Champion** button for approved/active models
- Audit trail timeline

## Champion Designation

Each model type can have one **Champion** — the primary model used for ECL calculation. Promote any approved or active model to champion status. The previous champion is automatically demoted.
