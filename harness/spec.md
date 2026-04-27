# Spec: IFRS 9 ECL Platform — Review & Improve

## Existing Project Context
- **Discovery report**: harness/discovery/discovery-report.md
- **Current quality baseline**: ~8.0/10 (strong financial modeling, weak type safety/testing breadth)
- **Existing features preserved**: All 21 feature modules, 140+ endpoints, full UI
- **Test migration plan**: Preserve sprint-organized tests, add domain-focused component tests
- **Architecture constraints**: FastAPI + React SPA, Lakebase PostgreSQL, Databricks Apps deployment

## Quality Target: 9.8/10

---

## Sprint Plan

### Sprint 1: Fix Financial Calculation Edge Cases + Remaining Bugs
**Type**: Fix | **Effort**: M | **Priority**: CRITICAL

**Acceptance Criteria:**
1. Fix Monte Carlo edge cases:
   - Handle zero EIR loans gracefully (use floor of 0.001 for discount calculation)
   - Guard against NaN/Inf in simulation outputs with post-computation validation
   - Handle edge case of n_sims=1 (std=0 → CV calculation)
   - Add validation for empty scenario_map entries
2. Fix all remaining U01-U10 bugs:
   - U01: Remove unused `trend` prop from KpiCard
   - U02: Remove unused `title` prop from DrillDownChart
   - U03: Fix Sidebar layoutId collision
   - U04: Add Framer Motion animation to CollapsibleSection
   - U05: Add viewport boundary detection to HelpTooltip
   - U06/U07: Replace hardcoded 'Current User' with auth context user
   - U09: Remove fabricated backtesting metrics from ModelExecution
   - U10: Document or remove hardcoded growth factors in SignOff
3. All 4,754+ tests pass
4. No new regressions

### Sprint 2: Frontend Type Safety + Python Code Quality
**Type**: Improve | **Effort**: L | **Priority**: HIGH

**Acceptance Criteria:**
1. Reduce ESLint errors from 559 to <50
   - Add proper TypeScript interfaces for all API responses
   - Replace `any` types with specific types across components
   - Fix React hook dependency warnings
2. Configure Python linting:
   - Add ruff configuration to pyproject.toml
   - Fix critical linting issues (unused imports, undefined names)
3. Add mypy/pyright baseline:
   - Configure pyright in pyproject.toml
   - Fix critical type errors in domain/ and ecl/ modules
4. All tests pass

### Sprint 3: Test Coverage Expansion
**Type**: Improve | **Effort**: L | **Priority**: HIGH

**Acceptance Criteria:**
1. Increase coverage threshold from 60% to 80%
2. Add React component tests for top 10 most-used components:
   - SetupWizard, SimulationPanel, Sidebar, DataTable, Toast
   - ErrorBoundary, ConfirmDialog, ProjectMembers, KpiCard, HelpTooltip
3. Add interaction tests for critical workflows:
   - Project creation flow
   - Simulation execution flow
   - Sign-off flow
4. Add missing backend tests:
   - ecl/helpers.py dedicated tests
   - reporting/pdf_export.py tests
   - Dashboard provisioning tests
5. Test count target: 5,500+
6. All tests pass

### Sprint 4: Security Hardening + Input Validation
**Type**: Improve | **Effort**: M | **Priority**: HIGH

**Acceptance Criteria:**
1. Add rate limiting middleware:
   - Global rate limit (100 req/min per user)
   - Expensive endpoint limits (simulation: 5/min, report generation: 10/min)
2. Tighten input validation:
   - Validate all request body types with Pydantic models
   - Add max-length constraints on text fields
   - Validate file uploads (if any)
3. Add CORS configuration review
4. Security test suite:
   - SQL injection attempt tests
   - XSS attempt tests
   - RBAC bypass attempt tests
5. All tests pass

### Sprint 5: Performance Optimization
**Type**: Improve | **Effort**: M | **Priority**: MEDIUM

**Acceptance Criteria:**
1. Add in-memory caching for read-heavy endpoints:
   - Portfolio summary (TTL: 30s)
   - Config data (TTL: 5min)
   - Stage distribution (TTL: 30s)
2. Optimize slow queries:
   - Add database indexes for common query patterns
   - Batch aggregation queries where possible
3. Frontend performance:
   - Lazy-load heavy page components
   - Memoize expensive chart computations
   - Virtual scrolling for large DataTable
4. Measure and document:
   - Baseline response times for top 10 endpoints
   - Simulation throughput (loans/second)
5. All tests pass

### Sprint 6: CI/CD + Production Readiness Polish
**Type**: Extend | **Effort**: M | **Priority**: MEDIUM

**Acceptance Criteria:**
1. GitHub Actions CI pipeline:
   - Lint (ruff + eslint)
   - Type check (pyright + tsc)
   - Backend tests (pytest)
   - Frontend tests (vitest)
   - Build verification
2. Pre-commit hooks:
   - ruff format + check
   - eslint --fix
3. Production readiness final sweep:
   - Verify all 15 checklist items
   - Documentation completeness
   - Installer verification
4. All tests pass

---

## Architecture

### Existing (Preserved)
```
React SPA (Vite) → FastAPI Backend → Lakebase (PostgreSQL)
                                   → Databricks Jobs (compute)
```

### Enhancements
- Add rate limiting middleware layer
- Add in-memory cache (functools.lru_cache / cachetools)
- Add CI/CD pipeline (GitHub Actions)
- Add Python type checking (pyright)
- Add Python linting (ruff)
