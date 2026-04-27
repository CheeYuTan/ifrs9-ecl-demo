# Discovery Report: IFRS 9 Expected Credit Losses Platform

## Project Overview
- **Name**: Expected Credit Losses (ECL)
- **Description**: Production-grade IFRS 9 ECL modeling, reporting, and governance platform on Databricks
- **Tech Stack**: Python 3.11 (FastAPI), React 19 (TypeScript), Vite 7.3, Tailwind CSS 4, Lakebase (PostgreSQL)
- **Lines of Code**: ~82,600 (55K Python + 28K TypeScript/TSX)
- **Test Count**: 4,754 total (4,214 backend + 540 frontend), 0 failures
- **Coverage**: 60% minimum threshold (from pyproject.toml)

---

## Architecture Map

### Backend
- **Framework**: FastAPI 0.115+ with uvicorn
- **Entry Point**: `app/app.py` (205 LOC)
- **Router/Endpoints**: 140+ endpoints across 23 route modules
- **Database**: Databricks Lakebase (Managed PostgreSQL) via psycopg2 with ThreadedConnectionPool (2-10 connections)
- **Auth**: Databricks OAuth (X-Forwarded-User header) + anonymous fallback for local dev
- **Middleware**: Error handler, request ID, analytics, auth (4 modules)
- **ORM**: None — raw parameterized SQL throughout

### Frontend
- **Framework**: React 19.2.0 with Vite 7.3.1
- **Component Structure**: Feature-based — 32 reusable components, 20+ page components, 6 sub-page modules
- **State Management**: React Context API + hooks (ThemeProvider, ToastProvider, useCurrentUser, usePermissions, useEclData)
- **Styling**: Tailwind CSS 4.2.1 with custom theme system (8 color presets, full dark mode)
- **Routing**: Internal state-based (no React Router) — conditional rendering in App.tsx
- **Charts**: Recharts 3.7.0 with custom drill-down components

### Infrastructure
- **Deploy Target**: Databricks Apps (native)
- **CI/CD**: None configured (no GitHub Actions)
- **Config Management**: PostgreSQL-backed config with admin API + env vars
- **Documentation**: Docusaurus 3.9.2 site with admin/user/developer guides

---

## Quality Audit

### Tests
- **Test Framework**: pytest (backend), Vitest 4.1.1 (frontend)
- **Test Directory Structure**: Organized by type (unit/integration/regression) with sprint-based naming
- **Test Count**: 4,214 backend + 540 frontend = 4,754 total
- **Test LOC**: ~31,500 lines of test code
- **Coverage**: 60% minimum threshold, actual coverage not measured recently
- **Test Quality**: HIGH — meaningful assertions, realistic fixtures, RBAC matrix verification, financial domain coverage
- **Missing Test Areas**: See gap analysis below

### Production Readiness Checklist
| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Error handling (global handler, no stack traces) | PRESENT | Global middleware + per-route handlers |
| 2 | Loading states (skeleton, spinners) | PRESENT | PageLoader, Suspense fallback, component-level |
| 3 | Toast notifications | PRESENT | Context-based, auto-dismiss, 3 types |
| 4 | Environment config (pydantic-settings, .env) | PRESENT | .env + admin_config DB + app.yaml |
| 5 | Data validation (client + server) | PRESENT | 29 validation rules + client form validation |
| 6 | Dark mode | PRESENT | Full implementation, 8 color presets |
| 7 | SEO & meta tags | PARTIAL | Docs site has it, main app is SPA |
| 8 | Accessibility (semantic HTML, keyboard nav) | PRESENT | WCAG AA, skip-to-content, ARIA, keyboard shortcuts |
| 9 | Performance basics | PRESENT | Vectorized NumPy, batch processing, code splitting |
| 10 | Rate limiting & security | PARTIAL | RBAC present, no explicit rate limiting middleware |
| 11 | Seed data / demo mode + onboarding | PRESENT | Setup wizard, seed-sample-data endpoint |
| 12 | Data governance & compliance | PRESENT | RBAC, audit trail, segregation of duties, hash verification |
| 13 | Feature flags | MISSING | No feature flag system |
| 14 | Analytics & telemetry | PRESENT | Usage analytics middleware, request tracking |
| 15 | CI/CD enhancement | MISSING | No CI/CD pipeline |

### Code Quality
- **Linting**: ESLint configured for frontend (559 errors, mostly `any` types); ruff not configured for Python
- **Type Safety**: TypeScript strict mode enabled; Python has no mypy/pyright enforcement
- **File Sizes**: Several files > 200 lines (SetupWizard.tsx: 985, SimulationPanel.tsx: 700, App.tsx: 627, jobs.py: 674)
- **Function Sizes**: Generally well-decomposed; `run_scenario_sims` is 55 lines (acceptable for vectorized NumPy)
- **Dead Code**: U01 (KpiCard trend prop), U02 (DrillDownChart title prop)
- **Hardcoded Values**: U06/U07 ('Current User' string in GLJournals/ModelRegistry), U09 (fabricated backtesting metrics), U10 (hardcoded growth factors)

### Documentation
- **README**: Exists, comprehensive (12 KB)
- **API Docs**: FastAPI auto-generated OpenAPI/Swagger
- **Docs Site**: Docusaurus with admin/user/developer guides (50+ pages)
- **Code Comments**: Minimal (appropriate for well-named code)

### Installer
- **install.sh**: Exists
- **deploy.sh**: Exists
- **app.yaml**: Exists (Databricks Apps config)
- **.env.example**: Exists

---

## Feature Inventory

| Feature | Routes | Backend Tests | Frontend Tests | UI Complete | API Complete | Notes |
|---------|--------|---------------|----------------|-------------|-------------|-------|
| Project CRUD + Workflow | 10 | Yes | Yes | Yes | Yes | 8-step workflow working |
| Monte Carlo ECL Simulation | 5 | Yes | Yes | Yes | Yes | Vectorized, batched |
| Scenario Management | 8 | Yes | Yes | Yes | Yes | 8 scenarios, weighted |
| Satellite Models | 6 | Yes | Yes | Yes | Yes | Comparison + selection |
| Markov Transition Matrices | 6 | Yes | No | Yes | Yes | Estimation + forecasting |
| Hazard Models (Cox PH/KM) | 6 | Yes | No | Yes | Yes | 3 estimators |
| Backtesting Engine | 4 | Yes | No | Yes | Yes | EBA-compliant metrics |
| Attribution Waterfall | 3 | Yes | No | Yes | Yes | IFRS 7.35I decomposition |
| GL Journal Generation | 6 | Yes | No | Yes | Yes | Balanced double-entry |
| IFRS 7 Regulatory Reports | 5 | Yes | No | Yes | Yes | PDF + CSV export |
| RBAC + Project Permissions | 12 | Yes | Yes | Yes | Yes | Dual-layer access control |
| Approval Workflow | 5 | Yes | No | Yes | Yes | Multi-level sign-off |
| Data Mapping | 8 | Yes | No | Yes | Yes | Column mapping wizard |
| Admin Config | 10 | Yes | No | Yes | Yes | Dynamic config management |
| Setup Wizard | 4 | Yes | No | Yes | Yes | Guided onboarding |
| Period-End Close Pipeline | 5 | Yes | No | Yes | Yes | 6-step orchestration |
| Stress Testing (Sensitivity/MC/Migration/Concentration) | 4 | Yes | No | Yes | Yes | 4 analysis tabs |
| Model Registry + Governance | 6 | Yes | No | Yes | Yes | Version control + promotion |
| Advanced Features (Cure/CCF/Collateral) | 6 | Yes | No | Yes | Yes | 3 analysis modules |
| Databricks Jobs | 4 | Yes | No | Yes | Yes | Job triggering + monitoring |
| Dark Mode + Theme | N/A | Yes | Yes | Yes | N/A | 8 color presets |
| Docusaurus Docs Site | N/A | Yes | N/A | Yes | N/A | 50+ pages |

---

## Existing Test Analysis

- **Current Structure**: Sprint-organized (`test_qa_sprint_N_*.py`) + functional domain tests
- **Migration Needed**: Consider reorganizing by domain module for maintainability
- **Test Gaps**:
  1. `ecl/helpers.py` — no dedicated test file
  2. `reporting/pdf_export.py` — may lack thorough PDF generation tests
  3. `dashboards/provision_dashboard.py` — only 81 lines of tests
  4. Frontend component tests — 0 React component tests (only hooks + utilities)
  5. Frontend page tests — smoke tests exist but no interaction tests
  6. No E2E tests with a real browser framework (Playwright/Cypress)
  7. No load/performance tests for simulation at scale
- **Test Quality**: HIGH — 31K+ LOC with realistic fixtures, RBAC matrix testing, financial domain assertions

---

## Bug & Issue Scan

### Previous QA Results
- **32 bugs found**, **25 fixed** (78% fix rate)
- **7 remaining unfixed bugs** (all LOW severity):

| ID | File | Description | Severity |
|----|------|-------------|----------|
| U01 | KpiCard.tsx | `trend` prop declared but never used | LOW |
| U02 | DrillDownChart.tsx | `title` prop accepted but voided | LOW |
| U03 | Sidebar.tsx | `layoutId` shared between mobile/desktop | LOW |
| U04 | CollapsibleSection.tsx | No animation on open/close | LOW |
| U05 | HelpTooltip.tsx | Tooltip can render off-screen | LOW |
| U06 | GLJournals.tsx | Hardcoded 'Current User' string | LOW |
| U07 | ModelRegistry.tsx | Hardcoded 'Current User' string | LOW |
| U09 | ModelExecution.tsx | Backtesting metrics fabricated from LGD values | LOW |
| U10 | SignOff.tsx | Hardcoded growth factors for opening balance | LOW |

### ESLint Issues
- **559 errors** in frontend (primarily `any` type usage)
- TypeScript strict mode enabled but many implicit `any` violations

### Python Issues
- No mypy/pyright configured — type safety not enforced
- No ruff/black configured — no consistent formatting enforcement

### Security Observations
- No hardcoded secrets found in source
- RBAC + project permissions properly enforced
- SQL injection prevented via parameterized queries throughout
- Segregation of duties enforced at sign-off
- No rate limiting middleware (potential DoS vector)
- No CSRF protection (relies on OAuth token)

---

## Work Classification

### Fix Sprints (repair what's broken)

1. **[Fix]: Remaining unfixed bugs U01-U10** — Severity: LOW
   - What's wrong: Dead props, hardcoded strings, missing animations, off-screen tooltips
   - Where: KpiCard.tsx, DrillDownChart.tsx, Sidebar.tsx, CollapsibleSection.tsx, HelpTooltip.tsx, GLJournals.tsx, ModelRegistry.tsx, ModelExecution.tsx, SignOff.tsx
   - Effort: S

2. **[Fix]: ESLint type safety errors** — Severity: MEDIUM
   - What's wrong: 559 `any` type violations throughout frontend
   - Where: Frontend components, pages, and utilities
   - Effort: L

3. **[Fix]: Financial calculation edge cases** — Severity: HIGH
   - What's wrong: Monte Carlo engine has edge cases: zero EIR loans (division by near-zero), zero GCA after amortization, single-simulation run (std=0)
   - Where: ecl/monte_carlo.py, ecl/simulation.py
   - Effort: M

### Improve Sprints (upgrade what exists)

4. **[Improve]: Add Python type checking + linting** — Priority: HIGH
   - Current: No mypy/pyright, no ruff
   - Target: Full type checking, consistent formatting
   - Effort: M

5. **[Improve]: Increase test coverage to 80%+** — Priority: HIGH
   - Current: 60% minimum, no component tests
   - Target: 80%+ with React component tests, interaction tests
   - Effort: L

6. **[Improve]: Add rate limiting middleware** — Priority: MEDIUM
   - Current: No rate limiting
   - Target: Per-endpoint rate limiting for DoS prevention
   - Effort: S

7. **[Improve]: Performance optimization** — Priority: MEDIUM
   - Current: All queries hit DB, no caching
   - Target: In-memory caching for read-heavy endpoints (portfolio summary, config)
   - Effort: M

8. **[Improve]: Accessibility audit + fixes** — Priority: MEDIUM
   - Current: WCAG AA partial compliance
   - Target: Full WCAG AA compliance
   - Effort: M

### Extend Sprints (build new features)

9. **[Extend]: CI/CD pipeline** — Priority: HIGH
   - Depends on: GitHub Actions or equivalent
   - Effort: M

10. **[Extend]: Feature flags system** — Priority: LOW
    - Depends on: Admin config infrastructure
    - Effort: S

---

## Recommended Sprint Plan

### Priority Order
1. **Critical fixes** — Edge cases in financial calculations, remaining bugs (Sprint 1)
2. **Code quality** — ESLint errors, Python type checking, linting (Sprint 2)
3. **Test coverage** — React component tests, integration tests, coverage increase (Sprint 3)
4. **Security hardening** — Rate limiting, input validation tightening (Sprint 4)
5. **Performance** — Caching, query optimization (Sprint 5)
6. **Production readiness** — CI/CD, documentation polish (Sprint 6)

### Suggested Sprints
| Sprint | Type | Focus | Effort |
|--------|------|-------|--------|
| 1 | Fix | Financial calculation edge cases + remaining U01-U10 bugs | M |
| 2 | Improve | ESLint type safety + Python linting + type checking | L |
| 3 | Improve | Test coverage: React component tests + coverage to 80% | L |
| 4 | Improve | Security: rate limiting + input validation + CSRF | M |
| 5 | Improve | Performance: caching + query optimization | M |
| 6 | Extend | CI/CD pipeline + production deployment readiness | M |

---

## Constraints & Risks
- **No CI/CD**: All testing is manual — changes can regress without automated checks
- **ESLint debt**: 559 errors make frontend type safety unreliable
- **No Python type enforcement**: Potential for runtime type errors in financial calculations
- **Single-threaded simulation**: Monte Carlo engine runs in-process; large portfolios may timeout
- **No caching layer**: Read-heavy endpoints (dashboard data) always hit DB
- **Frontend routing**: No URL-based routing means no deep-linking or browser back/forward support
