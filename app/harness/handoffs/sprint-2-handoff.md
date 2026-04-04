# Sprint 2 Handoff: Analytics Middleware + Request Tracking

## What Was Built

- `middleware/analytics.py`: Starlette `BaseHTTPMiddleware` that captures API request metrics (user, endpoint, method, status, duration, request_id, user_agent) and records them to Lakebase via fire-and-forget daemon threads
- Middleware registered in `app.py` between `ErrorHandlerMiddleware` (outermost) and `RequestIDMiddleware` (innermost)
- 20 unit tests covering path exclusion, header extraction, fire-and-forget behavior, middleware ordering, error tolerance

## Key Design Decisions

- **Fire-and-forget via `threading.Thread(daemon=True)`**: Recording runs in a daemon thread so it never blocks the HTTP response. If recording fails (DB down, pool exhausted), the exception is logged and swallowed.
- **Path exclusions**: `/assets/*`, `/docs/*`, and `/api/health` are excluded to avoid recording static asset requests, documentation serving, and health checks.
- **User identity**: Extracted from `X-Forwarded-User` header (Databricks Apps proxy), falling back to `X-User-Id`, then `"anonymous"`.
- **Request ID reuse**: Reads `request.state.request_id` set by the inner `RequestIDMiddleware` for cross-referencing with request logs.

## How to Test

- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- Make any API request (e.g., `GET /api/health/detailed`, `GET /api/projects`)
- Verify: records appear in `expected_credit_loss.app_usage_analytics` table
- Verify: `/assets/*`, `/docs/*`, and `/api/health` requests are NOT recorded

## Test Results

- `pytest tests/unit/test_analytics_middleware.py`: **20 passed** in 0.12s
- `pytest tests/` (full suite): **4010 passed, 61 skipped** in 641s
- 1 pre-existing failure (`test_simulation_seed.py::test_same_seed_same_result`) — confirmed failing identically without Sprint 2 changes (floating point non-determinism in ECL engine, unrelated)

## Known Limitations

- Recording is best-effort: if the DB pool is exhausted or unavailable, analytics records are silently dropped (logged at ERROR level)
- No batching: each request spawns one thread and one INSERT. For very high-throughput scenarios, a batching approach would be more efficient.

## Files Changed

- **Created**: `middleware/analytics.py` (88 lines)
- **Created**: `tests/unit/test_analytics_middleware.py` (197 lines)
- **Modified**: `app.py` (added 2 lines — import + middleware registration)
- **Modified**: `harness/contracts/sprint-2.md` (updated for current sprint)
