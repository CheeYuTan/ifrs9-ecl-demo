# Sprint 6 Handoff: Domain Logic — Workflow, Queries, Attribution, Validation (Iteration 2)

## What Was Built

196 tests covering 8 domain modules (189 original + 7 new in iteration 2):

| Module | Tests | Coverage Focus |
|--------|-------|---------------|
| `domain/workflow.py` | 27 | State machine, step validation, create/advance/reset/sign-off, audit events |
| `domain/queries.py` | 30 | All 27 query functions with SQL structure + column verification |
| `domain/attribution.py` | 20 | Full compute_attribution, waterfall sum-to-total, materiality, overlays |
| `domain/validation_rules.py` | 39 | D7-D10, DA-1 to DA-6, M-R3, M-R7, G-R4, boundary conditions |
| `domain/data_mapper.py` | 22 | _safe_identifier, type mapping, validate/suggest/get_mapping_status |
| `domain/model_runs.py` | 10 | Cohort queries, ECL drill-down explicit dimension, upsert + insert |
| `domain/audit_trail.py` | 7 | Hash computation, chain verification (multi-entry, tampering) |
| `domain/config_audit.py` | 10 | Config diff time ranges, JSON parsing, timestamp conversion |

## Iteration 2 Fixes (All 5 Evaluator Issues Resolved)

1. **Strengthened 6 thin query tests** (ISSUE-S6-1): `get_vintage_by_product`, `get_concentration_by_product_stage`, `get_ecl_by_scenario_product`, `get_dq_results`, `get_dq_summary`, `get_gl_reconciliation` now provide realistic mock data, verify column structure, and assert SQL keywords (GROUP BY, table names, ORDER BY)

2. **Waterfall sum-to-total test** (ISSUE-S6-2): `test_waterfall_components_sum_to_ecl_change` — IFRS 7.35I compliance verification

3. **Residual materiality boolean test** (ISSUE-S6-3): `test_residual_within_materiality` — verifies `within_materiality` is a boolean reflecting 5% threshold

4. **get_mapping_status tests** (ISSUE-S6-4): 2 tests — status dict keys/counts + graceful DB error handling

5. **2 additional model_runs tests** (ISSUE-S6-5): explicit dimension + insert new run

6. **Bonus**: `test_prior_attribution_returns_none` — validates opening==closing when no prior exists

## How to Test

```bash
cd "/Users/steven.tan/Expected Credit Losses/app"
source .venv/bin/activate
python -m pytest tests/unit/test_qa_sprint_6_domain_logic.py -v
```

## Test Results

```
Sprint 6 tests: 196 passed in 10.25s
Full suite:     3,608 passed, 61 skipped, 0 failures in 114.03s
Regressions:    0
```

## Contract Criteria Status

| Module | Required | Delivered | Status |
|--------|----------|-----------|--------|
| Workflow | 25+ | 27 | ✅ |
| Queries | 30+ | 30 | ✅ (6 strengthened with SQL assertions) |
| Attribution | 20+ | 20 | ✅ (+3 from iter 1) |
| Validation | 20+ | 39 | ✅ |
| Data Mapper | 20+ | 22 | ✅ (+2 from iter 1) |
| Audit/Config | 15+ | 17 | ✅ |
| Model Runs | 10+ | 10 | ✅ (+2 from iter 1) |

## Known Limitations

- `domain/data_mapper.py`: UC browsing functions require live Databricks SDK — deferred to Sprint 9 integration tests
- `domain/queries.py`: SQL correctness verified structurally but not against live DB — integration testing in Sprint 9

## Files Changed

- `tests/unit/test_qa_sprint_6_domain_logic.py` — 7 new tests, 6 tests strengthened
- `harness/state.json` — updated test counts
- `harness/handoffs/sprint-6-handoff.md` — this file
