---
sidebar_position: 8
title: Frontend Component & Page Testing
---

# Frontend Component & Page Testing

The frontend test suite provides comprehensive coverage of all 24 React components and 19 page-level views using Vitest and React Testing Library, ensuring the UI renders correctly, handles user interactions, and gracefully manages API errors and loading states.

## Overview

Sprint 8 expanded the frontend test suite from **103 tests** to **497 tests** (+394 new tests, a 383% increase) across 5 iterations, achieving 100% component and page-level coverage.

| Category | Before | After | Coverage |
|----------|--------|-------|----------|
| Component test files | 8/24 (33%) | 24/24 | **100%** |
| Page deep test files | 0/19 (0%) | 19/19 | **100%** |
| Hook test files | 0/2 (0%) | 1/2 (50%) | Both hooks tested |
| Lib test files | 3/3 | 3/3 | Unchanged |
| **Total vitest tests** | **103** | **497** | **+383%** |

![ECL Homepage](/img/guides/ecl-homepage.png)
*ECL platform homepage showing the dashboard with KPI cards and portfolio overview*

## Test Architecture

### Testing Stack

| Tool | Purpose |
|------|---------|
| **Vitest** | Test runner and assertion library |
| **React Testing Library** | DOM-based component testing |
| **MSW** (Mock Service Worker) | API mocking at the network level |
| **jsdom** | Browser environment simulation |

### Mock Strategy

The test suite uses a layered mocking approach:

- **API layer**: All API calls are intercepted by MSW handlers that return realistic responses
- **Chart libraries**: Recharts components are mocked at the library level (SVG rendering is not tested)
- **Animation**: Framer Motion animations are mocked to avoid timing issues
- **Complex sub-components**: Deep dependency chains (e.g., StressTesting sub-tabs) are mocked to isolate page-level behavior

## Component Tests (24/24 Covered)

Every shared component has dedicated tests verifying rendering, props, and interactions.

### Key Components Tested

| Component | Tests | Coverage Focus |
|-----------|-------|---------------|
| `SetupWizard` | 12+ | Step progression, validation at each step, completion |
| `SimulationPanel` | 10+ | Parameter inputs, run trigger, result display, defaults |
| `Sidebar` | 8+ | Navigation, active state, workflow step indicators |
| `DataTable` | 15+ | Sorting, filtering, pagination, empty state |
| `ApprovalForm` | 6+ | Form submission, validation, role checking |
| `ConfirmDialog` | 4+ | Open/close, confirm action, cancel |
| `PageHeader` | 3+ | Title display, breadcrumbs, actions |
| `KpiCard` | 4+ | Value formatting, trend indicators, loading |
| `DrillDownChart` | 5+ | Data rendering, empty data, dimension switching |
| `HelpPanel` | 3+ | Open/close, content display |
| `EmptyState` | 3+ | Message display, action button |
| `ChartTooltip` | 3+ | Value formatting, label display |

![ECL Create Project](/img/guides/ecl-create-project.png)
*Create Project dialog showing form fields and validation*

## Page Tests (19/19 Covered)

Every page component has deep tests covering rendering, data loading, user interactions, error states, and edge cases.

### Workflow Pages

| Page | Tests | Key Scenarios |
|------|-------|--------------|
| `CreateProject` | 8+ | Form validation, submission, error handling |
| `DataControl` | 8+ | Quality checks display, validation results |
| `DataMapping` | 8+ | Status cards, refresh, API errors, loading |
| `SatelliteModel` | 10+ | Locked banner (step < 3), model comparison, approval |
| `ModelExecution` | 10+ | Locked banner (step < 4), KPI cards, simulation defaults |
| `StressTesting` | 9+ | Locked banner (step < 5), 5 sub-tabs, KPI cards |
| `Overlays` | 6+ | Overlay list, add/remove, validation |
| `SignOff` | 8+ | Approval form, hash verification, lock behavior |

### Analytics Pages

| Page | Tests | Key Scenarios |
|------|-------|--------------|
| `Attribution` | 8+ | Waterfall chart, component breakdown |
| `Backtesting` | 8+ | Metric display, traffic lights, trend charts |
| `MarkovChains` | 8+ | Transition matrix, lifetime PD visualization |
| `HazardModels` | 8+ | Survival curves, model comparison |
| `ModelRegistry` | 8+ | Model list, status badges, lifecycle actions |

### Operational Pages

| Page | Tests | Key Scenarios |
|------|-------|--------------|
| `GLJournals` | 6+ | Journal list, post/reverse actions |
| `RegulatoryReports` | 8+ | Report generation, export (CSV/PDF) |
| `ApprovalWorkflow` | 8+ | Pending requests, approve/reject |
| `AdvancedFeatures` | 10+ | 3 tabs (cure, CCF, collateral), compute actions |
| `Admin` | 8+ | Config management, table discovery |

## Test Patterns

### Locked Page Testing

Pages that require specific workflow steps show a locked banner when prerequisites are not met:

```typescript
// Test: page shows locked banner when step is too early
it('shows locked banner when project step < 4', () => {
  render(<ModelExecution />, { project: { current_step: 2 } });
  expect(screen.getByText(/complete step/i)).toBeInTheDocument();
});
```

Pages tested with lock behavior: `SatelliteModel` (step < 3), `ModelExecution` (step < 4), `StressTesting` (step < 5).

### API Error Handling

Every page is tested for graceful API failure:

```typescript
// Test: page shows error state when API fails
it('handles API error gracefully', async () => {
  server.use(http.get('/api/data/*', () => HttpResponse.error()));
  render(<DataMapping />);
  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

### Null Project Handling

Pages that depend on an active project handle the null-project case:

```typescript
it('handles null project gracefully', () => {
  render(<ModelExecution />, { project: null });
  // Should not crash — shows appropriate empty or loading state
});
```

### Multi-API Data Loading

Complex pages that load data from multiple endpoints are tested for correct orchestration:

```typescript
// StressTesting loads from 6 APIs simultaneously
it('loads data from all required APIs', async () => {
  render(<StressTesting />);
  await waitFor(() => {
    expect(screen.getByText(/sensitivity/i)).toBeInTheDocument();
    expect(screen.getByText(/vintage/i)).toBeInTheDocument();
  });
});
```

## Running the Tests

### Full Frontend Suite

```bash
cd frontend && npx vitest run
```

All 497 tests complete in approximately 9 seconds.

### TypeScript Compilation

```bash
cd frontend && npx tsc -b
```

Zero errors, zero warnings — all test files are type-safe.

### Specific Test Files

```bash
# Run a single page test
npx vitest run src/pages/ModelExecution.test.tsx

# Run all component tests
npx vitest run src/components/

# Run with verbose output
npx vitest run --reporter=verbose
```

## Known Limitations

- **Chart rendering**: Recharts (SVG-based) components are mocked — chart pixel output is not tested
- **Animations**: Framer Motion animations are mocked to avoid test timing issues
- **Sub-tab isolation**: StressTesting sub-tabs are mocked to prevent deep dependency chains in page tests
- **Browser-specific behavior**: Tests run in jsdom, not a real browser — CSS layout and visual rendering are not validated (these are covered by Visual QA)

## Test Quality Standards

All frontend tests follow these conventions:

1. **No implementation testing** — tests check rendered output and user-visible behavior, not internal state
2. **Realistic mock data** — API mocks return data structures matching the actual backend responses
3. **Deterministic** — no reliance on timing, random data, or external state
4. **Fast** — the full suite runs in under 10 seconds
5. **Type-safe** — all test files compile with zero TypeScript errors
