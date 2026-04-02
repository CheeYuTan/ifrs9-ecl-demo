# Sprint 6 Contract: Domain Logic — Workflow, Queries, Attribution, Validation

## Scope
Test 8 domain modules with 150+ new tests covering untested paths, edge cases, and boundary conditions.

**Modules in scope:**
1. `domain/workflow.py` — Project state machine, step validation, audit events
2. `domain/queries.py` — 27 portfolio/ECL aggregation queries
3. `domain/attribution.py` — Waterfall decomposition (IFRS 7.35I)
4. `domain/validation_rules.py` — 23+ validation checks (data integrity, model reasonableness, governance, domain accuracy)
5. `domain/model_runs.py` — Run history, satellite model queries
6. `domain/data_mapper.py` — Column mapping logic, auto-suggest, validate, apply
7. `domain/audit_trail.py` — Immutable event logging, chain verification
8. `domain/config_audit.py` — Config change tracking, diff

## Existing Test Baseline
- 137 tests across 5 existing files
- Coverage gaps: workflow state machine, queries module (zero tests), data_mapper (zero tests), attribution compute_attribution flow, validation boundary/edge cases, config_diff time range

## Acceptance Criteria

### Workflow (domain/workflow.py) — 25+ new tests
- [ ] create_project: creates with correct step_status, audit log, upsert on conflict
- [ ] get_project: returns None for missing, parses JSON fields correctly
- [ ] list_projects: returns DataFrame ordered by created_at desc
- [ ] advance_step: valid advance, step_status update, audit log append, step index calculation
- [ ] advance_step: raises ValueError for missing project
- [ ] advance_step: non-completed status does NOT advance current_step
- [ ] save_overlays: stores JSON, triggers audit event
- [ ] save_scenario_weights: stores JSON, triggers audit event
- [ ] reset_project: resets step_status, raises for missing, raises for signed-off project
- [ ] sign_off_project: updates signed_off_by/at, computes ECL hash, adds attestation
- [ ] sign_off_project: raises for missing project
- [ ] STEPS constant: correct 8-step sequence

### Queries (domain/queries.py) — 30+ new tests
- [ ] Every query function returns a DataFrame (even if empty)
- [ ] get_portfolio_summary: groups by product_type
- [ ] get_stage_distribution: groups by assessed_stage, ordered
- [ ] get_ecl_summary: groups by product+stage
- [ ] get_ecl_by_product: aggregation and coverage ratio
- [ ] get_scenario_summary: ordered by weight
- [ ] get_top_exposures: limit parameter works
- [ ] get_loans_by_product: filters by product_type
- [ ] get_loans_by_stage: filters by assessed_stage
- [ ] get_sensitivity_data: implied_lgd calculation
- [ ] All 27 query functions called with correct SQL structure

### Attribution (domain/attribution.py) — 20+ new tests
- [ ] compute_attribution: full flow with mocked DB returns correct structure
- [ ] compute_attribution: waterfall components sum to total ECL change
- [ ] compute_attribution: residual is within materiality threshold
- [ ] compute_attribution: handles missing data gracefully (data_unavailable)
- [ ] compute_attribution: management overlays allocated by stage
- [ ] compute_attribution: overlays allocated proportionally when no target stage
- [ ] compute_attribution: unwind of discount uses quarterly EIR
- [ ] get_attribution: returns None when no data
- [ ] get_attribution_history: returns list ordered by computed_at desc
- [ ] _get_prior_attribution: returns None when no prior exists

### Validation Rules — 20+ new tests (gap coverage)
- [ ] D7: Stage 3 DPD >= 90 check — pass, fail, empty input
- [ ] D8: Stage 1 DPD < 30 check — pass, fail, empty input
- [ ] D9: Origination before reporting date — pass, fail, invalid date
- [ ] D10: Maturity after origination — pass, fail, invalid dates
- [ ] DA-1 through DA-6: All 6 domain accuracy rules with pass/fail/boundary
- [ ] M-R3: Satellite R² threshold check
- [ ] M-R7: PD aging factor bounds
- [ ] G-R4: Backtesting gate — no backtest, within limit, expired
- [ ] Boundary: scenario weights at tolerance edge (0.999, 1.001)
- [ ] Aggregate: run_all_pre with optional params
- [ ] has_critical_failures: mixed severity results

### Data Mapper (domain/data_mapper.py) — 20+ new tests
- [ ] _safe_identifier: valid identifiers pass, SQL injection rejected
- [ ] _uc_type_to_ecl_type: all UC type families mapped correctly
- [ ] validate_mapping: mandatory unmapped, source_missing, type_mismatch
- [ ] validate_mapping: all mandatory mapped — valid=True
- [ ] validate_mapping: optional columns don't cause errors
- [ ] suggest_mappings: exact, case-insensitive, normalized, partial matches
- [ ] suggest_mappings: no matches returns empty
- [ ] get_mapping_status: returns status dict for all tables

### Audit/Config Audit — 15+ new tests (gap coverage)
- [ ] config_diff: time range filtering, section filtering, combined filters
- [ ] config_diff: empty result when no changes in range
- [ ] verify_audit_chain: tampered hash detected
- [ ] verify_audit_chain: tampered previous_hash detected
- [ ] export_audit_package: includes all required keys
- [ ] _compute_hash: order-insensitive detail serialization (sort_keys)
- [ ] Timestamp serialization: datetime objects converted to ISO strings

### Model Runs — 10+ new tests (gap coverage)
- [ ] get_cohort_summary: returns grouped data
- [ ] get_cohort_summary_by_product: filters by product
- [ ] get_ecl_by_cohort: dimension-based grouping
- [ ] get_stage_by_cohort: product filter + stage grouping
- [ ] save_model_run: upsert behavior on conflict

## Test Plan
- File: `tests/unit/test_qa_sprint_6_domain_logic.py`
- Target: 150+ new tests
- All tests mock DB via `unittest.mock.patch` on `db.pool.query_df` and `db.pool.execute`
- No live database required
- Zero regressions on existing 3,412 tests
