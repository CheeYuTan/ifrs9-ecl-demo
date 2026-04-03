# Sprint 2 Contract: User Guide — Workflow Steps 1-4

## Acceptance Criteria

- [ ] `step-1-create-project.md` — Full page following User Guide template: prerequisites, step-by-step with screenshot references, project states, form fields explained, tips, "What's Next?"
- [ ] `step-2-data-processing.md` — KPI cards explained, stage distribution chart, portfolio table, drill-down interactions, IFRS 9 context for each metric
- [ ] `step-3-data-control.md` — DQ checks and GL reconciliation explained, materiality thresholds, approval/rejection workflow, maker-checker process
- [ ] `step-4-satellite-model.md` — 8 model types explained for business users (no math), model comparison dashboard, cohort analysis, R-squared/RMSE in plain language, pipeline execution, approval
- [ ] All pages use correct IFRS 9 terminology (PD, LGD, EAD, SICR, Stage 1/2/3)
- [ ] Zero Python/JSON code in any page (User Guide persona rule)
- [ ] Zero API endpoint references in any page
- [ ] Every page has: frontmatter, prerequisites, "What You'll Do", step-by-step, "Understanding the Results", tips/warnings, "What's Next?"
- [ ] Screenshot placeholders reference `/img/screenshots/` paths
- [ ] `npm run build` succeeds with 0 errors
- [ ] All internal cross-references resolve (links to other steps, overview, quick-start)

## Test Plan
- Build test: `cd docs-site && npm run build` — 0 errors, 0 warnings
- Link check: verify all `[text](path)` references point to existing docs
- Persona check: grep for Python/JSON/API patterns — must return 0 hits in the 4 files
- Word count: each page should be 150-300 lines (substantive, not stubs)

## Production Readiness Items This Sprint
- N/A (documentation project — no backend/frontend code changes)
