# IFRS 9 ECL Application — Comprehensive QA Audit

## Overview

Full functional, integration, and quality audit of the IFRS 9 Expected Credit Losses application. This is a testing-focused harness run — no new features, no UI changes. Every sprint produces new test files, bug fixes for discovered issues, and a coverage gap analysis. The goal is to validate every module, find every bug, and ensure production readiness across 107+ API endpoints, 25+ frontend pages, 9 ECL engine modules, 24 domain logic files, and 4 middleware components.

Existing baseline: 2,480 pytest + 103 vitest tests, all passing. The audit will add targeted tests for untested paths, edge cases, and integration scenarios that the current suite misses.

## Quality Target: 9.5/10

## Domain Context: IFRS 9 Expected Credit Loss

This is a financial services application implementing IFRS 9 (Financial Instruments) Section 5.5 — the forward-looking Expected Credit Loss impairment model. Domain accuracy is critical:

- **3-Stage Model**: Stage 1 (12-month ECL), Stage 2 (lifetime ECL, performing), Stage 3 (lifetime ECL, credit-impaired)
- **ECL Formula**: ECL = PD x LGD x EAD x Discount Factor, probability-weighted across macroeconomic scenarios
- **SICR**: Significant Increase in Credit Risk triggers stage transfers
- **IFRS 7 Disclosures**: Regulatory reporting requirements (35H-35N)
- **Validation**: PD in [0,1], LGD in [0,1], EAD >= 0, scenario weights sum to 1.0, stage 3 implies default

## Tech Stack (Existing)

- **Frontend**: React + TypeScript SPA (Vite build, served by FastAPI)
- **API Layer**: FastAPI (Python 3.11) on Databricks Apps
- **Database**: Lakebase (managed PostgreSQL)
- **ECL Engine**: Custom Monte Carlo with Cholesky-correlated PD-LGD draws
- **Testing**: pytest (backend) + vitest (frontend)

## Test Strategy

Each sprint focuses on a testing domain. The Build Agent writes tests, runs them, fixes bugs found, and documents gaps. The Evaluator verifies test quality, coverage, and that discovered bugs are actually fixed.

**Test file convention**: `tests/unit/test_qa_sprint_N_<area>.py` for new tests. Do NOT modify existing passing tests unless fixing a genuine bug in the test itself.

---

## Features by Sprint

### Sprint 1: Backend API — Core Workflow & Data Endpoints
Test the project lifecycle and portfolio data query endpoints (the most-used paths).

**Scope** (42+ endpoints):
- `routes/projects.py`: CRUD, advance, reset, overlays, scenario-weights, sign-off, verify-hash, approval-history (10 endpoints)
- `routes/data.py`: All 32 portfolio/ECL query endpoints (portfolio-summary, stage-distribution, ecl-summary, ecl-by-product, scenario-summary, mc-distribution, concentration, migration, sensitivity, vintage, drill-down, etc.)
- `routes/setup.py`: status, validate-tables, seed, complete, reset (5 endpoints)

**Test focus**:
- Happy path for every endpoint
- Error cases: missing project_id, invalid step advancement, sign-off without required role
- Edge cases: empty portfolio, single loan, project reset mid-workflow
- Data consistency: stage distribution sums match portfolio total
- Verify-hash integrity check with tampered data

### Sprint 2: Backend API — Simulation & Satellite Model
Test Monte Carlo simulation (inline, streaming, job-based) and satellite model endpoints.

**Scope** (18+ endpoints):
- `routes/simulation.py`: run, stream (SSE), job, validate, defaults, compare (6 endpoints)
- `routes/satellite.py`: model-comparison, model-selected, model-runs CRUD, cohort-summary, drill-down-dimensions, ecl-by-cohort, stage-by-cohort, portfolio-by-cohort, ecl-by-product-drilldown (12 endpoints)

**Test focus**:
- Simulation parameter validation (n_sims bounds, correlation matrix symmetry, PD/LGD floors/caps)
- SSE streaming response format and event sequence
- Job trigger with mock Databricks client
- Simulation comparison between two runs
- Satellite model comparison output structure
- Cohort drill-down with various dimension parameters
- Edge: zero loans, single scenario, extreme parameters

### Sprint 3: Backend API — Model Registry, Backtesting, Markov, Hazard
Test analytical model management and statistical engines.

**Scope** (24+ endpoints):
- `routes/models.py`: register, list, get, status-update, promote, compare, audit (7 endpoints)
- `routes/backtesting.py`: run, results, trend, get (4 endpoints)
- `routes/markov.py`: estimate, matrices, matrix detail, forecast, lifetime-pd, compare (6 endpoints)
- `routes/hazard.py`: estimate, models, survival-curve, term-structure, compare (6 endpoints)

**Test focus**:
- Model lifecycle: Draft -> Validated -> Champion -> Retired
- Invalid status transitions (e.g., Draft -> Champion directly)
- Promote champion when no existing champion exists
- Backtesting metrics correctness: AUC, Gini, KS, PSI, Brier score, H-L test
- Traffic light classification (Green/Amber/Red thresholds per Basel)
- Markov: transition matrix rows sum to 1.0, non-negative entries
- Markov: lifetime PD monotonically non-decreasing
- Hazard: Cox PH coefficient estimation, survival curve monotonically non-increasing
- Compare endpoints return meaningful diff structure

### Sprint 4: Backend API — GL Journals, Reports, RBAC, Audit, Admin
Test operational and governance endpoints.

**Scope** (45+ endpoints):
- `routes/gl_journals.py`: generate, list, post, reverse, trial-balance, chart-of-accounts (7 endpoints)
- `routes/reports.py`: generate (5 report types), list, get, finalize, export CSV, export PDF (6 endpoints but 5 report types = 25+ test paths)
- `routes/rbac.py`: users, approvals CRUD, approve, reject, history, permissions (8 endpoints)
- `routes/audit.py`: config changes, diff, project trail, verify chain, export (5 endpoints)
- `routes/admin.py`: config CRUD, validate-mapping, tables, columns, connection, defaults, schemas, preview, auto-detect, discover-products, auto-setup-lgd (16 endpoints)
- `routes/data_mapping.py`: catalogs, schemas, tables, columns, preview, validate, suggest, apply, status (9 endpoints)
- `routes/advanced.py`: cure-rates, ccf, collateral (9 endpoints)
- `routes/period_close.py`: start, steps, run, execute-step, complete, health, run-all (7 endpoints)

**Test focus**:
- GL journal double-entry: debits = credits for every generated journal
- Journal post/reverse idempotency
- Trial balance: total debits = total credits
- All 5 report types generate valid structure
- PDF export produces non-empty bytes
- RBAC: maker-checker-approver segregation of duties
- Approval workflow: create -> approve/reject -> history
- Audit chain integrity verification (hash chain)
- Admin config: save -> retrieve round-trip consistency
- Data mapping: suggest -> validate -> apply pipeline
- Period close pipeline: step ordering, failure handling, run-all stops on error

### Sprint 5: ECL Engine — Monte Carlo Correctness
Deep test of the core ECL calculation engine (ecl/ module, 9 files).

**Scope**:
- `ecl/simulation.py`: Main run_simulation() function
- `ecl/monte_carlo.py`: Correlated PD-LGD draw generation via Cholesky
- `ecl/aggregation.py`: Result aggregation across simulations
- `ecl/data_loader.py`: Loan and scenario data loading
- `ecl/config.py`: Schema/prefix configuration
- `ecl/constants.py`: Base LGD, satellite coefficients, default weights
- `ecl/defaults.py`: Default parameter generation
- `ecl/helpers.py`: Convergence checking, event emission

**Test focus**:
- **Formula correctness**: ECL = PD x LGD x EAD x DF for known inputs, verify exact result
- **Cholesky decomposition**: Correlation matrix must be positive semi-definite; verify correlated draws have expected correlation structure
- **Stage assignment**: SICR threshold logic — Stage 1 (12-month horizon), Stage 2/3 (remaining life)
- **PD term structure**: Flat hazard for Stage 1, increasing for Stage 2/3
- **Amortizing EAD**: Prepayment adjustment reduces exposure correctly
- **Quarterly discounting**: Verify discount factor = 1/(1+EIR)^t for each period
- **Scenario weighting**: Probability-weighted ECL = sum(weight_i x ECL_i), weights must sum to 1.0
- **Convergence**: CV check stabilizes with increasing n_sims
- **Edge cases**: Zero exposure (ECL=0), PD=1.0 (certain default), PD=0 (no loss), LGD=0 (full recovery), LGD=1.0 (total loss), single loan portfolio, 10,000 loan portfolio, single scenario
- **Numerical stability**: Very small PD (1e-6), very large EAD (1e12), negative correlation

### Sprint 6: Domain Logic — Workflow, Queries, Attribution, Validation
Test the first half of domain/ modules (core business logic).

**Scope** (8 modules):
- `domain/workflow.py`: Project state machine, step validation, audit events
- `domain/queries.py`: 27 portfolio/ECL aggregation queries
- `domain/model_runs.py`: Run history, satellite model queries
- `domain/attribution.py`: Waterfall decomposition (IFRS 7.35I)
- `domain/validation_rules.py`: 23 pre/post-calculation validation checks
- `domain/data_mapper.py`: Column mapping logic, auto-suggest, apply
- `domain/audit_trail.py`: Immutable event logging, chain verification
- `domain/config_audit.py`: Config change tracking, diff

**Test focus**:
- Workflow state machine: valid transitions, invalid transitions raise errors
- Step advancement requires prerequisite completion
- Attribution waterfall: components sum to total ECL change
- Attribution: IFRS 7.35I compliance (new originations, derecognitions, stage transfers, remeasurements, model changes)
- All 23 validation rules: each with passing input, failing input, and boundary input
- Scenario weights sum check with floating point tolerance (0.999 vs 1.001)
- Data mapper: suggest returns correct column mappings for known schemas
- Audit trail: entries are append-only, verify chain detects tampering

### Sprint 7: Domain Logic — Registry, Backtesting, Markov, Hazard, Advanced
Test the second half of domain/ modules (analytical engines).

**Scope** (10+ modules):
- `domain/model_registry.py`: Version management, champion/challenger, lifecycle
- `domain/backtesting.py` + `backtesting_stats.py` + `backtesting_traffic.py`: Metric calculation, traffic lights
- `domain/markov.py`: Transition matrix estimation, state forecasting
- `domain/hazard.py` + `hazard_*.py` (6 files): Survival analysis, Cox PH, discrete-time, non-parametric
- `domain/advanced.py`: Cure rates, CCF, collateral haircuts
- `domain/period_close.py`: Pipeline orchestration
- `domain/health.py`: Health check logic

**Test focus**:
- Model registry: version incrementing, champion replacement, audit trail on status change
- Backtesting statistics: AUC calculation with known ROC data, Gini = 2*AUC - 1
- PSI calculation with known distributions (< 0.1 Green, 0.1-0.25 Amber, > 0.25 Red)
- KS statistic: maximum separation between cumulative distributions
- Markov: transition matrix estimation from observed stage movements
- Markov: matrix power for multi-step forecast, absorbing states
- Hazard: Cox PH with known coefficients, survival function S(t) = exp(-H(t))
- Hazard: Kaplan-Meier non-parametric estimation
- Cure rates: transition from Stage 3 back to Stage 2/1
- CCF: credit conversion factor estimation from drawn/undrawn exposure
- Collateral haircuts: LGD adjustment with collateral values
- Period close: step dependency ordering, parallel-safe steps

### Sprint 8: Frontend — Component & Page Testing
Expand frontend test coverage from 103 to 200+ tests.

**Scope** (25+ pages, 40+ components):
- **Untested pages**: Admin, ApprovalWorkflow, AdvancedFeatures, Attribution, Backtesting, CreateProject, DataControl, DataMapping, DataProcessing, GLJournals, HazardModels, MarkovChains, ModelExecution, ModelRegistry, Overlays, RegulatoryReports, SatelliteModel, SignOff, StressTesting
- **Untested components**: SetupWizard, SimulationPanel, DrillDownChart, ThreeLevelDrillDown, ApprovalForm, ConfirmDialog, Sidebar, PageHeader, HelpPanel, ChartTooltip, EmptyState
- **Hooks**: useEclData

**Test focus**:
- Component rendering: every page renders without crashing
- Props/state: components display correct data from props
- User interactions: button clicks, form submissions, dropdown selections
- API integration: mock API calls, verify request parameters
- Error states: API failures show user-friendly messages
- Loading states: skeleton/spinner shown during data fetch
- SetupWizard: step progression, validation at each step
- SimulationPanel: parameter inputs, run trigger, result display
- Sidebar: navigation, active state, workflow step indicators
- DataTable: sorting, filtering, pagination (extend existing tests)
- Chart components: render with mock data, empty data handling

### Sprint 9: Middleware, Cross-Cutting & Integration Testing
Test middleware stack, error handling, and end-to-end integration flows.

**Scope**:
- `middleware/auth.py`: Permission checking, ECL hash verification
- `middleware/error_handler.py`: Global error handling, status code mapping
- `middleware/request_id.py`: Request correlation
- `db/pool.py`: Connection pool, OAuth token refresh
- End-to-end integration flows (multi-endpoint sequences)

**Test focus**:
- Auth: permission decorator blocks unauthorized access, allows authorized
- Auth: ECL hash computation and verification (tamper detection)
- Error handler: Python exceptions map to correct HTTP status codes
- Error handler: user-friendly messages (no stack traces in response)
- Request ID: every response has X-Request-ID header
- Request ID: propagated through nested calls
- Connection pool: handles token expiry gracefully
- **Integration flow 1**: Create project -> advance through all 8 steps -> sign-off
- **Integration flow 2**: Run simulation -> generate reports -> export PDF
- **Integration flow 3**: Register model -> backtest -> promote to champion
- **Integration flow 4**: Create approval -> approve -> verify in history
- **Integration flow 5**: Start period-close pipeline -> execute all steps -> complete
- **Integration flow 6**: Data mapping -> validate -> apply -> query data
- Regression: re-run all existing tests, verify zero regressions

### Sprint 10: Production Readiness & Final Gap Analysis
Final audit pass: security, performance, build verification, and coverage gap report.

**Scope**:
- Security audit: input validation on all endpoints accepting user input
- Build verification: `tsc` + `vite build` + `pytest` + `vitest`
- Coverage analysis: identify remaining untested code paths
- API input validation: Pydantic model coverage for all endpoints
- Error handling: no unhandled exceptions in any tested path

**Test focus**:
- **Security**: SQL injection attempts in query parameters, XSS in text fields, path traversal in file exports
- **Input validation**: oversized payloads, malformed JSON, missing required fields, type coercion
- **Build**: frontend compiles with zero TypeScript errors, zero warnings
- **Coverage report**: generate pytest-cov and vitest coverage, document gaps
- **Performance**: simulation with 1000 loans x 1000 sims completes in reasonable time
- **Deployment**: app.yaml valid, requirements.txt pins all versions, no missing deps
- **Final regression**: full test suite (all new + existing) passes with zero failures
- **Gap report**: document any untested paths with justification (e.g., requires live Databricks connection)

---

## Acceptance Criteria (Global)

1. All existing 2,480 pytest + 103 vitest tests continue to pass (zero regressions)
2. Each sprint adds meaningful new tests (not duplicates of existing coverage)
3. Bugs discovered during testing are fixed and regression-tested
4. Each sprint produces a test report documenting: tests added, bugs found, bugs fixed, remaining gaps
5. Final sprint produces comprehensive coverage gap report
6. Frontend test count reaches 200+ (from current 103)
7. Backend test count reaches 3,000+ (from current 2,480)
8. All 107+ API endpoints have at least one happy-path test
9. ECL formula verified with hand-calculated expected values
10. Domain validation rules each have positive and negative test cases
