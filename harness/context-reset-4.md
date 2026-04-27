# Context Reset 4 — After Sprint 5

## Current State
- Sprints completed: Sprint 1 (9.8), Sprint 2 (9.8), Sprint 3 (9.8), Sprint 4 (9.8), Sprint 5 (9.8)
- Current sprint: 6 — CI/CD + Production Readiness Polish
- Remaining spec items: Sprint 6 only
- Background agents pending: Install (Sprint 3), Integration (Sprint 3), Documentation (Sprint 5), Presentation (Sprint 5)
- Active debt: None

## Key Decisions Made
- Tests at `/Users/steven.tan/Expected Credit Losses/tests/` via `app/pytest.ini` with `testpaths = ../tests`
- Frontend tests at `app/frontend/src/components/*.test.tsx`, run via vitest
- TTL cache utility at `app/utils/cache.py` — thread-safe, supports `@cached` decorator with TTL and prefix
- All 33 domain/queries.py functions use `@cached(ttl=30)` — DATA_TTL=30
- Admin config uses `@cached(ttl=300)` — CONFIG_TTL=300
- Cache invalidation on writes: simulation routes flush `queries:` prefix, admin_config flushes `admin_config:` prefix
- PerfMiddleware tracks per-endpoint latency (ring buffer, p50/p95/p99)
- `tests/conftest.py` mock_db fixture clears global cache before/after each test
- Total test count: 5711 (5105 backend + 606 frontend)

## Sprint 6 Acceptance Criteria
1. GitHub Actions CI pipeline: lint (ruff + eslint), type check (pyright + tsc), backend tests (pytest), frontend tests (vitest)
2. Pre-commit hooks: ruff + eslint auto-format
3. Production deployment checklist document
4. Final polish pass: error messages, logging consistency, API response format
5. All tests pass

## Open Evaluator Feedback
- None — all sprints passed at 9.8 on first iteration

## Architecture
- backend.py is main FastAPI app with routes across domain modules
- React frontend at app/frontend/, built to app/static/
- FastAPI serves SPA + docs + API at port 8001
- 21 feature modules, 140+ endpoints
- TTL cache layer at utils/cache.py, performance middleware at middleware/perf.py

## Files to Read on Resume
- harness/spec.md (Sprint 6 section)
- harness/state.json
- app/app.py (app entry point)
