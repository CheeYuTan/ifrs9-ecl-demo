# Sprint 8 Handoff: Frontend — Component & Page Testing

## What Was Built

Expanded frontend vitest test coverage from **103 tests** to **250 tests** (+147 new tests) across 18 new test files.

### New Test Files (18 files)

**Component Tests (11 new files):**
- `components/ApprovalForm.test.tsx` — 10 tests: rendering, approve/reject actions, comment handling, Processing state, disabled reject without comment
- `components/ChartTooltip.test.tsx` — 8 tests: null rendering for inactive/empty, tooltip display, custom formatValue, color application
- `components/CollapsibleSection.test.tsx` — 6 tests: toggle expand/collapse, defaultOpen, aria-expanded, icon rendering
- `components/ConfirmDialog.test.tsx` — 10 tests: open/close, confirm/cancel, Escape key, loading state, dialog role, warning variant
- `components/EmptyState.test.tsx` — 7 tests: title, description, ActionButton click, custom ReactNode action, custom icon, className
- `components/ErrorDisplay.test.tsx` — 8 tests: title/message, retry, technical details toggle, dismiss, Report Issue link
- `components/HelpTooltip.test.tsx` — 18 tests: tooltip show/hide on hover, close button, IFRS9_HELP constants (ECL, PD, LGD, EAD, SICR, STAGE_1/2/3, GCA, COVERAGE_RATIO, GL_RECON)
- `components/JobRunLink.test.tsx` — 10 tests: null run, default/compact mode, status states (SUCCESS/RUNNING/FAILED), duration, tasks list, external link attrs
- `components/PageHeader.test.tsx` — 5 tests: title/subtitle, status badge, children rendering, h2 element
- `components/PageLoader.test.tsx` — 4 tests: spinner, role status, sr-only text, aria-label
- `components/ScenarioChecklist.test.tsx` — 8 tests: labels, weights, status indicators (Pending/Computing/done), ECL amount, duration, color dot
- `components/SimulationProgress.test.tsx` — 9 tests: header, elapsed time, progress %, phase, message, loan/sim counts, cancel, cap at 100%, scenario checklist
- `components/StepDescription.test.tsx` — 6 tests: description, IFRS ref, tips list, custom icon

**Page Tests (4 new files):**
- `pages/Admin.test.tsx` — 3 tests: tab labels, config loading, tab switching
- `pages/Attribution.test.tsx` — 2 tests: render + data loading, getAttribution API call
- `pages/CreateProject.test.tsx` — 4 tests: form rendering, inputs, pre-fill from project, project list loading
- `pages/page-smoke.test.tsx` — 16 tests: smoke tests for all untested pages (AdvancedFeatures, ApprovalWorkflow, Backtesting, DataControl, DataMapping, DataProcessing, GLJournals, HazardModels, MarkovChains, ModelExecution, ModelRegistry, Overlays, RegulatoryReports, SatelliteModel, SignOff, StressTesting)

**Hook Tests (1 new file):**
- `hooks/useEclData.test.ts` — 11 tests: useEclProductData (no-fetch, fetch, cohort fetch, loading, error handling) + useCohortsByProduct (empty, fetch, custom key, error skip, empty array skip)

### Testing Patterns Used
- `vi.mock('framer-motion')` — consistent mock for all motion components
- `vi.mock('recharts')` — mock for chart components
- `vi.mock('../lib/api')` — comprehensive API mock with 50+ endpoints
- `@testing-library/react` + `@testing-library/user-event` — RTL standard patterns
- `renderHook` + `waitFor` — for custom hook testing

## How to Test

- Start: `cd frontend && npx vitest run`
- All 250 tests should pass in ~5 seconds
- TypeScript build: `npx tsc -b` (zero errors)

## Test Results

- **vitest**: 250 passed, 0 failed (29 test files)
- **pytest**: 3838 passed, 61 skipped (zero regressions)
- **TypeScript build**: SUCCESS (zero errors)

## Coverage Summary

| Category | Before | After | Coverage |
|----------|--------|-------|----------|
| Component test files | 8 | 19 | 19/23 components tested (83%) |
| Page test files | 0 | 4 | 19/19 pages smoke-tested (100%) |
| Hook test files | 0 | 1 | 2/2 hooks tested (100%) |
| Lib test files | 3 | 3 | unchanged |
| Total vitest tests | 103 | 250 | +147 tests |

### Untested Components (4 remaining)
- `ScenarioProductBarChart` — complex recharts component with drill-down, requires extensive chart mocking
- `SimulationPanel` — 500+ lines, complex SSE streaming + state machine, needs dedicated test sprint
- `SimulationResults` — depends on SimulationPanel state
- `SetupWizard` — 985 lines (pre-existing debt), needs breaking up before testing

## Known Limitations
- Page smoke tests verify render without crash but don't test deep interactions
- Chart components (recharts-based) are mocked at the library level — visual rendering not tested
- `framer-motion` animations are mocked — animation behavior not verified
- SetupWizard (985 lines) is too large for meaningful unit testing without refactoring

## Files Changed

### New files (18)
- `frontend/src/components/ApprovalForm.test.tsx`
- `frontend/src/components/ChartTooltip.test.tsx`
- `frontend/src/components/CollapsibleSection.test.tsx`
- `frontend/src/components/ConfirmDialog.test.tsx`
- `frontend/src/components/EmptyState.test.tsx`
- `frontend/src/components/ErrorDisplay.test.tsx`
- `frontend/src/components/HelpTooltip.test.tsx`
- `frontend/src/components/JobRunLink.test.tsx`
- `frontend/src/components/PageHeader.test.tsx`
- `frontend/src/components/PageLoader.test.tsx`
- `frontend/src/components/ScenarioChecklist.test.tsx`
- `frontend/src/components/SimulationProgress.test.tsx`
- `frontend/src/components/StepDescription.test.tsx`
- `frontend/src/hooks/useEclData.test.ts`
- `frontend/src/pages/Admin.test.tsx`
- `frontend/src/pages/Attribution.test.tsx`
- `frontend/src/pages/CreateProject.test.tsx`
- `frontend/src/pages/page-smoke.test.tsx`

### Modified files (1)
- `harness/contracts/sprint-8.md` — updated contract for frontend testing scope
