# Sprint 3 Contract: Dashboard SQL Queries (7 Files)

## Acceptance Criteria
- [ ] `dashboards/` directory created with 7 SQL query files + `__init__.py`
- [ ] `01_user_activity.sql`: DAU, actions/user, login frequency from `audit_trail` + `app_usage_analytics`
- [ ] `02_project_analytics.sql`: Projects over time, status distribution, completion rates from `ecl_workflow`
- [ ] `03_model_performance.sql`: AUC/Gini/KS trends, model registry status from `backtest_metrics` + `model_registry`
- [ ] `04_job_execution.sql`: Pipeline run counts, success/failure rates, durations from `pipeline_runs`
- [ ] `05_api_usage.sql`: Endpoint popularity, p50/p95 latency, error rates from `app_usage_analytics`
- [ ] `06_cost_allocation.sql`: Storage by table via `pg_total_relation_size()`, compute estimates by job type
- [ ] `07_system_health.sql`: Error rate trends, latency trends, requests per minute
- [ ] All queries PostgreSQL-compatible, use `COALESCE`/`NULLIF` for empty tables, `DATE_TRUNC` for time-series
- [ ] `dashboards/__init__.py` with `load_query()` and `list_queries()` utilities
- [ ] Unit tests: SQL syntax validation, empty-table handling, date range parameterization
- [ ] All existing ~4011 tests continue to pass

## Table References (schema: `expected_credit_loss`)
| Query File | Source Tables |
|------------|-------------|
| 01 | `audit_trail`, `app_usage_analytics` |
| 02 | `ecl_workflow` |
| 03 | `backtest_metrics`, `model_registry` |
| 04 | `pipeline_runs` |
| 05 | `app_usage_analytics` |
| 06 | `pg_total_relation_size()` (system), `pipeline_runs` |
| 07 | `app_usage_analytics` |

## Test Plan
- Unit tests: SQL file loading via `dashboards` module, syntax validation, parameterization
- Verify each SQL query handles empty tables (COALESCE/NULLIF present)
- Regression: all existing tests pass

## Production Readiness Items
- SQL files use `{schema}` placeholder for schema name substitution
- No hardcoded schema names in SQL files
