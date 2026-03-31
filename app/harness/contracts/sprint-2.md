# Sprint 2 Contract: Workflow Pages Part 1 — Theme Audit

## Files in Scope (8 files)
1. `pages/CreateProject.tsx`
2. `pages/DataProcessing.tsx`
3. `pages/DataControl.tsx`
4. `pages/SatelliteModel.tsx`
5. `pages/ModelExecution.tsx`
6. `pages/StressTesting.tsx` (re-exports `stress-testing/index.tsx`)
7. `pages/Overlays.tsx`
8. `pages/SignOff.tsx`

## Acceptance Criteria
- [ ] Zero `bg-slate-[6-9]00` without `dark:` prefix in all 8 files
- [ ] Zero `bg-white/N` without a light-mode pair (`bg-black/N` or `dark:bg-white/N`)
- [ ] Zero `border-white/N` without light pair
- [ ] Zero `text-white/N` without light pair (excluding brand-colored button contexts)
- [ ] Zero `hover:bg-white/N` without `dark:hover:` pair
- [ ] Zero `from-slate-[78]00` without `dark:` prefix
- [ ] Zero `bg-[#0B0F1A]` without `dark:` prefix
- [ ] All existing `dark:` prefixed classes still intact (no regression)
- [ ] Automated scanner tests pass for all 8 files (mirroring Sprint 1 test pattern)

## Context-Sensitive Exceptions
- `text-white` inside brand-colored buttons/badges (e.g., `bg-brand text-white`) is CORRECT
- `text-white` inside always-dark hero/gradient sections is CORRECT
- `bg-slate-100` table headers (`bg-slate-100`) are light-mode patterns, NOT violations
- `bg-slate-50` is a light-mode color, NOT a violation
- Table hover `hover:bg-slate-50` is a light-mode hover, NOT a violation

## Test Plan
- Python scanner tests: `tests/unit/test_theme_audit_sprint2.py`
- 16 scanners × 8 files = comprehensive regression coverage
- All Sprint 1 tests must still pass (no regression)

## Production Readiness Items
- N/A (theme audit only — no new features)
