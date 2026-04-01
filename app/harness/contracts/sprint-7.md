# Sprint 7 Contract: SetupWizard.tsx Theme Audit (Dynamic Sprint A)

## Acceptance Criteria

- [ ] All bare `text-white/N` instances in SetupWizard.tsx have light-mode pairs (e.g., `text-slate-600 dark:text-white/60`)
- [ ] All bare `bg-white/[N]` instances have light-mode pairs (e.g., `bg-black/5 dark:bg-white/[0.03]`)
- [ ] All bare `border-white/[N]` instances have light-mode pairs (e.g., `border-slate-200 dark:border-white/[0.06]`)
- [ ] All bare `hover:bg-white/` and `hover:text-white/` instances have light-mode pairs
- [ ] Context-sensitive exceptions preserved (text-white inside gradient-brand buttons is correct)
- [ ] Scanner tests written covering all 20 theme patterns for SetupWizard.tsx
- [ ] All existing tests pass (pytest + vitest)
- [ ] Frontend builds successfully (tsc -b && vite build)

## Files Modified
- `frontend/src/components/SetupWizard.tsx` — theme fixes

## Files Created
- `frontend/src/tests/theme-scanners/test_setup_wizard_theme.test.ts` — scanner tests

## Test Plan
- Unit tests: Theme scanner tests for all 20 violation patterns
- Integration: Frontend build verification
- Regression: Full pytest + vitest suite must pass

## Violation Inventory (from grep analysis)

### Bare `text-white/N` (needs light pairs) — ~35 instances
Lines: 105, 371, 419, 439, 458, 462, 471, 478, 542, 548, 551, 566, 582, 585, 597, 599, 612, 620, 636, 639, 648, 665, 715, 774, 808, 863, 868, 871, 892, 957, 974, 977

### Bare `bg-white/[N]` (needs light pairs) — ~13 instances
Lines: 437, 450, 470, 560, 566, 593, 607, 620, 723, 774, 867, 883, 892, 946

### Bare `border-white/[N]` (needs light pairs) — ~10 instances
Lines: 437, 450, 470, 560, 593, 607, 723, 774, 867, 883, 892, 946

### Bare `hover:bg-white/` and `hover:text-white` — ~4 instances
Lines: 371, 566, 620, 665, 774, 808, 974, 977

### Already Correct (have dark: pairs)
Lines 72, 78, 280, 285, 292, 480, 726, 736, 742, 750, 753, 762, 785, 872, 885, 897, 904, 909, 915, 920, 927, 958

### Exceptions (leave as-is)
- `text-white` inside `gradient-brand` buttons (lines 69, 283, 412, 491, 539, 673, 816, 936, 964) — white on colored bg is correct
