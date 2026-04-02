# Sprint 1 Handoff: Backend API — Core Workflow & Data Endpoints

## What Was Built

New test file covering 47 route endpoints across 3 route modules:

- **`tests/unit/test_qa_sprint_1_core_routes.py`** — 140 new tests
  - `routes/projects.py`: 10 endpoints — 30 tests (happy path, 404, 422, 403, segregation-of-duties, hash verification, approval history)
  - `routes/data.py`: 32 endpoints — 97 tests (27 simple endpoints × 3 parametrized tests each = 81 happy/empty/error, plus 14 parameterized-endpoint tests + 2 NaN/Inf handling)
  - `routes/setup.py`: 5 endpoints — 13 tests (success + error for each, plus edge cases)

## Coverage Details

### Projects Routes (30 tests)
| Endpoint | Tests |
|----------|-------|
| GET /api/projects | 2 (with data, empty) |
| GET /api/projects/{id} | 3 (found, 404, field validation) |
| POST /api/projects | 4 (success, all fields, defaults, missing required 422) |
| POST /api/projects/{id}/advance | 4 (success, with detail, 404, missing field 422) |
| POST /api/projects/{id}/overlays | 3 (no comment, with comment advances step, empty overlays) |
| POST /api/projects/{id}/scenario-weights | 2 (success, empty weights) |
| POST /api/projects/{id}/sign-off | 4 (success, already signed 403, segregation-of-duties 403, with attestation) |
| GET /api/projects/{id}/verify-hash | 4 (valid, invalid, no hash, missing project 404) |
| GET /api/projects/{id}/approval-history | 3 (success, empty, error 500) |
| POST /api/projects/{id}/reset | 2 (success, error 400) |

### Data Routes (97 tests)
- 27 simple GET endpoints: 3 tests each (happy path with data, empty DataFrame, error 500)
- 5 parameterized endpoints: ecl-by-stage-product (stages 1,2,3 + error), ecl-by-scenario-product-detail (success + error), top-exposures (default + custom limit + error), loans-by-product (success + error), loans-by-stage (success + error)
- NaN/Inf sanitization: 2 tests verifying NaN and Inf become null in JSON

### Setup Routes (13 tests)
- status: 3 (complete, not complete, error)
- validate-tables: 3 (valid, missing tables, error)
- seed-sample-data: 2 (success, error)
- complete: 3 (default user, custom user, error)
- reset: 2 (success, error)

## How to Test

```bash
cd "/Users/steven.tan/Expected Credit Losses"
source .venv/bin/activate
python -m pytest tests/unit/test_qa_sprint_1_core_routes.py -v
```

## Test Results

```
140 passed in 0.70s
Full suite: 2559 passed, 61 skipped in 111.95s — ZERO failures
```

## Bugs Found
None — all endpoints behave as documented in the route code.

## Known Limitations
- Sign-off test mocks `require_permission` directly to bypass auth middleware dependency injection; a deeper integration test would test the full middleware chain
- Data route tests verify structure (list return, 500 on error) but don't validate DataFrame column schemas since those depend on the domain layer

## Files Changed
- `tests/unit/test_qa_sprint_1_core_routes.py` (NEW — 140 tests)
- `harness/contracts/sprint-1.md` (UPDATED — new QA contract)
- `harness/handoffs/sprint-1-handoff.md` (UPDATED — this file)
