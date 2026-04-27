# Sprint 4 Interaction Manifest — User Guide Feature Pages Part 1

## Testing Method
Docusaurus documentation site tested via HTTP requests against live dev server (localhost:3000) and production build verification. Content validated from pre-rendered HTML in `docs_site/` build output. Build verified with `npm run build` (0 errors, 0 warnings).

## Page: Model Registry (`/docs/user-guide/model-registry`)

| Element | Type | Action | Result | Status |
|---------|------|--------|--------|--------|
| Page load | Navigation | HTTP GET | 200 OK, 39,982 bytes built | TESTED |
| Sidebar: Model Registry | Nav link | Verify present | Correctly positioned after Step 8 | TESTED |
| Prev: Step 8: Sign-Off | Pagination | Verify link | Correct prev page | TESTED |
| Next: Backtesting | Pagination | Verify link | Correct next page | TESTED |
| H1: Model Registry | Heading | Verify render | Renders correctly | TESTED |
| Prerequisites section | Content | Verify present | Present with admonition | TESTED |
| What You'll Do section | Content | Verify present | Present with checklist | TESTED |
| Understanding Model Lifecycle | Content | Verify present | 5-state lifecycle documented | TESTED |
| Step 1: Browse Model Inventory | Content | Verify heading | H3 heading present | TESTED |
| Step 2: View Model Details | Content | Verify heading | H3 heading present | TESTED |
| Step 3: Compare Models Side-by-Side | Content | Verify heading | H3 heading present | TESTED |
| Step 4: Review the Model Card | Content | Verify heading | H3 heading present | TESTED |
| Step 5: Register a New Model | Content | Verify heading | H3 heading present | TESTED |
| Step 6: Approve and Promote Models | Content | Verify heading | H3 heading present | TESTED |
| Understanding Model Types | Content | Verify present | Present | TESTED |
| Tips & Best Practices | Content | Verify present | Present | TESTED |
| What's Next | Content | Verify present | Present with cross-links | TESTED |
| Image: model-registry-list.png | Image | Verify loads | 1280x720 PNG, 17,290 bytes, valid | TESTED |
| Tables (4) | Content | Verify render | All 4 tables render correctly | TESTED |
| Admonitions (7: info, warning x2, tip x3, caution) | Content | Verify render | All styled correctly | TESTED |
| Link: step-4-satellite-model | Navigation | Verify resolve | 200 OK | TESTED |
| Link: backtesting | Navigation | Verify resolve | 200 OK | TESTED |
| Link: regulatory-reports | Navigation | Verify resolve | 200 OK | TESTED |
| Dark mode CSS | Theme | Verify vars | [data-theme='dark'] configured | TESTED |
| No Python/JSON code | Anti-pattern | Verify absent | Clean — no code blocks | TESTED |
| No API endpoints | Anti-pattern | Verify absent | Clean — no /api/ references | TESTED |
| IFRS 9 terminology | Content | Verify | ECL(8), PD(8), LGD(6), EAD(4), IFRS(2) | TESTED |
| Content word count | Content | Verify | 1,335 words (175 source lines) | TESTED |

## Page: Backtesting (`/docs/user-guide/backtesting`)

| Element | Type | Action | Result | Status |
|---------|------|--------|--------|--------|
| Page load | Navigation | HTTP GET | 200 OK, 41,127 bytes built | TESTED |
| Sidebar: Backtesting | Nav link | Verify present | After Model Registry | TESTED |
| Prev: Model Registry | Pagination | Verify link | Correct | TESTED |
| Next: Regulatory Reports | Pagination | Verify link | Correct | TESTED |
| H1: Backtesting | Heading | Verify render | Renders correctly | TESTED |
| Prerequisites section | Content | Verify present | Present | TESTED |
| What You'll Do section | Content | Verify present | Present | TESTED |
| Traffic Light System | Content | Verify present | Green/Amber/Red documented | TESTED |
| Step 1: Select a Model | Content | Verify heading | H3 present | TESTED |
| Step 2: Configure the Backtest | Content | Verify heading | H3 present | TESTED |
| Step 3: Run the Backtest | Content | Verify heading | H3 present | TESTED |
| Step 4: Read Results — PD Models | Content | Verify heading | H3 present | TESTED |
| Discrimination Metrics (AUC, Gini, KS) | Content | Verify subsection | H4, thresholds documented | TESTED |
| Calibration Metrics (Hosmer-Lemeshow) | Content | Verify subsection | H4, thresholds documented | TESTED |
| Stability Metrics (PSI, Brier) | Content | Verify subsection | H4, thresholds documented | TESTED |
| Step 5: Read Results — LGD Models | Content | Verify heading | H3 present (MAE, RMSE, Bias) | TESTED |
| Step 6: Per-Cohort Performance | Content | Verify heading | H3 present | TESTED |
| Step 7: Historical Trends | Content | Verify heading | H3 present | TESTED |
| When to Retrain a Model | Content | Verify present | Decision matrix | TESTED |
| Tips & Best Practices | Content | Verify present | Present | TESTED |
| What's Next | Content | Verify present | Cross-links | TESTED |
| Image: backtesting-traffic-light.png | Image | Verify loads | 1280x720 PNG, 18,548 bytes | TESTED |
| Image: backtesting-cohort.png | Image | Verify loads | 1280x720 PNG, 18,299 bytes | TESTED |
| Tables (7) | Content | Verify render | All 7 render correctly | TESTED |
| Admonitions (5: info, tip x2, warning, caution) | Content | Verify render | All styled correctly | TESTED |
| Link: model-registry | Navigation | Verify resolve | 200 OK | TESTED |
| Link: step-6-stress-testing | Navigation | Verify resolve | 200 OK | TESTED |
| Link: step-4-satellite-model | Navigation | Verify resolve | 200 OK | TESTED |
| Dark mode CSS | Theme | Verify vars | Inherits dark theme | TESTED |
| No Python/JSON code | Anti-pattern | Verify absent | Clean | TESTED |
| No API endpoints | Anti-pattern | Verify absent | Clean | TESTED |
| "loss rate" terminology | Content | Context check | Valid usage (observed rates, not LGD substitute) | TESTED |
| Content word count | Content | Verify | 1,503 words (177 source lines) | TESTED |

## Page: Regulatory Reports (`/docs/user-guide/regulatory-reports`)

| Element | Type | Action | Result | Status |
|---------|------|--------|--------|--------|
| Page load | Navigation | HTTP GET | 200 OK, 43,590 bytes built | TESTED |
| Sidebar: Regulatory Reports | Nav link | Verify present | After Backtesting | TESTED |
| Prev: Backtesting | Pagination | Verify link | Correct | TESTED |
| Next: GL Journals | Pagination | Verify link | Correct | TESTED |
| H1: Regulatory Reports | Heading | Verify render | Renders correctly | TESTED |
| Prerequisites section | Content | Verify present | Present | TESTED |
| What You'll Do section | Content | Verify present | Present | TESTED |
| IFRS 7 Disclosure Sections | Content | Verify present | 35F through 36 documented | TESTED |
| Step 1: Navigate to Reports | Content | Verify heading | H3 present | TESTED |
| Step 2: Select Report Type | Content | Verify heading | 5 report types documented | TESTED |
| Step 3: Generate the Report | Content | Verify heading | H3 present | TESTED |
| Step 4: Review IFRS 7 Disclosure | Content | Verify heading | H3 present | TESTED |
| Section 35F subsection | Content | Verify | Credit Risk Exposure by Grade | TESTED |
| Section 35H subsection | Content | Verify | Loss Allowance by Stage (Stage 1/2/3) | TESTED |
| Section 35I subsection | Content | Verify | Reconciliation | TESTED |
| Section 35J subsection | Content | Verify | Collateral and LGD | TESTED |
| Sections 35K-35M subsection | Content | Verify | Additional Disclosures | TESTED |
| Section 36 subsection | Content | Verify | Sensitivity Analysis | TESTED |
| Step 5: Export the Report | Content | Verify heading | PDF, CSV formats | TESTED |
| Step 6: Finalise the Report | Content | Verify heading | Draft → Final → Submitted | TESTED |
| Understanding the Results | Content | Verify present | Present | TESTED |
| Tips & Best Practices | Content | Verify present | Auditor-focus guidance | TESTED |
| What's Next | Content | Verify present | Cross-links | TESTED |
| Image: regulatory-reports-generate.png | Image | Verify loads | 1280x720 PNG, 17,640 bytes | TESTED |
| Tables (5) | Content | Verify render | All 5 render correctly | TESTED |
| Admonitions (7: info, tip x4, warning, caution) | Content | Verify render | All styled correctly | TESTED |
| Link: step-8-sign-off | Navigation | Verify resolve | 200 OK | TESTED |
| Link: backtesting | Navigation | Verify resolve | 200 OK | TESTED |
| Link: gl-journals | Navigation | Verify resolve | 200 OK | TESTED |
| Link: attribution | Navigation | Verify resolve | 200 OK | TESTED |
| Dark mode CSS | Theme | Verify vars | Inherits dark theme | TESTED |
| No Python/JSON code | Anti-pattern | Verify absent | Clean | TESTED |
| No API endpoints | Anti-pattern | Verify absent | Clean | TESTED |
| IFRS terminology | Content | Verify | IFRS(18), ECL(37), PD(6), LGD(9), EAD(4), Stages(9) | TESTED |
| Content word count | Content | Verify | 1,582 words (199 source lines) | TESTED |

## Page: GL Journals (`/docs/user-guide/gl-journals`)

| Element | Type | Action | Result | Status |
|---------|------|--------|--------|--------|
| Page load | Navigation | HTTP GET | 200 OK, 45,469 bytes built | TESTED |
| Sidebar: GL Journals | Nav link | Verify present | After Regulatory Reports | TESTED |
| Prev: Regulatory Reports | Pagination | Verify link | Correct | TESTED |
| Next: Approval Workflow | Pagination | Verify link | Correct | TESTED |
| H1: GL Journals | Heading | Verify render | Renders correctly | TESTED |
| Prerequisites section | Content | Verify present | Present | TESTED |
| What You'll Do section | Content | Verify present | Present | TESTED |
| Chart of Accounts (9 accounts) | Content | Verify present | Asset, contra-asset, expense, income | TESTED |
| Step 1: Navigate to GL Journals | Content | Verify heading | H3 present | TESTED |
| Step 2: Generate Journal Entries | Content | Verify heading | H3 present | TESTED |
| Step 3: Understand Journal Types | Content | Verify heading | H3 present | TESTED |
| ECL Provision Journals subsection | Content | Verify | Debit/credit explanations | TESTED |
| Management Overlay Journals subsection | Content | Verify | Present | TESTED |
| Write-off Journals subsection | Content | Verify | Present | TESTED |
| Step 4: Review Journal Details | Content | Verify heading | H3 present | TESTED |
| Step 5: Post Journals | Content | Verify heading | Posting workflow | TESTED |
| Step 6: Review Trial Balance | Content | Verify heading | Present | TESTED |
| Step 7: Reverse a Journal | Content | Verify heading | Corrections workflow | TESTED |
| Step 8: Review Chart of Accounts | Content | Verify heading | Present | TESTED |
| Understanding Double-Entry for ECL | Content | Verify present | Plain-language for non-accountants | TESTED |
| Tips & Best Practices | Content | Verify present | Present | TESTED |
| What's Next | Content | Verify present | Cross-links | TESTED |
| Image: gl-journals-list.png | Image | Verify loads | 1280x720 PNG, 15,303 bytes | TESTED |
| Image: gl-trial-balance.png | Image | Verify loads | 1280x720 PNG, 16,301 bytes | TESTED |
| Tables (6) | Content | Verify render | All 6 render correctly | TESTED |
| Admonitions (9: info, tip x4, warning x2, caution x2) | Content | Verify render | All styled correctly | TESTED |
| Link: step-8-sign-off | Navigation | Verify resolve | 200 OK | TESTED |
| Link: step-7-overlays | Navigation | Verify resolve | 200 OK | TESTED |
| Link: regulatory-reports | Navigation | Verify resolve | 200 OK | TESTED |
| Link: attribution | Navigation | Verify resolve | 200 OK | TESTED |
| Dark mode CSS | Theme | Verify vars | Inherits dark theme | TESTED |
| No Python/JSON code | Anti-pattern | Verify absent | Clean | TESTED |
| No API endpoints | Anti-pattern | Verify absent | Clean | TESTED |
| ECL terminology | Content | Verify | ECL(46), Stage 1(8), Stage 2(5), Stage 3(8), IFRS(2) | TESTED |
| Content word count | Content | Verify | 1,678 words (225 source lines) | TESTED |

## Summary

| Category | Total | TESTED | BUG | SKIPPED |
|----------|-------|--------|-----|---------|
| Page loads | 4 | 4 | 0 | 0 |
| Navigation (sidebar, prev/next) | 12 | 12 | 0 | 0 |
| Content sections | 52 | 52 | 0 | 0 |
| Images | 6 | 6 | 0 | 0 |
| Tables | 22 | 22 | 0 | 0 |
| Admonitions | 28 | 28 | 0 | 0 |
| Internal links | 14 | 14 | 0 | 0 |
| Anti-pattern checks | 8 | 8 | 0 | 0 |
| Terminology checks | 4 | 4 | 0 | 0 |
| Dark mode | 4 | 4 | 0 | 0 |
| Build verification | 1 | 1 | 0 | 0 |
| Regression (Sprint 1-3) | 11 | 11 | 0 | 0 |
| **TOTAL** | **166** | **166** | **0** | **0** |
