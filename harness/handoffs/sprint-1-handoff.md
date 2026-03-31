# Sprint 1 Handoff: QA Bug Fixes & Code Quality Polish

## What Was Built
Fixed all 10 remaining LOW severity bugs from the QA bug hunt, bringing the total bugs fixed from 22 to 32 (all 32 found).

### Bug Fixes

| ID | File | Fix |
|----|------|-----|
| U01 | KpiCard.tsx | Removed unused `trend` prop from Props interface |
| U02 | DrillDownChart.tsx | Used `title` prop as `aria-label` on chart container instead of voiding it |
| U03 | Sidebar.tsx | Added `layoutScope` param to `NavButton`; mobile and desktop now use distinct `layoutId` values (`sidebar-active-pill-mobile` / `sidebar-active-pill-desktop`) |
| U04 | CollapsibleSection.tsx | Added framer-motion `AnimatePresence` with height animation on open/close, plus chevron rotation animation |
| U05 | HelpTooltip.tsx | Added viewport boundary detection via `useEffect` that checks tooltip `getBoundingClientRect()` and adjusts position if off-screen |
| U06 | GLJournals.tsx | Replaced 3x hardcoded `'Current User'` with `getCurrentUser()` from new `lib/userContext.ts` |
| U07 | ModelRegistry.tsx | Replaced 3x hardcoded `'Current User'` with `getCurrentUser()` from new `lib/userContext.ts` |
| U08 | Card.tsx, CollapsibleSection.tsx | Added `dark:text-slate-200` to card title and collapsible section title |
| U09 | ModelExecution.tsx | Added amber info banner stating backtesting metrics are illustrative placeholders |
| U10 | SignOff.tsx | Added detailed comment explaining growth factor assumptions (Stage 1: 8%, Stage 2: 15%, Stage 3: 22%) |

### New Files
- `app/frontend/src/lib/userContext.ts` — Centralized user identity function (placeholder for future RBAC/OAuth integration)

## How to Test
- Start: `cd app && python app.py` (backend on port 8000)
- Frontend: `cd app/frontend && npm run build` (build output in `../static`)
- Navigate to: http://localhost:8000
- Verify:
  - Sidebar navigation pills animate independently on mobile vs desktop
  - CollapsibleSection sections animate smoothly on open/close
  - HelpTooltips near screen edges reposition instead of clipping
  - GL Journals and Model Registry show "ECL System User" instead of "Current User"
  - ModelExecution backtesting section shows amber "illustrative" banner
  - Card titles readable in dark mode

## Test Results
- `python3 -m pytest tests/ --ignore=tests/unit/test_reports_routes.py -q`: **927 passed, 61 skipped** (0 regressions)
- `npm run build`: **SUCCESS** (0 errors, 0 warnings)

## Known Limitations
- `getCurrentUser()` returns a static string until RBAC/OAuth is wired in (Sprint 7 per PRODUCT_SPEC)
- Dark mode text fix applied to shared Card and CollapsibleSection components; page-level `text-slate-700` instances without `dark:` remain in some pages but are visually acceptable due to global CSS dark mode overrides
- HelpTooltip viewport detection runs on initial render; if user scrolls after tooltip opens, position won't re-adjust (edge case)

## Files Changed
- `app/frontend/src/components/KpiCard.tsx` — Removed unused `trend` prop
- `app/frontend/src/components/DrillDownChart.tsx` — Used `title` prop as aria-label
- `app/frontend/src/components/Sidebar.tsx` — Unique layoutId per mobile/desktop context
- `app/frontend/src/components/CollapsibleSection.tsx` — Added animation, dark mode text
- `app/frontend/src/components/HelpTooltip.tsx` — Viewport boundary detection
- `app/frontend/src/components/Card.tsx` — Dark mode text on title
- `app/frontend/src/pages/GLJournals.tsx` — getCurrentUser() replacement
- `app/frontend/src/pages/ModelRegistry.tsx` — getCurrentUser() replacement
- `app/frontend/src/pages/ModelExecution.tsx` — Illustrative metrics banner
- `app/frontend/src/pages/SignOff.tsx` — Documented growth factor assumptions
- `app/frontend/src/lib/userContext.ts` — New file: centralized user identity
