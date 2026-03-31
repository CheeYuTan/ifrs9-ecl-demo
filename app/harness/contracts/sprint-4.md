# Sprint 4 Contract: Data Mapping Module Theme Audit (8 files)

## Acceptance Criteria
- [ ] All 8 data-mapping files audited for theme violations
- [ ] Every `text-slate-600` without a `dark:` pair gets `dark:text-slate-400` or `dark:text-slate-500`
- [ ] Every `bg-slate-600` without a `dark:` pair gets appropriate dark variant
- [ ] Inverted dark/light contrast pairs corrected (e.g., `text-slate-400 dark:text-slate-600`)
- [ ] Zero violations from sprint 4 file set when scanned with all 17 theme violation patterns
- [ ] All existing tests pass (backend + frontend + theme)
- [ ] No regressions in existing `dark:` classes

## Files in Scope
1. `data-mapping/index.tsx` — ChevronRight icon `text-slate-600` without dark pair
2. `data-mapping/SourceBrowser.tsx` — null indicator `text-slate-600` without dark pair
3. `data-mapping/ColumnMapper.tsx` — ArrowRight icon `text-slate-600` without dark pair + `bg-slate-600` dot
4. `data-mapping/ValidationStep.tsx` — ArrowRight icon `text-slate-600` without dark pair + inverted muted text
5. `data-mapping/ApplyStep.tsx` — audit (appears clean)
6. `data-mapping/StatusCards.tsx` — audit (appears clean)
7. `data-mapping/types.tsx` — audit (appears clean)
8. `DataMapping.tsx` — re-export only, audit

## Violations Found

| File | Line | Pattern | Fix |
|------|------|---------|-----|
| index.tsx | 337 | `text-slate-600` (ChevronRight) | `text-slate-400 dark:text-slate-500` |
| SourceBrowser.tsx | 139 | `text-slate-600` (null span) | `text-slate-400 dark:text-slate-500` |
| ColumnMapper.tsx | 77 | `bg-slate-600` (optional dot) | `bg-slate-300 dark:bg-slate-600` |
| ColumnMapper.tsx | 87 | `text-slate-600` (ArrowRight) | `text-slate-400 dark:text-slate-500` |
| ValidationStep.tsx | 98 | `text-slate-600` (ArrowRight) | `text-slate-400 dark:text-slate-500` |
| ValidationStep.tsx | 103 | `text-slate-400 dark:text-slate-600` (inverted) | `text-slate-500 dark:text-slate-500` |

## Test Plan
- Run all 17 theme scanners on sprint 4 files
- Run full `pytest` suite
- Run frontend tests
