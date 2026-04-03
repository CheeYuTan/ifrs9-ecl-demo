# Documentation Batch 2 Report — QA Audit Run

**Sprints covered**: Sprint 3 (Model Registry, Backtesting, Markov, Hazard), Sprint 4 (GL Journals, Reports, RBAC, Audit, Admin, Data Mapping, Advanced, Period Close), Sprint 5 (ECL Engine Monte Carlo)
**Date**: 2026-04-02

## New Feature Guides

### 1. Operational & Governance Features (`docs/guides/operational-governance.md`)
- **Sprint 4 coverage**: 67 endpoints across 8 route modules
- Sections: GL Journals (double-entry, trial balance, reversal), Regulatory Reports (5 IFRS 7 types, CSV/PDF export), RBAC (maker-checker, segregation of duties), Audit Trail (hash chain verification), Admin Console (config, discovery, schema validation), Data Mapping (suggest → validate → apply pipeline), Advanced Analytics (cure rates, CCF, collateral), Period Close (pipeline orchestration)
- 5 screenshots: gl-journals, reports, approval-workflow, admin, advanced, data-mapping pages

### 2. ECL Engine Deep Dive (`docs/guides/ecl-engine.md`)
- **Sprint 5 coverage**: 9 modules in `ecl/` package (141 tests)
- Sections: ECL formula (PD x LGD x EAD x DF), Cholesky-correlated draws, stage-aware calculation (Stage 1/2/3 horizons), SICR stage transfer logic, parameter controls (PD/LGD bounds, amortizing EAD), scenario weighting, convergence diagnostics, aggregation outputs, numerical stability
- Hand-calculated verification examples with 1e-6 tolerance
- 2 screenshots: monte-carlo-workflow, ecl-homepage

### 3. Existing Guide (Sprint 3) — Already documented
- `docs/guides/model-analytics.md` was created in Batch 1 covering Model Registry, Backtesting, Markov Chains, and Hazard Models

## Updated Structural Pages

| Page | Changes |
|------|---------|
| `overview.md` | Added GL Journals, Period Close, Data Mapping, Advanced Analytics to features table |
| `architecture.md` | Added 4 new API route table entries (admin, data-mapping, advanced, period-close); expanded ECL engine section with convergence and numerical stability; added `ecl/` and `reporting/` modules to directory tree; updated test count to 3,400+ |

## Updated Configuration

| File | Changes |
|------|---------|
| `sidebars.ts` | Added `operational-governance` and `ecl-engine` to Feature Guides category |
| `docusaurus.config.ts` | Added footer links for new guides; removed deprecated `onBrokenMarkdownLinks` config |
| `src/pages/index.tsx` | Fixed broken `/docs/intro` link → `/docs/overview` |

## Screenshots Captured (9 total)

| Screenshot | File | Feature |
|-----------|------|---------|
| GL Journals page | `gl-journals-page.png` | Journal generation and posting |
| Regulatory Reports | `reports-page.png` | IFRS 7 report generation and export |
| Approval Workflow | `approval-workflow-page.png` | Pending approvals and history |
| Admin Console | `admin-page.png` | Database config and table management |
| Advanced Features | `advanced-page.png` | Cure rates, CCF, collateral |
| Data Mapping | `data-mapping-page.png` | Schema discovery and column mapping |
| Monte Carlo Workflow | `monte-carlo-workflow.png` | Simulation config and execution |
| ECL Homepage | `ecl-homepage.png` | Platform homepage with ECL summary |
| Workflow Overview | `ecl-workflow-overview.png` | 8-step ECL workflow stepper |

## Build Verification

```
$ cd docs-site && npm run build
[SUCCESS] Generated static files in "build".
```

- Build: **PASS** (zero errors)
- Warnings: **0**
- Broken links: **0** (fixed `/docs/intro` → `/docs/overview`)

## Checklist

- [x] Each major feature has its own guide (5 guides total: 3 from Batch 1 + 2 new)
- [x] All internal links resolve (`onBrokenLinks: 'throw'` verified)
- [x] Every feature has screenshots (9 this batch, 15+ total)
- [x] All visuals freshly captured from running app
- [x] Doc site builds with zero warnings
- [x] Sidebar updated with new entries
- [x] Footer navigation updated
- [x] Overview and architecture pages updated for Sprint 4/5 features

## Status: PASS
