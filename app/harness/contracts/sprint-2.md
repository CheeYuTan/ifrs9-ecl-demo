# Sprint 2 Contract: Analytics Middleware + Request Tracking

## Acceptance Criteria

- [ ] `middleware/analytics.py` exists with `AnalyticsMiddleware` class extending `BaseHTTPMiddleware`
- [ ] Middleware captures: user_id (from `X-Forwarded-User` / `X-User-Id` headers), endpoint, method, status_code, duration_ms, request_id (from `request.state.request_id`), user_agent
- [ ] Fire-and-forget recording via `threading.Thread(daemon=True)` — does not block responses
- [ ] Excluded paths: `/assets/`, `/docs/`, `/api/health` — no recording for these
- [ ] Middleware registered in `app.py` between `ErrorHandlerMiddleware` and `RequestIDMiddleware`
- [ ] All existing tests (~3946+45) continue passing
- [ ] New unit tests cover: path exclusion, header extraction, fire-and-forget behavior, middleware ordering, error handling during recording

## API Contract

No new API endpoints in this sprint. The middleware operates transparently on all requests.

## Test Plan

- **Unit tests** (`tests/unit/test_analytics_middleware.py`):
  1. Path exclusion: `/assets/foo.js`, `/docs/guide`, `/api/health` are skipped
  2. Normal path: `/api/projects` is recorded
  3. Header extraction: `X-Forwarded-User` and `X-User-Id` fallback
  4. Default user_id when no header present
  5. Fire-and-forget: `threading.Thread` is called with `daemon=True`
  6. Duration measurement: duration_ms is calculated and > 0
  7. Error during recording does not crash the response
  8. Middleware ordering verification in `app.py`
  9. Request ID extracted from `request.state.request_id`
  10. User-Agent header captured

## Production Readiness Items This Sprint

- Zero performance impact: fire-and-forget threading ensures <1ms added latency
- Graceful degradation: recording failures are logged but never block responses
