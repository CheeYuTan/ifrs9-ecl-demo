# Sprint 3 Handoff: Dashboard SQL Queries (7 Files)

## What Was Built

Created the `dashboards/` module with 7 PostgreSQL-compatible SQL query files for Databricks Lakeview dashboard provisioning, plus a Python utility module for loading and parameterising the queries.

### SQL Query Files
1. **`01_user_activity.sql`** — DAU, actions per user, audit trail activity by event type, login frequency (sources: `audit_trail`, `app_usage_analytics`)
2. **`02_project_analytics.sql`** — Projects over time, status distribution, completion rate, project type distribution, avg time to completion (source: `ecl_workflow`)
3. **`03_model_performance.sql`** — AUC/Gini/KS trends over time, latest metrics per model, registry status distribution, champion models (sources: `backtest_metrics`, `model_registry`)
4. **`04_job_execution.sql`** — Pipeline runs over time, success/failure rates, avg duration by status, recent runs (source: `pipeline_runs`)
5. **`05_api_usage.sql`** — Endpoint popularity, p50/p95/p99 latency percentiles, error rate by endpoint, hourly request volume (source: `app_usage_analytics`)
6. **`06_cost_allocation.sql`** — Storage by table via `pg_total_relation_size()`, total schema storage, compute estimates by job type (sources: `pg_tables`, `pipeline_runs`)
7. **`07_system_health.sql`** — Hourly error rate trend, latency trend (p50/p95), requests per minute, status code distribution (source: `app_usage_analytics`)

### Python Module
- **`dashboards/__init__.py`** — `load_query(filename, schema)`, `load_all_queries(schema)`, `list_queries()`. Handles `{schema}` placeholder substitution with SQL-injection-safe schema validation.

## How to Test
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python -m pytest tests/unit/test_dashboard_queries.py -v`
- All 75 tests should pass
- Manual: `python -c "import dashboards; print(dashboards.load_query('01_user_activity.sql'))"`

## Test Results
- `pytest tests/unit/test_dashboard_queries.py`: **75 passed** in 0.12s
- Full suite: **4073 passed**, 61 skipped, 13 failed (all 13 pre-existing — docs homepage regressions + intermittent middleware ordering)
- Coverage: SQL loading, schema substitution, validation, syntax checks, empty-table patterns, table references

## Known Limitations
- SQL queries are designed for PostgreSQL/Lakebase; `PERCENTILE_CONT` and `pg_total_relation_size()` are PostgreSQL-specific
- Queries use multi-statement format (separated by comments) — the provisioning script in Sprint 4 will need to split on `-- ──` boundaries
- 13 pre-existing test failures are not related to this sprint

## Files Changed
- `dashboards/__init__.py` (new — 55 lines)
- `dashboards/01_user_activity.sql` (new — 46 lines)
- `dashboards/02_project_analytics.sql` (new — 54 lines)
- `dashboards/03_model_performance.sql` (new — 43 lines)
- `dashboards/04_job_execution.sql` (new — 49 lines)
- `dashboards/05_api_usage.sql` (new — 50 lines)
- `dashboards/06_cost_allocation.sql` (new — 48 lines)
- `dashboards/07_system_health.sql` (new — 53 lines)
- `tests/unit/test_dashboard_queries.py` (new — 75 tests)
- `harness/contracts/sprint-3.md` (updated)
- `harness/handoffs/sprint-3-handoff.md` (updated)
- `harness/state.json` (updated)
