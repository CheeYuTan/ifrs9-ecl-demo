---
sidebar_position: 3
title: Architecture
---

# Architecture

## System Overview

```
┌─────────────────────────────────────────────────┐
│                  Browser (SPA)                   │
│         React + TypeScript + Vite                │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/JSON
┌──────────────────▼──────────────────────────────┐
│              FastAPI Application                  │
│                                                  │
│  ┌──────────┐  ┌────────────┐  ┌─────────────┐  │
│  │  Routes   │  │ Middleware  │  │  ECL Engine │  │
│  │ (20 files)│  │ (req-id,   │  │ (Monte Carlo│  │
│  │          │  │  error-hdl) │  │  Markov,    │  │
│  │          │  │            │  │  Hazard)    │  │
│  └────┬─────┘  └────────────┘  └──────┬──────┘  │
│       │                                │         │
│  ┌────▼────────────────────────────────▼──────┐  │
│  │           backend.py (Data Layer)          │  │
│  │        SQL queries → Lakebase              │  │
│  └────────────────────┬───────────────────────┘  │
└───────────────────────┼──────────────────────────┘
                        │ PostgreSQL protocol
┌───────────────────────▼──────────────────────────┐
│         Lakebase (Managed PostgreSQL)             │
│              Databricks Platform                  │
└──────────────────────────────────────────────────┘
```

## Directory Structure

```
app/
├── app.py                  # FastAPI entrypoint, middleware, static serving
├── backend.py              # Database layer (Lakebase connection pool, queries)
├── ecl_engine.py           # Monte Carlo simulation engine
├── app.yaml                # Databricks Apps deployment config
├── requirements.txt        # Python dependencies
│
├── routes/                 # API route modules (one per domain)
│   ├── projects.py         # Project CRUD, workflow advancement, sign-off
│   ├── data.py             # Portfolio data queries (32 endpoints)
│   ├── setup.py            # Initial setup wizard
│   ├── simulation.py       # Monte Carlo: run, stream, compare
│   ├── satellite.py        # Satellite model selection & cohort analysis
│   ├── models.py           # Model registry: register, promote, compare
│   ├── backtesting.py      # Model validation: run, results, trend
│   ├── markov.py           # Transition matrices, forecasting, lifetime PD
│   ├── hazard.py           # Survival analysis: Cox PH, Kaplan-Meier
│   ├── gl_journals.py      # GL journal generation and posting
│   ├── reports.py          # IFRS 7 disclosure reports, export
│   ├── rbac.py             # Role-based access control
│   ├── audit.py            # Audit trail and config change tracking
│   ├── admin.py            # Database configuration and table management
│   ├── data_mapping.py     # Schema discovery and column mapping
│   ├── advanced.py         # Cure rates, CCF, collateral analytics
│   ├── attribution.py      # ECL attribution analysis
│   ├── period_close.py     # Period close workflow
│   └── jobs.py             # Databricks job management
│
├── middleware/             # Cross-cutting concerns
│   ├── request_id.py       # Request ID injection
│   └── error_handler.py    # Global error handling
│
├── domain/                 # Business logic modules
│   └── ...                 # Workflow, validation, registry, etc.
│
├── frontend/               # React SPA
│   ├── src/
│   │   ├── App.tsx         # Main app with 8-step stepper
│   │   ├── pages/          # 19 page components
│   │   ├── components/     # 30+ shared components
│   │   └── lib/            # API client, config, theme
│   └── ...
│
├── ecl/                    # ECL calculation engine (9 modules)
│   ├── simulation.py       # Orchestration
│   ├── monte_carlo.py      # Cholesky-correlated draws, ECL math
│   ├── aggregation.py      # Result aggregation, percentiles
│   ├── data_loader.py      # Lakebase data loading
│   ├── config.py           # Schema/prefix configuration
│   ├── constants.py        # Base LGD, satellite coefficients
│   ├── defaults.py         # Default parameter generation
│   └── helpers.py          # Convergence, event emission
│
├── reporting/              # IFRS 7 report generation
│   └── _ifrs7_sections_a.py  # Sections 35H-35N
│
└── tests/                  # Test suite (3,838 pytest + 497 vitest)
    ├── unit/               # Unit tests by module
    ├── regression/         # Regression tests for discovered bugs
    └── ...
```

## API Layer

The FastAPI application exposes 107+ REST endpoints organized by domain:

| Route Module | Endpoints | Purpose |
|-------------|-----------|---------|
| `/api/projects/*` | 10 | Project lifecycle, workflow, sign-off |
| `/api/data/*` | 32 | Portfolio queries, ECL summaries, drill-downs |
| `/api/setup/*` | 5 | Database setup wizard |
| `/api/simulate*` | 6 | Monte Carlo simulation (inline, SSE, job) |
| `/api/data/satellite-*` | 12 | Satellite models, cohort analysis |
| `/api/models/*` | 7 | Model registry and governance |
| `/api/backtest/*` | 4 | Backtesting and model validation |
| `/api/markov/*` | 6 | Markov chain transition modeling |
| `/api/hazard/*` | 6 | Hazard/survival models |
| `/api/gl-journals/*` | 7 | General ledger journal entries |
| `/api/reports/*` | 6 | Regulatory reports and export |
| `/api/rbac/*` | 8 | Role-based access and approvals |
| `/api/audit/*` | 5 | Audit trail and integrity |
| `/api/admin/*` | 16 | Database configuration and management |
| `/api/data-mapping/*` | 9 | Schema discovery and column mapping |
| `/api/advanced/*` | 9 | Cure rates, CCF, collateral analytics |
| `/api/period-close/*` | 7 | Period close pipeline orchestration |

## ECL Engine

The core simulation engine (`ecl_engine.py`) implements:

1. **Cholesky-correlated draws** — PD and LGD are drawn jointly using a correlation matrix decomposed via Cholesky factorization
2. **Scenario weighting** — Base, optimistic, and pessimistic macroeconomic scenarios with probability weights that must sum to 1.0
3. **Stage-aware calculation** — ECL = PD x LGD x EAD x Discount Factor, computed differently for each impairment stage
4. **Streaming support** — SSE (Server-Sent Events) for real-time progress reporting during long simulations
5. **Convergence diagnostics** — CV-based stability monitoring across simulation iterations
6. **Numerical stability** — Tested with extreme PD (1e-6), EAD (1e12), and near-unity correlations

## Middleware

| Middleware | Purpose |
|-----------|---------|
| `RequestIDMiddleware` | Injects unique request ID into every response for traceability |
| `ErrorHandlerMiddleware` | Catches unhandled exceptions, returns structured JSON errors |

## Deployment

## Domain Logic Layer

The `domain/` directory contains business logic modules organized into two groups:

**Core Business Logic** (8 modules):
- `workflow.py` — Project state machine and step validation
- `queries.py` — 27 portfolio/ECL query builders
- `attribution.py` — ECL waterfall decomposition (IFRS 7.35I)
- `validation_rules.py` — 23 pre/post-calculation validation checks
- `data_mapper.py` — Column mapping and auto-suggest
- `model_runs.py` — Run history and cohort queries
- `audit_trail.py` — Immutable hash-chained event logging
- `config_audit.py` — Config change tracking and diff

**Analytical Engines** (10+ modules):
- `model_registry.py` — Model lifecycle governance (Draft → Validated → Champion → Retired)
- `backtesting.py` + `backtesting_stats.py` + `backtesting_traffic.py` — Validation metrics and Basel traffic lights
- `markov.py` — Transition matrix estimation and stochastic forecasting
- `hazard.py` + 6 sub-modules — Cox PH, discrete-time, Kaplan-Meier survival analysis
- `advanced.py` — Cure rates, CCF, collateral haircuts
- `period_close.py` — End-of-period pipeline orchestration
- `health.py` — System health monitoring

## Deployment

The platform deploys to Databricks Apps using the `app.yaml` configuration:

```yaml
command:
  - python
  - app.py
env:
  - name: LAKEBASE_INSTANCE_NAME
    value: "${LAKEBASE_INSTANCE_NAME}"
  - name: LAKEBASE_DATABASE
    value: databricks_postgres
resources:
  - name: lakebase-db
    lakebase:
      instance_name: "${LAKEBASE_INSTANCE_NAME}"
      permission: CAN_USE
```

The app reads `DATABRICKS_APP_PORT` at runtime and serves the React SPA as static files from the `frontend/dist/` directory.
