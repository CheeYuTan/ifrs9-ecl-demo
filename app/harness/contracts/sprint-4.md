# Sprint 4 Contract: User Guide — Feature Pages Part 1

## Acceptance Criteria

- [ ] `model-registry.md` — 150+ lines, follows User Guide template, covers lifecycle states, performance metrics, model comparison, model cards, no code/API references
- [ ] `backtesting.md` — 150+ lines, covers traffic light system (green/amber/red), discrimination & calibration metrics explained for business users, when to retrain
- [ ] `regulatory-reports.md` — 150+ lines, covers IFRS 7 paragraphs 35F-36, report generation workflow, export formats (PDF/CSV), what auditors expect
- [ ] `gl-journals.md` — 150+ lines, covers double-entry ECL provisioning, chart of accounts, trial balance, posting workflow, reversals
- [ ] All 4 pages use correct IFRS 9 terminology throughout
- [ ] All 4 pages have Prerequisites, What You'll Do, Step-by-Step, Understanding the Results, Tips, What's Next sections
- [ ] All 4 pages include screenshot placeholders with descriptive alt text
- [ ] All 4 pages include admonitions (tip, warning, info, caution) with actionable content
- [ ] No Python code, no JSON, no API endpoints in any User Guide page
- [ ] `npm run build` succeeds with 0 errors
- [ ] Build output deployed to `docs_site/`

## Test Plan

- Build verification: `cd docs-site && npm run build` — 0 errors, 0 warnings
- Content audit: each page >= 150 lines
- Persona isolation: grep for API/code patterns in User Guide pages returns 0 matches
- Internal links: all cross-references point to valid page IDs
- Deploy: `rm -rf ../docs_site/* && cp -r build/* ../docs_site/`

## Production Readiness Items This Sprint

- Screenshot placeholders for all workflow steps
- Cross-references between related pages (model-registry <-> backtesting, regulatory-reports <-> gl-journals <-> step-8)
