# Sprint 1 Contract: Validation Rules Enforcement + Test Coverage Expansion
STATUS: AGREED

## Scope
Wire the existing 16 validation rules into the application flow so they are actually enforced (currently dead code). Add the 7 missing domain rules. Then expand test coverage by adding unit tests for the 6 untested domain modules (markov, hazard, advanced, gl_journals, model_runs, queries partial). Target: 500+ total passing tests.

## Acceptance Criteria
1. [ ] `run_all_pre_calculation_checks()` called in simulation route before ECL execution
2. [ ] `run_all_post_calculation_checks()` called after simulation completes
3. [ ] 7 new rules implemented: D7, D8, D9, D10, M-R3, M-R7, G-R4
4. [ ] Validation results included in simulation API response
5. [ ] Critical validation failures block ECL execution with 400 response
6. [ ] `test_markov.py` with 15+ tests
7. [ ] `test_hazard.py` with 15+ tests
8. [ ] `test_advanced.py` with 15+ tests
9. [ ] `test_gl_journals.py` with 12+ tests
10. [ ] `test_model_runs.py` with 12+ tests
11. [ ] Expanded `test_attribution.py` and `test_model_registry.py`
12. [ ] Total: 500+ tests passing, 0 new failures
13. [ ] All existing 422 tests still pass

## How to Test
- `pytest tests/ -q` → 500+ passed, 0 failed
- Check `app/routes/simulation.py` for validation rule calls
- Check `app/domain/validation_rules.py` for 23 rules

## Out of Scope
- Fixing synthetic data in advanced.py (Sprint 2)
- Fixing Markov hardcoded default rate (Sprint 2)
- Fixing attribution plug figure (Sprint 2)
- Terminology changes (Sprint 3)
