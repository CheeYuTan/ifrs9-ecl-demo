# Sprint 5 Handoff: User Guide — Feature Pages Part 2 + FAQ (Iteration 3)

## What Was Built

Five User Guide documentation pages (unchanged from iteration 1), plus accumulated bug fixes from Sprint 1–3 evaluations.

### Sprint 5 Pages (5 pages, 962 lines total)

1. **approval-workflow.md** (183 lines) — Maker-checker governance, 4 request types, role permissions matrix, approval queue, history tab, audit trail
2. **attribution.md** (166 lines) — IFRS 7.35I loss allowance reconciliation, 12-component waterfall, reconciliation check, stage breakdown
3. **markov-hazard.md** (200 lines) — Transition matrices (4-state model), heatmap reading, stage forecast, lifetime PD curves, 3 hazard model types
4. **advanced-features.md** (217 lines) — Cure rates (DPD buckets), CCF analysis (utilisation bands), collateral haircuts (7 types, LGD waterfall)
5. **faq.md** (196 lines) — 26 questions across 7 sections, business-user language, cross-references to all major features

### Iteration 3 Fixes (accumulated bugs from Sprint 1–3 evaluations)

**BUG-S1-001 + BUG-S1-002 (Homepage meta):**
- `docs-site/src/pages/index.tsx` — Removed "Hello from" prefix from `<title>`. Replaced stock placeholder `<meta description>` with real IFRS 9 ECL description.

**BUG-S1-003 (Stock Docusaurus feature cards):**
- `docs-site/src/components/HomepageFeatures/index.tsx` — Replaced 3 stock Docusaurus cards ("Easy to Use", "Focus on What Matters", "Powered by React" with dinosaur SVGs) with IFRS 9-relevant cards: "3-Stage Impairment Model", "Monte Carlo Simulation", "Regulatory Reporting". Used emoji icons instead of SVGs.

**BUG-S1-004 (onBrokenLinks):**
- `docs-site/docusaurus.config.ts` — Changed `onBrokenLinks: 'warn'` to `onBrokenLinks: 'throw'` so broken links fail the build.

**FIND-S3-001 (Step 5 confidence intervals):**
- `docs-site/docs/user-guide/step-5-model-execution.md` — Added paragraph in "Understanding the Results" explaining confidence intervals (P50, P75, P95, P99) with cross-reference to Step 6.

**FIND-S3-002 (Step 6 frontmatter):**
- `docs-site/docs/user-guide/step-6-stress-testing.md` — Updated frontmatter description to include "Monte Carlo distribution" as the first of 5 analysis dimensions.

### Iteration 2 Fixes (from prior iteration)
- MDX fixes in 3 files: `model-configuration.md` (≤/≥ → Unicode), `theme-customization.md` (<html> → escaped), `ecl-engine.md` (≥ → Unicode)

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
# Homepage (verify fixed feature cards):
#   http://localhost:3000/docs/
```

## Build Results

- `npm run build`: **0 errors, 0 warnings** (with `onBrokenLinks: 'throw'`)
- Deployed to `docs_site/`
- All Sprint 5 pages + all prior pages build correctly

## Content Quality Checks

- All 5 Sprint 5 pages ≥150 lines
- No Python/JSON code in any User Guide page
- No API endpoint references in any User Guide page
- Correct IFRS 9 terminology throughout
- All internal cross-references point to valid page IDs
- Homepage now shows IFRS 9-relevant feature cards (not stock Docusaurus)
- Homepage meta title and description are correct
- Broken links now fail the build (`onBrokenLinks: 'throw'`)
- Step 5 now mentions confidence intervals with cross-reference to Step 6
- Step 6 frontmatter description includes Monte Carlo distribution

## Known Limitations

- Screenshot placeholders need to be replaced with actual app screenshots
- Cure rate reference values are based on seed data analysis
- CCF/collateral values are regulatory baselines

## Files Changed

### Iteration 3 (this iteration)
- `docs-site/src/pages/index.tsx` — Fixed meta title and description (BUG-S1-001, BUG-S1-002)
- `docs-site/src/components/HomepageFeatures/index.tsx` — Replaced stock feature cards (BUG-S1-003)
- `docs-site/docusaurus.config.ts` — `onBrokenLinks: 'throw'` (BUG-S1-004)
- `docs-site/docs/user-guide/step-5-model-execution.md` — Added confidence intervals paragraph (FIND-S3-001)
- `docs-site/docs/user-guide/step-6-stress-testing.md` — Updated frontmatter description (FIND-S3-002)
- `docs_site/` — Rebuilt and deployed

### Sprint 5 pages (iteration 1, unchanged)
- `docs-site/docs/user-guide/approval-workflow.md` — 183 lines
- `docs-site/docs/user-guide/attribution.md` — 166 lines
- `docs-site/docs/user-guide/markov-hazard.md` — 200 lines
- `docs-site/docs/user-guide/advanced-features.md` — 217 lines
- `docs-site/docs/user-guide/faq.md` — 196 lines
- `docs-site/static/img/screenshots/` — 8 placeholder PNGs
