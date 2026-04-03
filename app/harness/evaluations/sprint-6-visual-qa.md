# Sprint 6 Visual QA Report — Domain Logic Testing (Iteration 2)

## Sprint Type

**Backend test-only sprint** — 196 new unit tests covering 8 domain modules (189 original + 7 new in iteration 2). No UI changes, no API changes, no frontend changes. Visual QA focuses on regression verification.

## Application Status

- **Dev server**: Running on port 8000, responding to requests
- **SPA**: Loads correctly, returns valid HTML with React app
- **API**: All tested endpoints return valid JSON responses
- **Projects**: 4 projects accessible, project detail includes step_status and audit_log

## API Regression Check

All tested API endpoints respond correctly with no errors:

| Category | Endpoints Tested | Result |
|----------|-----------------|--------|
| Project lifecycle | 2 (list, detail) | PASS |
| Data queries | 4 (portfolio, stage, ECL summary, ECL by product) | PASS |
| Scenario data | 1 (scenario summary) | PASS |
| Admin config | 1 (config) | PASS |
| Audit trail | 2 (config changes, trail) | PASS |
| Setup | 1 (status) | PASS |
| **Total** | **11** | **ALL PASS** |

## Test Suite Results

```
Sprint 6 tests:  196 passed in 10.02s
Full suite:      3,608 passed, 61 skipped, 0 failures in 113.25s
Regressions:     0
```

## Data Integrity Observations

- **Stage distribution**: 3 stages (77,552 / 1,212 / 975 loans) — realistic IFRS 9 distribution with ~97% Stage 1
- **Portfolio summary**: 5 product types (commercial_loan, residential_mortgage, personal_loan, credit_card, auto_loan) with valid GCA, EIR, DPD, PD values
- **ECL summary**: Coverage ratios in reasonable range (0.03-1.83%)
- **Scenario summary**: 7 macroeconomic scenarios with probability weights, ECL values consistent across scenarios
- **Audit chain**: `chain_verification.valid = true` for both config and trail endpoints

## Console Errors

No server-side errors observed. All API responses returned 200 status codes for valid requests.

## Design Consistency

N/A — no UI changes in this sprint. The frontend SPA loads the same assets as before (index-DNaCEbyM.js, motion-DSndAWGS.js, charts-nV4Kelm5.js, index-DF6l7LEH.css).

## Lighthouse Scores

N/A — no frontend changes to evaluate. SPA serves the same compiled assets.

## Iteration 2 Fix Verification

All 5 evaluator issues from iteration 1 were addressed:

1. **ISSUE-S6-1**: 6 thin query tests strengthened with SQL keyword assertions (GROUP BY, table names, ORDER BY) — VERIFIED
2. **ISSUE-S6-2**: Waterfall sum-to-total test added (`test_waterfall_components_sum_to_ecl_change`) — VERIFIED (IFRS 7.35I compliance)
3. **ISSUE-S6-3**: Residual materiality boolean test added (`test_residual_within_materiality`) — VERIFIED (5% threshold check)
4. **ISSUE-S6-4**: `get_mapping_status` tests added (2 tests: keys/counts + DB error handling) — VERIFIED
5. **ISSUE-S6-5**: 2 additional `model_runs` tests added (explicit dimension + insert new run) — VERIFIED
6. **Bonus**: `test_prior_attribution_returns_none` — validates opening==closing when no prior exists — VERIFIED

## Recommendation

**PROCEED** — No regressions detected. All 196 new tests pass. Full suite of 3,608 tests passes with 0 failures. API endpoints respond correctly. Application loads and serves data properly. All 5 iteration 1 evaluator issues have been resolved. This is a clean test-only sprint with no risk to the live application.
