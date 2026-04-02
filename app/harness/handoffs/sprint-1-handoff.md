# Sprint 1 Handoff: Backend API — Core Workflow & Data Endpoints

## Iteration 2 — Edge Cases & Deeper Coverage

### What Changed in Iteration 2

Added 34 new tests covering edge cases and untested code paths identified by reading the route source code:

**Sign-Off Edge Cases (5 tests)**:
- `audit_log` stored as JSON string instead of list (exercises the `isinstance(audit_log, str)` branch in projects.py:88-93)
- `audit_log` as invalid JSON string (exercises the `except` branch in projects.py:93)
- Empty audit_log (no executor found → sign-off succeeds)
- Different executor and signer (segregation passes)
- Multiple audit entries → verifies LAST executor is used (reversed iteration)

**Project CRUD Edge Cases (4 tests)**:
- Create with empty strings for optional fields
- Create with non-default project_type ("cecl")
- Advance with custom status parameter
- Advance ValueError detail preserved in 404 response

**Hash Verification (2 tests)**:
- Full response shape validation (all 6 fields)
- not_computed response shape validation

**Overlay Edge Cases (2 tests)**:
- Multiple overlay items at once (verifies all passed through)
- Optional `ifrs9` field preserved in serialization

**Scenario Weights (2 tests)**:
- Standard 3-scenario IFRS 9 setup
- Single scenario edge case (weight 1.0)

**Data Endpoint Validation (5 tests)**:
- Missing required `scenario` query param → 422
- Invalid stage (non-integer) → 422
- Negative and zero limit values

**Serialization (2 tests)**:
- Decimal values become float (exercises `_SafeEncoder`)
- datetime values serialize to ISO format

**Error Messages (3 tests)**:
- Verify 500 error details are descriptive and mention the endpoint context

**Large/Small DataFrames (2 tests)**:
- 100-row DataFrame returns all rows
- Single-row DataFrame

**Setup Edge Cases (3 tests)**:
- seed-data response shape
- validate-tables response shape
- Status error message is descriptive

**Project List & Reset Edge Cases (4 tests)**:
- 50-project large result set
- Projects with signed_off_by values
- Reset returns step 1 with clean state
- Reset error message preserved in 400

## Cumulative Stats (Iteration 1 + 2)

- **Total new tests**: 174 (140 from iter 1 + 34 from iter 2)
- **Endpoints covered**: 47 (10 projects + 32 data + 5 setup)
- **Full suite**: 2,593 passed, 61 skipped, 0 failures

## How to Test

```bash
cd "/Users/steven.tan/Expected Credit Losses"
source .venv/bin/activate
python -m pytest tests/unit/test_qa_sprint_1_core_routes.py -v
```

## Test Results

```
174 passed in 0.68s
Full suite: 2593 passed, 61 skipped in 109.50s — ZERO failures
```

## Bugs Found
None — all endpoints behave as documented. The JSON-string audit_log path and invalid-JSON path both work correctly.

## Known Limitations
- Sign-off tests mock `require_permission` directly rather than testing the full auth middleware chain
- Data route tests verify structure (list return, 500 on error) but don't validate DataFrame column schemas since those depend on the domain layer

## Files Changed
- `tests/unit/test_qa_sprint_1_core_routes.py` (UPDATED — 174 tests, +34 from iteration 2)
- `harness/handoffs/sprint-1-handoff.md` (UPDATED — this file)
