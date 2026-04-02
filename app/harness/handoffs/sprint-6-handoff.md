# Sprint 6 Handoff: Domain Logic — Workflow, Queries, Attribution, Validation

## What Was Built

189 new tests covering 8 domain modules (first half of `domain/`):

| Module | New Tests | Coverage Focus |
|--------|-----------|---------------|
| `domain/workflow.py` | 27 | State machine, step validation, create/advance/reset/sign-off, audit events |
| `domain/queries.py` | 30 | All 27 query functions: portfolio, ECL, drill-down, analytics, stress |
| `domain/attribution.py` | 17 | Full compute_attribution flow, waterfall, overlays, reconciliation |
| `domain/validation_rules.py` | 39 | D7-D10, DA-1 to DA-6, M-R3, M-R7, G-R4, boundary conditions |
| `domain/data_mapper.py` | 20 | _safe_identifier, type mapping, validate/suggest mappings |
| `domain/model_runs.py` | 8 | Cohort queries, ECL drill-down, upsert behavior |
| `domain/audit_trail.py` | 7 | Hash computation, chain verification (multi-entry, tampering) |
| `domain/config_audit.py` | 10 | Config diff time ranges, JSON parsing, timestamp conversion |

### Key Test Areas

**Workflow state machine**: All CRUD operations, step advancement logic (completed vs in_progress), signed-off project protection, audit event propagation

**Queries (100% function coverage)**: Every one of the 27 query functions tested — portfolio summary, stage distribution, ECL by product/stage/scenario, vintage, concentration, drill-down, sensitivity, stress testing

**Attribution waterfall**: Full compute_attribution flow with mocked DB, IFRS 7.35I waterfall structure (12 items), overlay allocation (by stage and proportional), unwind discount, FX placeholder, reconciliation check

**Validation rules (gap coverage)**: D7-D10 (stage DPD, origination/maturity dates), all 6 domain accuracy rules (DA-1 to DA-6), backtesting gate (G-R4), boundary tests (floating point tolerance)

**Data mapper**: SQL injection prevention, UC type mapping, validate/suggest mapping with exact/case-insensitive/normalized matching

**Audit chain**: Deterministic hashing, sort_keys for detail order independence, multi-entry chain verification, tampering detection

## Test File

`tests/unit/test_qa_sprint_6_domain_logic.py` — 189 tests

## How to Test

```bash
# Run sprint 6 tests only
cd app && python -m pytest tests/unit/test_qa_sprint_6_domain_logic.py -v

# Run full suite
cd app && python -m pytest tests/ -q
```

## Test Results

```
3601 passed, 61 skipped in 113.86s
```

- **New tests**: 189
- **Total pytest**: 3,601 (up from 3,412)
- **Regressions**: 0
- **Failures**: 0

## Known Limitations

- `domain/data_mapper.py`: UC browsing functions (list_uc_catalogs, list_uc_schemas, list_uc_tables, preview_uc_table, apply_mapping) require live Databricks SDK and cannot be unit tested without extensive mocking of the workspace client — deferred to Sprint 9 integration tests
- `domain/queries.py`: SQL correctness verified structurally (correct columns, parameters) but not against live DB — integration testing in Sprint 9

## Files Changed

- `tests/unit/test_qa_sprint_6_domain_logic.py` (new, 189 tests)
- `harness/contracts/sprint-6.md` (new)
- `harness/state.json` (updated)
- `harness/handoffs/sprint-6-handoff.md` (this file)
