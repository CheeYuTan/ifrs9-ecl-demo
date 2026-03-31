# Sprint 1 Contract: Core Layout & Shared Components Theme Audit

## Scope
Audit and fix the 19 Sprint 1 files (App Shell + Data Display + Feedback Components) for dark-mode-only Tailwind CSS violations.

## Key Finding
The `index.css` already contains comprehensive `.dark` overrides covering most common Tailwind classes (`bg-white`, `bg-slate-50/100/200`, `text-slate-300-800`, `border-slate-50/100/200`, colored `-50/-100/-200` variants, gradient overrides). This means many classes used WITHOUT explicit `dark:` prefixes are NOT violations — they're handled by CSS.

## Acceptance Criteria

- [ ] Zero `bg-slate-[6-9]00` without `dark:` prefix or intentional always-dark context (Toast/Tooltip exceptions allowed)
- [ ] Zero `hover:bg-slate-[6-9]00` without `dark:` prefix or light-mode pair
- [ ] Zero `bg-[color]-100/50` opacity variants without `dark:` pair (CSS overrides don't match opacity-modified variants)
- [ ] Zero `border-[direction]-slate-800` without `dark:` pair, unless inside intentional always-dark context
- [ ] All files pass `npm test`
- [ ] All existing `pytest` tests still pass

## Known Exceptions (NOT violations)
- `text-white` inside gradient-brand buttons/badges (white on colored bg)
- `text-white/*` inside hero sections (always-dark gradient)
- Toast info variant (`bg-slate-800` always-dark) — spec says "leave as-is"
- Tooltip bubble (`bg-slate-800`) — standard always-dark UI pattern
- Classes covered by `.dark` CSS overrides in index.css

## Files
**Batch 1A**: App.tsx, Sidebar.tsx, main.tsx
**Batch 1B**: DataTable.tsx, Card.tsx, KpiCard.tsx, CollapsibleSection.tsx, ThreeLevelDrillDown.tsx, DrillDownChart.tsx, ScenarioProductBarChart.tsx, ChartTooltip.tsx
**Batch 1C**: Toast.tsx, ErrorBoundary.tsx, ErrorDisplay.tsx, ConfirmDialog.tsx, StatusBadge.tsx, LockedBanner.tsx, HelpTooltip.tsx, HelpPanel.tsx

## Test Plan
1. Grep all Sprint 1 files for remaining violations
2. Fix each violation with proper light/dark pair
3. Run `npm test` — all must pass
4. Run `pytest` — all must pass
