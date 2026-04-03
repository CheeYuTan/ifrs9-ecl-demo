# Sprint 9 Contract: Middleware, Cross-Cutting & Integration Testing

## Acceptance Criteria

- [ ] middleware/auth.py: test get_current_user with all header combinations (X-Forwarded-User, X-User-Id, x-user-id, none)
- [ ] middleware/auth.py: test require_permission blocks unauthorized roles, allows authorized
- [ ] middleware/auth.py: test require_permission bypasses RBAC when no auth header present
- [ ] middleware/auth.py: test require_project_not_locked blocks signed-off projects, allows unsigned
- [ ] middleware/auth.py: test compute_ecl_hash produces consistent SHA-256 for same input
- [ ] middleware/auth.py: test verify_ecl_hash detects tampered data
- [ ] middleware/error_handler.py: test unhandled exceptions return 500 with structured JSON
- [ ] middleware/error_handler.py: test error response includes request_id and path
- [ ] middleware/error_handler.py: test no stack traces leak in error response
- [ ] middleware/request_id.py: test X-Request-ID header added to every response
- [ ] middleware/request_id.py: test client-provided X-Request-ID is preserved
- [ ] middleware/request_id.py: test request_id stored on request.state
- [ ] middleware/request_id.py: test /assets/ and /docs/ paths excluded from logging
- [ ] db/pool.py: test _is_auth_error detects all known error patterns
- [ ] db/pool.py: test _t() builds correct table names with schema/prefix
- [ ] db/pool.py: test load_schema_from_config loads and caches schema
- [ ] db/pool.py: test query_df retry logic on OperationalError
- [ ] db/pool.py: test execute retry logic on OperationalError
- [ ] Integration flow 1: Create project -> advance through all steps -> sign-off (full lifecycle)
- [ ] Integration flow 2: Run simulation validation -> get defaults -> verify consistency
- [ ] Integration flow 3: Model registration -> backtest -> promote champion flow
- [ ] Integration flow 4: Approval request -> approve -> verify in history
- [ ] Integration flow 5: Period-close pipeline step sequencing
- [ ] Integration flow 6: Data mapping suggest -> validate -> apply pipeline

## Test Plan

- **Unit tests**: `tests/unit/test_qa_sprint_9_middleware.py` — middleware auth, error handler, request ID
- **Unit tests**: `tests/unit/test_qa_sprint_9_db_pool.py` — connection pool, retry, auth error detection
- **Integration tests**: `tests/unit/test_qa_sprint_9_integration_flows.py` — 6 end-to-end multi-endpoint flows

## Test File Convention

All new test files: `tests/unit/test_qa_sprint_9_*.py`
Do NOT modify existing passing tests.

## Regression Tests

No bugs reported from prior Sprint 9 evaluations (iteration 1).
