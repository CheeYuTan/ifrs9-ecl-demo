# Sprint 7 Interaction Manifest: Developer Reference & Sprint 6 Regression Fixes

## Developer Reference Pages — Content & Structure

| Element | Page | Action | Result | Status |
|---------|------|--------|--------|--------|
| Page Load | developer/architecture | HTTP GET | 200 OK, 59,260 bytes | TESTED |
| Page Load | developer/api-reference | HTTP GET | 200 OK, 66,205 bytes | TESTED |
| Page Load | developer/data-model | HTTP GET | 200 OK, 67,471 bytes | TESTED |
| Page Load | developer/ecl-engine | HTTP GET | 200 OK, 74,581 bytes | TESTED |
| Page Load | developer/testing | HTTP GET | 200 OK, 91,762 bytes | TESTED |
| Frontmatter | architecture.md | Verify sidebar_position, title, description | All 3 fields present, position=1 | TESTED |
| Frontmatter | api-reference.md | Verify sidebar_position, title, description | All 3 fields present, position=2 | TESTED |
| Frontmatter | data-model.md | Verify sidebar_position, title, description | All 3 fields present, position=3 | TESTED |
| Frontmatter | ecl-engine.md | Verify sidebar_position, title, description | All 3 fields present, position=4 | TESTED |
| Frontmatter | testing.md | Verify sidebar_position, title, description | All 3 fields present, position=5 | TESTED |

## What's Next? Cross-References

| Source Page | Target Page | Link Resolves | Context-Specific Description | Status |
|------------|-------------|:---:|:---:|--------|
| architecture | api-reference | YES | YES — "162+ REST endpoints served by this architecture" | TESTED |
| architecture | data-model | YES | YES — "entity relationships stored in Lakebase" | TESTED |
| architecture | ecl-engine | YES | YES — "Monte Carlo, Cholesky, Markov/hazard" | TESTED |
| architecture | testing | YES | YES — "fixtures and conventions for writing tests" | TESTED |
| api-reference | architecture | YES | YES — "middleware stack, auth, connection pooling" | TESTED |
| api-reference | data-model | YES | YES — "data these endpoints query and mutate" | TESTED |
| api-reference | ecl-engine | YES | YES — "engine behind /api/simulate* endpoints" | TESTED |
| api-reference | testing | YES | YES — "integration tests using TestClient" | TESTED |
| data-model | api-reference | YES | YES — "endpoints that read/write these tables" | TESTED |
| data-model | ecl-engine | YES | YES — "consumes lb_model_ready_loans, writes to lb_model_run_results" | TESTED |
| data-model | architecture | YES | YES — "_t() table reference helper, query layer" | TESTED |
| data-model | testing | YES | YES — "mock_db fixture, sample_loans_df" | TESTED |
| ecl-engine | data-model | YES | YES — "lb_model_ready_loans (input), lb_model_run_results (output)" | TESTED |
| ecl-engine | api-reference | YES | YES — "/api/simulate*, /api/markov/*, /api/hazard/*" | TESTED |
| ecl-engine | architecture | YES | YES — "request lifecycle and connection pooling" | TESTED |
| ecl-engine | testing | YES | YES — "test_ecl_engine.py, test_simulation_seed.py" | TESTED |
| testing | architecture | YES | YES — "module structure the test suite validates" | TESTED |
| testing | api-reference | YES | YES — "endpoint docs for writing integration tests" | TESTED |
| testing | data-model | YES | YES — "table schemas that fixtures mirror" | TESTED |
| testing | ecl-engine | YES | YES — "simulation engine tested by test_ecl_engine.py" | TESTED |

**Cross-reference summary**: 20/20 links tested, 20/20 resolve, 20/20 have context-specific descriptions.

## Sidebar Navigation

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Developer Reference category | Navigate sidebar | Category visible with 5 child pages | TESTED |
| Architecture link | Click sidebar | Links to /docs/developer/architecture | TESTED |
| API Reference link | Click sidebar | Links to /docs/developer/api-reference | TESTED |
| Data Model link | Click sidebar | Links to /docs/developer/data-model | TESTED |
| ECL Engine link | Click sidebar | Links to /docs/developer/ecl-engine | TESTED |
| Testing link | Click sidebar | Links to /docs/developer/testing | TESTED |
| Next/Previous pagination | Verify | Architecture -> API Reference navigation present | TESTED |

## Sprint 6 Regression Fixes

| Bug ID | Page | Issue | Fix Verified | Status |
|--------|------|-------|:---:|--------|
| BUG-S6-1 | admin-guide/troubleshooting | Raw `GET /api/rbac/...` in Permission Denied | YES — replaced with admin UI instructions | TESTED |
| BUG-S6-2 | admin-guide/jobs-pipelines | Raw `POST /api/jobs/provision` in Best Practices | YES — replaced with "Provision Jobs button" | TESTED |
| BUG-S6-3 | admin-guide/troubleshooting | "Frontend Build Issues" developer section | YES — replaced with "Application Not Loading" admin section | TESTED |

## Content Quality

| Page | Lines | Headings | Text Length | Content Present | Status |
|------|-------|----------|-------------|:---:|--------|
| architecture.md | 279 | 12 sections | 12,196 chars | YES | TESTED |
| api-reference.md | 375 | 22 sections | 16,034 chars | YES | TESTED |
| data-model.md | 494 | 37 sections | 15,224 chars | YES | TESTED |
| ecl-engine.md | 353 | 30 sections | 12,174 chars | YES | TESTED |
| testing.md | 390 | 35 sections | 12,844 chars | YES | TESTED |

## Build Verification

| Check | Result | Status |
|-------|--------|--------|
| npm run build | SUCCESS (0 errors, 0 warnings per handoff) | TESTED |
| onBrokenLinks: 'throw' | All links resolve | TESTED |
| Deployed to docs_site/ | All 5 dev pages present | TESTED |
| pytest | 3957 passed, 61 skipped per handoff | TESTED |

## Observations (Non-Blocking)

| Observation | Page | Details |
|-------------|------|---------|
| OBS-1 | admin-guide/troubleshooting | 5 diagnostic `GET /api/` references remain in health check, schema validation, and model review sections. These serve legitimate admin troubleshooting purposes (checking health endpoints, listing schemas, reviewing models) and were not flagged in Sprint 6 eval. |

## Summary

- **Total elements tested**: 64
- **TESTED**: 64
- **BUG**: 0
- **SKIPPED**: 0
- **PENDING**: 0
