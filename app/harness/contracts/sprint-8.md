# Sprint 8 Contract: Frontend — Component & Page Testing

## Objective
Expand frontend vitest test coverage from 103 to 200+ tests by adding tests for all untested pages, components, and hooks.

## Acceptance Criteria

### Components (15+ untested → all tested)
- [ ] ApprovalForm: renders, handles form submission
- [ ] ChartTooltip: renders tooltip content
- [ ] CollapsibleSection: toggles expand/collapse
- [ ] ConfirmDialog: renders, handles confirm/cancel
- [ ] DrillDownChart: renders chart with mock data, empty data
- [ ] EmptyState: renders message and optional action
- [ ] ErrorDisplay: renders error messages
- [ ] HelpPanel: toggles open/close
- [ ] HelpTooltip: renders tooltip
- [ ] JobRunLink: renders link with URL
- [ ] NotebookLink: renders link
- [ ] PageHeader: renders title
- [ ] PageLoader: renders spinner
- [ ] ScenarioChecklist: renders checkboxes
- [ ] SetupWizard: step progression, validation
- [ ] SimulationPanel: parameter inputs
- [ ] SimulationProgress: progress bar
- [ ] SimulationResults: results display
- [ ] StepDescription: step info
- [ ] ThreeLevelDrillDown: drill-down levels

### Pages (19 untested → all smoke-tested)
- [ ] Every page renders without crashing
- [ ] Key interactions: buttons, forms, navigation
- [ ] Error states from API failures
- [ ] Loading states during data fetch

### Hooks
- [ ] useEclProductData: fetches data, handles loading/error
- [ ] useCohortsByProduct: fetches per-product cohorts

### Quality Gates
- [ ] Total vitest test count >= 200
- [ ] Zero test failures
- [ ] No modifications to existing passing tests

## Test Plan
- Unit tests: rendering, props, user interactions (RTL + userEvent)
- API mocking: vi.mock for fetch, test request params
- Error/loading states
- Follow existing test patterns (describe/it, screen queries)
