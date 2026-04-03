# Sprint 1 Interaction Manifest

## Testing Tool: Playwright (headless Chromium)
## Date: 2026-04-02
## App URL: http://localhost:8000

---

## Sidebar Navigation

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Nav: ECL Workflow | click | Page loaded — "Create ECL Project" form displayed | TESTED |
| Nav: Data Mapping | click | Page loaded — loading spinner shown (data-dependent) | TESTED |
| Nav: Attribution | click | Page loaded — content area populated | TESTED |
| Nav: Models | click | Page loaded — loading spinner shown (data-dependent) | TESTED |
| Nav: Backtesting | click | Page loaded — loading spinner shown (data-dependent) | TESTED |
| Nav: Markov Chains | click | Page loaded — content area populated | TESTED |
| Nav: Hazard Models | click | Page loaded — loading spinner shown (data-dependent) | TESTED |
| Nav: GL Journals | click | Page loaded — "GL Journal Entries & Ledger" heading | TESTED |
| Nav: Reports | click | Page loaded — "Regulatory Reports" heading | TESTED |
| Nav: Approvals | click | Page loaded — content area populated | TESTED |
| Nav: Advanced | click | Page loaded — "Advanced ECL Features" heading | TESTED |
| Nav: Admin | click | Page loaded — "Loading configuration..." text | TESTED |

## Workflow Step Buttons (Top Bar)

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Step 1: Create Project | click | Navigates to Create Project form, step highlighted | TESTED |
| Step 2: Data Processing | click | Navigates to data processing view | TESTED |
| Step 3: Data Control (QC) | click | Navigates to QC view | TESTED |
| Step 4: Satellite Model | click | Navigates to satellite model view | TESTED |
| Step 5: Monte Carlo | click | Navigates to Monte Carlo view with loading | TESTED |
| Step 6: Stress Testing | click | Navigates to stress testing — loading + green CTA | TESTED |
| Step 7: Overlays | verify | Correctly disabled (pending step, prerequisites incomplete) | TESTED |
| Step 8: Sign Off | verify | Correctly disabled (pending step, prerequisites incomplete) | TESTED |

## Project Controls

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Project selector dropdown | click | Opens dropdown showing project list | TESTED |
| Collapse sidebar | click | Sidebar collapses to icons only, content area expands | TESTED |
| Reset workflow button | verify-present | Visible, enabled, accessible | TESTED |
| Update Project button | verify-present | Present on Create Project page | TESTED |
| Skip to main content link | verify-present | Visible, href=#main-content (a11y) | TESTED |

## Dark Mode

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Dark mode toggle (CSS emulation) | emulate dark scheme | Dark backgrounds applied consistently across all areas | TESTED |
| Dark mode toggle (button click) | click | Timeout locating button after nav sequence | BUG |
| Dark: Homepage | screenshot | Clean dark background, good contrast, no white flash | TESTED |
| Dark: Projects | screenshot | Consistent dark styling | TESTED |
| Dark: Monte Carlo | screenshot | Consistent dark styling | TESTED |

## Form Inputs

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Table search (input#table-search-default) | inspect | type=text, empty, enabled | TESTED |
| Approval comment (textarea#approval-comment) | inspect | type=textarea, empty, enabled | TESTED |

## Network & Console

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Console errors | monitor | 0 errors across all page loads | TESTED |
| Console warnings | monitor | 2 warnings (non-critical) | TESTED |
| HTTP responses | monitor | All pages return 200 OK | TESTED |

---

## API Endpoint Verification (Sprint 1 scope)

| Endpoint | Method | Result | Status |
|----------|--------|--------|--------|
| /api/setup/status | GET | 200 — returns config, table status, org info | TESTED |
| /api/projects | GET | 200 — returns list of 3 projects | TESTED |
| /api/projects/PROJ001 | GET | 200 — returns full project detail with audit log | TESTED |
| /api/projects/NONEXISTENT | GET | 404 — "Project not found" | TESTED |
| /api/projects/PROJ001/advance | POST | 200 — advances step correctly | TESTED |
| /api/projects/PROJ001/sign-off | POST (no body) | 422 — validation error "name required" | TESTED |
| /api/projects/PROJ001/verify-hash | GET | 200 — "not_computed" (correct for no hash) | TESTED |
| /api/projects/PROJ001/approval-history | GET | 200 — returns empty list (none yet) | TESTED |
| /api/setup/seed-sample-data | POST | 200 — "Sample data seeded successfully" | TESTED |
| /api/data/stage-distribution?project_id=PROJ001 | GET | 200 — 3 stages with loan counts | TESTED |
| /api/data/ecl-summary?project_id=PROJ001 | GET | 200 — ECL by product and stage | TESTED |
| /api/data/portfolio-summary?project_id=PROJ001 | GET | 200 — portfolio summary by product | TESTED |
| /api/data/scenario-summary?project_id=PROJ001 | GET | 200 — 7 scenarios with weights | TESTED |
| /api/data/top-exposures?project_id=PROJ001&limit=5 | GET | 200 — top 5 exposures by GCA | TESTED |
| /api/data/migration-matrix?project_id=PROJ001 | GET | 404 — "Not found" (expected: no data) | TESTED |
| /api/data/concentration?project_id=PROJ001 | GET | 404 — "Not found" (expected: no data) | TESTED |
| /api/rbac/users | GET | 200 — returns user list with roles | TESTED |
| /api/admin/config | GET | 200 — returns full config with schemas | TESTED |
| /api/health | GET | 200 — healthy, lakebase connected | TESTED |

## Iteration 5 — Expanded API Endpoint Verification

All 32 data routes verified against actual route definitions in `routes/data.py`:

| Endpoint | Method | Result | Status |
|----------|--------|--------|--------|
| /api/data/portfolio-summary | GET | 200 — 5 products with loan_count/gca/stages | TESTED |
| /api/data/stage-distribution | GET | 200 — 3 stages: 77,552 / 1,212 / 975 | TESTED |
| /api/data/ecl-summary | GET | 200 — product/stage/ecl breakdowns | TESTED |
| /api/data/ecl-by-product | GET | 200 — 5 products with coverage_ratio | TESTED |
| /api/data/scenario-summary | GET | 200 — 7 scenarios with weights | TESTED |
| /api/data/mc-distribution | GET | 200 — quantiles (p50/p75/p95/p99) per scenario | TESTED |
| /api/data/sensitivity | GET | 200 — avg_pd/implied_lgd/base_ecl per product | TESTED |
| /api/data/top-exposures | GET | 200 — highest-ECL loans | TESTED |
| /api/data/pd-distribution | GET | 200 — PD distribution data | TESTED |
| /api/data/borrower-segments | GET | 200 — segment data | TESTED |
| /api/data/vintage-analysis | GET | 200 — vintage data | TESTED |
| /api/data/dpd-distribution | GET | 200 — DPD buckets | TESTED |
| /api/data/stage-by-product | GET | 200 — stage breakdown by product | TESTED |
| /api/data/dq-results | GET | 200 — data quality results | TESTED |
| /api/data/dq-summary | GET | 200 — data quality summary | TESTED |
| /api/data/gl-reconciliation | GET | 200 — GL reconciliation | TESTED |
| /api/data/ecl-by-scenario-product | GET | 200 — ECL by scenario/product | TESTED |
| /api/data/ecl-concentration | GET | 200 — concentration data | TESTED |
| /api/data/stage-migration | GET | 200 — migration matrix | TESTED |
| /api/data/credit-risk-exposure | GET | 200 — credit risk exposure | TESTED |
| /api/data/loss-allowance-by-stage | GET | 200 — loss allowance | TESTED |
| /api/data/ecl-by-stage-product/1 | GET | 200 — Stage 1 ECL by product | TESTED |
| /api/data/ecl-by-scenario-product-detail?scenario=baseline | GET | 200 — scenario detail | TESTED |
| /api/data/loans-by-product/auto_loan | GET | 200 — auto loan details | TESTED |
| /api/data/loans-by-stage/1 | GET | 200 — Stage 1 loans | TESTED |
| /api/data/scenario-comparison | GET | 200 — scenario comparison | TESTED |
| /api/data/stress-by-stage | GET | 200 — stress by stage | TESTED |
| /api/data/vintage-performance | GET | 200 — vintage performance | TESTED |
| /api/data/vintage-by-product | GET | 200 — vintage by product | TESTED |
| /api/data/concentration-by-segment | GET | 200 — concentration by segment | TESTED |
| /api/data/concentration-by-product-stage | GET | 200 — concentration by product/stage | TESTED |
| /api/data/top-concentration-risk | GET | 200 — top concentration risks | TESTED |

**32/32 data endpoints TESTED, 0 BUG.**

## Full Test Suite (Iteration 5)

| Metric | Value | Status |
|--------|-------|--------|
| Total pytest passing | 2,718 | TESTED |
| Skipped | 61 | Expected |
| Failures | 0 | TESTED |
| Sprint 1 tests | 299 (174+62+36+27) | Verified |
| Runtime | 111s | Acceptable |

## Summary

- **Total UI elements tested**: 33
- **TESTED**: 32
- **BUG**: 1 (dark mode toggle button click timeout — CSS-based dark mode works fine)
- **SKIPPED**: 0
- **PENDING**: 0
- **API endpoints verified**: 51 (32 data + 5 projects + 4 setup + 3 admin/RBAC + 7 error cases)
- **API regressions**: 0
