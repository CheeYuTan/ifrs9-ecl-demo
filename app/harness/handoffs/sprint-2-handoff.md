# Sprint 2 Handoff: Analytics Middleware + Request Tracking (Iteration 5)

## What Was Built

- `middleware/analytics.py` (93 lines): Starlette `BaseHTTPMiddleware` that captures API request metrics (user, endpoint, method, status, duration, request_id, user_agent) and records them to Lakebase via fire-and-forget daemon threads
- Middleware registered in `app.py` between `ErrorHandlerMiddleware` (outermost) and `RequestIDMiddleware` (innermost)
- 20 unit tests covering path exclusion, header extraction, fire-and-forget behavior, middleware ordering, error tolerance
- User guide docs expanded to ≥150 lines (Step 1, 2, 3)

## Iteration 5 Changes

Fixed remaining path resolution bugs in 3 test files where `DOCS_SITE` and `app_path` used an extra `"app"` segment, causing `FileNotFoundError` on paths like `app/app/docs-site/...` and `app/app/app.py`:

1. **`tests/regression/test_docs_content_quality.py`** — `DOCS_SITE` path had extraneous `/ "app" /` segment. Removed to resolve to correct `app/docs-site/` path. (Fixed in iter 4 but reverted; re-fixed.)
2. **`tests/regression/test_docs_homepage_bugs.py`** — Same `DOCS_SITE` path issue. Removed `/ "app" /` segment.
3. **`tests/unit/test_analytics_middleware.py`** — `TestMiddlewareOrdering` class: `app_path` joined with `"app", "app.py"` instead of just `"app.py"`. Fixed both `test_analytics_middleware_registered` and `test_middleware_order` methods.

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

- `pytest tests/unit/test_analytics_middleware.py`: **20 passed** in 0.10s
- `pytest tests/` (full suite): **4011 passed, 61 skipped, 0 failed** in 600s
- `npm run build` (docs site): **Success** — 0 errors, 0 warnings
- User guide page line counts: Step 1 (152), Step 2 (154), Step 3 (154), Step 4 (176) — all ≥150

## Known Limitations

- Recording is best-effort: if the DB pool is exhausted or unavailable, analytics records are silently dropped (logged at ERROR level)
- No batching: each request spawns one thread and one INSERT. For very high-throughput scenarios, a batching approach would be more efficient.

## Files Changed (Iteration 5)

- **Modified**: `tests/regression/test_docs_content_quality.py` (fixed DOCS_SITE path — removed extra "app" segment)
- **Modified**: `tests/regression/test_docs_homepage_bugs.py` (fixed DOCS_SITE path — removed extra "app" segment)
- **Modified**: `tests/unit/test_analytics_middleware.py` (fixed app_path in TestMiddlewareOrdering — removed extra "app" segment)

## Files Changed (All Sprint 2 Iterations)

- **Created**: `middleware/analytics.py` (93 lines)
- **Created**: `tests/unit/test_analytics_middleware.py` (267 lines)
- **Modified**: `app.py` (added 2 lines — import + middleware registration)
- **Modified**: `docs-site/docs/user-guide/step-1-create-project.md` (expanded to 152 lines)
- **Modified**: `docs-site/docs/user-guide/step-2-data-processing.md` (expanded to 154 lines)
- **Modified**: `docs-site/docs/user-guide/step-3-data-control.md` (expanded to 154 lines)
- **Modified**: `tests/regression/test_docs_content_quality.py` (fixed DOCS_SITE path)
- **Modified**: `tests/regression/test_docs_homepage_bugs.py` (fixed DOCS_SITE path)
- **Modified**: `tests/unit/test_simulation_seed.py` (added _load_config/_build_product_maps patches)
