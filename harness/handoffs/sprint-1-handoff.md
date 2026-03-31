# Sprint 1 Handoff: ECL Attribution Analysis Frontend

## What Was Built

### New Files
- `app/frontend/src/pages/Attribution.tsx` — Full Attribution Analysis page with:
  - Waterfall chart visualization (recharts stacked BarChart with invisible base bars)
  - Stage-level breakdown table showing all 10 IFRS 7.35I components
  - Reconciliation status card with materiality check (pass/fail badge)
  - Compute Attribution button for fresh recomputation
  - Attribution history selector with period-over-period comparison
  - Data gap indicators (amber badges for unavailable components)
  - Estimated data indicators (blue badges for proxy-computed values)
  - Loading skeleton, empty state, and error state handling
  - Full dark mode support via Tailwind dark: classes

### Modified Files
- `app/frontend/src/components/Sidebar.tsx` — Added `attribution` ViewType and sidebar nav item under "Analytics" group with BarChart3 icon
- `app/frontend/src/App.tsx` — Added lazy import for Attribution page and routing case in `renderSecondaryView`

### Backend (pre-existing, no changes needed)
- `app/domain/attribution.py` — Full attribution engine (530 lines, already built)
- `app/routes/attribution.py` — REST endpoints (GET/POST, already built)
- `app/frontend/src/lib/api.ts` — API client methods (already built)

## How to Test
- Start: `cd app && uvicorn app:app --reload --port 8000`
- Navigate to: http://localhost:8000
- Click "Attribution" in the sidebar under "Analytics"
- Test: Click "Recompute" button — waterfall chart + breakdown table should render
- Test: Verify dark mode toggle works on the attribution page
- Test: Verify loading skeleton shows during data fetch

## Test Results
- `npm run build` — SUCCESS (0 errors, 0 warnings)
- `pytest tests/ --ignore=tests/unit/test_reports_routes.py` — 925 passed, 61 skipped, 2 failed (pre-existing path issues in test_installation_sprint7.py, unrelated to this sprint)
- Attribution-specific tests: 17 passed in 0.11s

## Known Limitations
- Attribution page uses hardcoded project ID `demo_2025q1` — should eventually read from project context
- Waterfall chart uses stacked bars with invisible base; this is a common recharts pattern but may have tooltip precision issues on very small movement components
- No frontend unit tests added for the new React component (existing backend tests cover the engine)

## Files Changed
| File | Lines | Action |
|------|-------|--------|
| `app/frontend/src/pages/Attribution.tsx` | 358 | NEW |
| `app/frontend/src/components/Sidebar.tsx` | 3 lines changed | MODIFIED |
| `app/frontend/src/App.tsx` | 8 lines added | MODIFIED |
| `harness/contracts/sprint-1.md` | — | NEW |
