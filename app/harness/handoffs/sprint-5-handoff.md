# Sprint 5 Handoff: User Guide — Feature Pages Part 2 + FAQ (Iteration 4)

## What Was Built

Five User Guide documentation pages plus accumulated bug fixes from Sprint 1–3 evaluations. Iteration 4 verified all prior work remains intact with zero regressions.

### Sprint 5 Pages (5 pages, 962 lines total)

1. **approval-workflow.md** (183 lines) — Maker-checker governance, 4 request types, role permissions matrix, approval queue, history tab, audit trail
2. **attribution.md** (166 lines) — IFRS 7.35I loss allowance reconciliation, 12-component waterfall, reconciliation check, stage breakdown
3. **markov-hazard.md** (200 lines) — Transition matrices (4-state model), heatmap reading, stage forecast, lifetime PD curves, 3 hazard model types
4. **advanced-features.md** (217 lines) — Cure rates (DPD buckets), CCF analysis (utilisation bands), collateral haircuts (7 types, LGD waterfall)
5. **faq.md** (196 lines) — 26 questions across 7 sections, business-user language, cross-references to all major features

### Bug Fixes Applied (iterations 2-3)

- **BUG-S1-001 + BUG-S1-002**: Homepage meta title and description fixed in `index.tsx`
- **BUG-S1-003**: Stock Docusaurus feature cards replaced with IFRS 9-relevant cards (3-Stage Impairment Model, Monte Carlo Simulation, Regulatory Reporting)
- **BUG-S1-004**: `onBrokenLinks: 'throw'` in `docusaurus.config.ts` — broken links now fail the build
- **FIND-S3-001**: Step 5 confidence intervals paragraph added with cross-reference to Step 6
- **FIND-S3-002**: Step 6 frontmatter updated to include Monte Carlo distribution
- **MDX fixes**: Unicode replacements in `model-configuration.md`, `theme-customization.md`, `ecl-engine.md`

## How to Test

```bash
cd '/Users/steven.tan/Expected Credit Losses/app'

# Build docs site (must produce 0 errors)
cd docs-site && npm run build

# Deploy
cd .. && rm -rf docs_site/* && cp -r docs-site/build/* docs_site/

# Start local dev server for browsing
cd docs-site && npm start
# Sprint 5 pages:
#   http://localhost:3000/docs/user-guide/approval-workflow
#   http://localhost:3000/docs/user-guide/attribution
#   http://localhost:3000/docs/user-guide/markov-hazard
#   http://localhost:3000/docs/user-guide/advanced-features
#   http://localhost:3000/docs/user-guide/faq
# Homepage (verify feature cards):
#   http://localhost:3000/docs/
```

## Build Results

- `npm run build`: **0 errors, 0 warnings** (with `onBrokenLinks: 'throw'`)
- Deployed to `docs_site/`
- All 32 pages across all sections build correctly (18 user guide + 9 admin + 5 developer)

## Content Quality Checks

- All 5 Sprint 5 pages ≥ 150 lines (range: 166–217)
- No Python/JSON code blocks in any User Guide page
- No API endpoint references in User Guide pages
- Correct IFRS 9 terminology throughout (ECL, PD, LGD, EAD, SICR, CCF)
- All internal cross-references valid (build succeeds with `onBrokenLinks: 'throw'`)
- Homepage shows IFRS 9-relevant feature cards
- Homepage meta title and description are correct

## Known Limitations

- Screenshot placeholders need to be replaced with actual app screenshots
- Cure rate reference values are based on seed data analysis
- CCF/collateral values are regulatory baselines

## Files Changed

### Sprint 5 pages (iteration 1)
- `docs-site/docs/user-guide/approval-workflow.md` — 183 lines
- `docs-site/docs/user-guide/attribution.md` — 166 lines
- `docs-site/docs/user-guide/markov-hazard.md` — 200 lines
- `docs-site/docs/user-guide/advanced-features.md` — 217 lines
- `docs-site/docs/user-guide/faq.md` — 196 lines
- `docs-site/static/img/screenshots/` — 8 placeholder PNGs

### Bug fix files (iterations 2-3)
- `docs-site/src/pages/index.tsx` — Meta title and description
- `docs-site/src/components/HomepageFeatures/index.tsx` — IFRS 9 feature cards
- `docs-site/docusaurus.config.ts` — `onBrokenLinks: 'throw'`
- `docs-site/docs/user-guide/step-5-model-execution.md` — Confidence intervals paragraph
- `docs-site/docs/user-guide/step-6-stress-testing.md` — Updated frontmatter
- `docs-site/docs/admin-guide/model-configuration.md` — MDX Unicode fix
- `docs-site/docs/admin-guide/theme-customization.md` — MDX Unicode fix
- `docs-site/docs/developer/ecl-engine.md` — MDX Unicode fix
- `docs_site/` — Rebuilt and deployed
