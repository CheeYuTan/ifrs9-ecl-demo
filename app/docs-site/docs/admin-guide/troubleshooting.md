---
sidebar_position: 9
title: "Troubleshooting"
description: "Common issues, error patterns, and solutions for the IFRS 9 ECL Platform."
---

# Troubleshooting

This page catalogs the most common issues encountered when operating the IFRS 9 ECL Platform, organized by subsystem. Each entry includes the symptoms, root cause, and resolution steps.

:::info Who Should Read This
System administrators, DevOps engineers, and support staff diagnosing platform issues in development or production environments.
:::

## Database Connection Errors

### Token Expired / SSL Connection Closed

**Symptoms:**
- API calls return 500 errors with messages like `SSL connection has been closed unexpectedly` or `password authentication failed`.
- The quick health check (`GET /api/health`) returns `"status": "degraded"`.

**Root cause:** Lakebase OAuth tokens expire after approximately 60 minutes. If the background token refresh thread has failed or has not yet run, queries may hit an expired token.

**Resolution:**

1. **Automatic recovery** -- The platform detects auth-related errors and automatically reinitializes the connection pool with fresh credentials. The failed query is retried once. In most cases, the user sees a brief delay but the request succeeds.

2. **Manual reconnect** -- If automatic recovery fails, restart the application. On startup, the platform creates a fresh connection pool and starts a new token refresh thread.

3. **Verify the refresh thread** -- Check the application logs for:
   ```
   INFO  Proactive token refresh succeeded
   ```
   If you see `Proactive token refresh failed` repeatedly, investigate the underlying credential source (Databricks SDK configuration, workspace permissions, or environment variables).

**Error patterns recognized by the auto-recovery logic:**
- `invalid authorization`
- `password authentication failed`
- `token expired` / `token is expired`
- `ssl connection has been closed`
- `connection reset`
- `server closed the connection unexpectedly`

### Connection Pool Exhaustion

**Symptoms:** Requests hang or time out. Logs show `connection pool exhausted` or long delays on `getconn()`.

**Root cause:** The connection pool has a maximum of 10 connections. If queries are long-running or connections are not being returned properly, the pool can become exhausted.

**Resolution:**
1. Check for long-running queries in Lakebase.
2. Restart the application to reset the pool.
3. If the issue persists, investigate whether any code paths are holding connections without returning them.

## Missing Required Tables

**Symptoms:**
- The detailed health check (`GET /api/health/detailed`) reports `"all_present": false` with entries in the `missing` array.
- API endpoints for specific features return 500 errors referencing `relation "expected_credit_loss.lb_model_ready_loans" does not exist`.

**Root cause:** The data tables (`model_ready_loans`, `loan_level_ecl`, `loan_ecl_weighted`) are populated by the data pipeline, not auto-created on startup. If the pipeline has not run, these tables do not exist.

**Resolution:**
1. Run the **Data Mapping Wizard** in the admin UI to configure your source tables and column mappings.
2. Execute the data pipeline jobs (via the Jobs page or Databricks workflow) to populate the required tables.
3. Re-check the health endpoint to verify the tables are present.

## Schema and Table Validation Errors

**Symptoms:**
- The Data Mapping page shows validation errors like `Column type mismatch` or `Required column not found`.
- The admin config page reports schema errors.

**Root cause:** The column mappings in the admin configuration do not match the actual schema of the source tables in Lakebase.

**Resolution:**

1. **Check admin config** -- Navigate to the Admin Settings page and review the data source configuration. Verify that the `lakebase_schema` and `lakebase_prefix` values match your actual database.

2. **Check schemas** -- Use `GET /api/admin/schemas` to list available schemas and `GET /api/admin/tables/{schema}` to list tables within a schema.

3. **Type compatibility** -- The platform uses a `TYPE_COMPAT` map to determine which PostgreSQL types are compatible with each expected type:

   | Expected Type | Compatible PostgreSQL Types |
   |--------------|---------------------------|
   | `TEXT` | `text`, `character varying`, `varchar`, `char`, `character`, `name`, `uuid` |
   | `INT` | `integer`, `bigint`, `smallint`, `int`, `int4`, `int8`, `int2`, `numeric` |
   | `FLOAT` | `double precision`, `real`, `numeric`, `decimal`, `float4`, `float8` |
   | `DATE` | `date`, `timestamp`, `timestamp without time zone`, `timestamp with time zone` |
   | `BOOLEAN` | `boolean`, `bool` |

   If a column in your source table uses a type not in this map, you may need to cast it in a view or update the mapping.

## Model Configuration Issues

**Symptoms:**
- Model creation fails with validation errors.
- Backtesting produces unexpected results or refuses to run.

**Root cause:** The model configuration may have invalid parameters, unsupported model types, or SICR thresholds that are out of range.

**Resolution:**

1. **Verify model type** -- The platform supports specific model types for PD, LGD, and EAD. Ensure the `model_type` field in your configuration matches one of the supported values listed in the Model Configuration admin page.

2. **Check SICR ranges** -- SICR (Significant Increase in Credit Risk) thresholds define the boundaries between Stage 1, Stage 2, and Stage 3. Verify that:
   - Stage 1 upper bound is less than Stage 2 upper bound.
   - All threshold values are positive numbers.
   - The absolute and relative thresholds are consistent with your institution's risk appetite.

3. **Review model registry** -- Use `GET /api/models` to list registered models and verify their configuration is complete.

## Job Execution Failures

**Symptoms:**
- Jobs submitted via the Jobs page fail immediately or show `FAILED` status in Databricks.
- Error logs reference `FileNotFoundException` or `notebook not found`.

**Root cause:** The platform dispatches jobs as Databricks notebook tasks. The `scripts_base_path` in the admin configuration must point to the correct workspace path where the job scripts are deployed.

**Resolution:**

1. **Verify scripts base path** -- The platform auto-detects the scripts path from the Databricks App deployment location. If auto-detection fails, set it manually in the admin config under `jobs_config.scripts_base_path`.

2. **Check job logs** -- Navigate to the Databricks Jobs UI and inspect the failed run's output. Common issues include:
   - Missing dependencies in the cluster environment.
   - Incorrect table references in the notebook.
   - Insufficient cluster permissions.

3. **Available jobs:**

   | Job Key | Script | Description |
   |---------|--------|-------------|
   | `02_build_pd_model` | `02_build_pd_model.py` | Build PD transition matrices |
   | `02a_build_lgd_model` | `02a_build_lgd_model.py` | Build LGD models |
   | `02b_build_ead_model` | `02b_build_ead_model.py` | Build EAD models |
   | `03a_aggregate_models` | `03a_aggregate_models.py` | Aggregate model outputs |
   | `03b_run_ecl_calculation` | `03b_run_ecl_calculation.py` | Run deterministic ECL |
   | `03c_run_monte_carlo` | `03c_run_monte_carlo.py` | Run Monte Carlo simulation |
   | `04_sync_to_lakebase` | `04_sync_to_lakebase.py` | Sync results to Lakebase |

## Backtest Minimum Sample Size

**Symptoms:**
- LGD backtesting returns `"status": "insufficient_data"` with a message about minimum defaults.
- PD backtesting produces unreliable metrics.

**Root cause:** Statistical backtesting requires minimum sample sizes to produce meaningful results.

**Resolution:**

The platform enforces these minimums:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `MIN_SAMPLE_SIZE` | 30 | Minimum total observations for PD backtesting. |
| `MIN_DEFAULTS_FOR_LGD` | 20 | Minimum resolved defaults with recovery data for LGD backtesting. |
| `MIN_DEFAULTS_PER_GRADE` | 5 | Minimum defaults per risk grade for grade-level PD analysis. |

If your dataset does not meet these thresholds:
1. Extend the observation period to capture more defaults.
2. Pool similar segments to increase sample size.
3. The API response includes the actual count vs. the minimum required, which helps determine how far below the threshold you are.

## Monte Carlo Convergence

**Symptoms:**
- Monte Carlo simulation results vary significantly between runs.
- The convergence check flag in simulation output indicates non-convergence.

**Root cause:** The number of simulation paths is too low for the portfolio complexity. The default is 1,000 simulations, which may not be sufficient for large or heterogeneous portfolios.

**Resolution:**

1. **Increase simulations** -- Adjust the `n_simulations` parameter in the admin configuration under `model_config.default_parameters`:
   ```json
   {
     "n_simulations": 10000,
     "max_simulations": 50000,
     "pd_lgd_correlation": 0.30
   }
   ```

2. **Convergence guidelines:**
   - 1,000 simulations: Suitable for small, homogeneous portfolios.
   - 5,000-10,000 simulations: Recommended for production use with diverse portfolios.
   - 50,000 simulations: Maximum allowed. Use for regulatory submissions where precision is critical.

3. **Runtime tradeoff** -- Each doubling of simulation count approximately doubles the computation time. Monitor job duration and adjust based on your reporting deadlines.

## Audit Trail Hash Chain Breaks

**Symptoms:**
- The audit chain verification endpoint returns `"valid": false` with a `broken_at_index`.
- Audit export packages show chain integrity failures.

**Root cause:** The hash chain breaks when an audit entry is modified or deleted directly in the database, bypassing the platform API. Each entry's hash depends on the previous entry's hash, so any modification cascades through the chain.

**Resolution:**

1. **Investigate the break point** -- The `broken_at_index` tells you which entry was tampered with. Query the audit table directly to inspect entries around that index.

2. **Prevention** -- The audit tables are designed as INSERT-only. No `UPDATE` or `DELETE` operations should ever be performed on `audit_trail` or `config_audit_log`. Enforce this at the database level with restricted permissions if possible.

3. **Recovery** -- There is no automated way to repair a broken hash chain. The broken chain serves as evidence that data integrity was compromised. Document the incident and the investigation findings for your audit committee.

:::danger
A broken audit trail hash chain is a serious compliance issue. It may indicate unauthorized data modification and should be escalated to your risk and compliance team immediately.
:::

## Permission Denied Errors

**Symptoms:**
- API calls return HTTP 403 with `"Permission denied: role 'X' does not have 'Y' permission"`.
- Users cannot access features they expect to have.

**Root cause:** The user's assigned role does not include the required permission for the requested action.

**Resolution:**

1. **Check the user's role:**
   ```
   GET /api/rbac/users/{user_id}
   ```

2. **Check the permission:**
   ```
   GET /api/rbac/check-permission?user_id={user_id}&action={action}
   ```

3. **Upgrade the role** if appropriate. Refer to the [User Management](./user-management.md) page for the complete permission matrix.

4. **Development environment** -- If no `X-Forwarded-User` or `X-User-Id` header is sent, the user is treated as anonymous with no permissions in the permission list (though RBAC enforcement is bypassed in this case). Ensure you are sending the correct header in your API calls.

## Frontend Build Issues

**Symptoms:**
- The UI does not load or shows a blank page.
- Build errors during deployment.

**Root cause:** Frontend dependency or build configuration issues.

**Resolution:**

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start the development server with hot reload. Use for local development. |
| `npm run build` | Create a production build. Check for TypeScript and build errors in the output. |
| `npm run preview` | Serve the production build locally for testing before deployment. |

Common build issues:

1. **Missing dependencies** -- Run `npm install` to ensure all packages are present.
2. **TypeScript errors** -- The build will fail on type errors. Check the build output for specific file and line references.
3. **Environment variables** -- Ensure `VITE_API_BASE_URL` or equivalent environment variables are set correctly for your deployment target.

## Configuration Reset

**Symptoms:**
- Platform behavior is erratic due to corrupted or invalid configuration.
- You need to return to a known-good state.

**Endpoint:**
```
POST /api/admin/seed-defaults
```

This resets all configuration sections to factory defaults. Use it when:
- Configuration has been corrupted by invalid manual edits.
- You want to start fresh after experimentation.
- Upgrading from a previous version that had incompatible config structure.

:::danger
This operation destroys all custom configuration including data source mappings, model parameters, SICR thresholds, and job settings. There is no undo. Export your current configuration first if you may need to restore it.
:::

## Request Tracing

Every API request is tagged with an `X-Request-ID` for end-to-end tracing.

### How It Works

1. If the client sends an `X-Request-ID` header, that value is preserved.
2. Otherwise, the platform generates a 12-character identifier.
3. The ID is included in the response `X-Request-ID` header.
4. All log entries for that request include the `request_id` field.

### Using Request IDs for Diagnosis

When a user reports an error:

1. Ask for the `X-Request-ID` from the error response (it is included in the JSON error body).
2. Search the application logs for that request ID:
   ```
   grep "request_id=a1b2c3d4e5f6" /path/to/app.log
   ```
3. The logs will show the complete request lifecycle including method, path, status code, duration, and any error stack traces.

**Example log sequence:**
```
INFO  request_id=a1b2c3d4e5f6 method=POST path=/api/models/run status=500 duration_ms=1234.5
ERROR Unhandled error: request_id=a1b2c3d4e5f6 path=/api/models/run error=division by zero
```

## Quick Diagnostic Checklist

When the platform is not functioning correctly, work through this checklist:

| Step | Check | Command / Endpoint |
|------|-------|--------------------|
| 1 | Is the application running? | Check process / container status |
| 2 | Can it reach Lakebase? | `GET /api/health` |
| 3 | Are all tables present? | `GET /api/health/detailed` |
| 4 | Is the config loaded? | `GET /api/admin/config` |
| 5 | Is SciPy available? | `GET /api/health/detailed` (check `scipy` section) |
| 6 | Are credentials valid? | Check logs for token refresh status |
| 7 | Is the user authenticated? | Check `X-Forwarded-User` header is present |
| 8 | Does the user have permission? | `GET /api/rbac/check-permission` |
| 9 | Is the project locked? | Check `signed_off` flag on the project |
| 10 | Is the audit chain intact? | `GET /api/audit/{project_id}/verify` |
