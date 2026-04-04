# Sprint 1 Contract: Usage Analytics Backend

## Acceptance Criteria
- [ ] New table `expected_credit_loss.app_usage_analytics` with columns: id SERIAL, timestamp TIMESTAMP DEFAULT NOW(), user_id TEXT, method TEXT, endpoint TEXT, status_code INT, duration_ms FLOAT, request_id TEXT, user_agent TEXT
- [ ] `ensure_usage_table()` creates table idempotently (safe to call multiple times)
- [ ] Table has `COMMENT ON TABLE` with `ifrs9ecl:` prefix tag
- [ ] `record_request()` inserts a usage record with all fields
- [ ] `get_usage_stats(days=7)` returns summary metrics (total requests, unique users, avg duration)
- [ ] `get_recent_requests(limit=50)` returns recent N records ordered by timestamp desc
- [ ] Module registered in `backend.py` re-exports
- [ ] `ensure_usage_table()` wired into `domain/workflow.py` init chain (after `ensure_rbac_tables`)
- [ ] All unit tests pass

## API Contract
- No new HTTP endpoints this sprint (backend domain layer only)
- Functions: `ensure_usage_table()`, `record_request(...)`, `get_usage_stats(days)`, `get_recent_requests(limit)`

## Test Plan
- Unit tests (~10): table creation DDL, idempotency, record_request insertion, get_usage_stats with data, get_usage_stats empty table, get_recent_requests with data, get_recent_requests empty, SCHEMA/PREFIX usage, backend.py re-export accessibility

## Production Readiness Items This Sprint
- Table creation follows existing pattern (CREATE TABLE IF NOT EXISTS)
- COMMENT ON TABLE for catalog discoverability
- Logging consistent with existing domain modules
