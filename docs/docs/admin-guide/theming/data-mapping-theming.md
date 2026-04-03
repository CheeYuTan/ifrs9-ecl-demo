---
sidebar_position: 5
title: Data Mapping Theming
---

# Data Mapping Module Theming

This guide covers the theme audit results for the Data Mapping module — 8 files audited in Sprint 4. The Data Mapping feature allows administrators to map source data columns to the ECL engine's expected schema.

## Pages Audited

| File | Violations Found | Status |
|------|-----------------|--------|
| `data-mapping/index.tsx` | 1 fix | PASS |
| `data-mapping/SourceBrowser.tsx` | 1 fix | PASS |
| `data-mapping/ColumnMapper.tsx` | 2 fixes | PASS |
| `data-mapping/ValidationStep.tsx` | 2 fixes | PASS |
| `data-mapping/ApplyStep.tsx` | 0 (already clean) | PASS |
| `data-mapping/StatusCards.tsx` | 0 (already clean) | PASS |
| `data-mapping/types.tsx` | 0 (type-only, no UI) | PASS |
| `DataMapping.tsx` | 0 (re-export only) | PASS |

**Total: 6 violations fixed across 4 files.** Four files were already clean or contained no UI code.

## Visual Comparison

| Light Mode | Dark Mode |
|:---:|:---:|
| ![Data Mapping light](/img/theme-audit/data-mapping-light.png) | ![Data Mapping dark](/img/theme-audit/data-mapping-dark.png) |

## What Was Fixed

### Icon Visibility (4 fixes)

The most common issue was `text-slate-600` on small icons (chevrons, arrows) that were nearly invisible against dark backgrounds. Slate-600 (`#475569`) has poor contrast against slate-800/900 dark backgrounds.

**Files affected**: `index.tsx`, `SourceBrowser.tsx`, `ColumnMapper.tsx`, `ValidationStep.tsx`

```diff
<!-- ChevronRight icon in breadcrumb navigation -->
- <ChevronRight className="text-slate-600" />
+ <ChevronRight className="text-slate-400 dark:text-slate-500" />

<!-- Null indicator in source browser preview -->
- <span className="text-slate-600">null</span>
+ <span className="text-slate-400 dark:text-slate-500">null</span>

<!-- ArrowRight mapping indicator -->
- <ArrowRight className="text-slate-600" />
+ <ArrowRight className="text-slate-400 dark:text-slate-500" />
```

The fix uses `text-slate-400 dark:text-slate-500` which provides good contrast in both modes:
- **Light mode**: slate-400 (`#94a3b8`) on white/grey backgrounds — visible
- **Dark mode**: slate-500 (`#64748b`) on dark backgrounds — visible

### Optional Column Dot (1 fix)

The column mapper shows a small dot indicator for optional columns. It used `bg-slate-600` without a light-mode variant, making it overly dark on light backgrounds.

```diff
- <span className="bg-slate-600 rounded-full w-2 h-2" />
+ <span className="bg-slate-300 dark:bg-slate-600 rounded-full w-2 h-2" />
```

### Inverted Contrast (1 fix)

`ValidationStep.tsx` had an inverted contrast pattern where dark mode text was actually *darker* than the surrounding background — a logic error, not just a missing prefix:

```diff
<!-- Arrow icon had INVERTED contrast: lighter in light mode, darker in dark mode -->
- <ArrowRight className="text-slate-400 dark:text-slate-600" />
+ <ArrowRight className="text-slate-400 dark:text-slate-500" />
```

This is a subtle class of bug: the `dark:` prefix was present but the value was wrong. The 16-scanner automated tests catch missing prefixes, but inverted contrast requires visual inspection or a contrast-ratio scanner.

## Testing

**128 automated tests** (16 scanners x 8 files) verify zero theme violations across all Data Mapping module files.

```bash
# Run Sprint 4 theme tests
pytest tests/unit/test_theme_audit_sprint4.py -v

# Run all theme tests (full regression)
pytest tests/unit/test_theme_audit_sprint1.py tests/unit/test_theme_audit_sprint2.py tests/unit/test_theme_audit_sprint3.py tests/unit/test_theme_audit_sprint4.py -v
```

## Design Patterns for Data Mapping

When extending the Data Mapping module, follow these theming patterns:

| Element | Pattern |
|---------|---------|
| Navigation icons (chevrons, arrows) | `text-slate-400 dark:text-slate-500` |
| Null/empty indicators | `text-slate-400 dark:text-slate-500` |
| Status dots (optional) | `bg-slate-300 dark:bg-slate-600` |
| Status dots (required) | `bg-brand` (uses CSS variable) |
| Source table headers | Use `DataTable` component (already themed) |
| Validation messages | `text-red-600 dark:text-red-400` for errors |
