# Sprint 2 Handoff: User Guide — Workflow Steps 1-4

## What Was Built

Four comprehensive User Guide pages documenting the first four steps of the IFRS 9 ECL workflow. Each page follows the User Guide template with frontmatter, prerequisites, step-by-step instructions, tables explaining UI elements, IFRS 9 context, tips/warnings, and "What's Next?" navigation.

### Pages Written

| Page | Lines | Words | Key Content |
|------|-------|-------|-------------|
| `step-1-create-project.md` | 121 | 953 | Project form fields, project states, audit trail, immutability after sign-off |
| `step-2-data-processing.md` | 130 | 1,239 | Data lineage, 4 KPI cards, stage distribution chart, portfolio table, drill-down charts |
| `step-3-data-control.md` | 141 | 1,308 | DQ checks, GL reconciliation, materiality thresholds, approval/rejection form, maker-checker |
| `step-4-satellite-model.md` | 176 | 1,725 | 8 model types explained, pipeline execution, run history, cohort comparison, R-squared/RMSE in plain language |

### Screenshot Placeholders Created

6 placeholder PNGs in `docs-site/static/img/screenshots/`:
- `step-1-create-project.png`
- `step-2-stage-distribution.png`
- `step-3-data-control.png`
- `step-3-approval-form.png`
- `step-4-run-pipeline.png`
- `step-4-model-comparison.png`

Also references 1 existing screenshot from `docs-site/static/img/guides/portfolio-dashboard.png`.

### Files Changed
- `docs-site/docs/user-guide/step-1-create-project.md` (rewritten from stub)
- `docs-site/docs/user-guide/step-2-data-processing.md` (rewritten from stub)
- `docs-site/docs/user-guide/step-3-data-control.md` (rewritten from stub)
- `docs-site/docs/user-guide/step-4-satellite-model.md` (rewritten from stub)
- `docs-site/static/img/screenshots/` (6 new placeholder PNGs)
- `docs_site/` (rebuilt and deployed)
- `harness/contracts/sprint-2.md` (updated for docs transformation)

## How to Test
- Build: `cd docs-site && npm run build` — must succeed with 0 errors
- Serve locally: `cd docs-site && npm run serve` → navigate to `/user-guide/step-1-create-project`
- Deploy: `rm -rf docs_site/* && cp -r docs-site/build/* docs_site/`

## Test Results
- **Build**: 0 errors, 0 warnings
- **Persona check**: Zero Python/JSON/API violations in all 4 pages
- **Link check**: All internal cross-references resolve (verified by build)
- **Deployed**: `docs_site/` updated with built output

## Known Limitations
- Screenshot placeholders are grey rectangles — to be replaced with actual screenshots captured from the live app during Visual QA
- Existing screenshot at `/img/guides/portfolio-dashboard.png` is referenced in Step 2; may need updating if the current UI differs

## Bugs Found
- None
