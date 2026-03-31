# Sprint 1 Handoff: Core Layout & Shared Components Theme Audit (Iteration 3)

## What Was Built

### Iteration 3: Fix test collection errors from app/ directory

**Root cause**: Three test files (`test_api.py`, `test_ecl_engine.py`, `test_models.py`) use `from conftest import PRODUCT_TYPES` / `MODEL_KEYS` / `SCENARIOS`. When pytest runs from `app/`, it finds `app/conftest.py` first (which didn't export these symbols) instead of the root `tests/conftest.py`.

**Fix**: Updated `app/conftest.py` to dynamically load the root `tests/conftest.py` and re-export `PRODUCT_TYPES`, `MODEL_KEYS`, and `SCENARIOS`. This resolves all 3 collection errors.

**Result**: All 1367 backend tests now pass from `app/` directory with zero collection errors.

### Prior Iterations

**Iteration 2**: Created `app/tests` symlink → `../tests` so test paths work from `app/` directory.

**Iteration 1 (5 sub-iterations)**:
- Fixed all dark-mode-only Tailwind CSS violations across 19 Sprint 1 files
- 16 automated scanners covering all violation patterns
- CSS safety nets in `index.css` for hover states, scrollbar themes
- 329 tests total (265 base + 42 scanner #15-#16 + 4 CSS dependency + 18 file existence)

**Files Verified Clean (No Violations)**:
- **Batch 1A — App Shell:** App.tsx, Sidebar.tsx, main.tsx
- **Batch 1B — Data Display:** DataTable.tsx, Card.tsx, KpiCard.tsx, CollapsibleSection.tsx, ThreeLevelDrillDown.tsx, DrillDownChart.tsx, ScenarioProductBarChart.tsx, ChartTooltip.tsx
- **Batch 1C — Feedback Components:** Toast.tsx, ErrorBoundary.tsx, ErrorDisplay.tsx, ConfirmDialog.tsx, StatusBadge.tsx, LockedBanner.tsx, HelpTooltip.tsx, HelpPanel.tsx

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

### Running all tests from app/ directory (evaluator's working directory)
```bash
cd "/Users/steven.tan/Expected Credit Losses/app"

# Theme audit tests only
python -m pytest tests/unit/test_theme_audit_sprint1.py -v

# ALL backend tests (including previously-failing test_api, test_ecl_engine, test_models)
python -m pytest tests/ -q

# Frontend tests
cd frontend && npx vitest run
```

### Running from project root (alternative)
```bash
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest tests/ -q
```

### Visual Verification
- Start dev server: `cd "/Users/steven.tan/Expected Credit Losses/app/frontend" && npm run dev`
- Navigate to `http://localhost:5173`
- Toggle light/dark mode on any page
- In light mode: verify no invisible text, no white-on-white backgrounds
- In dark mode: verify no regressions, hover states work properly

## Test Results

- **Theme audit (pytest)**: 329 passed, 0 failed (0.30s)
- **Full backend (pytest from app/)**: 1367 passed, 61 skipped, 0 errors, 0 failed (73.32s)
- **Frontend (Vitest)**: 103 passed, 0 failed (2.07s)

## Known Limitations

- Toast info variant (`bg-slate-800`) and HelpTooltip bubble (`bg-slate-800`) are intentionally always-dark per spec
- App.tsx hero stepper uses `bg-white/[0.06]`, `border-white/[0.08]` etc. on always-dark gradient — intentional
- CSS override approach in `index.css` handles many "violations" automatically without per-file `dark:` prefixes
- Global scrollbar uses CSS variables `--scrollbar-thumb` / `--scrollbar-hover` — already theme-aware

## Files Changed (Iteration 3)

- `app/conftest.py` — Updated to re-export `PRODUCT_TYPES`, `MODEL_KEYS`, `SCENARIOS` from root `tests/conftest.py`, fixing 3 test collection errors when running from `app/` directory
