# Sprint 5 Handoff: User Guide — Feature Pages Part 2 + FAQ

## What Was Built

Five User Guide documentation pages, each 150+ lines, following the established page template with Prerequisites, What You'll Do, Step-by-Step Instructions, Understanding the Results, Tips & Best Practices, and What's Next sections.

### Pages Created/Expanded

1. **approval-workflow.md** (183 lines) — Maker-checker governance pattern, four request types (model approval, overlay approval, journal posting, sign-off), cumulative role permissions matrix (Analyst → Reviewer → Approver → Admin), dashboard with 4 KPI cards, pending queue with sortable table, request detail/action flow, approval history (immutable), user directory with permissions grid, priority and due date management.

2. **attribution.md** (166 lines) — IFRS 7.35I loss allowance reconciliation, twelve waterfall components (opening ECL, new originations, derecognitions, stage transfers, model parameter changes, macro scenario changes, management overlays, write-offs, unwind of discount, FX changes, residual, closing ECL), reconciliation check with 1% materiality threshold, waterfall bar chart interpretation (anchor/increase/decrease/change bars), stage-level breakdown table with computed/estimated/unavailable status badges, history selector for period comparison.

3. **markov-hazard.md** (200 lines) — Two-part structure: Part 1 covers Markov Chain transition matrices (4-state model: Stage 1/2/3/Default as absorbing state), cohort estimation methodology, colour-coded heatmap reading, 4 KPI metrics (SICR probability, cure rate, default probability, Stage 1 retention), stage distribution forecast via matrix exponentiation, lifetime PD curves with 3 summary cards, matrix comparison. Part 2 covers three hazard model types (Cox PH, Kaplan-Meier, discrete-time logistic), survival/hazard/PD term structure/coefficients tabs, model comparison.

4. **advanced-features.md** (217 lines) — Three sections: Cure rates (DPD bucket breakdown with reference rates 72%→45%→22%→8%, product type and customer segment segmentation, 12-month trend chart), CCF analysis (formula CCF = (EAD−drawn)/(limit−drawn), revolving vs non-revolving, stage-dependent CCFs, 5 utilisation bands, EAD calculation), Collateral haircuts (7 collateral types with haircuts/recovery rates/time-to-recovery, IFRS 9 B5.5.55 reference, LGD waterfall visualisation, secured vs unsecured blended LGD).

5. **faq.md** (196 lines) — Comprehensive FAQ in 7 sections: General (4 questions: what is IFRS 9, what does the platform do, who is it for, what are the roles), The 8-Step Workflow (4 questions: what is it, order requirement, going back, timing), Models and Simulation (5 questions: satellite models, Monte Carlo, stages, SICR triggers, PD/LGD/EAD definitions), Results and Reporting (3 questions: validation mechanisms, report types, export), Overlays (3 questions: what/when/negative), Governance and Audit (3 questions: audit trail, hash verification, re-opening), Troubleshooting (4 questions: stuck simulation, high/low ECL diagnosis, greyed button, build failures).

### Placeholder Screenshots Created

8 placeholder PNG images (1280×720) in `docs-site/static/img/screenshots/`:
- `approval-dashboard.png`
- `approval-queue.png`
- `attribution-waterfall.png`
- `attribution-breakdown.png`
- `markov-heatmap.png`
- `hazard-survival.png`
- `advanced-cure-rates.png`
- `advanced-collateral.png`

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

- `npm run build`: 0 errors, 0 warnings
- Deployed to `docs_site/`
- All 5 pages render correctly in build output

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

- Screenshot placeholders need to be replaced with actual app screenshots from the live app
- Cure rate reference values (72%, 45%, 22%, 8%) are based on codebase analysis of seed data — actual institutional rates will differ
- CCF values shown are platform defaults — institutions should calibrate to their own portfolio data
- Collateral haircut percentages are regulatory baselines — institutions may have different recovery experience
- FAQ troubleshooting section covers common scenarios but is not exhaustive

## Files Changed

- `docs-site/docs/user-guide/approval-workflow.md` — expanded from 11 to 183 lines
- `docs-site/docs/user-guide/attribution.md` — expanded from 11 to 166 lines
- `docs-site/docs/user-guide/markov-hazard.md` — expanded from 11 to 200 lines
- `docs-site/docs/user-guide/advanced-features.md` — expanded from 11 to 217 lines
- `docs-site/docs/user-guide/faq.md` — expanded from 12 to 196 lines
- `docs-site/static/img/screenshots/approval-dashboard.png` — new placeholder
- `docs-site/static/img/screenshots/approval-queue.png` — new placeholder
- `docs-site/static/img/screenshots/attribution-waterfall.png` — new placeholder
- `docs-site/static/img/screenshots/attribution-breakdown.png` — new placeholder
- `docs-site/static/img/screenshots/markov-heatmap.png` — new placeholder
- `docs-site/static/img/screenshots/hazard-survival.png` — new placeholder
- `docs-site/static/img/screenshots/advanced-cure-rates.png` — new placeholder
- `docs-site/static/img/screenshots/advanced-collateral.png` — new placeholder
- `harness/contracts/sprint-5.md` — updated sprint contract
- `docs_site/` — rebuilt and deployed
