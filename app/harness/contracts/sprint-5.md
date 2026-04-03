# Sprint 5 Contract: User Guide — Feature Pages Part 2 + FAQ

## Acceptance Criteria

- [ ] `approval-workflow.md` — 150+ lines, covers maker-checker pattern, 4 request types, role permissions matrix, approval queue, history tab, audit trail. No API endpoints or code.
- [ ] `attribution.md` — 150+ lines, covers ECL waterfall analysis, 12 waterfall components, reconciliation check, stage-level breakdown, history selector. No API endpoints or code.
- [ ] `markov-hazard.md` — 150+ lines, covers transition matrices (heatmap interpretation), stage forecasting, lifetime PD curves, hazard models (Cox PH, Kaplan-Meier, discrete-time), survival curves. No API endpoints or code.
- [ ] `advanced-features.md` — 150+ lines, covers cure rates (by DPD, product, segment), CCF (utilization bands, revolving vs non-revolving), collateral haircuts (7 types, recovery rates, LGD waterfall). No API endpoints or code.
- [ ] `faq.md` — 150+ lines, comprehensive FAQ organized by topic (general, workflow, models, simulation, results, troubleshooting). Business user language only.
- [ ] All pages follow established template: frontmatter, intro, Prerequisites, What You'll Do, Step-by-Step, Understanding Results, Tips & Best Practices, What's Next
- [ ] All IFRS 9 terminology is correct (ECL, PD, LGD, EAD, SICR, CCF, etc.)
- [ ] All internal cross-references point to valid page IDs
- [ ] Placeholder screenshots created for key views
- [ ] `npm run build` succeeds with 0 errors
- [ ] Deployed to `docs_site/`

## Test Plan

- Build: `cd docs-site && npm run build` — 0 errors
- Deploy: `rm -rf ../docs_site/* && cp -r build/* ../docs_site/`
- Line count: `wc -l` on each file ≥ 150
- Persona isolation: grep for API endpoints, Python code, JSON — must find none
- Cross-references: all `[text](page-id)` links point to existing pages

## Pages

| Page | File | Min Lines | Screenshots |
|------|------|-----------|-------------|
| Approval Workflow | `user-guide/approval-workflow.md` | 150 | approval-dashboard.png, approval-queue.png |
| ECL Attribution | `user-guide/attribution.md` | 150 | attribution-waterfall.png, attribution-breakdown.png |
| Markov & Hazard | `user-guide/markov-hazard.md` | 150 | markov-heatmap.png, hazard-survival.png |
| Advanced Features | `user-guide/advanced-features.md` | 150 | advanced-cure-rates.png, advanced-collateral.png |
| FAQ | `user-guide/faq.md` | 150 | — |
