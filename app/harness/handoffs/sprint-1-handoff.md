# Sprint 1 Handoff: Core Layout & Shared Components Theme Audit (Iteration 5)

## What Was Built

### Iterations 1-4 (preserved)

1. **ErrorBoundary.tsx:33** — "Try Again" button light mode fix
2. **ErrorDisplay.tsx:74** — Dark mode technical details bg fix
3. **HelpTooltip.tsx:56-59** — Arrow CSS dark: variants
4. **test_attribution_audit_routes_sprint4c.py:29-35** — Pre-existing test bug fix
5. **tests/unit/test_theme_audit_sprint1.py** — 265 automated regression tests (12 scanners x 19 files + CSS dependency + structural consistency)

### Iteration 5: Test Infrastructure Fix

**Root cause of "0 tests collected" failure**: The evaluator ran `pytest` from the `app/` subdirectory, but the test file lives at `tests/unit/test_theme_audit_sprint1.py` relative to the project root (`/Users/steven.tan/Expected Credit Losses/`). The `app/` directory had no pytest configuration, so pytest couldn't discover tests.

**Fixes applied:**

6. **app/pytest.ini** (NEW) — Added pytest configuration for the `app/` subdirectory that points `testpaths` to `../tests`, enabling test discovery when pytest is run from `app/`.

7. **app/conftest.py** (NEW) — Adds the project root to `sys.path` so test imports resolve correctly when running from `app/`.

8. **tests/unit/test_installation_sprint7.py** — Fixed 2 pre-existing test failures (`test_scipy_in_requirements`, `test_fpdf2_in_requirements`) that hardcoded `app/requirements.txt` as a relative path (only worked from project root). Changed to use `os.path.dirname(__file__)` for directory-agnostic resolution.

### Files Verified Clean (No Violations)

**Batch 1A — App Shell:** App.tsx, Sidebar.tsx, main.tsx
**Batch 1B — Data Display:** DataTable.tsx, Card.tsx, KpiCard.tsx, CollapsibleSection.tsx, ThreeLevelDrillDown.tsx, DrillDownChart.tsx, ScenarioProductBarChart.tsx, ChartTooltip.tsx
**Batch 1C — Feedback Components:** Toast.tsx, ErrorBoundary.tsx, ErrorDisplay.tsx, ConfirmDialog.tsx, StatusBadge.tsx, LockedBanner.tsx, HelpTooltip.tsx, HelpPanel.tsx

## Scanner Inventory (12 scanners, 265 tests)

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

## How to Test

### From project root (preferred)
```bash
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest tests/unit/test_theme_audit_sprint1.py -v
```

### From app/ directory (also works now)
```bash
cd "/Users/steven.tan/Expected Credit Losses/app"
python -m pytest -k "test_theme_audit_sprint1" -v
# OR run all tests:
python -m pytest -q
```

### Visual Verification
- Navigate to any page in **light mode** — verify no dark backgrounds or invisible text
- Toggle to **dark mode** — verify no regressions
- Trigger error boundary — verify "Try Again" button readable in both modes
- Hover over any `?` help icon — verify tooltip renders correctly in both modes

## Test Results

- **Theme audit (pytest)**: 265 passed, 0 failed (0.25s)
- **Full backend (pytest from app/)**: 1303 passed, 61 skipped, 0 failed (75.17s)
- **Full backend (pytest from root/)**: 1303 passed, 61 skipped, 0 failed (74.24s)
- **Frontend (Vitest)**: 103 passed, 0 failed (3.22s)

## Known Limitations

- Toast info variant (`bg-slate-800`) and HelpTooltip bubble (`bg-slate-800`) are intentionally always-dark per spec
- App.tsx hero stepper uses `bg-white/[0.06]`, `border-white/[0.08]` etc. on always-dark gradient — intentional
- The CSS override approach in `index.css` handles many "violations" automatically without per-file `dark:` prefixes

## Files Changed

### Iteration 5
- `app/pytest.ini` — NEW: pytest config for app/ subdirectory (testpaths, asyncio_mode, markers)
- `app/conftest.py` — NEW: sys.path setup for test imports from app/
- `tests/unit/test_installation_sprint7.py` — Fixed hardcoded `app/requirements.txt` path to use `__file__`-relative resolution

### Iterations 1-4
- `app/frontend/src/components/ErrorBoundary.tsx` — Light mode button colors
- `app/frontend/src/components/ErrorDisplay.tsx` — Dark mode technical details bg
- `app/frontend/src/components/HelpTooltip.tsx` — Arrow dark: variants
- `tests/unit/test_attribution_audit_routes_sprint4c.py` — Pre-existing test bug fix
- `tests/unit/test_theme_audit_sprint1.py` — 265 theme audit regression tests
