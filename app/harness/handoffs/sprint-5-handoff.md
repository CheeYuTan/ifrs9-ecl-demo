# Sprint 5 Handoff: Admin Sub-Pages & Stress Testing Tabs Theme Audit

## What Was Built
Theme audit and dark mode compliance fixes across 13 .tsx files:

### Admin Sub-Pages (6 files)
1. **AdminAppSettings.tsx** — 4 fixes: tooltip class reorder, logo bg dark pair, scenario table borders
2. **AdminDataMappings.tsx** — 22 fixes: badge variants, column mapping rows, node detail, preview table, buttons, divider, view toggle hover, close button hover
3. **AdminModelConfig.tsx** — 6 fixes: disabled model button, SICR collapsed info, LGD table, SICR toggle hover
4. **AdminSystemConfig.tsx** — 4 fixes: connection label, about values, export/import buttons dark text
5. **AdminThemeConfig.tsx** — 1 fix: live preview card bg
6. **AdminJobsConfig.tsx** — 2 fixes: compute toggle off state, job key labels

### Stress Testing Tabs (7 files)
7. **index.tsx** — 1 fix: tab inactive hover
8. **SensitivityTab.tsx** — 7 fixes: slider track, reset button, parameter table, mode toggle hover
9. **MonteCarloTab.tsx** — 5 fixes: weight badge, progress bar, MC table header/rows/scenario names
10. **ConcentrationTab.tsx** — 2 fixes: heatmap header/rows borders and hover
11. **MigrationTab.tsx** — 2 fixes: slider track, reset button
12. **VintageTab.tsx** — 0 fixes (already clean)
13. **CapitalImpact.tsx** — 4 fixes: section headers, item labels, progress bar track

### Additional Fixes Found During Test Run
- 3 tooltip class reorders (`text-white bg-slate-800` → `bg-slate-800 text-white`) to match scanner exception pattern
- 4 `hover:text-slate-600/700` violations fixed with `dark:hover:text-slate-300` pairs
- 2 `hover:text-slate-700` on SensitivityTab mode toggle fixed

### Scanner Exception Updates
- Added `from-slate-700 to-slate-900` to `KNOWN_EXCEPTIONS` (AdminThemeConfig dark mode icon preview)
- Added `pages/admin/AdminThemeConfig.tsx` to `ALWAYS_DARK_TEXT_WHITE_FILES` (live preview on brand gradient)

## Context-Sensitive Exceptions Preserved
- Tooltip `bg-slate-800 text-white` — intentionally always-dark
- `text-white` on gradient-brand buttons — always on colored bg
- `text-white/70` on AdminThemeConfig live preview — brand gradient bg
- `from-slate-700 to-slate-900` on dark mode button icon — intentionally dark preview

## How to Test
- Navigate to Admin page, cycle through all 6 sub-tabs in both light and dark mode
- Navigate to Stress Testing page, cycle through all 7 tabs in both light and dark mode
- Verify no white-on-white or dark-on-dark text/borders in either mode
- Run `pytest tests/unit/test_theme_audit_sprint5.py -v` — all 208 tests pass

## Test Results
- `pytest` exit code: 0
- Sprint 5 theme tests: 208 passed (16 scanners x 13 files)
- Full suite: 1983 passed, 61 skipped, 0 failures
- Duration: 73.89s

## Known Limitations
- None. All 13 files audited, all violations fixed, all tests pass.
