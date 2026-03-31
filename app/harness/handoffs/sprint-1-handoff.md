# Sprint 1 Handoff: Core Layout & Shared Components Theme Audit (Iteration 2)

## What Was Built

### Iteration 2: Dark Mode Hover Bug Fix + New Scanner

**BUG FIX: DataTable row hover flashes white in dark mode**

`DataTable.tsx` line 114 used `hover:bg-slate-50/80` without a `dark:hover:` pair. The CSS override `.dark .bg-slate-50` does NOT match Tailwind's `hover:bg-slate-50/80` because it's a different generated class. This caused non-clickable table rows to flash a nearly-white background on hover in dark mode.

**Fix**: Added `dark:hover:bg-white/[0.04]` to provide a subtle dark-mode hover.

**New test scanner (#13)**: `find_bare_hover_bg_slate_light_opacity` — catches `hover:bg-slate-50/N` or `hover:bg-slate-100/N` without `dark:hover:` pairs. CSS overrides don't match hover+opacity combinations.

**New regression test**: `test_datatable_hover_row_has_dark_pair` — ensures DataTable's row hover has a dark mode variant.

### Prior Iterations (preserved)

1. **ErrorBoundary.tsx** — "Try Again" button light mode fix
2. **ErrorDisplay.tsx** — Dark mode technical details bg fix
3. **HelpTooltip.tsx** — Arrow CSS dark: variants
4. **test_theme_audit_sprint1.py** — 285 automated regression tests (13 scanners x 19 files + CSS dependency + structural + regression)
5. **pytest.ini / conftest.py** — Test infrastructure for app/ directory
6. **test_installation_sprint7.py** — Fixed hardcoded path resolution

### Files Verified Clean (No Violations)

**Batch 1A — App Shell:** App.tsx, Sidebar.tsx, main.tsx
**Batch 1B — Data Display:** DataTable.tsx, Card.tsx, KpiCard.tsx, CollapsibleSection.tsx, ThreeLevelDrillDown.tsx, DrillDownChart.tsx, ScenarioProductBarChart.tsx, ChartTooltip.tsx
**Batch 1C — Feedback Components:** Toast.tsx, ErrorBoundary.tsx, ErrorDisplay.tsx, ConfirmDialog.tsx, StatusBadge.tsx, LockedBanner.tsx, HelpTooltip.tsx, HelpPanel.tsx

## Scanner Inventory (13 scanners, 285 tests)

| # | Scanner | Pattern | Files |
|---|---------|---------|-------|
| 1 | `find_bare_bg_slate_600_plus` | `bg-slate-[6-9]00` without `dark:` | 19 |
| 2 | `find_bare_bg_white_opacity` | `bg-white/N` without light pair | 19 |
| 3 | `find_bare_border_white` | `border-white/N` without light pair | 19 |
| 4 | `find_bare_text_white_opacity` | `text-white/N` without light pair | 19 |
| 5 | `find_bare_hover_bg_white` | `hover:bg-white/N` without `dark:hover:` | 19 |
| 6 | `find_bare_hover_bg_slate_dark` | `hover:bg-slate-[6-9]00` without `dark:hover:` | 19 |
| 7 | `find_bare_from_slate` | `from-slate-[78]00` without `dark:` | 19 |
| 8 | `find_bare_bg_hex` | `bg-[#0B0F1A]` without `dark:` | 19 |
| 9 | `find_bare_border_dir_slate_dark` | `border-[tblr]-slate-800` without `dark:` | 19 |
| 10 | `find_bare_to_slate_dark` | `to-slate-[6-9]00` without `dark:` | 19 |
| 11 | `find_bare_via_slate_dark` | `via-slate-[6-9]00` without `dark:` | 19 |
| 12 | `find_bare_focus_bg_slate_dark` | `focus:bg-slate-[6-9]00` without `dark:focus:` | 19 |
| 13 | `find_bare_hover_bg_slate_light_opacity` | `hover:bg-slate-50\|100/N` without `dark:hover:` | 19 |

## How to Test

### From project root (preferred)
```bash
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest tests/unit/test_theme_audit_sprint1.py -v
```

### From app/ directory (also works)
```bash
cd "/Users/steven.tan/Expected Credit Losses/app"
python -m pytest -k "test_theme_audit_sprint1" -v
```

### Visual Verification
- Navigate to any page with a DataTable in **dark mode** — hover non-clickable rows → should show subtle `white/[0.04]` hover, NOT a white flash
- Toggle to **light mode** — hover should show `slate-50/80` (very subtle gray)
- All other pages in both light and dark mode — no regressions

## Test Results

- **Theme audit (pytest)**: 285 passed, 0 failed (0.27s)
- **Full backend (pytest from app/)**: 1323 passed, 61 skipped, 0 failed (74s)
- **Frontend (Vitest)**: 103 passed, 0 failed (1.97s)

## Known Limitations

- Toast info variant (`bg-slate-800`) and HelpTooltip bubble (`bg-slate-800`) are intentionally always-dark per spec
- App.tsx hero stepper uses `bg-white/[0.06]`, `border-white/[0.08]` etc. on always-dark gradient — intentional
- KpiCard `border-[color]-100/50` and `bg-[color]-500/10` are not caught by CSS overrides, but at low opacity they render acceptably in both modes (10% tint on any background is subtle)
- The CSS override approach in `index.css` handles many "violations" automatically without per-file `dark:` prefixes

## Files Changed (Iteration 2)

- `app/frontend/src/components/DataTable.tsx` — Added `dark:hover:bg-white/[0.04]` for row hover
- `tests/unit/test_theme_audit_sprint1.py` — Added scanner #13 (`find_bare_hover_bg_slate_light_opacity`) + regression test `test_datatable_hover_row_has_dark_pair` (285 total tests, up from 265)
