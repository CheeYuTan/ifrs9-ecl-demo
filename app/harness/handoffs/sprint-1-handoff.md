# Sprint 1 Handoff: Core Layout & Shared Components Theme Audit (Iteration 3)

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

5. **tests/unit/test_theme_audit_sprint1.py** — 155 automated regression tests (7 scanners × 19 files + 3 specific + 19 existence)

### Iteration 3: Enhanced Scanner Coverage + New Scanners

6. **tests/unit/test_theme_audit_sprint1.py** — Enhanced from 155 → **193 tests**:
   - **Bracket notation support**: All 7 violation scanners now catch both numeric (`bg-white/10`) and bracket (`bg-white/[0.06]`) opacity notations
   - **Compound prefix detection**: New `_match_is_in_dark_prefix()` helper correctly identifies `dark:hover:bg-white/[0.04]` as NOT a violation (the `dark:` is in the compound prefix chain)
   - **New scanner: `hover:bg-slate-[6-9]00`** — Catches bare hover dark-slate backgrounds without `dark:hover:` pair (19 parameterized tests)
   - **New scanner: `border-[tblr]-slate-800`** — Catches directional border dark-slate without `dark:` pair (19 parameterized tests)
   - **Always-dark file exceptions**: `ALWAYS_DARK_WHITE_OPACITY_FILES` set for App.tsx (hero stepper) and HelpTooltip.tsx (tooltip bubble) — skips `bg-white/`, `border-white/`, `hover:bg-white/` scans for files entirely on dark backgrounds
   - Deep re-audit confirmed all 19 Sprint 1 files remain violation-free

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

- **Theme audit (pytest)**: 193 passed, 0 failed (0.22s)
- **Backend (pytest)**: 1231 passed, 61 skipped, 0 failed (72.62s)
- **Frontend (Vitest)**: 103 passed, 0 failed (2.10s)

## Known Limitations

- Toast info variant (`bg-slate-800`) and HelpTooltip bubble (`bg-slate-800`) are intentionally always-dark per spec
- App.tsx hero stepper uses `bg-white/[0.06]`, `border-white/[0.08]` etc. on always-dark gradient — intentional, not violations
- The CSS override approach in `index.css` handles many "violations" automatically without per-file `dark:` prefixes
- Tests must run from the project root (`/Users/steven.tan/Expected Credit Losses`), not from `app/`

## Files Changed

### Iteration 1
- `app/frontend/src/components/ErrorBoundary.tsx` — Light mode button colors
- `app/frontend/src/components/ErrorDisplay.tsx` — Dark mode technical details bg
- `app/frontend/src/components/HelpTooltip.tsx` — Arrow dark: variants
- `tests/unit/test_attribution_audit_routes_sprint4c.py` — Pre-existing test bug fix

### Iteration 2
- `tests/unit/test_theme_audit_sprint1.py` — 155 theme audit regression tests

### Iteration 3
- `tests/unit/test_theme_audit_sprint1.py` — Enhanced to 193 tests: bracket notation, compound dark: prefixes, 2 new scanners, always-dark file exceptions
