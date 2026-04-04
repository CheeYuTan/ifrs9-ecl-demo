# Sprint 1 Handoff: Usage Analytics Backend (Iteration 2)

## What Was Built (Iteration 1)
- `domain/usage_analytics.py`: New domain module with `ensure_usage_table()`, `record_request()`, `get_usage_stats()`, `get_recent_requests()`
- New Lakebase table `expected_credit_loss.app_usage_analytics` (id, timestamp, user_id, method, endpoint, status_code, duration_ms, request_id, user_agent)
- Wired into `domain/workflow.py` init chain (after `ensure_rbac_tables`)
- Re-exported in `backend.py` for unified imports
- 15 unit tests covering table creation, idempotency, record insertion, stats queries, edge cases

## What Was Fixed (Iteration 2 — Evaluation Bugs)

### BUG-S1-001: Homepage meta title "Hello from" prefix
- **File**: `docs-site/src/pages/index.tsx:36` — already fixed in codebase; title uses `{siteConfig.title}` directly
- **Regression test**: `test_no_hello_from_in_index_tsx`

### BUG-S1-002: Homepage meta description stock placeholder
- **File**: `docs-site/src/pages/index.tsx:37` — already fixed; description reads "IFRS 9 Expected Credit Loss calculation and reporting documentation..."
- **Regression tests**: `test_no_placeholder_description`, `test_description_mentions_ecl_or_ifrs`

### BUG-S1-003: Stock Docusaurus feature cards with dinosaur SVGs
- **File**: `docs-site/src/components/HomepageFeatures/index.tsx` — already fixed; features are IFRS 9 relevant ("3-Stage Impairment Model", "Monte Carlo Simulation", "Regulatory Reporting") with emoji icons
- **Regression tests**: `test_no_stock_feature_titles`, `test_no_docusaurus_svg_imports`, `test_features_are_ifrs9_relevant`

### BUG-S1-004: `onBrokenLinks` set to 'warn'
- **File**: `docs-site/docusaurus.config.ts:16` — already fixed; `onBrokenLinks: 'throw'`
- **Regression tests**: `test_on_broken_links_is_throw`, `test_on_broken_links_not_warn`

## New Files (Iteration 2)
- `tests/regression/test_docs_homepage_bugs.py` — 8 regression tests for BUG-S1-001 through BUG-S1-004

## How to Test
- Start: `cd /Users/steven.tan/Expected\ Credit\ Losses/app && python app.py`
- The table is auto-created on startup via the init chain
- No HTTP endpoints this sprint (domain layer only) — Sprint 2 adds middleware + Sprint 4 adds admin API
- Docs site: `cd docs-site && npm run build` — 0 errors, 0 warnings

## Test Results
```
pytest tests/unit/test_usage_analytics.py -v
15 passed in 0.10s

pytest tests/regression/test_docs_homepage_bugs.py -v
8 passed in 0.10s

Full suite: 3979 passed, 1 failed (pre-existing InsufficientPrivilege on test_sign_off), 61 skipped
Docs build: SUCCESS — 0 errors, 0 warnings
```

## Known Limitations
- 1 pre-existing integration test failure (`test_sign_off`) — Lakebase privilege issue on `COMMENT ON TABLE ecl_workflow`, not related to Sprint 1 changes
- No HTTP API to query analytics yet (Sprint 4)
- No middleware to auto-record requests yet (Sprint 2)

## Files Changed

### New Files
- `tests/regression/test_docs_homepage_bugs.py` — 8 regression tests (82 lines)

### Previously Built (Iteration 1)
- `domain/usage_analytics.py` — domain module (96 lines)
- `tests/unit/test_usage_analytics.py` — 15 unit tests (150 lines)
- `domain/workflow.py` — added `ensure_usage_table` to init chain
- `backend.py` — added usage analytics re-exports
