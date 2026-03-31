# Sprint 1 Handoff: Core Layout & Shared Components Theme Audit (Iteration 2)

## What Was Built

### Iteration 1 Fixes (preserved)

1. **ErrorBoundary.tsx:33** — "Try Again" button had `bg-slate-600 hover:bg-slate-700` (always-dark, no light pair)
   - Fixed: `bg-slate-200 text-slate-800 dark:bg-slate-600 dark:text-white hover:bg-slate-300 dark:hover:bg-slate-700`

2. **ErrorDisplay.tsx:74** — Technical details section used `bg-red-100/50` (opacity-modified variant not caught by CSS `.dark .bg-red-100` override)
   - Fixed: Added `dark:bg-red-900/20`

3. **HelpTooltip.tsx:56-59** — Arrow CSS triangles used `border-[dir]-slate-800` without dark variant to match `dark:bg-slate-700` tooltip body
   - Fixed: Added `dark:border-[dir]-slate-700` to all 4 arrow directions

4. **test_attribution_audit_routes_sprint4c.py:29-35** — Pre-existing test bug fixed

### Iteration 2: Theme Audit Regression Tests

5. **tests/unit/test_theme_audit_sprint1.py** — NEW — 155 automated regression tests covering all 19 Sprint 1 files:
   - **7 violation scanner tests × 19 files = 133 parameterized tests**: Scans each file for bare `bg-slate-[6-9]00`, `bg-white/N`, `border-white/N`, `text-white/N`, `hover:bg-white/N`, `from-slate-[78]00`, `bg-[#0B0F1A]` without proper light/dark pairs
   - **3 specific regression tests**: ErrorBoundary button, ErrorDisplay tech details, HelpTooltip arrows
   - **19 file-existence tests**: Ensures all Sprint 1 files exist
   - Context-aware exception handling:
     - Toast info variant (`bg-slate-800`) — intentionally always-dark
     - HelpTooltip bubble — intentionally always-dark
     - App.tsx hero stepper — renders on always-dark gradient bg
     - Lines with `dark:` pairs (including compound prefixes like `dark:hover:bg-slate-700`)
     - Lines where `bg-white/N` has a corresponding `dark:bg-` pair

### Files Verified Clean (No Violations)

**Batch 1A — App Shell:** App.tsx, Sidebar.tsx, main.tsx
**Batch 1B — Data Display:** DataTable.tsx, Card.tsx, KpiCard.tsx, CollapsibleSection.tsx, ThreeLevelDrillDown.tsx, DrillDownChart.tsx, ScenarioProductBarChart.tsx, ChartTooltip.tsx
**Batch 1C — Feedback Components:** Toast.tsx, ErrorBoundary.tsx, ErrorDisplay.tsx, ConfirmDialog.tsx, StatusBadge.tsx, LockedBanner.tsx, HelpTooltip.tsx, HelpPanel.tsx

## How to Test

### Automated
```bash
# From project root:
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest tests/unit/test_theme_audit_sprint1.py -v
```

### Visual Verification
- Navigate to any page in **light mode** — verify no dark backgrounds or invisible text
- Toggle to **dark mode** — verify no regressions
- Trigger error boundary: add `throw new Error('test')` to any component — verify "Try Again" button is readable in both modes
- Hover over any `?` help icon — verify tooltip renders correctly in both modes

## Test Results

- **Theme audit (pytest)**: 155 passed, 0 failed (0.20s)
- **Backend (pytest)**: 1193 passed, 61 skipped, 0 failed (75.54s)
- **Frontend (Vitest)**: 103 passed, 0 failed (2.02s)
- **TypeScript**: Clean (no errors)

## Known Limitations

- Toast info variant (`bg-slate-800`) and HelpTooltip bubble (`bg-slate-800`) are intentionally always-dark per spec
- The CSS override approach in `index.css` handles many "violations" automatically without per-file `dark:` prefixes
- Tests must run from the project root (`/Users/steven.tan/Expected Credit Losses`), not from `app/`

## Files Changed

### Iteration 1
- `app/frontend/src/components/ErrorBoundary.tsx` — Light mode button colors
- `app/frontend/src/components/ErrorDisplay.tsx` — Dark mode technical details bg
- `app/frontend/src/components/HelpTooltip.tsx` — Arrow dark: variants
- `tests/unit/test_attribution_audit_routes_sprint4c.py` — Pre-existing test bug fix

### Iteration 2
- `tests/unit/test_theme_audit_sprint1.py` — NEW: 155 theme audit regression tests
