---
sidebar_position: 1
title: "Architecture"
description: "System design, tech stack, data flow between components, and module structure."
---

# Architecture

This page describes the system design, technology stack, data flow, and module structure of the IFRS 9 ECL Platform.

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.12, FastAPI, Uvicorn | REST API server, SSE streaming, async lifespan management |
| **Frontend** | React 18, TypeScript, Vite | Single-page application with interactive dashboards |
| **Database** | Databricks Lakebase (PostgreSQL wire protocol) | Persistent storage for portfolio data, ECL results, governance state |
| **Compute** | NumPy, SciPy, pandas | Monte Carlo simulation, Markov chains, hazard models |
| **Infrastructure** | Databricks Apps, Databricks SDK | Deployment, OAuth, job orchestration |
| **Documentation** | Docusaurus | Embedded developer and user documentation |

## Module Structure

The backend lives in the `app/` directory. Each subdirectory is a Python package with a focused responsibility.

```
app/
├── app.py                  # FastAPI application, lifespan, static file mounts
├── backend.py              # Lakebase connection pool, query_df(), execute()
├── ecl_engine.py           # Thin re-export shim for ecl/simulation.py
├── admin_config.py         # Configuration CRUD (app_config table)
├── admin_config_defaults.py# Default LGD, scenarios, satellite coefficients
├── admin_config_schema.py  # Pydantic schema for admin config validation
├── admin_config_setup.py   # First-run setup wizard logic
├── jobs.py                 # Databricks Jobs SDK integration
│
├── db/
│   └── pool.py             # Connection pooling, query_df(), execute(), _t() helper
│
├── ecl/
│   ├── simulation.py       # run_simulation() orchestrator
│   ├── monte_carlo.py      # Low-level vectorized batch loop
│   ├── aggregation.py      # Result assembly (portfolio, scenario, product breakdowns)
│   ├── constants.py        # Fallback LGD, satellite coefficients, scenario weights
│   ├── config.py           # Load LGD/weights from admin_config
│   ├── data_loader.py      # SQL queries to load loans and scenarios
│   ├── defaults.py         # get_defaults() for simulation parameter API
│   └── helpers.py          # Progress callback, convergence checks, DataFrame utils
│
├── domain/
│   ├── queries.py          # Reusable SQL query builders
│   ├── workflow.py         # Project lifecycle state machine (ecl_workflow table)
│   ├── model_registry.py   # Model CRUD, status transitions, champion promotion
│   ├── model_runs.py       # Simulation and satellite run persistence
│   ├── markov.py           # Transition matrix estimation, forecasting, lifetime PD
│   ├── hazard.py           # Hazard model dispatcher (Cox PH, KM, logistic)
│   ├── hazard_estimation.py# Estimation algorithms
│   ├── hazard_cox_ph.py    # Cox proportional hazards implementation
│   ├── hazard_nonparam.py  # Kaplan-Meier and Nelson-Aalen estimators
│   ├── hazard_analysis.py  # Survival curve and term structure computation
│   ├── hazard_retrieval.py # Hazard model persistence layer
│   ├── hazard_tables.py    # DDL for hazard model tables
│   ├── backtesting.py      # PD backtesting engine
│   ├── backtesting_stats.py# Binomial test, traffic light, Hosmer-Lemeshow
│   ├── backtesting_traffic.py # Traffic light aggregation
│   ├── attribution.py      # ECL waterfall attribution
│   ├── validation_rules.py # 23 domain rules (D1-D10, M-R1-R8, G-R1-G-R5)
│   ├── advanced.py         # Cure rates, CCF, collateral haircuts
│   ├── audit_trail.py      # Immutable hash-chained audit log
│   ├── config_audit.py     # Configuration change tracking
│   ├── period_close.py     # Period-end close pipeline orchestrator
│   ├── data_mapper.py      # Unity Catalog to Lakebase data ingestion
│   └── health.py           # Detailed health check (tables, config, scipy)
│
├── governance/
│   └── rbac.py             # Role-based access control, approval workflows
│
├── reporting/
│   ├── reports.py          # Report generation dispatcher
│   ├── report_crud.py      # Report persistence
│   ├── report_helpers.py   # Shared formatting utilities
│   ├── ifrs7_disclosure.py # IFRS 7 disclosure report sections
│   ├── ecl_movement.py     # ECL movement schedule report
│   ├── stage_migration.py  # Stage migration analysis report
│   ├── sensitivity.py      # Sensitivity analysis data queries
│   ├── sensitivity_report.py # Sensitivity analysis report builder
│   ├── concentration.py    # Concentration risk data queries
│   ├── concentration_report.py # Concentration risk report builder
│   ├── gl_journals.py      # General ledger journal generation
│   └── pdf_export.py       # PDF report rendering
│
├── middleware/
│   ├── request_id.py       # RequestIDMiddleware
│   ├── auth.py             # Authentication, RBAC deps, ECL hash verification
│   └── error_handler.py    # ErrorHandlerMiddleware
│
├── routes/                 # 18 route modules (see API Reference)
│   ├── projects.py         # /api/projects/*
│   ├── data.py             # /api/data/*
│   ├── simulation.py       # /api/simulate*
│   ├── models.py           # /api/models/*
│   ├── markov.py           # /api/markov/*
│   ├── hazard.py           # /api/hazard/*
│   ├── backtesting.py      # /api/backtest/*
│   ├── attribution.py      # /api/data/attribution/*
│   ├── satellite.py        # /api/data/satellite-*, model-runs, cohorts
│   ├── reports.py          # /api/reports/*
│   ├── gl_journals.py      # /api/gl/*
│   ├── rbac.py             # /api/rbac/*
│   ├── advanced.py         # /api/advanced/*
│   ├── admin.py            # /api/admin/*
│   ├── audit.py            # /api/audit/*
│   ├── jobs.py             # /api/jobs/*
│   ├── data_mapping.py     # /api/data-mapping/*
│   ├── period_close.py     # /api/pipeline/*
│   ├── setup.py            # /api/setup/*
│   └── _utils.py           # Shared utilities (df_to_records, DecimalEncoder)
│
├── frontend/               # React SPA source (Vite + TypeScript)
├── static/                 # Vite build output (served at /)
└── docs_site/              # Docusaurus build output (served at /docs)
```

## URL Routing and Static File Serving

The application serves three distinct interfaces from a single FastAPI process:

| URL Pattern | Served Content | Source |
|------------|---------------|--------|
| `/` and `/{path}` | React SPA | `app/static/` (Vite build output) |
| `/api/*` | REST API endpoints | FastAPI route handlers |
| `/api/swagger` | OpenAPI interactive docs | FastAPI built-in Swagger UI |
| `/api/redoc` | OpenAPI ReDoc | FastAPI built-in ReDoc |
| `/docs` and `/docs/{path}` | Docusaurus site | `app/docs_site/` or `docs/build/` |

The SPA catch-all route explicitly avoids intercepting `/api/*` and `/docs/*` paths, raising a 404 for those prefixes so the dedicated handlers take precedence.

Docusaurus static assets (JS, CSS, images) are mounted at `/docs/assets` and `/docs/img`. Screenshot directories are mounted at `/docs/screenshots` and `/docs/eval-screenshots` when present on disk.

## Connection Pooling and Token Refresh

The database layer (`backend.py`) manages a `psycopg2.ThreadedConnectionPool`:

| Parameter | Value |
|-----------|-------|
| `minconn` | 2 |
| `maxconn` | 10 |
| `sslmode` | `require` |
| Token refresh interval | 45 minutes (tokens expire after ~60 min) |
| Retry on `OperationalError` | 1 automatic retry with pool reinitialization |

**Authentication modes** (resolved in order):

1. **Auto-injected env vars**: `PGHOST` + `PGUSER` + `PGPASSWORD` set by Databricks Apps Lakebase resource.
2. **SDK OAuth**: `PGHOST` + `PGUSER` present but no password; generates an OAuth token via `WorkspaceClient().config.authenticate()`.
3. **SDK credential generation**: No PG env vars; uses `WorkspaceClient().database.get_database_instance()` and `generate_database_credential()` to connect.

A daemon thread runs `_token_refresh_loop()`, calling `_force_reinit()` every 45 minutes to close all connections and create a fresh pool with new credentials. Both `query_df()` and `execute()` also detect auth and connection errors at query time and retry once with a fresh pool.

All table references use the `_t(name)` helper, which resolves to `{SCHEMA}.{PREFIX}{name}` (default: `expected_credit_loss.lb_{name}`). The schema and prefix are loaded from admin configuration on startup.

## Request Lifecycle

Every HTTP request passes through the middleware stack before reaching the route handler.

```
Incoming Request
       │
       ▼
┌─────────────────────┐
│ RequestIDMiddleware  │  Assigns X-Request-ID (12-char UUID prefix),
│                     │  stores on request.state, logs timing
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ ErrorHandlerMiddle. │  Catches unhandled exceptions,
│                     │  returns structured JSON {error, message, request_id, path}
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Route Handler     │  FastAPI path operation with Pydantic request models
│  + Auth Dependencies│  get_current_user / require_permission / require_project_not_locked
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Domain Layer      │  Business logic, validation, computation
│  (domain/, ecl/)    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Data Layer        │  backend.query_df(sql, params) / backend.execute(sql, params)
│  (backend.py)       │  with automatic retry on connection errors
└─────────┬───────────┘
          │
          ▼
    Lakebase (PG)
```

### Middleware Stack

Middleware is registered in `app.py` with **outermost-first** ordering. The `RequestIDMiddleware` is added second (so it executes first), and `ErrorHandlerMiddleware` is added first (so it wraps everything including the request ID layer):

```python
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestIDMiddleware)
```

**RequestIDMiddleware**: Accepts an incoming `X-Request-ID` header or generates one. Logs structured `request_id=... method=... path=... status=... duration_ms=...` for all non-static paths. The request ID is propagated back in the response header.

**ErrorHandlerMiddleware**: Catches any unhandled exception and returns HTTP 500 with a JSON body containing `error`, `message`, `request_id`, and `path`. This prevents raw stack traces from reaching clients.

### Authentication Dependencies

Authentication is implemented as FastAPI dependencies rather than middleware, allowing per-endpoint control:

- **`get_current_user(request)`**: Extracts user identity from `X-Forwarded-User` (Databricks Apps OAuth proxy), `X-User-Id` (development), or returns an anonymous user with `analyst` role.
- **`require_permission(action)`**: Dependency factory that checks the user's role grants the specified permission. Raises HTTP 403 on failure. When no auth header is present (local development), RBAC is bypassed.
- **`require_project_not_locked(project_id_param)`**: Blocks mutations on signed-off projects.
- **`compute_ecl_hash()` / `verify_ecl_hash()`**: SHA-256 integrity verification for signed-off ECL results, using canonical JSON serialization.

## Deployment

The platform deploys as a Databricks App. The `app.yaml` declares the command, environment variables, and a Lakebase resource:

```yaml
command:
  - python
  - app.py
env:
  - name: LAKEBASE_INSTANCE_NAME
    value: "${LAKEBASE_INSTANCE_NAME}"
  - name: LAKEBASE_DATABASE
    value: databricks_postgres
  - name: DATABRICKS_APP_NAME
    value: "${DATABRICKS_APP_NAME}"
resources:
  - name: lakebase-db
    lakebase:
      instance_name: "${LAKEBASE_INSTANCE_NAME}"
      permission: CAN_USE
```

When deployed, the platform automatically receives:

- **`PGHOST`**, **`PGUSER`**, **`PGPASSWORD`**: Auto-injected by the Lakebase resource for database connectivity.
- **`DATABRICKS_APP_PORT`**: Port for Uvicorn (defaults to 8000).
- **`DATABRICKS_APP_NAME`**: Detected at runtime to distinguish deployed vs. local context.
- **OAuth proxy headers**: `X-Forwarded-User` is set by the Databricks Apps reverse proxy for authenticated users.

### Application Lifespan

The FastAPI `lifespan` async context manager runs on startup and triggers the following initialization sequence:

1. Create the `ThreadedConnectionPool` with SSL
2. Verify connectivity with `SELECT version()`
3. Ensure the `ecl_workflow` table exists (`domain.workflow.ensure_workflow_table()`)
4. Load admin configuration (schema and prefix from the `app_config` table)
5. Start the background token refresh daemon thread (45-minute interval)

## JSON Serialization

The platform handles several non-standard JSON types through a custom encoder pipeline:

- **`_SafeEncoder`**: Extends `json.JSONEncoder` to serialize `Decimal` as `float` and `datetime`/`date` as ISO 8601 strings.
- **`_sanitize()`**: Recursively replaces `NaN` and `Inf` float values with `None` for JSON safety.
- **`df_to_records()`**: Converts pandas DataFrames to JSON-safe list-of-dicts by combining sanitization and safe encoding.

These utilities are used throughout the route layer to ensure all API responses are valid JSON regardless of underlying numeric precision or missing data patterns.
