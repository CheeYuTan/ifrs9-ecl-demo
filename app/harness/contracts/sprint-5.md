# Sprint 5 Contract: Admin Sub-pages + Stress Testing Tabs Theme Audit

## Acceptance Criteria
- [ ] All 13 files audited and fixed for light/dark theme compliance
- [ ] Zero `bg-slate-800/900` used as content bg without `dark:` prefix (tooltips excepted)
- [ ] All `bg-slate-50/100` backgrounds have `dark:bg-slate-800` counterparts
- [ ] All `text-slate-600/700` in body text has `dark:text-slate-300/200` counterparts
- [ ] All `border-slate-100/200` has `dark:border-slate-700` counterparts
- [ ] All `hover:bg-slate-50/200` has dark hover counterparts
- [ ] Intentional exceptions documented (tooltips, colored button text)
- [ ] Regression tests written for all fixed violations
- [ ] All tests pass

## Files (13 total)

### Admin sub-pages (6 files)
1. `admin/AdminAppSettings.tsx` — logo bg-white needs dark pair
2. `admin/AdminDataMappings.tsx` — badge, table, divider dark pairs
3. `admin/AdminModelConfig.tsx` — card backgrounds, table rows
4. `admin/AdminSystemConfig.tsx` — minimal (mostly already themed)
5. `admin/AdminThemeConfig.tsx` — preview card bg-slate-50
6. `admin/AdminJobsConfig.tsx` — compute toggle dark pair

### Stress testing tabs (7 files)
7. `stress-testing/index.tsx` — tab hover state
8. `stress-testing/SensitivityTab.tsx` — slider, buttons, table rows
9. `stress-testing/MonteCarloTab.tsx` — weight badge, progress bar, table rows
10. `stress-testing/ConcentrationTab.tsx` — table rows
11. `stress-testing/MigrationTab.tsx` — slider, buttons
12. `stress-testing/VintageTab.tsx` — clean, audit only
13. `stress-testing/CapitalImpact.tsx` — progress bar track

## Context-Sensitive Exceptions (DO NOT change)
- Tooltip `bg-slate-800 text-white` — intentionally dark in both modes
- `text-white` on gradient/brand buttons — white on colored bg is correct
- `text-white/70` in AdminThemeConfig live preview — on gradient bg
- `from-slate-700 to-slate-900` in mode button — conditional class for dark visual

## Test Plan
- Regression tests for each file's violations
- Grep verification: zero remaining violations in sprint files
