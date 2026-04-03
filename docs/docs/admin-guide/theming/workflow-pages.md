---
sidebar_position: 3
title: Workflow Page Theming
---

# Workflow Page Theming

This guide covers the theme audit results for the 8 core ECL workflow pages. These pages form the heart of the application — each step in the IFRS 9 ECL calculation workflow now renders correctly in both light and dark modes.

## Pages Audited

| Page | File | Violations Found | Status |
|------|------|-----------------|--------|
| Create Project | `CreateProject.tsx` | 0 (already clean) | PASS |
| Data Processing | `DataProcessing.tsx` | 0 (already clean) | PASS |
| Data Control | `DataControl.tsx` | 0 (properly paired) | PASS |
| Satellite Model | `SatelliteModel.tsx` | 6 fixes applied | PASS |
| Model Execution | `ModelExecution.tsx` | 0 (properly paired) | PASS |
| Stress Testing | `stress-testing/index.tsx` | 0 (properly paired) | PASS |
| Overlays | `Overlays.tsx` | 0 (properly paired) | PASS |
| Sign Off | `SignOff.tsx` | 0 (properly paired) | PASS |

## Data Control

![Data control in light mode](/img/theme-audit/light-mode-data-control.png)

*Data Control page in light mode showing quality check results with appropriate contrast.*

The Data Control step displays data quality validation results. All status indicators, progress bars, and result tables respect the current theme.

## Satellite Model (Key Fixes)

The Satellite Model page required the most attention during the audit. Six violations were fixed across three iterations:

### What Was Fixed

1. **Hover states on tab buttons** — Three `hover:bg-slate-700` classes were missing their `dark:hover:` prefix. In light mode, hovering over product tabs produced an inappropriately dark background.

2. **Conditional styling for active states** — Three light-only conditional classes (applied when a model or tab is selected) were missing their dark-mode base state pairs.

### Before and After

| Issue | Before (Light Mode) | After (Light Mode) |
|-------|--------------------|--------------------|
| Tab hover | Dark grey flash on hover | Subtle light grey hover |
| Active tab | Missing background contrast | Proper light/dark backgrounds |
| Run history button | Incorrect hover shade | Theme-appropriate hover |

## Dark-Mode Text Contrast

A global CSS approach handles text contrast inversion. Rather than adding `dark:text-*` classes to every element, the application uses CSS overrides in `index.css`:

```css
.dark .text-slate-800 { color: #F1F5F9; }  /* → slate-50 */
.dark .text-slate-700 { color: #E2E8F0; }  /* → slate-200 */
.dark .text-slate-600 { color: #CBD5E1; }  /* → slate-300 */
.dark .text-slate-500 { color: #94A3B8; }  /* → slate-400 */
```

This ensures that any text using Tailwind's grey scale automatically inverts in dark mode without per-element class changes.

## Models Page

![Models page in dark mode](/img/theme-audit/dark-mode-models.png)

*Model Registry in dark mode — table headers, filters, and status badges all adapt correctly.*

## Backtesting

![Backtesting in dark mode](/img/theme-audit/dark-mode-backtesting.png)

*Backtesting page in dark mode showing traffic-light scoring and model comparison charts.*

## Testing

**120 automated tests** verify zero theme violations across all 8 workflow pages. These tests use the same 16 scanner patterns established for core components:

```bash
# Run workflow page theme tests
pytest tests/unit/test_theme_audit_sprint2.py -v

# Run core component theme tests (regression)
pytest tests/unit/test_theme_audit_sprint1.py -v

# Run all tests
pytest tests/ -v
```

## Troubleshooting

### Text is invisible on a workflow page

If text appears invisible in light mode, check whether the element uses a bare `text-white` class without a `dark:` prefix. The fix is:

```diff
- <span class="text-white">
+ <span class="text-gray-900 dark:text-white">
```

### Background blends into the page

If a section's background disappears in light mode, look for bare `bg-slate-800` or `bg-slate-900`:

```diff
- <div class="bg-slate-800">
+ <div class="bg-white dark:bg-slate-800">
```

### Hover state looks wrong

Hover effects that flash dark in light mode typically have bare `hover:bg-white/N` or `hover:bg-slate-*`:

```diff
- <button class="hover:bg-white/10">
+ <button class="hover:bg-black/5 dark:hover:bg-white/10">
```
