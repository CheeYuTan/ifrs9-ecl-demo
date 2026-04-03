# Context Reset 1 — After Sprint 3

## Current State
- **Phase**: BUILD_AGENT
- **Sprint**: Starting Sprint 4 of 7
- **Quality Target**: 9.0/10
- **Score Trajectory**: Sprints 1-3 passed (no evaluator scoring yet — need to add)

## Architecture Decisions Made
1. **Compatibility shim approach**: `backend.py` re-exports all symbols from new modules so existing `import backend` and `patch("backend.func")` in tests continue to work
2. **sys.path-based imports**: All modules use bare imports (`from db.pool import ...`) since `app/` is on sys.path
3. **No test modifications**: All 33 new modules created without changing any existing test file
4. **scipy dependency**: Added for calibration tests (binomial, Hosmer-Lemeshow, Jeffreys, Spiegelhalter)

## Domain Context (SME Active)
- IFRS 9 Expected Credit Loss platform for banking
- Key regulatory references: IFRS 9.5.5.1-5.5.20, IFRS 7.35H-35N, BCBS d350, EBA/GL/2017/16
- Core ECL methodology is sound; improvements focus on governance, validation, auditability
- See `harness/sme/domain-brief.md` for full analysis

## Completed Sprints
1. **Modularize Backend** — Split 4,807-line backend.py into 13 domain + 16 route modules
2. **Real Backtesting Engine** — Replaced hardcoded LGD metrics, added calibration tests
3. **RBAC Enforcement** — Auth middleware, permission dependencies, ECL hash verification

## Remaining Sprints
4. **Attribution Waterfall from Actual Data** — Fix IFRS 7.35I compliance, eliminate hardcoded percentage fallbacks
5. **Model Registry & Validation Framework** — Model lifecycle, challenger comparison, out-of-sample testing
6. **Domain Validation Rules & Data Quality** — 23 domain rules enforced programmatically
7. **Comprehensive Testing & Polish** — Full coverage, terminology cleanup, docs updates

## Exact Next Step
- Write `harness/contracts/sprint-4.md`
- Read `app/domain/attribution.py` (446 lines) to understand current waterfall implementation
- Replace hardcoded percentage fallbacks with loan-level attribution computation
- Write unit tests for attribution engine
- Run evaluator

## Files to Read on Resume
1. `harness/state.json` — current state
2. `harness/progress.md` — sprint status table
3. `harness/spec.md` — full improvement plan
4. `harness/sme/domain-brief.md` — Section 7 (Attribution Requirements)
5. `app/domain/attribution.py` — current implementation to improve
6. `app/backend.py` — re-export shim (verify it's up to date)

## Test Baseline
```
153 passed, 2 pre-existing failures (job config)
New test files: test_backtesting.py (45), test_rbac.py (25)
```
