# Sprint 4 Contract: Backend API — GL Journals, Reports, RBAC, Audit, Admin, Data Mapping, Advanced, Period Close

## Acceptance Criteria
- [ ] All 7 GL journal endpoints tested (generate, list, get, post, reverse, trial-balance, chart-of-accounts)
- [ ] All 6 report endpoints tested with 5 report types (generate x5, list, get, finalize, export CSV, export PDF)
- [ ] All 8 RBAC endpoints tested (users list, user get, approvals CRUD, approve, reject, history, permissions)
- [ ] All 5 audit endpoints tested (config changes, config diff, project trail, verify chain, export)
- [ ] All 16 admin endpoints tested (config CRUD, validate-mapping, tables, columns, connection, defaults, schemas, preview, validate-typed, suggest, auto-detect, discover-products, auto-setup-lgd)
- [ ] All 9 data mapping endpoints tested (catalogs, schemas, tables, columns, preview, validate, suggest, apply, status)
- [ ] All 9 advanced endpoints tested (cure-rates compute/list/get, ccf compute/list/get, collateral compute/list/get)
- [ ] All 7 period close endpoints tested (start, steps, run get, execute-step, complete, health, run-all)
- [ ] Error paths: 404 for missing resources, 400 for invalid inputs, 500 for backend exceptions
- [ ] GL journal double-entry validation: debits = credits
- [ ] RBAC maker-checker: analyst cannot approve, approver can
- [ ] Audit chain integrity verification tested
- [ ] Period close pipeline: step ordering, failure handling, run-all stops on error
- [ ] All existing tests continue to pass (zero regressions)
- [ ] 150+ new tests added

## Test Plan
- Unit tests: `tests/unit/test_qa_sprint_4_gl_reports_rbac.py` — GL, Reports, RBAC
- Unit tests: `tests/unit/test_qa_sprint_4_audit_admin_mapping.py` — Audit, Admin, Data Mapping
- Unit tests: `tests/unit/test_qa_sprint_4_advanced_pipeline.py` — Advanced, Period Close
- All tests mock backend functions (no real DB)
- Pattern: TestClient + patch backend functions per existing sprint test patterns
