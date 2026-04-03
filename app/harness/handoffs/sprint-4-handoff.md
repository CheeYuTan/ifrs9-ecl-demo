# Sprint 4 Handoff: User Guide — Feature Pages Part 1

## What Was Built

Four User Guide documentation pages, each 150+ lines, following the established page template with Prerequisites, What You'll Do, Step-by-Step Instructions, Understanding the Results, Tips & Best Practices, and What's Next sections.

### Pages Created/Expanded

1. **model-registry.md** (175 lines) — Model governance lifecycle (Draft → Pending Review → Approved → Active → Retired), browsing the inventory, comparing models side-by-side with radar charts, reviewing auto-generated model cards, registering new models, approving and promoting champions. Includes segregation of duties warning.

2. **backtesting.md** (177 lines) — EBA traffic light system (green/amber/red), discrimination metrics (AUC, Gini, KS) with thresholds and plain-language explanations, calibration metrics (Hosmer-Lemeshow, binomial test), stability metrics (PSI, Brier Score), LGD backtesting (MAE, RMSE, Mean Bias), per-cohort analysis, trend tracking, and when-to-retrain decision matrix.

3. **regulatory-reports.md** (199 lines) — All eight IFRS 7 disclosure sections (35F through 36) with what each paragraph requires, report generation workflow, five report types (IFRS 7 Disclosure, ECL Movement, Stage Migration, Sensitivity, Concentration Risk), export formats (PDF, CSV), report lifecycle (Draft → Final → Submitted), and auditor-focus guidance.

4. **gl-journals.md** (225 lines) — Complete chart of accounts (9 accounts: asset, contra-asset, expense, income), three journal types (ECL provision, overlay, write-off) with debit/credit explanations, posting workflow, trial balance review, journal reversal process, and a plain-language section explaining double-entry ECL accounting for non-accountants.

### Placeholder Screenshots Created

6 placeholder PNG images (1280×720) in `docs-site/static/img/screenshots/`:
- `model-registry-list.png`
- `backtesting-traffic-light.png`
- `backtesting-cohort.png`
- `regulatory-reports-generate.png`
- `gl-journals-list.png`
- `gl-trial-balance.png`

## How to Test

```bash
cd '/Users/steven.tan/Expected Credit Losses/app'

# Build docs site
cd docs-site && npm run build

# Deploy
cd .. && rm -rf docs_site/* && cp -r docs-site/build/* docs_site/

# Start local dev server for browsing
cd docs-site && npm start
# Navigate to: http://localhost:3000/docs/user-guide/model-registry
# Navigate to: http://localhost:3000/docs/user-guide/backtesting
# Navigate to: http://localhost:3000/docs/user-guide/regulatory-reports
# Navigate to: http://localhost:3000/docs/user-guide/gl-journals
```

## Build Results

- `npm run build`: 0 errors, 0 warnings
- Deployed to `docs_site/`
- All 4 pages render correctly in build output

## Content Quality Checks

- All pages ≥150 lines (175, 177, 199, 225)
- No Python/JSON code in any User Guide page
- No API endpoint references in any User Guide page
- Correct IFRS 9 terminology throughout (ECL, PD, LGD, EAD, SICR, etc.)
- All internal cross-references point to valid page IDs
- All screenshot references point to existing files
- Admonitions used throughout (info, tip, warning, caution)
- Tables used extensively for structured information

## Known Limitations

- Screenshot placeholders need to be replaced with actual app screenshots from the live app
- Model Registry page describes 5 lifecycle states — if the app uses different states, page may need adjustment
- Backtesting thresholds are based on codebase analysis; verify against current configuration
- GL chart of accounts codes are platform-internal; page advises mapping to institution GL

## Files Changed

- `docs-site/docs/user-guide/model-registry.md` — expanded from 11 to 175 lines
- `docs-site/docs/user-guide/backtesting.md` — expanded from 11 to 177 lines
- `docs-site/docs/user-guide/regulatory-reports.md` — expanded from 11 to 199 lines
- `docs-site/docs/user-guide/gl-journals.md` — expanded from 11 to 225 lines
- `docs-site/static/img/screenshots/model-registry-list.png` — new placeholder
- `docs-site/static/img/screenshots/backtesting-traffic-light.png` — new placeholder
- `docs-site/static/img/screenshots/backtesting-cohort.png` — new placeholder
- `docs-site/static/img/screenshots/regulatory-reports-generate.png` — new placeholder
- `docs-site/static/img/screenshots/gl-journals-list.png` — new placeholder
- `docs-site/static/img/screenshots/gl-trial-balance.png` — new placeholder
- `harness/contracts/sprint-4.md` — updated sprint contract
- `docs_site/` — rebuilt and deployed
