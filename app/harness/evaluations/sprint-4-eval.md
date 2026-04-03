# Sprint 4 Evaluation

**Sprint**: 4 (Iteration 2)
**Date**: 2026-04-02
**Quality Target**: 9.5/10
**Evaluator**: Independent evaluation — no context from Build Agent reasoning

---

## Test Suite Results

- **Full suite**: 3,271 passed, 61 skipped, 0 failed (78.19s)
- **Sprint 4 tests**: 225 collected (77 GL/Reports/RBAC + 72 Audit/Admin/Mapping + 53 Advanced/Pipeline + 11 regression + parametrized expansions)
- **Regressions**: 0
- **Contract target (150+ new tests)**: EXCEEDED (225 tests)

---

## Contract Criteria Assessment

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | All 7 GL journal endpoints tested | **PASS** | generate, list, get, post, reverse, trial-balance, chart-of-accounts all covered |
| 2 | All 6 report endpoints tested (5 types) | **PASS** | generate x5, list, get, finalize, export CSV, export PDF — all tested |
| 3 | All 8 RBAC endpoints tested | **PASS** | users list/get, approvals CRUD, approve/reject, history, permissions |
| 4 | All 5 audit endpoints tested | **PASS** | config changes, diff, project trail, verify chain, export |
| 5 | All 16 admin endpoints tested | **PASS** | Full coverage across config, mapping, tables, columns, etc. |
| 6 | All 9 data mapping endpoints tested | **PASS** | catalogs, schemas, tables, columns, preview, validate, suggest, apply, status |
| 7 | All 9 advanced endpoints tested | **PASS** | cure-rates, CCF, collateral — compute/list/get for each |
| 8 | All 7 period close endpoints tested | **PASS** | start, steps, run get, execute-step, complete, health, run-all |
| 9 | Error paths (404, 400, 500) | **PASS** | Missing resources, invalid inputs, backend exceptions all tested |
| 10 | GL double-entry validation | **PASS** | debits = credits verified in tests |
| 11 | RBAC maker-checker | **PASS** | Analyst cannot approve, approver can — segregation tested |
| 12 | Audit chain integrity | **PASS** | Hash chain verification tested |
| 13 | Period close pipeline ordering | **PASS** | Step ordering, failure handling, run-all stops on error |
| 14 | All existing tests pass (zero regressions) | **PASS** | 3,271 passed, 0 failed |
| 15 | 150+ new tests added | **PASS** | 225 new tests (exceeds by 50%) |

**Contract compliance: 15/15 criteria PASS**

---

## Scores

| Criterion | Weight | Score | Notes | Remediation |
|-----------|--------|-------|-------|-------------|
| Feature Completeness | 25% | 9/10 | 225 tests across 67 endpoints, all contract criteria met. 3 bug fixes attempted, 1 fully fixed (BUG-S4-001), 1 partially effective (BUG-S4-002), 1 appropriate (BUG-S4-003). BUG-S4-002 fix failed in production — the ALTER TABLE is silently swallowed. | **Fix:** `domain/attribution.py:60-63` — replace silent `except: pass` with proper error handling: either re-raise the exception so compute_attribution() doesn't proceed, or use `DROP TABLE IF EXISTS` + `CREATE TABLE` as a fallback when ALTER fails. |
| Code Quality & Architecture | 15% | 9/10 | Test code is well-structured: clear fixtures, proper mocking, parametrized edge cases. Regression tests are thorough. One file (test_qa_sprint_4_gl_reports_rbac.py) is 786 lines but acceptable for a test file. `routes/simulation.py` is 394 lines (>200 line limit) but pre-existing, not introduced by Sprint 4. | No remediation needed for Sprint 4 scope. |
| Testing Coverage | 15% | 9/10 | 225 new tests covering 67 endpoints. Domain-specific validation (double-entry, maker-checker, chain integrity, cure-rate bounds, CCF bounds) is excellent. Tests use proper mocking patterns consistent with prior sprints. | No remediation needed. |
| UI/UX Polish | 20% | 8/10 | This is a testing sprint with no new UI features. However, 3 pre-existing API bugs were discovered and NOT fully resolved: (1) CSV export broken for all reports, (2) attribution compute still HTTP 500, (3) pipeline health NaN serialization. These are production-impacting bugs that degrade the user experience. | **Fix:** See bug list below — all 3 bugs need resolution. |
| Production Readiness | 15% | 8/10 | Zero test regressions. BUG-S4-001 fix is solid (timestamp serialization). But BUG-S4-002 fix is ineffective in production (silent error swallowing is an anti-pattern). The `except: pass` at `attribution.py:63` masks real errors. Pipeline health endpoint at `routes/period_close.py:85-88` has no error handling at all — bare return with no try/except. | **Fix:** `domain/attribution.py:62-63` — do NOT silently swallow ALTER TABLE errors. Re-raise or log at ERROR level and abort. **Fix:** `routes/period_close.py:85-88` — wrap `get_pipeline_health()` call in try/except, sanitize NaN values before JSON serialization. |
| Deployment Compatibility | 10% | 9/10 | Tests run clean, no new deps introduced, all existing tests pass. Bug fixes are backward-compatible. | No remediation needed. |
| Domain Accuracy | +10% (reweight) | 9/10 | IFRS 9 domain tests are accurate: GL chart of accounts structure correct, cure rates decrease by DPD (73.4% to 4%), CCF revolving vs amortizing correct, collateral haircuts 3%-43%, maker-checker-approver hierarchy correct, audit chain hash verification correct. | No remediation needed. |

### Weighted Total

| Criterion | Weight (reweighted) | Score | Contribution |
|-----------|---------------------|-------|-------------|
| Feature Completeness | 22.7% | 9 | 2.045 |
| Code Quality & Architecture | 13.6% | 9 | 1.227 |
| Testing Coverage | 13.6% | 9 | 1.227 |
| UI/UX Polish | 18.2% | 8 | 1.455 |
| Production Readiness | 13.6% | 8 | 1.091 |
| Deployment Compatibility | 9.1% | 9 | 0.818 |
| Domain Accuracy | 9.1% | 9 | 0.818 |
| **Weighted Total** | **100%** | | **8.68/10** |

---

## Bugs Found

### BUG-S4-E-001: Attribution Compute Still Broken (CRITICAL)
- **Endpoint**: `POST /api/data/attribution/{project_id}/compute`
- **Error**: `column "reconciliation" of relation "ecl_attribution" does not exist`
- **Repro**: `curl -s -X POST http://localhost:8000/api/data/attribution/1/compute` returns HTTP 500
- **Root cause**: The iteration 2 fix at `domain/attribution.py:60-63` uses `ALTER TABLE ADD COLUMN IF NOT EXISTS` but catches the `InsufficientPrivilege` exception with a bare `except: pass`. The column is never added, and `compute_attribution()` proceeds to INSERT which fails.
- **Fix:** `domain/attribution.py:60-63` — Replace `except: pass` with proper error handling. Option A: catch the specific exception, log at ERROR, and re-raise so `compute_attribution()` aborts with a clear error message ("Cannot migrate ecl_attribution table — insufficient privileges. Contact your DB admin to grant ALTER privileges or drop and recreate the table."). Option B: As a fallback, try `DROP TABLE ecl_attribution` then `CREATE TABLE` with the new schema (this will work if the app user has DROP privileges).

### BUG-S4-E-002: Report CSV Export Broken (MAJOR)
- **Endpoint**: `GET /api/reports/{report_id}/export`
- **Error**: `dict contains fields not in fieldnames: 'gross_carrying_amount', 'credit_grade', 'assessed_stage', 'loan_count', 'avg_pd', 'ecl_amount'`
- **Repro**: `curl -s http://localhost:8000/api/reports/<any_report_id>/export` returns HTTP 500
- **Root cause**: `routes/reports.py:75` initializes `csv.DictWriter` with `fieldnames=rows[0].keys()`. When report data rows have inconsistent keys (some rows have more fields than the first row), DictWriter raises ValueError.
- **Fix:** `routes/reports.py:75` — Collect ALL unique keys across ALL rows: `fieldnames = list(dict.fromkeys(k for row in rows for k in row.keys()))`, then pass to DictWriter with `extrasaction='ignore'` as safety net.

### BUG-S4-E-003: Pipeline Health NaN Serialization (MAJOR)
- **Endpoint**: `GET /api/pipeline/health/{project_id}`
- **Error**: `Out of range float values are not JSON compliant: nan`
- **Repro**: `curl -s http://localhost:8000/api/pipeline/health/proj-001` returns HTTP 500 (for projects with no prior pipeline runs)
- **Root cause**: `domain/period_close.py:get_pipeline_health()` computes metrics that produce NaN (likely division by zero when no runs exist). The `routes/period_close.py:85-88` endpoint returns the result directly with no error handling or NaN sanitization.
- **Fix:** `routes/period_close.py:85-88` — Add try/except around `get_pipeline_health()`. In `domain/period_close.py`, sanitize NaN values before returning: `import math; result = {k: (0.0 if isinstance(v, float) and math.isnan(v) else v) for k, v in result.items()}`. Also handle the "no runs" case explicitly to prevent division by zero.

---

## Product Suggestions → New Sprints

| ID | Suggestion | Priority | Added to Backlog? |
|----|-----------|----------|-------------------|
| SUG-S4-001 | Fix all 3 production bugs (attribution, CSV export, pipeline health) | HIGH | Yes — should be addressed before Sprint 5 proceeds |
| SUG-S4-002 | Add integration tests that hit the live DB (not just mocked tests) for critical paths like attribution compute | HIGH | Yes — Sprint 9 (integration testing sprint) |
| SUG-S4-003 | Add `extrasaction='ignore'` as default safety to all CSV export paths | LOW | No — skip, single fix in reports.py is sufficient |

---

## Recommendation: REFINE

### Rationale

The sprint achieves excellent test coverage (225 tests, 67 endpoints, all contract criteria met) and the test code quality is high. However, the weighted score of **8.68/10** falls below the quality target of **9.5/10** because:

1. **CRITICAL**: BUG-S4-002 (attribution compute) was claimed as fixed but is NOT fixed in production. The fix uses a silent `except: pass` that masks the real error — this is an anti-pattern that makes debugging harder, not better.
2. **MAJOR**: Report CSV export is broken for every report (BUG-S4-E-002). This is a core feature.
3. **MAJOR**: Pipeline health endpoint crashes with NaN serialization (BUG-S4-E-003). This breaks monitoring.

The VQA report recommended "PROCEED with caveats" and classified these as "pre-existing production bugs." While it's true Sprint 4's *test code* didn't introduce these bugs, Sprint 4's *bug fix scope* explicitly included BUG-S4-002, and that fix failed. The other two bugs were discovered during Sprint 4 testing and have clear, specific fixes — they should be addressed before advancing.

### If REFINE: Prioritized Fixes (builder acts on these directly)

1. **[CRITICAL Fix]**: `domain/attribution.py:60-63` — Remove silent `except: pass`. Either re-raise with a clear error message ("Cannot migrate ecl_attribution — insufficient privileges"), or implement a DROP + CREATE fallback. The compute_attribution() function must NOT proceed when the table schema is wrong.

2. **[MAJOR Fix]**: `routes/reports.py:75` — Replace `fieldnames=rows[0].keys()` with `fieldnames = list(dict.fromkeys(k for row in rows for k in row.keys()))` to collect all unique field names across all rows. This ensures DictWriter handles inconsistent row schemas.

3. **[MAJOR Fix]**: `routes/period_close.py:85-88` — Add try/except around `get_pipeline_health()`. In `domain/period_close.py`, sanitize NaN values before returning and handle the zero-runs case explicitly to prevent division by zero.

4. **[Regression Tests]**: Add regression tests for all 3 bugs (at least 3 tests each) in `tests/regression/test_sprint_4_bugs.py`.
