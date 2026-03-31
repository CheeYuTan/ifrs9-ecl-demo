# Sprint 1 Contract: QA Bug Fixes & Code Quality Polish
STATUS: AGREED

## Scope
Fix all 10 remaining LOW severity bugs from the QA bug hunt, clean up dead code, add animation to CollapsibleSection, add viewport-aware tooltip positioning, and ensure the frontend builds cleanly. Replace hardcoded 'Current User' strings with a configurable user context.

## Acceptance Criteria
1. [ ] U01: Remove unused `trend` prop from KpiCard.tsx (clean up Props interface)
2. [ ] U02: Use `title` prop in DrillDownChart.tsx instead of voiding it (add as chart heading or aria-label)
3. [ ] U03: Fix shared `layoutId` in Sidebar between mobile/desktop (use unique IDs)
4. [ ] U04: Add smooth open/close animation to CollapsibleSection.tsx
5. [ ] U05: Add viewport boundary detection to HelpTooltip so it doesn't render off-screen
6. [ ] U06: Replace hardcoded 'Current User' in GLJournals.tsx with user context
7. [ ] U07: Replace hardcoded 'Current User' in ModelRegistry.tsx with user context
8. [ ] U08: Ensure dark mode text colors use CSS variable/Tailwind dark: classes consistently
9. [ ] U09: Add note/indicator in ModelExecution.tsx that backtesting metrics are illustrative
10. [ ] U10: Document hardcoded growth factors in SignOff.tsx with a comment explaining the estimation
11. [ ] Frontend builds successfully (`cd frontend && npm run build`)
12. [ ] All existing 927+ tests pass (0 new failures)

## How to Test
- Run `cd app/frontend && npm run build` — clean build with 0 errors
- Run `python3 -m pytest tests/ --ignore=tests/unit/test_reports_routes.py -q` — 927+ passed
- Visual inspection of fixed components in browser

## Out of Scope
- New feature development (attribution engine already built)
- Backend changes (all bugs are frontend)
- Full RBAC integration for user context (use simple hook/context placeholder)

## Domain Criteria (SME)
- No domain accuracy changes — all fixes are UI/UX quality improvements
