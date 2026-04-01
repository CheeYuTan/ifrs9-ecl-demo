# Sprint 8 Contract: Final Regression + Visual Verification (Dynamic Sprint C)

## Acceptance Criteria

- [ ] ZERO bare `text-slate-600` without `dark:text-slate-300` pair (except hover: contexts with dark:hover: pairs)
- [ ] ZERO bare `text-slate-700` without `dark:text-slate-200` pair (except hover: contexts with dark:hover: pairs)
- [ ] ZERO bare `bg-slate-[89]00` without `dark:` prefix (excluding documented tooltip exceptions)
- [ ] ZERO bare `bg-white/` without light-mode pair (excluding hero area exceptions in App.tsx)
- [ ] ZERO bare `border-white/` without light-mode pair (excluding hero area exceptions)
- [ ] ZERO bare `text-white/` without light-mode pair (excluding hero area, tooltip exceptions)
- [ ] ZERO bare `hover:bg-white/` without light-mode pair (excluding hero area)
- [ ] All existing tests pass (pytest + vitest)
- [ ] Frontend builds successfully (tsc -b && vite build)
- [ ] Comprehensive scanner tests covering all violation patterns across all affected files

## Documented Exceptions (NOT violations)
- App.tsx hero area (lines ~60-170, 477-488): always-dark gradient hero
- Toast.tsx, AdminAppSettings.tsx, AdminModelConfig.tsx, ColumnMappingRow.tsx, HelpTooltip.tsx: intentionally dark tooltips
- AdminThemeConfig.tsx: theme preview swatch (always on dark preview bg)
- RegulatoryReports.tsx: `bg-white/20` inside brand button
- hover:text-slate-600/700 WITH matching dark:hover: pairs are correct

## Files to Fix

### text-slate-600 violations (~30 instances):
- ConfirmDialog.tsx, StepDescription.tsx, SimulationPanel.tsx, KpiCard.tsx, SimulationResults.tsx
- DrillDownChart.tsx, DataTable.tsx, ThreeLevelDrillDown.tsx, JobRunLink.tsx
- ScenarioProductBarChart.tsx, ScenarioChecklist.tsx, SatelliteModel.tsx
- SignOff.tsx, ModelExecution.tsx

### text-slate-700 violations (~35 instances):
- App.tsx, SimulationPanel.tsx, SimulationResults.tsx, ApprovalForm.tsx
- DrillDownChart.tsx, ThreeLevelDrillDown.tsx, HelpPanel.tsx, EmptyState.tsx
- ScenarioProductBarChart.tsx, ScenarioChecklist.tsx, Overlays.tsx
- SatelliteModel.tsx, DataControl.tsx

## Test Plan
- Scanner tests for text-slate-600/700 patterns across all affected files
- Full pytest + vitest pass
- Frontend build success
