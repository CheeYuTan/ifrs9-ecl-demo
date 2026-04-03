# Sprint 1 Contract — Run 7: Refactor Large Frontend Files

## Goal
Split StressTesting.tsx (1022 lines) and DataMapping.tsx (874 lines) into focused sub-components, each <200 lines.

## Acceptance Criteria
1. StressTesting.tsx refactored into stress-testing/ directory with sub-components
2. DataMapping.tsx refactored into data-mapping/ directory with sub-components
3. All existing tests pass — zero regressions
4. Frontend builds cleanly with `npm run build` — no TS errors
5. No file exceeds 200 lines in the new directories (main orchestrators may be slightly over)

## Refactoring Plan

### StressTesting.tsx → pages/stress-testing/
- `index.tsx` — main component: state, data loading, tab switching (~150 lines)
- `MonteCarloTab.tsx` — MC distribution charts and tables (~160 lines)
- `SensitivityTab.tsx` — Parameter shocks, quick estimate, full simulation (~200 lines)
- `VintageTab.tsx` — Vintage delinquency curves (~60 lines)
- `ConcentrationTab.tsx` — ECL concentration heatmap (~100 lines)
- `MigrationTab.tsx` — Stage migration simulator (~100 lines)
- `CapitalImpact.tsx` — Capital impact analysis and reverse stress test (~70 lines)
- `types.ts` — Shared interfaces and constants

### DataMapping.tsx → pages/data-mapping/
- `index.tsx` — main component: state, data loading, wizard control (~180 lines)
- `StatusCards.tsx` — Table status card grid (~60 lines)
- `SourceBrowser.tsx` — UC catalog/schema/table browsing (~100 lines)
- `ColumnMapper.tsx` — Column mapping table with drag/search (~100 lines)
- `ValidationStep.tsx` — Validation results display (~80 lines)
- `ApplyStep.tsx` — Apply mapping UI and results (~90 lines)
- `types.ts` — Shared interfaces and helpers (TypeBadge, StatusIcon)

## Test Plan
- `npm run build` passes
- All existing pytest tests pass
- Visual: pages render identically (Visual QA will verify)
