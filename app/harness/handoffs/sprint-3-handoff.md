# Sprint 3 Handoff: Workflow Pages Part 2 + Admin Theme Audit (Iteration 5)

## What Was Built

Audited and fixed all dark-mode-only Tailwind CSS violations across 10 workflow/admin page files. Over 5 iterations, found and fixed 18+ violations including a scanner gap for `*-slate-50` patterns.

### Files Changed

| File | Violations Fixed (total) | Fix Types |
|------|--------------------------|-----------|
| `pages/GLJournals.tsx` | 3 | bare bg-slate-800 totals row, bare hover:text-slate-700, bare hover:bg-slate-200 |
| `pages/Admin.tsx` | 3 | border-white/60 tab bar, hover:bg-white/80 tab, hover:text-slate-700 tab |
| `pages/HazardModels.tsx` | 4 | hover:bg-white/50, hover:text-slate-700, bg-white/50 tab, **border-slate-50 → border-slate-100 dark:border-slate-700** |
| `pages/AdvancedFeatures.tsx` | 3 | hover:bg-white/50, hover:text-slate-700, bg-white/50 tab |
| `pages/ModelRegistry.tsx` | 5 | hover:bg-slate-100 close buttons, gradient dark pair, border visibility, **bg-slate-50 draft badge → dark:bg-slate-800** |
| `pages/Backtesting.tsx` | 1 | hover:bg-slate-100 on close button |
| `pages/MarkovChains.tsx` | 1 | hover:text-slate-700 on tab inactive |
| `pages/ApprovalWorkflow.tsx` | 8 | hover:bg-slate-100, hover:text-slate-700, XCircle icon, border divider, **bg-slate-50 priority badge → dark:bg-slate-800, bg-slate-50 status badge → dark:bg-slate-800, hover:bg-slate-50 → dark:hover:bg-slate-800** |
| `pages/Attribution.tsx` | 0 | Already clean |
| `pages/RegulatoryReports.tsx` | 0 | Already clean |

### Iteration 5 Fixes (from eval BUG-S3-001 + new scanner discoveries)

1. **BUG-S3-001** — `HazardModels.tsx:661`: `border-slate-50` Row component → `border-slate-100 dark:border-slate-700`
2. **ModelRegistry.tsx:28**: Draft status badge `bg-slate-50` → added `dark:bg-slate-800 dark:border-slate-600`
3. **ApprovalWorkflow.tsx:75**: Normal priority badge `bg-slate-50` → added `dark:bg-slate-800 dark:border-slate-600`
4. **ApprovalWorkflow.tsx:460**: Inactive status badge `bg-slate-50` → added `dark:bg-slate-800 dark:border-slate-600`
5. **ApprovalWorkflow.tsx:514**: Pending request button `hover:bg-slate-50` → added `dark:hover:bg-slate-800`

### New Scanner Added (17th scanner)

Added `find_bare_slate_50()` to `test_theme_audit_sprint1.py` — catches `border-slate-50`, `bg-slate-50`, `ring-slate-50` without `dark:` pair. This scanner found 4 additional violations in Sprint 3 files beyond the original BUG-S3-001.

### Test File
- `tests/unit/test_theme_audit_sprint3.py` — **160 tests** (16 scanners × 10 files, parametrized)

## How to Test

1. Start: `cd frontend && npm run dev`
2. Navigate to each page listed above
3. Toggle between light and dark mode on each page
4. Verify:
   - **HazardModels**: Term structure Row borders visible in both modes
   - **ModelRegistry**: Draft status badge readable in dark mode; performance metrics gradient visible
   - **ApprovalWorkflow**: Normal priority and Inactive status badges readable in dark mode; pending request buttons have visible hover state in dark mode
   - **GLJournals**: Totals row at bottom renders with visible text in both modes
   - **Admin**: Tab bar border visible in light mode
   - All other pages: No visual regressions

## Test Results (Iteration 5)

```
Backend: 1647 passed, 61 skipped (73.15s)
Frontend: 103 passed (1.98s)
Sprint 3 theme tests: 160 passed (0.26s)
Total: 1910 passed, 61 skipped, 0 failures
```

## Known Limitations

- None. All 16 scanner patterns return zero violations for all 10 files.

## Files Changed (Iteration 5)
- `frontend/src/pages/HazardModels.tsx` — 1 fix (BUG-S3-001: border-slate-50 dark pair)
- `frontend/src/pages/ModelRegistry.tsx` — 1 fix (bg-slate-50 draft badge dark pair)
- `frontend/src/pages/ApprovalWorkflow.tsx` — 3 fixes (bg-slate-50 badge dark pairs, hover:bg-slate-50 dark pair)
- `tests/unit/test_theme_audit_sprint1.py` — added 17th scanner `find_bare_slate_50()`
- `tests/unit/test_theme_audit_sprint3.py` — added 16th test parametrization for slate-50 scanner (160 tests total)
