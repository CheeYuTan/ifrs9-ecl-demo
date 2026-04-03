---
sidebar_position: 7
title: "System Administration"
description: "Monitoring system health, managing database connections, and operational procedures."
---

# System Administration

This page covers the operational aspects of running the IFRS 9 ECL Platform: health monitoring, database connection management, table initialization, middleware infrastructure, and audit trail integrity. These topics are essential for keeping the platform running reliably in production.

:::info Who Should Read This
System administrators, DevOps engineers, and SREs responsible for platform uptime, database connectivity, and operational monitoring.
:::

## Health Check Endpoints

The platform exposes two health check endpoints for monitoring and alerting integration.

### Quick Health Check

Available at the `/api/health` endpoint, the quick health check performs a lightweight connectivity test against Lakebase. It returns immediately and is suitable for load balancer probes and uptime monitors.

The response indicates either **healthy** (database connected) or **degraded** (database unreachable, with an error description).

### Detailed Health Check

Available at the `/api/health/detailed` endpoint, the detailed health check runs a comprehensive verification across all platform subsystems. This check takes longer to respond and should be used for monitoring dashboards rather than high-frequency probes.

The detailed check reports the status of each subsystem and whether all required tables exist with their current row counts.

### Health Check Components

The detailed health check verifies four subsystems:

| Component | What It Checks | Failure Impact |
|-----------|---------------|----------------|
| **Lakebase connection** | Executes `SELECT 1` against the PostgreSQL-compatible Lakebase instance. | All data operations fail. Platform is non-functional. |
| **Required tables** | Verifies that `ecl_workflow`, `model_ready_loans`, `loan_level_ecl`, `loan_ecl_weighted`, and `app_config` exist and reports row counts. | Missing tables prevent specific workflows from executing. |
| **Admin config** | Loads the admin configuration and reports available sections. | Platform may operate with defaults but lacks user-configured settings. |
| **SciPy availability** | Imports `scipy` and reports its version. | Backtesting statistical tests (Hosmer-Lemeshow, chi-squared) are unavailable. |

### Status Interpretation

The overall status is determined by a logical AND of all components:

- **`healthy`** -- All four components pass their checks.
- **`degraded`** -- One or more components have failed. The platform may still serve some requests, but functionality is impaired.

## Database Initialization

On first startup, the platform automatically creates the required schema and tables. No manual migration step is needed.

### Auto-Creation Sequence

When `init_pool()` is called (triggered by the first database query or at application startup), the following sequence executes:

1. **Connection pool creation** -- A `ThreadedConnectionPool` is established with the Lakebase instance.
2. **Version verification** -- The platform runs `SELECT version()` to confirm connectivity.
3. **Workflow table** -- `ensure_workflow_table()` creates the `ecl_workflow` table if it does not exist.
4. **Schema configuration** -- The schema name and table prefix are loaded from admin config (defaults: schema `expected_credit_loss`, prefix `lb_`).

Additional tables are created on-demand when their respective modules initialize:

| Table | Created By | Purpose |
|-------|-----------|---------|
| `ecl_workflow` | `domain.workflow` | Project and workflow state management |
| `model_registry` | `domain.model_registry` | Registered PD, LGD, and EAD models |
| `backtesting` / `backtest_metrics` / `backtest_cohorts` | `domain.backtesting` | Backtest results and performance metrics |
| `markov_chains` | `domain.markov` | Transition matrix storage |
| `hazard_rates` | `domain.hazard` | Hazard rate curve storage |
| `rbac_users` / `rbac_approval_requests` | `governance.rbac` | User accounts and approval workflows |
| `app_config` | `admin_config` | Platform configuration key-value store |
| `audit_trail` / `config_audit_log` | `domain.audit_trail` | Immutable audit records |

All `CREATE TABLE` statements use `IF NOT EXISTS`, making the initialization idempotent. Restarting the application never drops or recreates existing tables.

## Token Refresh Monitoring

Lakebase connections are authenticated via OAuth tokens that expire approximately every 60 minutes. The platform runs a background daemon thread that proactively refreshes the connection pool every 45 minutes to prevent mid-request token expiration.

### How It Works

1. A background `threading.Thread` (daemon=True) starts when the connection pool initializes.
2. The thread sleeps for `TOKEN_REFRESH_INTERVAL` (45 minutes = 2700 seconds).
3. On each cycle, it destroys the existing connection pool and creates a new one with fresh credentials.
4. If the refresh fails, it logs an exception and retries on the next cycle.

### Monitoring Token Refresh

Watch for these log entries:

```
INFO  Started background token refresh thread (every 2700s)
INFO  Proactive token refresh: reinitializing Lakebase pool
INFO  Proactive token refresh succeeded
```

If refresh fails:

```
ERROR Proactive token refresh failed — will retry next cycle
```

### Reactive Recovery

In addition to proactive refresh, the platform detects auth errors on individual queries and triggers an immediate pool re-initialization. The following error patterns are recognized:

- `invalid authorization`
- `password authentication failed`
- `token expired` / `token is expired`
- `ssl connection has been closed`
- `connection reset`
- `server closed the connection unexpectedly`

When any of these patterns are detected, the platform automatically retries the failed query once with a fresh connection pool.

## Connection Pool Management

The platform uses `psycopg2.pool.ThreadedConnectionPool` configured as follows:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `minconn` | 2 | Minimum connections kept open at all times. |
| `maxconn` | 10 | Maximum concurrent connections to Lakebase. |
| `sslmode` | `require` | All connections use TLS encryption. |

### Connection Lifecycle

- Connections are obtained from the pool via `getconn()` before each query.
- After query execution, connections are returned via `putconn()`.
- On `OperationalError`, the connection is returned with `close=True` to discard it from the pool.
- Pool re-initialization calls `closeall()` to cleanly terminate all connections before creating new ones.

### Environment Variables

The connection pool reads from these environment variables (auto-injected by Databricks Apps):

| Variable | Description | Default |
|----------|-------------|---------|
| `PGHOST` | Lakebase hostname | (none) |
| `PGDATABASE` | Database name | `databricks_postgres` |
| `PGUSER` | Database user | (none) |
| `PGPASSWORD` | OAuth token or password | (none) |
| `PGPORT` | PostgreSQL port | `5432` |

If `PGHOST` and `PGUSER` are set but `PGPASSWORD` is not, the platform generates an OAuth token via the Databricks SDK. If `PGHOST` is not set, it falls back to SDK-based instance discovery using the `LAKEBASE_INSTANCE_NAME` environment variable (default: `ifrs9-ecl-demo-db`).

## Audit Trail Integrity

The audit trail is a tamper-evident, hash-chained log that records every significant action in the platform. It is designed to comply with IAS 8 (changes in accounting estimates), SOX Section 302 (management attestation), and BCBS 239 (data governance).

### Hash Chain Structure

Each audit entry contains:

| Field | Description |
|-------|-------------|
| `previous_hash` | The `entry_hash` of the preceding entry, or `"GENESIS"` for the first entry. |
| `entry_hash` | SHA-256 hash computed from the entry's `previous_hash`, `event_type`, `entity_id`, `action`, `detail`, and `created_at`. |

This forms a linked chain where modifying any historical entry would break the hash of all subsequent entries.

### Verifying Chain Integrity

The platform provides an audit chain verification feature accessible from the **Audit** section of each project. Verification recomputes every hash in the chain and confirms they match the stored values.

- **If the chain is intact**: Verification confirms the number of entries and reports "Audit chain is intact."
- **If tampering is detected**: Verification identifies the exact entry where the chain breaks, indicating which record was modified.

### INSERT-Only Design

The audit tables (`audit_trail` and `config_audit_log`) are designed as INSERT-only. No `UPDATE` or `DELETE` operations are performed by platform code. This ensures the historical record is immutable.

:::warning
Direct database modifications to audit tables will break the hash chain. Always use the platform API to create audit entries.
:::

## Middleware Stack

The platform uses a layered middleware stack that processes every HTTP request.

### Request ID Middleware

Every request is assigned a unique identifier for tracing through logs and error reports. If the client sends an `X-Request-ID` header, that value is used; otherwise, a unique ID is generated automatically. The request ID appears in the response headers and all related log entries, making it easy to trace a specific request through the system.

All non-static requests are logged with the request ID, HTTP method, path, status code, and response time in milliseconds.

### Error Handler Middleware

Unhandled exceptions are caught and returned as structured error responses that include the request ID and a human-readable error message. This prevents raw technical details from reaching end users while preserving enough context for troubleshooting. The full stack trace is logged server-side for investigation.

## Configuration Management

### Viewing Current Configuration

The full platform configuration can be viewed from the **Admin > Settings** page. All four configuration sections (data sources, model configuration, jobs, and app settings) are displayed with their current values. See [App Settings](app-settings) for details on each section.

### Resetting to Factory Defaults

The factory reset option is available from the Admin Settings page. It resets all configuration sections to their default values.

:::danger
Factory reset destroys all custom configuration including data source mappings, model parameters, SICR thresholds, scenario definitions, and governance settings. Use it only during initial setup or when recovering from a corrupt configuration state.
:::

### Testing Database Connectivity

The Admin Settings page includes a **Test Connection** button that verifies the database connection by executing a simple query. Use this to verify connectivity after infrastructure changes or Lakebase maintenance.

## Operational Procedures

### Restarting the Application

On restart, the platform:

1. Creates a new connection pool with fresh credentials.
2. Runs `ensure_*` functions to verify all required tables exist.
3. Loads admin configuration from the database.
4. Starts the background token refresh thread.

No data is lost on restart. All state is stored in Lakebase.

### Monitoring Recommendations

| Metric | Endpoint / Source | Alert Threshold |
|--------|------------------|-----------------|
| Overall health | `GET /api/health` | Any non-`healthy` status |
| Detailed health | `GET /api/health/detailed` | Any service `healthy: false` |
| Request latency | Application logs (`duration_ms`) | p99 > 5000ms |
| Token refresh | Application logs | Any `refresh failed` message |
| Audit chain integrity | `GET /api/audit/{id}/verify` | `valid: false` |

### Log Levels

The platform uses Python's standard `logging` module. Key loggers:

| Logger | Content |
|--------|---------|
| `db.pool` | Connection pool events, token refresh, query retries |
| `governance.rbac` | RBAC table initialization, user lookups |
| `domain.audit_trail` | Audit entry creation, chain verification |
| `domain.health` | Health check results |
| `middleware.request_id` | Per-request timing and status codes |
| `middleware.error_handler` | Unhandled exceptions with full stack traces |

## What's Next?

- [App Settings](app-settings) — Configure organization identity, scenarios, and governance
- [User Management](user-management) — Manage user accounts and RBAC roles
- [Troubleshooting](troubleshooting) — Resolve specific platform issues by subsystem
- [Jobs & Pipelines](jobs-pipelines) — Monitor and manage ECL calculation jobs
