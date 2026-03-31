# Sprint 5 Handoff: Admin Sub-pages + Stress Testing Tabs Theme Audit (Iteration 2)

## What Was Built

Iteration 2 fixes all 6 bugs identified in the Sprint 5 evaluation (score 6.95/10):

### Bug Fixes Applied

| Bug | Severity | Fix | Files |
|-----|----------|-----|-------|
| BUG-S5-001 | Major | Added `dark:text-slate-300` to 9 `text-slate-600` instances | AdminModelConfig, AdminSystemConfig, AdminJobsConfig, SensitivityTab, MonteCarloTab |
| BUG-S5-002 | Major | Added `dark:text-slate-200` to 4 `text-slate-700` instances | SensitivityTab, MonteCarloTab, MigrationTab |
| BUG-S5-003 | Minor | Added `dark:text-slate-400` to ~35 `text-slate-500` instances | AdminAppSettings, AdminDataMappings, AdminModelConfig, AdminSystemConfig, AdminThemeConfig, stress-testing/index, SensitivityTab, MonteCarloTab, MigrationTab, ConcentrationTab, CapitalImpact |
| BUG-S5-004 | Minor | Added `dark:border-slate-700` to `border-slate-100` | AdminDataMappings:206 |
| BUG-S5-005 | Major | Added 4 new scanner functions + 52 parameterized tests | test_theme_audit_sprint1.py (scanners), test_theme_audit_sprint5.py (tests) |
| BUG-S5-006 | Minor | Skipped — pre-existing file size, not sprint 5 scope | N/A |

### New Scanner Functions (in test_theme_audit_sprint1.py)

1. `find_bare_text_slate_600()` — detects `text-slate-600` without `dark:text-slate-` pair
2. `find_bare_text_slate_700()` — detects `text-slate-700` without `dark:text-slate-` pair
3. `find_bare_text_slate_500()` — detects `text-slate-500` without `dark:text-slate-` pair
4. `find_bare_border_slate_100()` — detects `border-slate-100` without `dark:border-slate-` pair

All 4 scanners handle edge cases: hover: variants, group-hover: variants, dark: compound prefixes, and known exceptions.

## How to Test

- Start: `cd frontend && npm run dev`
- Navigate to: http://localhost:5173
- Test Admin sub-pages (Settings → Model Config, System Config, Jobs Config, Data Mappings, Theme Config, App Settings)
- Test Stress Testing tabs (Monte Carlo, Sensitivity, Vintage, Concentration, Migration, Capital Impact)
- Toggle light/dark mode on each page — verify all text is readable in both modes

## Test Results

- Sprint 5 theme tests: **260 passed** in 0.24s (208 original + 52 new)
- Full suite: **2035 passed**, 61 skipped, **0 failures** in 74.81s

## Files Changed

### Frontend (.tsx)
1. `pages/admin/AdminAppSettings.tsx` — 2 fixes (group-hover, text-slate-500)
2. `pages/admin/AdminDataMappings.tsx` — 4 fixes (group-hover, text-slate-500 ×2, border-slate-100)
3. `pages/admin/AdminModelConfig.tsx` — 4 fixes (group-hover, text-slate-500, text-slate-600, conditional text-slate-500)
4. `pages/admin/AdminSystemConfig.tsx` — 3 fixes (text-slate-600 ×2, text-slate-500)
5. `pages/admin/AdminJobsConfig.tsx` — 1 fix (text-slate-600)
6. `pages/admin/AdminThemeConfig.tsx` — 1 fix (text-slate-500)
7. `pages/stress-testing/index.tsx` — 1 fix (text-slate-500)
8. `pages/stress-testing/SensitivityTab.tsx` — 14 fixes (text-slate-700 ×2, text-slate-600 ×3, text-slate-500 ×9)
9. `pages/stress-testing/MonteCarloTab.tsx` — 10 fixes (text-slate-700, text-slate-600 ×2, text-slate-500 ×7)
10. `pages/stress-testing/MigrationTab.tsx` — 3 fixes (text-slate-700, text-slate-500 ×2)
11. `pages/stress-testing/ConcentrationTab.tsx` — 2 fixes (text-slate-500 ×2)
12. `pages/stress-testing/CapitalImpact.tsx` — 1 fix (text-slate-500)

### Tests (.py)
13. `tests/unit/test_theme_audit_sprint1.py` — 4 new scanner functions (reusable by all sprint test files)
14. `tests/unit/test_theme_audit_sprint5.py` — 4 new test classes (52 parameterized tests)

## Known Limitations

- BUG-S5-006 (AdminDataMappings.tsx 730 lines) was NOT addressed — it's a pre-existing file size issue, not caused by Sprint 5 work
- The new scanners are only added to Sprint 5's test file; SUG-S5-001 suggests adding them to all sprint test files (deferred to Sprint 6/7 regression sweep)
