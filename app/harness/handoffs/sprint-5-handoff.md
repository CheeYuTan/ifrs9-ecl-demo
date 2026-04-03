# Sprint 5 Handoff: User Guide — Feature Pages Part 2 + FAQ (Iteration 2)

## What Was Built

Five User Guide documentation pages, each 150+ lines, following the established page template with Prerequisites, What You'll Do, Step-by-Step Instructions, Understanding the Results, Tips & Best Practices, and What's Next sections.

### Pages Created/Expanded

1. **approval-workflow.md** (183 lines) — Maker-checker governance pattern, four request types (model approval, overlay approval, journal posting, sign-off), cumulative role permissions matrix (Analyst → Reviewer → Approver → Admin), dashboard with 4 KPI cards, pending queue with sortable table, request detail/action flow, approval history (immutable), user directory with permissions grid, priority and due date management.

2. **attribution.md** (166 lines) — IFRS 7.35I loss allowance reconciliation, twelve waterfall components (opening ECL, new originations, derecognitions, stage transfers, model parameter changes, macro scenario changes, management overlays, write-offs, unwind of discount, FX changes, residual, closing ECL), reconciliation check with 1% materiality threshold, waterfall bar chart interpretation (anchor/increase/decrease/change bars), stage-level breakdown table with computed/estimated/unavailable status badges, history selector for period comparison.

3. **markov-hazard.md** (200 lines) — Two-part structure: Part 1 covers Markov Chain transition matrices (4-state model: Stage 1/2/3/Default as absorbing state), cohort estimation methodology, colour-coded heatmap reading, 4 KPI metrics (SICR probability, cure rate, default probability, Stage 1 retention), stage distribution forecast via matrix exponentiation, lifetime PD curves with 3 summary cards, matrix comparison. Part 2 covers three hazard model types (Cox PH, Kaplan-Meier, discrete-time logistic), survival/hazard/PD term structure/coefficients tabs, model comparison.

4. **advanced-features.md** (217 lines) — Three sections: Cure rates (DPD bucket breakdown with reference rates 72%→45%→22%→8%, product type and customer segment segmentation, 12-month trend chart), CCF analysis (formula CCF = (EAD−drawn)/(limit−drawn), revolving vs non-revolving, stage-dependent CCFs, 5 utilisation bands, EAD calculation), Collateral haircuts (7 collateral types with haircuts/recovery rates/time-to-recovery, IFRS 9 B5.5.55 reference, LGD waterfall visualisation, secured vs unsecured blended LGD).

5. **faq.md** (196 lines) — Comprehensive FAQ in 7 sections: General (4 questions), The 8-Step Workflow (4 questions), Models and Simulation (5 questions), Results and Reporting (3 questions), Overlays (3 questions), Governance and Audit (3 questions), Troubleshooting (4 questions).

### Iteration 2 Fixes

**Build-breaking MDX errors fixed in 3 files:**

1. **admin-guide/model-configuration.md** — Replaced `<=` and `>=` operators in table cells with Unicode equivalents (`≤`, `≥`) to prevent MDX JSX parsing errors. Lines 113–114 (stage classification rules) and lines 124–125 (threshold parameters).

2. **admin-guide/theme-customization.md** — Replaced bare `<html>` in prose text (lines 131, 156, 167) with backtick-escaped or descriptive alternatives to prevent MDX JSX parsing errors.

3. **developer/ecl-engine.md** — Replaced `>=` in table cells (lines 72–73) with Unicode `≥` to prevent MDX JSX parsing errors.

**Progress tracking updated:**
- `harness/progress.md` — updated from stale "all PENDING" state to reflect actual sprint completion status (Sprints 1-4 COMPLETE with scores).

### Placeholder Screenshots

8 placeholder PNG images (1280×720) in `docs-site/static/img/screenshots/`:
- `approval-dashboard.png`, `approval-queue.png`
- `attribution-waterfall.png`, `attribution-breakdown.png`
- `markov-heatmap.png`, `hazard-survival.png`
- `advanced-cure-rates.png`, `advanced-collateral.png`

## How to Test

```bash
cd '/Users/steven.tan/Expected Credit Losses/app'

# Build docs site
cd docs-site && npm run build

# Deploy
cd .. && rm -rf docs_site/* && cp -r docs-site/build/* docs_site/

# Start local dev server for browsing
cd docs-site && npm start
# Navigate to: http://localhost:3000/docs/user-guide/approval-workflow
# Navigate to: http://localhost:3000/docs/user-guide/attribution
# Navigate to: http://localhost:3000/docs/user-guide/markov-hazard
# Navigate to: http://localhost:3000/docs/user-guide/advanced-features
# Navigate to: http://localhost:3000/docs/user-guide/faq
```

## Build Results

- `npm run build`: **0 errors, 0 warnings** (confirmed after iteration 2 fixes)
- Deployed to `docs_site/`
- All 5 Sprint 5 pages + all prior pages render correctly

## Content Quality Checks

- All pages ≥150 lines (183, 166, 200, 217, 196)
- No Python/JSON code in any User Guide page
- No API endpoint references in any User Guide page
- Correct IFRS 9 terminology throughout (ECL, PD, LGD, EAD, SICR, CCF, etc.)
- All internal cross-references point to valid page IDs
- All screenshot references point to existing files
- Admonitions used throughout (info, tip, warning, caution)
- Tables used extensively for structured information
- FAQ organised by topic with clear section headings

## Known Limitations

- Screenshot placeholders need to be replaced with actual app screenshots
- Cure rate reference values are based on codebase analysis of seed data — actual institutional rates will differ
- CCF values shown are platform defaults — institutions should calibrate to their own portfolio data
- Collateral haircut percentages are regulatory baselines

## Files Changed

### Sprint 5 pages (iteration 1 — unchanged in iteration 2)
- `docs-site/docs/user-guide/approval-workflow.md` — 183 lines
- `docs-site/docs/user-guide/attribution.md` — 166 lines
- `docs-site/docs/user-guide/markov-hazard.md` — 200 lines
- `docs-site/docs/user-guide/advanced-features.md` — 217 lines
- `docs-site/docs/user-guide/faq.md` — 196 lines
- `docs-site/static/img/screenshots/` — 8 placeholder PNGs

### Iteration 2 fixes
- `docs-site/docs/admin-guide/model-configuration.md` — fixed MDX `<=`/`>=` parsing errors
- `docs-site/docs/admin-guide/theme-customization.md` — fixed MDX `<html>` parsing errors
- `docs-site/docs/developer/ecl-engine.md` — fixed MDX `>=` parsing error
- `harness/progress.md` — updated to reflect actual sprint completion status
- `docs_site/` — rebuilt and deployed
