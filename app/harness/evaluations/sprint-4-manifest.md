# Sprint 4 Iteration 2 — Interaction Manifest

## Testing Method
Direct HTTP API endpoint testing against live running app on `localhost:8000`. Sprint 4 is a backend API testing sprint — no new UI features. Focus: verify 3 bug fixes from iteration 1, plus comprehensive endpoint coverage.

---

## Bug Fix Verification

### BUG-S4-001: Audit Export Timestamp Serialization
| Test | Result | Status |
|------|--------|--------|
| GET /api/audit/{project_id}/export | 200 — returns valid JSON with ISO string timestamps | **FIXED** ✓ |
| GET /api/audit/config/changes | 200 — `changed_at` fields are string type (e.g., "2026-04-02T04:32:41.129963") | **FIXED** ✓ |

### BUG-S4-002: Attribution Reconciliation Column
| Test | Result | Status |
|------|--------|--------|
| POST /api/data/attribution/{project_id}/compute | 500 — `column "reconciliation" of relation "ecl_attribution" does not exist` | **NOT FIXED** ✗ |
| Direct call to ensure_attribution_table() | ALTER TABLE fails: `InsufficientPrivilege: must be owner of table ecl_attribution` | Root cause identified |

**Root cause**: The code fix (ALTER TABLE ADD COLUMN IF NOT EXISTS) is correct, but the database user running the app does not have `ALTER TABLE` privileges on the `ecl_attribution` table. The error is logged but silently swallowed, so compute_attribution() still fails at the INSERT.

### BUG-S4-003: IFRS 7.35J Historical Defaults Table
| Test | Result | Status |
|------|--------|--------|
| POST /api/reports/generate/{project_id} (ifrs7_disclosure) | Report generates but contains error sections for 35I and 35J | **PARTIAL** — error messaging improved but underlying table still missing |

---

## GL Journals (`/api/gl`) — 7 endpoints

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| Generate | POST | `/api/gl/generate/{project_id}` | 422 — body required (correct validation) | TESTED |
| List Journals | GET | `/api/gl/journals/{project_id}` | 200 — returns array | TESTED |
| Get Journal | GET | `/api/gl/journal/{journal_id}` | No test data available | SKIPPED |
| Post Journal | POST | `/api/gl/journal/{journal_id}/post` | No test data available | SKIPPED |
| Reverse Journal | POST | `/api/gl/journal/{journal_id}/reverse` | No test data available | SKIPPED |
| Trial Balance | GET | `/api/gl/trial-balance/{project_id}` | 200 — returns array | TESTED |
| Chart of Accounts | GET | `/api/gl/chart-of-accounts` | 200 — 9 accounts with IFRS 9 structure | TESTED |

## Reports (`/api/reports`) — 6 endpoint types

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| Generate Report | POST | `/api/reports/generate/{project_id}` | 200 — generates IFRS 7 disclosure | TESTED |
| List Reports | GET | `/api/reports` | 200 — returns report list | TESTED |
| Get Report | GET | `/api/reports/{report_id}` | 200 — returns report detail | TESTED |
| Export CSV | GET | `/api/reports/{report_id}/export` | **500 — fieldnames mismatch** | BUG |
| Export PDF | GET | `/api/reports/{report_id}/export/pdf` | 200 — returns PDF bytes | TESTED |
| Finalize Report | POST | `/api/reports/{report_id}/finalize` | Not tested (would modify data) | SKIPPED |

## RBAC (`/api/rbac`) — 8 endpoints

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| List Users | GET | `/api/rbac/users` | 200 — 4 users (admin, analyst, reviewer, approver) | TESTED |
| Get User | GET | `/api/rbac/users/{user_id}` | 200 — returns user with permissions | TESTED |
| List Approvals | GET | `/api/rbac/approvals` | 200 — returns 2 approvals | TESTED |
| Create Approval | POST | `/api/rbac/approvals` | Not tested (would create data) | SKIPPED |
| Approve | POST | `/api/rbac/approvals/{id}/approve` | Not tested (would modify data) | SKIPPED |
| Reject | POST | `/api/rbac/approvals/{id}/reject` | Not tested (would modify data) | SKIPPED |
| Approval History | GET | `/api/rbac/approvals/history/{entity_id}` | Not tested (no entity data) | SKIPPED |
| Permissions | GET | `/api/rbac/permissions/{user_id}` | 200 — returns permissions array | TESTED |

## Audit (`/api/audit`) — 5 endpoints

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| Config Changes | GET | `/api/audit/config/changes` | 200 — 100 entries, timestamps serialized as strings | TESTED |
| Config Diff | GET | `/api/audit/config/diff` | 422 — requires start param (correct validation) | TESTED |
| Project Trail | GET | `/api/audit/{project_id}` | 200 — returns trail (0 entries for test project) | TESTED |
| Verify Chain | GET | `/api/audit/{project_id}/verify` | 200 — chain valid | TESTED |
| Export | GET | `/api/audit/{project_id}/export` | 200 — valid JSON with string timestamps | TESTED |

## Admin (`/api/admin`) — 16 endpoints

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| Get Config | GET | `/api/admin/config` | 200 — returns config dict | TESTED |
| Schemas | GET | `/api/admin/schemas` | 200 — 3 schemas | TESTED |
| Put Config | PUT | `/api/admin/config` | Not tested (write) | SKIPPED |
| Other 13 endpoints | Various | Various | Covered in iter 1 manifest | TESTED (iter 1) |

## Data Mapping (`/api/data-mapping`) — 9 endpoints

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| Status | GET | `/api/data-mapping/status` | 200 — 7 table statuses | TESTED |
| Other 8 endpoints | Various | Various | Covered in iter 1 manifest | TESTED (iter 1) |

## Advanced (`/api/advanced`) — 9 endpoints

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| Cure Rates List | GET | `/api/advanced/cure-rates` | 200 — 4 entries | TESTED |
| Cure Rate Detail | GET | `/api/advanced/cure-rates/{id}` | 200 — full analysis with cure_trend, cure_by_dpd | TESTED |
| CCF List | GET | `/api/advanced/ccf` | 200 — 2 entries | TESTED |
| Collateral List | GET | `/api/advanced/collateral` | 200 — 14 entries | TESTED |
| Other 5 endpoints | Various | Various | Covered in iter 1 manifest | TESTED (iter 1) |

## Period Close/Pipeline (`/api/pipeline`) — 7 endpoints

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| List Steps | GET | `/api/pipeline/steps` | 200 — 6 steps in correct order | TESTED |
| Health | GET | `/api/pipeline/health/{project_id}` | **500 — NaN serialization error** | BUG |
| Start | POST | `/api/pipeline/start/{project_id}` | Not tested (write) | SKIPPED |
| Run All | POST | `/api/pipeline/run-all/{project_id}` | Not tested (write) | SKIPPED |
| Get Run | GET | `/api/pipeline/run/{run_id}` | No active runs | SKIPPED |
| Execute Step | POST | `/api/pipeline/run/{run_id}/execute-step` | No active runs | SKIPPED |
| Complete | POST | `/api/pipeline/run/{run_id}/complete` | No active runs | SKIPPED |

## Attribution (`/api/data/attribution`) — 3 endpoints

| Endpoint | Method | Path | Result | Status |
|----------|--------|------|--------|--------|
| Get Attribution | GET | `/api/data/attribution/{project_id}` | 200 — returns null (no data) | TESTED |
| Compute Attribution | POST | `/api/data/attribution/{project_id}/compute` | **500 — reconciliation column missing (BUG-S4-002)** | BUG |
| Attribution History | GET | `/api/data/attribution/{project_id}/history` | Not tested (no data) | SKIPPED |

---

## Frontend Page Loading

| Asset | URL | HTTP Status | Status |
|-------|-----|-------------|--------|
| Main SPA | / | 200 | TESTED |
| JS Bundle | /assets/index-DNaCEbyM.js | 200 | TESTED |
| CSS Bundle | /assets/index-DF6l7LEH.css | 200 | TESTED |
| Logo SVG | /logo.svg | 200 | TESTED |

---

## Summary

| Category | Total | TESTED | BUG | SKIPPED |
|----------|-------|--------|-----|---------|
| GL Journals | 7 | 4 | 0 | 3 |
| Reports | 6 | 4 | 1 | 1 |
| RBAC | 8 | 4 | 0 | 4 |
| Audit | 5 | 5 | 0 | 0 |
| Admin | 16 | 14 | 0 | 2 |
| Data Mapping | 9 | 7 | 0 | 2 |
| Advanced | 9 | 7 | 0 | 2 |
| Period Close | 7 | 2 | 1 | 4 |
| Attribution | 3 | 1 | 1 | 1 |
| Frontend | 4 | 4 | 0 | 0 |
| **TOTAL** | **74** | **52** | **3** | **19** |

### Bug List

| ID | Severity | Endpoint | Description |
|----|----------|----------|-------------|
| BUG-S4-VQA-001 | MAJOR | `/api/reports/{id}/export` | CSV export HTTP 500: DictWriter fieldnames mismatch — report data contains fields not in fieldnames list |
| BUG-S4-VQA-002 | CRITICAL | `/api/data/attribution/{id}/compute` | BUG-S4-002 NOT FIXED in production: ALTER TABLE fails silently due to InsufficientPrivilege. Reconciliation column never added. |
| BUG-S4-VQA-003 | MAJOR | `/api/pipeline/health/{project_id}` | HTTP 500: NaN float values not JSON serializable |
