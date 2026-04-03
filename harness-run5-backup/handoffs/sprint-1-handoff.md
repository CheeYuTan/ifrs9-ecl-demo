# Sprint 1 Handoff: Tamper-Proof Audit Trail (Audit Persona)

## What Was Built

### New Files
1. **`app/domain/audit_trail.py`** (175 lines) — Immutable hash-chained audit trail module
   - `ensure_audit_tables()` — Creates `audit_trail` and `config_audit_log` tables
   - `append_audit_entry()` — Appends entry with SHA-256 hash chain (each entry references previous entry's hash)
   - `verify_audit_chain()` — Validates entire hash chain is unbroken
   - `get_audit_trail()` — Retrieves ordered audit entries for a project
   - `log_config_change()` — Logs config parameter changes with old/new values
   - `get_config_audit_log()` — Retrieves config change history
   - `export_audit_package()` — Exports complete audit package (trail + verification + config changes)

2. **`app/routes/audit.py`** (43 lines) — Audit API endpoints
   - `GET /api/audit/{project_id}` — Full audit trail with chain verification
   - `GET /api/audit/{project_id}/verify` — Chain verification only
   - `GET /api/audit/{project_id}/export` — Downloadable JSON audit package
   - `GET /api/audit/config/changes` — Config change log with optional section filter

3. **`tests/unit/test_audit_trail.py`** (23 tests) — Comprehensive tests for:
   - Hash computation (deterministic, collision-resistant, chain-dependent)
   - Append-only entries with hash chain
   - Chain verification (valid chains, broken chains, empty chains)
   - Config change logging
   - Export package completeness

### Modified Files
4. **`app/domain/workflow.py`** — Wired audit trail into all workflow actions:
   - `create_project()` → audit entry for project creation
   - `advance_step()` → audit entry for each step advancement
   - `save_overlays()` → audit entry for overlay changes
   - `save_scenario_weights()` → audit entry for weight changes
   - `sign_off_project()` → audit entry + ECL hash computation + attestation persistence
   - Added `attestation_data` (JSONB) and `ecl_hash` (TEXT) columns to `ecl_workflow`

5. **`app/admin_config.py`** — Wired config change tracking:
   - `save_config_section()` now captures old value before save and logs to `config_audit_log`

6. **`app/app.py`** — Registered audit router

## How to Test
- Start: `cd app && python app.py`
- Create a project via POST `/api/projects`
- Advance steps, save overlays, sign off
- GET `/api/audit/{project_id}` — verify hash chain entries
- GET `/api/audit/{project_id}/verify` — should return `{"valid": true}`
- Change admin config via PUT `/api/admin/config/model`
- GET `/api/audit/config/changes` — verify config change logged
- Run `pytest tests/ --ignore=tests/unit/test_reports_routes.py` — 468 pass, 0 fail

## Contract Deviations
- None. All 13 acceptance criteria addressed.

## Known Limitations
- 45 pre-existing test failures in `test_reports_routes.py` (data_mapping routes removed from app.py but tests still reference them) — these existed before Sprint 1
- Audit trail best-effort: if DB write fails, workflow action still succeeds (logged as warning)
- No frontend UI for audit trail viewing yet (out of scope per contract)

## pytest Results
- 23 new tests in `test_audit_trail.py`: all pass
- 468 total passing (excluding 45 pre-existing failures in test_reports_routes.py)
- 0 new failures introduced
