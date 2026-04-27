# Context Reset 3 — After Sprint 4 (Current Run)

## Current State
- Sprints completed: Sprint 1 (9.8), Sprint 2 (9.8), Sprint 3 (9.8)
- Current sprint: 4 — Security Hardening + Input Validation
- Remaining spec items: Sprint 4, Sprint 5 (Performance), Sprint 6 (CI/CD + Polish)
- Background agents pending: Install (Sprint 3), Integration (Sprint 3)
- Active debt: None

## Key Decisions Made
- Tests at `/Users/steven.tan/Expected Credit Losses/tests/` via `app/pytest.ini` with `testpaths = ../tests`
- Frontend tests at `app/frontend/src/components/*.test.tsx`, run via vitest
- Backend reporting tests mock `reporting.report_helpers as _h` for DB access
- ECL tests mock `backend` module for DB access
- `_safe_identifier()` in data_mapper handles SQL injection prevention
- Total test count: 5601 (4995 backend + 606 frontend)

## Sprint 4 Acceptance Criteria
1. Rate limiting middleware (100 req/min global, 5/min simulation, 10/min reports)
2. Pydantic input validation on all request bodies with max-length constraints
3. CORS configuration review
4. Security test suite: SQL injection, XSS, RBAC bypass tests
5. All tests pass

## Open Evaluator Feedback
- None — all sprints passed at 9.8 on first iteration

## Architecture
- backend.py is main FastAPI app with routes across domain modules
- React frontend at app/frontend/, built to app/static/
- FastAPI serves SPA + docs + API at port 8001
- 21 feature modules, 140+ endpoints

## Files to Read on Resume
- harness/spec.md (Sprint 4 section)
- harness/state.json
- app/backend.py (main FastAPI app with routes)
- app/app.py (app entry point)
