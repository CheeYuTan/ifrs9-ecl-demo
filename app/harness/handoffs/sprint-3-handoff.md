# Sprint 3 Handoff: Dashboard SQL Queries (7 Files)

## What Was Built

### Iteration 1: Dashboard SQL Module
Created the `dashboards/` module with 7 PostgreSQL-compatible SQL query files for Databricks Lakeview dashboard provisioning, plus a Python utility module for loading and parameterising the queries.

### Iteration 2: Fix 13 Pre-existing Test Failures
Fixed path resolution bugs in 3 test files that failed when pytest collected tests through the symlinked `tests/` directory. Root cause: `Path(__file__).parents[2]` resolved to the wrong directory because `app/tests` is a symlink to `../tests`, and pytest loaded modules from their real (non-symlink) path.

**Files fixed:**
- `tests/regression/test_docs_content_quality.py` — Added `_find_app_root()` helper that walks up from `__file__` looking for `docs-site/`
- `tests/regression/test_docs_homepage_bugs.py` — Same `_find_app_root()` fix
- `tests/unit/test_analytics_middleware.py` — Added `_find_app_py()` static method that walks up looking for `app.py`

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
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python -m pytest -q`
- All 4086 tests should pass (0 failures)
- Dashboard-specific: `python -m pytest tests/unit/test_dashboard_queries.py -v`
- Manual: `python -c "import dashboards; print(dashboards.load_query('01_user_activity.sql'))"`

## Test Results
- `pytest`: **4086 passed**, 61 skipped, **0 failed**
- Previous run had 13 pre-existing failures — all 13 now fixed
- Dashboard query tests: 75 passed
- Coverage: SQL loading, schema substitution, validation, syntax checks, empty-table patterns, table references

## Known Limitations
- SQL queries are designed for PostgreSQL/Lakebase; `PERCENTILE_CONT` and `pg_total_relation_size()` are PostgreSQL-specific
- Queries use multi-statement format (separated by comments) — the provisioning script in Sprint 4 will need to split on `-- ──` boundaries

## Files Changed
### Iteration 1 (new files)
- `dashboards/__init__.py` (55 lines)
- `dashboards/01_user_activity.sql` (46 lines)
- `dashboards/02_project_analytics.sql` (54 lines)
- `dashboards/03_model_performance.sql` (43 lines)
- `dashboards/04_job_execution.sql` (49 lines)
- `dashboards/05_api_usage.sql` (50 lines)
- `dashboards/06_cost_allocation.sql` (48 lines)
- `dashboards/07_system_health.sql` (53 lines)
- `tests/unit/test_dashboard_queries.py` (75 tests)

### Iteration 2 (bug fixes)
- `tests/regression/test_docs_content_quality.py` — path resolution fix
- `tests/regression/test_docs_homepage_bugs.py` — path resolution fix
- `tests/unit/test_analytics_middleware.py` — path resolution fix
