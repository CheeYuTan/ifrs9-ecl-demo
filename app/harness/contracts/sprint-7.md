# Sprint 7 Contract: Developer Reference — Complete (5 Pages)

## Acceptance Criteria

### Content Completeness
- [ ] `developer/architecture.md` — System design, tech stack, data flow, module structure, deployment
- [ ] `developer/api-reference.md` — All 162+ endpoints grouped by domain, request/response examples, error codes
- [ ] `developer/data-model.md` — All tables with column specifications, entity relationships, data dictionary
- [ ] `developer/ecl-engine.md` — ECL formula, Monte Carlo details, Cholesky decomposition, convergence, Markov, hazard
- [ ] `developer/testing.md` — Test framework, directory structure, fixtures, running tests, writing tests

### Template Compliance
- [ ] Every page has frontmatter (sidebar_position, title, description)
- [ ] Every page has introductory paragraph explaining purpose
- [ ] Code examples use Python, JSON, SQL as appropriate (developer persona allows code)
- [ ] Every page has "What's Next?" section with cross-references

### Cross-References
- [ ] Architecture links to API Reference, Data Model, ECL Engine
- [ ] API Reference links to Data Model, Architecture
- [ ] Data Model links to API Reference, ECL Engine
- [ ] ECL Engine links to Data Model, API Reference
- [ ] Testing links to Architecture and all other developer pages

### Regression Fixes (from Sprint 6 evaluation)
- [ ] BUG-S6-1: Remove raw API endpoint references from admin-guide/troubleshooting.md
- [ ] BUG-S6-2: Remove raw API endpoint from admin-guide/jobs-pipelines.md
- [ ] BUG-S6-3: Replace developer-focused "Frontend Build Issues" section in troubleshooting.md

### Build Verification
- [ ] `cd docs-site && npm run build` succeeds with 0 errors
- [ ] Deploy to `docs_site/` via copy
- [ ] All cross-references resolve (onBrokenLinks: 'throw')
