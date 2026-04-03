# Sprint 1 Contract: Tamper-Proof Audit Trail (Audit Persona)
STATUS: AGREED

## Scope
Implement an immutable, hash-chained audit log system that replaces the current mutable JSON audit log in `ecl_workflow`. Add parameter change tracking for admin config changes. Persist sign-off attestation text to the database. Wire `compute_ecl_hash()` into the sign-off flow. Provide an API endpoint to export the full audit trail.

## Acceptance Criteria
1. [ ] New `audit_trail` table with columns: id, project_id, event_type, entity_type, entity_id, action, user, detail (JSONB), previous_hash, entry_hash, created_at
2. [ ] Each audit entry's `entry_hash` = SHA-256(previous_hash + event_type + entity_id + action + detail + created_at)
3. [ ] `append_audit_entry()` function that computes hash chain and INSERTs (never UPDATE/DELETE)
4. [ ] `verify_audit_chain()` function that validates the hash chain is unbroken
5. [ ] Workflow actions (advance_step, sign_off, save_overlays, save_scenario_weights) call `append_audit_entry()`
6. [ ] `config_audit_log` table for admin config changes (section, key, old_value, new_value, changed_by, changed_at)
7. [ ] `admin_config.save_config_section()` automatically logs changes to `config_audit_log`
8. [ ] Sign-off stores attestation text in `ecl_workflow` table (new column `attestation_data` JSONB)
9. [ ] `compute_ecl_hash()` called during sign-off; hash stored in `ecl_workflow.ecl_hash` column
10. [ ] GET `/api/audit/{project_id}` returns full audit trail with chain verification status
11. [ ] GET `/api/audit/{project_id}/export` returns downloadable JSON audit package
12. [ ] 15+ new tests covering: hash chain integrity, append-only enforcement, config change logging, attestation persistence, ECL hash at sign-off, chain verification, export
13. [ ] All existing 543 tests still pass

## How to Test
- Start: `cd app && python app.py`
- Create a project, advance through steps, sign off
- GET `/api/audit/{project_id}` — verify hash chain
- Change admin config — verify `config_audit_log` entry created
- Sign off — verify attestation and ECL hash stored
- Run `pytest` — 558+ tests pass, 0 failures

## Out of Scope
- Frontend UI for audit trail viewing (future sprint)
- Data snapshot versioning (separate goal)
- Multi-level approval chains (separate goal)

## Domain Criteria (SME)
- Audit entries must use IFRS 9 terminology (e.g., "ECL measurement sign-off" not "project approval")
- Hash chain must be verifiable without access to application code (SHA-256 is standard)
- Config change log must capture old AND new values for regulatory change-in-estimate disclosure (IAS 8)
