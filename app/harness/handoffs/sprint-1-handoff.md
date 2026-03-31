# Sprint 1 Handoff: Core Layout & Shared Components Theme Audit (Iteration 2)

## What Was Built

### Iteration 2: Test Infrastructure Fix

**Root cause**: The evaluator ran `python -m pytest tests/unit/test_theme_audit_sprint1.py` from the `app/` directory, but `tests/` lives at the project root (`../tests/` relative to `app/`). This resulted in "collected 0 items" — the test file wasn't found.

**Fix**: Created a symlink `app/tests -> ../tests` so that test paths work correctly from the `app/` working directory. Now both of these work:

```bash
# From project root (original — always worked)
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest tests/unit/test_theme_audit_sprint1.py -v

# From app/ directory (NEW — now works via symlink)
cd "/Users/steven.tan/Expected Credit Losses/app"
python -m pytest tests/unit/test_theme_audit_sprint1.py -v
```

All 329 theme audit tests pass from both locations.

### Prior Iterations (preserved from iteration 1)

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
| 13 | `find_bare_hover_bg_slate_light_opacity` | `hover:bg-slate-50\|100/N` without `dark:hover:` | 19 |
| 14 | `find_css_scrollbar_theme_issues` | CSS scrollbar `rgba(255,255,255)` without `.dark` scope | 1 |
| 15 | `find_bare_hover_bg_slate_light_plain` | `hover:bg-slate-100/200` (plain) without `dark:hover:` | 19 |
| 16 | `find_bare_hover_text_slate_dark` | `hover:text-slate-[6-8]00` without `dark:hover:` | 19 |

## How to Test

### Running theme audit tests

**From app/ directory** (evaluator's working directory):
```bash
cd "/Users/steven.tan/Expected Credit Losses/app"
python -m pytest tests/unit/test_theme_audit_sprint1.py -v
```

**From project root** (alternative):
```bash
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest tests/unit/test_theme_audit_sprint1.py -v
```

### Running all backend tests
```bash
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest tests/ -q
```

### Running frontend tests
```bash
cd "/Users/steven.tan/Expected Credit Losses/app/frontend"
npx vitest run
```

### Visual Verification
- Start dev server: `cd "/Users/steven.tan/Expected Credit Losses/app/frontend" && npm run dev`
- Navigate to `http://localhost:5173` (or whatever port Vite assigns)
- Toggle light/dark mode on any page
- In light mode: verify no invisible text, no white-on-white backgrounds
- In dark mode: verify no regressions, hover states work properly
- DataTable hover in dark mode: subtle `white/[0.04]` hover, NOT white flash
- Sidebar scrollbar in light mode: visible dark gray thumb

## Test Results

- **Theme audit (pytest)**: 329 passed, 0 failed (0.30s)
- **Full backend (pytest)**: 1367 passed, 61 skipped, 0 failed (74.52s)
- **Frontend (Vitest)**: 103 passed, 0 failed (2.30s)

## Known Limitations

- Toast info variant (`bg-slate-800`) and HelpTooltip bubble (`bg-slate-800`) are intentionally always-dark per spec
- App.tsx hero stepper uses `bg-white/[0.06]`, `border-white/[0.08]` etc. on always-dark gradient — intentional
- CSS override approach in `index.css` handles many "violations" automatically without per-file `dark:` prefixes
- Global scrollbar uses CSS variables `--scrollbar-thumb` / `--scrollbar-hover` — already theme-aware
- CSS hover safety nets are defensive — Sprint 1 files already have explicit `dark:hover:` pairs, but the CSS ensures later sprints are also covered
- 3 pre-existing test collection errors (`test_api.py`, `test_ecl_engine.py`, `test_models.py`) when running via symlink from `app/` due to conftest.py resolution — these are NOT Sprint 1 issues and pass normally from the project root

## Files Changed (Iteration 2)

- `app/tests` — NEW symlink → `../tests` (enables test discovery from `app/` working directory)
