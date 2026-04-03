---
sidebar_position: 1
title: "Setup & Installation"
description: "Deploying the IFRS 9 ECL Platform on Databricks Apps with Lakebase connectivity."
---

# Setup & Installation

Deploy the IFRS 9 ECL Platform on Databricks Apps, configure database connectivity, and verify a healthy running instance.

:::info Who Should Read This
System administrators responsible for deploying, configuring, and maintaining the platform infrastructure.
:::

## Prerequisites

Before deploying the platform, ensure the following components are provisioned in your Databricks workspace:

| Component | Requirement |
|-----------|-------------|
| **Databricks Workspace** | Premium or Enterprise tier with Unity Catalog enabled |
| **Lakebase Instance** | A PostgreSQL-compatible Lakebase database instance provisioned via the workspace |
| **Unity Catalog** | At least one catalog with schemas containing your loan portfolio data |
| **Service Principal** | A service principal with `CAN_USE` permission on the Lakebase instance |
| **Python Environment** | Python 3.10+ with `psycopg2`, `pandas`, `fastapi`, `uvicorn`, `databricks-sdk` |

## Application Manifest (app.yaml)

The platform is deployed as a Databricks App. The `app.yaml` file defines the entry point, environment variables, and resource bindings:

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

The `resources` block declares a dependency on a Lakebase instance. At deploy time, Databricks resolves the instance name and auto-injects connection credentials (`PGHOST`, `PGUSER`, `PGPASSWORD`) into the app environment.

## Environment Variables

The following environment variables control platform behavior. Some are auto-injected by Databricks Apps; others must be set manually for local development.

### Auto-Injected (Databricks Apps Runtime)

| Variable | Description |
|----------|-------------|
| `PGHOST` | Lakebase PostgreSQL hostname (read-write DNS) |
| `PGDATABASE` | Database name (default: `databricks_postgres`) |
| `PGUSER` | Service principal or user identity for database authentication |
| `PGPASSWORD` | OAuth token or password for database authentication |
| `PGPORT` | PostgreSQL port (default: `5432`) |
| `DATABRICKS_APP_NAME` | Name of the deployed Databricks App |
| `DATABRICKS_APP_PORT` | Port the app listens on (default: `8000`) |
| `DATABRICKS_SOURCE_CODE_PATH` | Workspace path to the app source code (used for script detection) |

### Configurable

| Variable | Description | Default |
|----------|-------------|---------|
| `LAKEBASE_INSTANCE_NAME` | Lakebase instance name for SDK-based connections | `ifrs9-ecl-demo-db` |
| `LAKEBASE_DATABASE` | Target database name | `databricks_postgres` |
| `DATABRICKS_CONFIG_PROFILE` | Databricks CLI profile for local development | `lakemeter` |

## Connection Flow

The platform uses a prioritized connection strategy to establish connectivity with Lakebase. Each priority level falls through to the next if the required variables are not available.

### Priority 1: Auto-Injected Credentials

When all three of `PGHOST`, `PGUSER`, and `PGPASSWORD` are present (the standard path for Databricks Apps), the platform connects directly:

```
PGHOST + PGUSER + PGPASSWORD → Direct psycopg2 connection with sslmode=require
```

This is the default path in production. Databricks Apps auto-inject these from the `resources` block in `app.yaml`.

### Priority 2: OAuth Token Generation

When `PGHOST` and `PGUSER` are set but `PGPASSWORD` is absent, the platform generates an OAuth token via the Databricks SDK:

```
PGHOST + PGUSER → WorkspaceClient().config.authenticate() → OAuth Bearer token as password
```

This path is used when the app has partial environment injection or when running under a service principal that authenticates via OAuth.

### Priority 3: SDK-Based Discovery

When `PGHOST` is not set at all, the platform falls back to full SDK-based connection:

```
LAKEBASE_INSTANCE_NAME → SDK get_database_instance() → resolve DNS + generate credential
```

The SDK retrieves the instance's read-write DNS, generates a short-lived credential, and resolves the current user identity. This is the standard path for local development.

## Token Refresh

OAuth tokens issued by Databricks last approximately 60 minutes. To prevent query failures from expired tokens, the platform runs a **background daemon thread** that proactively refreshes the connection pool.

- **Refresh interval**: Every 45 minutes (configurable via `TOKEN_REFRESH_INTERVAL`)
- **Mechanism**: The thread destroys the existing connection pool, re-authenticates, and creates a new pool with fresh credentials
- **Failure handling**: If a refresh fails, the thread logs the error and retries on the next cycle
- **Query-level retry**: If a query encounters an authentication error (expired token, connection reset), the pool is re-initialized once and the query is retried automatically

## Database Schema

All platform tables are created in the `expected_credit_loss` schema with a `lb_` prefix:

```
expected_credit_loss.lb_loan_tape
expected_credit_loss.lb_borrower_master
expected_credit_loss.lb_model_ready_loans
expected_credit_loss.lb_loan_ecl_weighted
...
```

The schema and prefix are configurable through the admin configuration (`data_sources.lakebase_schema` and `data_sources.lakebase_prefix`). The helper function `_t(name)` resolves any table name to its fully qualified form: `{SCHEMA}.{PREFIX}{name}`.

System tables (workflows, config, audit trail, pipelines) are created directly in the schema without the `lb_` prefix:

```
expected_credit_loss.app_config
expected_credit_loss.workflow_state
expected_credit_loss.audit_trail
expected_credit_loss.pipeline_runs
```

## Connection Pool

The platform uses `psycopg2.pool.ThreadedConnectionPool` for safe concurrent access from FastAPI's async request handlers:

| Parameter | Value |
|-----------|-------|
| `minconn` | 2 |
| `maxconn` | 10 |
| `sslmode` | `require` |

The pool is initialized during FastAPI's lifespan startup event. If the pool has not been initialized when a query is attempted, `init_pool()` is called lazily. Failed connections trigger automatic pool re-initialization with fresh credentials.

## Deployment Steps

### Deploy to Databricks Apps

1. **Sync the source code** to the Databricks workspace:

```bash
databricks sync . /Workspace/Users/<your-email>/ifrs9-ecl-app --profile <profile>
```

2. **Deploy the app**:

```bash
databricks apps deploy ifrs9-ecl --profile <profile>
```

3. **Verify the deployment** by checking the app URL in the Databricks workspace UI or by calling the health endpoint.

### First-Run Initialization

On first startup, the platform automatically:

1. Initializes the Lakebase connection pool
2. Creates the `workflow_state` table
3. Creates the `app_config` table and seeds default configuration
4. Starts the background token refresh thread

No manual database migration is required. All tables are created with `CREATE TABLE IF NOT EXISTS`.

## Health Checks

The platform exposes two health check endpoints for monitoring and alerting.

### Basic Health Check

```
GET /api/health
```

Executes `SELECT 1` against Lakebase and returns:

```json
{
  "status": "healthy",
  "lakebase": "connected",
  "rows": 1
}
```

If the database is unreachable:

```json
{
  "status": "degraded",
  "lakebase": "error",
  "error": "connection refused"
}
```

### Detailed Health Check

```
GET /api/health/detailed
```

Performs comprehensive verification including:

- Lakebase connectivity
- Required table existence
- Configuration integrity
- Scientific library availability (scipy, scikit-learn)

Use the detailed health check for deployment validation and periodic monitoring. Use the basic health check for load balancer probes.

## Local Development Setup

For local development outside of Databricks Apps:

1. **Configure a Databricks CLI profile** named `lakemeter` (or set `DATABRICKS_CONFIG_PROFILE`):

```bash
databricks configure --profile lakemeter
```

2. **Set the Lakebase instance name** (if different from default):

```bash
export LAKEBASE_INSTANCE_NAME=your-lakebase-instance
```

3. **Start the application**:

```bash
python app.py
```

The platform will use Priority 3 (SDK-based) connection, authenticating via your CLI profile to discover the Lakebase instance and generate credentials.

4. **Access the application**:

- API: `http://localhost:8000/api/swagger`
- Frontend: `http://localhost:8000`
- Documentation: `http://localhost:8000/docs`

:::tip
The local development server uses `uvicorn` with the port from `DATABRICKS_APP_PORT` (default `8000`). All API routes are prefixed with `/api/` and the React frontend is served as a single-page application from the root path.
:::
