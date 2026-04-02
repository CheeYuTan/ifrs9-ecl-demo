# Sprint 1 Handoff: Backend API — Core Workflow & Data Endpoints

## Iteration 3 — Utils Unit Tests + Gap Coverage

### What Changed in Iteration 3

Added 62 new tests in a supplementary file covering previously untested paths:

**`_utils.py` Direct Unit Tests (32 tests)**:
- `_sanitize`: NaN, Inf, -Inf become None; nested dict/list sanitization; mixed types; empty containers; passthrough for strings/None/int
- `_SafeEncoder`: Decimal→float, datetime→ISO, date→ISO, unsupported type raises TypeError, DecimalEncoder alias
- `df_to_records`: simple DF, empty DF, NaN columns, Decimal columns, mixed types, single column, all-NaN column
- `serialize_project`: None→None, Decimal conversion, datetime conversion, nested structures, empty dict

**Sign-Off Gap Coverage (4 tests)**:
- `get_project` returns `None` → sign-off still calls backend (no 404 check after signed_off check)
- Project dict missing `audit_log` key → defaults to empty list safely
- Non-dict audit log entries (strings, ints) → skipped safely during executor search
- Non-dict entries with matching executor → segregation of duties still enforced

**Verify-Hash Tampered Data (4 tests)**:
- Tampered data → `status: "invalid"`, `match: false`, different `stored_hash` vs `computed_hash`
- Valid hash → `status: "valid"`, `match: true`, hashes match
- Correct `ecl_data` dict (project_id, step_status, overlays, scenario_weights) passed to verify function
- `signed_off_by` and `signed_off_at` fields present in response

**Setup Route Gaps (4 tests)**:
- `POST /api/setup/complete` without body → uses default "admin" user
- `POST /api/setup/complete` with explicit user → passes to backend
- `POST /api/setup/seed-sample-data` → calls `backend.ensure_tables()`
- Seed data error → preserves original error message in 500

**Overlay Advance Verification (3 tests)**:
- With comment → `advance_step` called with correct args ("overlays", "Overlays Submitted", "Credit Risk Analyst", comment)
- Without comment (empty string) → `advance_step` NOT called
- Multiple overlay items with `ifrs9` field → `model_dump()` produces correct dict shape, default "" for missing ifrs9

**Data Endpoint Mixed Types (5 tests)**:
- Boolean columns preserved (True/False)
- None values in DataFrame
- Integer columns preserved (no float coercion)
- Large numeric values (1e12)
- Unicode/special characters in strings

**Data Consistency (5 tests)**:
- Stage distribution: all 3 IFRS9 stages present, loan counts sum correctly
- Scenario-specific ECL queries return different data per scenario
- `top-exposures` limit parameter passed through
- `loans-by-product` passes product_type string to backend
- `loans-by-stage` passes stage as int to backend

**Project Lifecycle (3 tests)**:
- Create then get returns consistent project_id
- `advance_step` receives all body fields (action, user, detail, status)
- `save_scenario_weights` receives weights dict correctly

**Approval History (2 tests)**:
- Returns list of approval action dicts
- ImportError in governance.rbac → 500

## Cumulative Stats (Iterations 1 + 2 + 3)

- **Total new tests**: 236 (140 iter 1 + 34 iter 2 + 62 iter 3)
- **Test files**: `test_qa_sprint_1_core_routes.py` (174 tests) + `test_qa_sprint_1_utils_and_gaps.py` (62 tests)
- **Endpoints covered**: 47 (10 projects + 32 data + 5 setup) + `_utils.py` utility module
- **Full suite**: 2,655 passed, 61 skipped, 0 failures

## How to Test

```bash
cd "/Users/steven.tan/Expected Credit Losses"
source .venv/bin/activate
python -m pytest tests/unit/test_qa_sprint_1_core_routes.py tests/unit/test_qa_sprint_1_utils_and_gaps.py -v
```

## Test Results

```
Sprint 1 tests: 236 passed (174 + 62) in ~0.95s
Full suite: 2,655 passed, 61 skipped in 111s — ZERO failures
```

## Bugs Found
None — all endpoints behave as documented. Notable finding: `sign_off` endpoint does NOT check for project existence before calling `sign_off_project`, which means signing off a non-existent project delegates the error to the backend layer rather than returning 404 from the route.

## Known Limitations
- Sign-off tests mock `require_permission` directly rather than testing full auth middleware chain
- Data route tests verify structure but don't validate backend query logic (mocked)
- Hash verification tests mock `compute_ecl_hash`/`verify_ecl_hash` rather than testing actual hash algorithm

## Files Changed
- `tests/unit/test_qa_sprint_1_core_routes.py` (unchanged — 174 tests from iterations 1-2)
- `tests/unit/test_qa_sprint_1_utils_and_gaps.py` (NEW — 62 tests for iteration 3)
- `harness/handoffs/sprint-1-handoff.md` (UPDATED — this file)
- `harness/state.json` (UPDATED)
- `harness/progress.md` (UPDATED)
