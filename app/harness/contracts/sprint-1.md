# Sprint 1 Contract: Backend API — Core Workflow & Data Endpoints

## Acceptance Criteria

### Projects Routes (10 endpoints)
- [ ] GET /api/projects — returns list, empty when no projects
- [ ] GET /api/projects/{id} — returns project dict; 404 for missing
- [ ] POST /api/projects — creates project with all fields; verify response shape
- [ ] POST /api/projects/{id}/advance — advances step; 404 for missing project
- [ ] POST /api/projects/{id}/overlays — saves overlays; with and without comment
- [ ] POST /api/projects/{id}/scenario-weights — saves weights; verify response
- [ ] POST /api/projects/{id}/sign-off — signs off; 403 if already signed; 403 segregation-of-duties
- [ ] GET /api/projects/{id}/verify-hash — valid hash, invalid hash, no hash, missing project
- [ ] GET /api/projects/{id}/approval-history — returns history; 500 on failure
- [ ] POST /api/projects/{id}/reset — resets project; 400 on error

### Data Routes (32 endpoints)
- [ ] All 32 GET endpoints return list on success (happy path with real DataFrame data)
- [ ] Parameterized endpoints: ecl-by-stage-product/{stage}, loans-by-product/{type}, loans-by-stage/{stage}, ecl-by-scenario-product-detail?scenario=X, top-exposures?limit=N
- [ ] Empty DataFrame returns empty list
- [ ] Error paths return 500 (fill gaps not covered by existing tests)

### Setup Routes (5 endpoints)
- [ ] GET /api/setup/status — returns status dict; 500 on error
- [ ] POST /api/setup/validate-tables — returns validation dict; 500 on error
- [ ] POST /api/setup/seed-sample-data — returns ok status; 500 on error
- [ ] POST /api/setup/complete — with and without body; 500 on error
- [ ] POST /api/setup/reset — returns result; 500 on error

## Test Plan
- File: `tests/unit/test_qa_sprint_1_core_routes.py`
- Pattern: mock backend functions, test via FastAPI TestClient
- Minimum 80 new tests across all three route modules
- No modification of existing passing tests

## Production Readiness Items
- N/A (QA audit sprint — testing only)
