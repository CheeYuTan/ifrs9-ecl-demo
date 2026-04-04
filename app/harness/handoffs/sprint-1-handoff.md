# Sprint 1 Handoff: Usage Analytics Backend

## What Was Built
- `domain/usage_analytics.py`: New domain module with `ensure_usage_table()`, `record_request()`, `get_usage_stats()`, `get_recent_requests()`
- New Lakebase table `expected_credit_loss.app_usage_analytics` (id, timestamp, user_id, method, endpoint, status_code, duration_ms, request_id, user_agent)
- Wired into `domain/workflow.py` init chain (after `ensure_rbac_tables`)
- Re-exported in `backend.py` for unified imports
- 15 unit tests covering table creation, idempotency, record insertion, stats queries, edge cases

## How to Test
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- The table is auto-created on startup via the init chain
- No HTTP endpoints this sprint (domain layer only) — Sprint 2 adds middleware + Sprint 4 adds admin API

### Verify programmatically:
```python
from domain.usage_analytics import ensure_usage_table, record_request, get_usage_stats, get_recent_requests
ensure_usage_table()  # idempotent
record_request("test-user", "GET", "/api/projects", 200, 42.5, "req-123", "test-agent")
stats = get_usage_stats(days=7)
recent = get_recent_requests(limit=10)
```

## Test Results
```
pytest tests/unit/test_usage_analytics.py -v
15 passed in 0.10s
```

## Known Limitations
- No HTTP API to query analytics yet (Sprint 4)
- No middleware to auto-record requests yet (Sprint 2)
- Table uses PostgreSQL INTERVAL syntax for date filtering (Lakebase compatible)

## Files Changed

### New Files
- `domain/usage_analytics.py` — domain module (96 lines)
- `tests/unit/test_usage_analytics.py` — 15 unit tests (131 lines)

### Modified Files
- `domain/workflow.py` — added `ensure_usage_table` to init chain (4 lines added)
- `backend.py` — added usage analytics re-exports (7 lines added)
