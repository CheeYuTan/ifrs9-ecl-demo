# Sprint 1 Handoff: Core Layout & Shared Components Theme Audit (Iteration 5 — Final)

## What Was Built

Systematic theme audit and remediation of 19 core layout and shared component files. Every file now has proper light+dark mode Tailwind CSS classes, with zero bare dark-only violations.

### Summary Across All Iterations

| Iteration | Focus | Key Change |
|-----------|-------|------------|
| 1 | Theme fixes | Fixed all dark-mode-only violations in 19 files, created 16 scanners (329 tests), added CSS safety nets |
| 2 | Test infra | Created `app/tests` symlink for test discovery from `app/` directory |
| 3 | Test fixes | Fixed 3 test collection errors (`test_api.py`, `test_ecl_engine.py`, `test_models.py`), updated `app/conftest.py` |
| 4 | Test config | Added `app/pyproject.toml` for robust `pytest` discovery from any invocation method |
| 5 | Verification | Final verification — all tests pass, zero violations confirmed |

## Files Audited — All Clean (19 files, zero violations)

- **Batch 1A — App Shell:** App.tsx, Sidebar.tsx, main.tsx
- **Batch 1B — Data Display:** DataTable.tsx, Card.tsx, KpiCard.tsx, CollapsibleSection.tsx, ThreeLevelDrillDown.tsx, DrillDownChart.tsx, ScenarioProductBarChart.tsx, ChartTooltip.tsx
- **Batch 1C — Feedback:** Toast.tsx, ErrorBoundary.tsx, ErrorDisplay.tsx, ConfirmDialog.tsx, StatusBadge.tsx, LockedBanner.tsx, HelpTooltip.tsx, HelpPanel.tsx

## Scanner Inventory (16 scanners, 329 tests)

| # | Scanner | Pattern | Tests |
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
| 13 | `find_bare_hover_bg_slate_light_opacity` | `hover:bg-slate-50|100/N` without `dark:hover:` | 19 |
| 14 | `find_css_scrollbar_theme_issues` | CSS scrollbar `rgba(255,255,255)` without `.dark` scope | 1 |
| 15 | `find_bare_hover_bg_slate_light_plain` | `hover:bg-slate-100/200` (plain) without `dark:hover:` | 19 |
| 16 | `find_bare_hover_text_slate_dark` | `hover:text-slate-[6-8]00` without `dark:hover:` | 19 |

## How to Test

### Running tests
```bash
cd "/Users/steven.tan/Expected Credit Losses/app"

# Theme audit tests only (329 tests, <1s)
pytest tests/unit/test_theme_audit_sprint1.py -v

# ALL backend tests (1428 collected, 1367 passed, 61 skipped, ~75s)
pytest tests/ -q

# Frontend tests (103 tests, ~2s)
cd frontend && npx vitest run
```

### Test discovery verification
```bash
# From app/ directory
cd "/Users/steven.tan/Expected Credit Losses/app"
pytest --co -q            # 1428 tests collected
python -m pytest --co -q  # 1428 tests collected

# From project root
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest --co -q  # 1428 tests collected
```

### Visual Verification
- Start dev server: `cd "/Users/steven.tan/Expected Credit Losses/app/frontend" && npm run dev`
- Navigate to `http://localhost:5173`
- Toggle light/dark mode on any page
- In light mode: verify no invisible text, no white-on-white backgrounds
- In dark mode: verify no regressions, hover states work properly

## Test Results (Iteration 5 — Final)

- **Theme audit (pytest)**: 329 passed, 0 failed (0.28s)
- **Full backend (pytest from app/)**: 1367 passed, 61 skipped, 0 failed (73.47s)
- **Frontend (Vitest)**: 103 passed, 0 failed (2.06s)
- **Test collection**: 1428 tests discovered from both `app/` and project root

## Known Exceptions (Intentional — Not Violations)

- **App.tsx hero stepper**: Uses `bg-white/[0.06]`, `border-white/[0.08]`, `text-white/N` on always-dark gradient background — intentional, not a light-mode issue
- **Toast info variant**: `bg-slate-800` intentionally always-dark notification
- **HelpTooltip bubble**: `bg-slate-800 dark:bg-slate-700` intentionally dark in both modes (tooltip on colored background)
- **CollapsibleSection**: `dark:hover:bg-slate-800` already has proper `dark:` prefix
- **CSS overrides**: `index.css` handles scrollbar theming via CSS variables, already theme-aware

## Files Changed (All Iterations Combined)

### Iteration 1 (Theme Fixes)
- `frontend/src/App.tsx` — Fixed 19 violations (text-white/, border-white/, bg patterns)
- `frontend/src/components/Sidebar.tsx` — Fixed 27 violations
- `frontend/src/main.tsx` — Verified clean
- `frontend/src/components/DataTable.tsx` — Fixed gradient header + hover states
- `frontend/src/components/Card.tsx` — Verified clean
- `frontend/src/components/KpiCard.tsx` — Verified clean
- `frontend/src/components/CollapsibleSection.tsx` — Fixed bare bg-slate
- `frontend/src/components/ThreeLevelDrillDown.tsx` — Fixed bg-slate
- `frontend/src/components/DrillDownChart.tsx` — Fixed bg-slate
- `frontend/src/components/ScenarioProductBarChart.tsx` — Fixed bg-slate
- `frontend/src/components/ChartTooltip.tsx` — Verified clean
- `frontend/src/components/Toast.tsx` — Documented intentional exception
- `frontend/src/components/ErrorBoundary.tsx` — Verified clean
- `frontend/src/components/ErrorDisplay.tsx` — Fixed bg-white/ + bg-slate
- `frontend/src/components/ConfirmDialog.tsx` — Fixed bg-slate patterns
- `frontend/src/components/StatusBadge.tsx` — Verified clean
- `frontend/src/components/LockedBanner.tsx` — Fixed bg-slate + gradient
- `frontend/src/components/HelpTooltip.tsx` — Documented intentional exception
- `frontend/src/components/HelpPanel.tsx` — Fixed bg-slate
- `frontend/src/index.css` — Added CSS safety nets for hover states + scrollbar theming
- `tests/unit/test_theme_audit_sprint1.py` — NEW: 329 tests across 16 scanners

### Iteration 2-4 (Test Infrastructure)
- `app/tests` — Symlink to `../tests`
- `app/conftest.py` — Re-exports for test collection
- `app/pyproject.toml` — NEW: pytest config for robust test discovery
