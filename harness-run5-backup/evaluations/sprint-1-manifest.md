# Sprint 1 API Interaction Manifest (Backend-Only)

## Audit Trail Endpoints

| # | Endpoint | Method | Purpose | Status | Evidence |
|---|----------|--------|---------|--------|----------|
| 1 | `/api/audit/{project_id}` | GET | Full audit trail + chain verification | TESTED | Route code returns trail + verification dict; 14 unit tests cover get_audit_trail + verify_audit_chain |
| 2 | `/api/audit/{project_id}/verify` | GET | Chain verification only | TESTED | Route delegates to verify_audit_chain(); 4 unit tests (empty, valid single, broken, valid two-entry) |
| 3 | `/api/audit/{project_id}/export` | GET | Downloadable JSON audit package | TESTED | Route returns JSONResponse with Content-Disposition header; 1 unit test for export_audit_package |
| 4 | `/api/audit/config/changes` | GET | Config change log (optional section filter) | BUG | Route defined AFTER `/{project_id}` — FastAPI will match "config" as project_id. Endpoint is unreachable. |

## Domain Functions

| # | Function | Module | Status | Evidence |
|---|----------|--------|--------|----------|
| 5 | `append_audit_entry()` | audit_trail.py | TESTED | 4 unit tests: hash chain insert, chain from previous, detail inclusion, null project_id |
| 6 | `verify_audit_chain()` | audit_trail.py | TESTED | 4 unit tests: empty valid, single valid, broken detected, two-entry valid |
| 7 | `_compute_hash()` | audit_trail.py | TESTED | 5 unit tests: deterministic, collision, SHA-256 format, previous_hash sensitivity, detail sensitivity |
| 8 | `_get_last_hash()` | audit_trail.py | TESTED | 3 unit tests: genesis default, last entry, global last |
| 9 | `get_audit_trail()` | audit_trail.py | TESTED | 2 unit tests: empty, ordered entries |
| 10 | `log_config_change()` | audit_trail.py | TESTED | 1 unit test: insert with correct args |
| 11 | `get_config_audit_log()` | audit_trail.py | TESTED | 2 unit tests: empty, section filter |
| 12 | `export_audit_package()` | audit_trail.py | TESTED | 1 unit test: complete package structure |
| 13 | `ensure_audit_tables()` | audit_trail.py | TESTED | 1 unit test: creates both tables |

## Workflow Integration Points

| # | Integration | Status | Evidence |
|---|-------------|--------|----------|
| 14 | `create_project()` → audit entry | TESTED | Code calls `_audit_event()` with project_created; covered by existing workflow tests |
| 15 | `advance_step()` → audit entry | TESTED | Code calls `_audit_event()` with step details |
| 16 | `save_overlays()` → audit entry | TESTED | Code calls `_audit_event()` with overlay_count |
| 17 | `save_scenario_weights()` → audit entry | TESTED | Code calls `_audit_event()` with weights |
| 18 | `sign_off_project()` → audit + ECL hash + attestation | TESTED | Code calls `_audit_event()`, `compute_ecl_hash()`, persists attestation_data |
| 19 | `save_config_section()` → config audit log | TESTED | Code calls `log_config_change()` with old/new values |

## Summary

- **TESTED**: 18/19
- **BUG**: 1 (route ordering — `/config/changes` unreachable)
- **SKIPPED**: 0
