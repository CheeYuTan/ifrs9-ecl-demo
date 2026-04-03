# IFRS 9 ECL Platform — Product Goals (Run 5: Persona-Driven Quality Hardening)

**Quality Target**: 9.0/10
**SME Mode**: Active (IFRS 9 / Basel III / EBA Guidelines)
**Approach**: Persona-driven — each goal represents what a specific user persona should be able to accomplish end-to-end.

---

## Domain Context

See `harness/sme/domain-brief-run5.md` for the full SME audit. Key regulatory references:
- IFRS 9.5.5 (ECL measurement), IFRS 7.35F-36 (disclosure requirements)
- EBA/GL/2017/16 (model validation guidelines)
- BCBS 239 (data governance principles)
- IAS 1.36 (reporting period), IAS 8 (changes in estimates)

---

## Product Goals

### Goal 1: Audit Persona — Tamper-Proof Audit Trail

**What the auditor should be able to do**: Trace every ECL number back to its source data, see who changed what parameter and when, verify that results have not been modified after sign-off, and export a complete audit package.

**Quality criteria**:
- [ ] Audit log stored in append-only table with hash chain (each entry references prior entry's hash)
- [ ] `compute_ecl_hash()` called during sign-off and stored with the project record
- [ ] Parameter change tracking: every config change (scenario weights, LGD assumptions, SICR thresholds) logged with user, timestamp, old value, new value
- [ ] Sign-off attestation text persisted to database (not just React state)
- [ ] API endpoint to export full audit trail for a project as JSON
- [ ] Existing 543+ tests still pass, 15+ new tests for audit trail

### Goal 2: Simulation Persona — Reproducible & Comparable Runs

**What the risk analyst should be able to do**: Run a simulation with a specific random seed, get identical results when re-running with the same seed, compare two simulation runs side-by-side, and see convergence diagnostics.

**Quality criteria**:
- [ ] `random_seed` parameter added to simulation config (optional — auto-generated if not provided)
- [ ] Seed stored in run metadata; re-running with same seed + same data produces identical ECL
- [ ] Run comparison endpoint: given two run IDs, returns delta by product, stage, scenario
- [ ] Convergence diagnostics: running mean, running std, and 95% CI width reported per product
- [ ] Simulation cap raised from 5,000 to 50,000 (configurable)
- [ ] 10+ new tests for reproducibility and convergence

### Goal 3: Reporting Persona — Prior-Period Comparatives & Export

**What the regulatory reporting team should be able to do**: Generate IFRS 7 disclosures with prior-period comparatives, export reports as formatted PDF, and see write-off disclosures per IFRS 7.35J.

**Quality criteria**:
- [ ] IFRS 7.35H disclosure shows opening balance, closing balance, and reconciliation movement
- [ ] Prior-period ECL results stored and retrievable for any project
- [ ] IFRS 7.35J write-off disclosure section added to regulatory reports
- [ ] PDF export endpoint using a Python PDF library (weasyprint, reportlab, or fpdf2)
- [ ] PDF output includes formatted tables, headers, page numbers, and organization branding
- [ ] 10+ new tests for comparative reporting and PDF generation

### Goal 4: Approval Persona — Attestation Persistence & ECL Integrity

**What the CFO/CRO should be able to do**: Sign off with attestation text that is permanently recorded, know that the ECL result has not been tampered with (hash verification), and see a clear approval history.

**Quality criteria**:
- [ ] Attestation checkboxes and text stored in `ecl_workflow` table alongside sign-off
- [ ] ECL hash computed at sign-off time and stored; verification endpoint available
- [ ] Approval history endpoint shows all approvals/rejections with comments and timestamps
- [ ] Sign-off page shows hash verification status (valid/invalid/not computed)
- [ ] 8+ new tests for attestation persistence and hash verification

### Goal 5: Maintenance Persona — Period-End Close Orchestration

**What the operations team should be able to do**: Trigger a complete period-end close that runs all pipeline steps in sequence (data refresh → DQ checks → model execution → ECL calculation → report generation), monitor progress, and see pipeline health.

**Quality criteria**:
- [ ] Period-end close API endpoint that orchestrates the full pipeline as a sequence of steps
- [ ] Each step reports status (pending → running → completed/failed) via SSE or polling
- [ ] Pipeline health summary: last successful run, duration, step-level status, data freshness timestamp
- [ ] Data freshness check: warn if loan tape is older than configurable threshold (default 7 days)
- [ ] 10+ new tests for orchestration and health monitoring

### Goal 6: Configuration Persona — Config Change Tracking

**What the risk manager should be able to do**: Change scenario weights, LGD assumptions, or SICR thresholds and have every change recorded with who, when, old value, new value. View config change history in the Admin UI.

**Quality criteria**:
- [ ] `config_audit_log` table stores every config change with section, key, old_value, new_value, changed_by, changed_at
- [ ] Admin API automatically logs changes when saving config sections
- [ ] Admin UI shows "Change History" tab with filterable log
- [ ] Config diff endpoint: given two timestamps, shows what changed between them
- [ ] 10+ new tests for config audit logging

### Goal 7: Installation Persona — Dependency & Health Check Fixes

**What the IT admin should be able to do**: Install the app with all dependencies resolving correctly, and see a health check that verifies all dependent services.

**Quality criteria**:
- [ ] `scipy` added to `app/requirements.txt` (currently missing, causes production failure)
- [ ] Health check endpoint verifies: Lakebase connection, required tables exist, config is loaded
- [ ] Health check returns structured JSON with per-service status
- [ ] 5+ new tests for health check

---

## Non-Negotiable Requirements

1. All existing 543 tests must continue to pass (zero regressions)
2. Every new feature must have unit tests
3. All domain logic changes reviewed against IFRS 9 terminology standards
4. No file should exceed 200 lines without justification
5. Evaluator must interact with the live running app for every sprint evaluation

## Design Language

Maintain existing: dark/light mode, Tailwind CSS, Recharts, consistent card-based layout, professional financial application aesthetic.
