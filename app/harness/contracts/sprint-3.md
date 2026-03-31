# Sprint 3 Contract: Workflow Pages Part 2 + Admin Theme Audit (10 files)

## Scope

Audit and fix all dark-mode-only Tailwind CSS violations in 10 files:
1. `pages/ModelRegistry.tsx`
2. `pages/Backtesting.tsx`
3. `pages/MarkovChains.tsx`
4. `pages/HazardModels.tsx`
5. `pages/AdvancedFeatures.tsx`
6. `pages/Attribution.tsx`
7. `pages/Admin.tsx`
8. `pages/GLJournals.tsx`
9. `pages/RegulatoryReports.tsx`
10. `pages/ApprovalWorkflow.tsx`

## Audit Findings

After running all 16 scanner patterns against these files, **2 violations** found:

### Violation 1: GLJournals.tsx line 505
- **Pattern**: `bg-slate-800 text-white` — bare dark background with no light-mode pair
- **Context**: Totals row at bottom of trial balance table
- **Fix**: `bg-white dark:bg-slate-800 text-gray-900 dark:text-white`
- Also fix inner `text-slate-400` → `text-gray-500 dark:text-slate-400` for muted labels

### Violation 2: Admin.tsx line 140
- **Pattern**: `border-white/60` — white-opacity border with no light-mode equivalent
- **Context**: Tab bar container border
- **Fix**: `border-gray-200 dark:border-slate-700` (replace `border-white/60 dark:border-slate-700`)

### Not Violations (verified clean)
- All other `bg-slate-800/900` references already have `dark:` prefix
- `hover:bg-white/50` and `hover:bg-white/80` in HazardModels, AdvancedFeatures, Admin all have `dark:hover:` pairs
- `from-slate-800` in Backtesting and ApprovalWorkflow already have `dark:from-slate-800` prefix
- No bare `text-white/N`, `border-white/N`, `bg-white/N`, `bg-[#0B0F1A]` found

## Acceptance Criteria

- [ ] All 16 scanner patterns return zero violations across all 10 files
- [ ] GLJournals.tsx totals row renders correctly in light and dark mode
- [ ] Admin.tsx tab bar border is visible in light mode
- [ ] All existing tests continue to pass
- [ ] Sprint 3 theme scanner tests written and passing

## Test Plan

- Reuse 16 scanner functions from `test_theme_audit_sprint1.py`
- Write `test_theme_audit_sprint3.py` with parametrized tests for all 10 files
- Run full `pytest` suite to confirm no regressions
