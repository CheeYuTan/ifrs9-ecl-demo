---
sidebar_position: 1
title: Light & Dark Mode
---

# Light & Dark Mode Support

The IFRS 9 ECL application fully supports both light and dark colour modes. Every component — from the sidebar and navigation to data tables, charts, and workflow pages — renders correctly in both themes.

## How It Works

The theme system uses Tailwind CSS's `dark:` class prefix strategy. When the user toggles dark mode, the `<html>` element receives a `dark` class, which activates all `dark:` prefixed utility classes.

### CSS Custom Properties

Global theme tokens are defined in `frontend/src/index.css`:

| Variable | Light Value | Dark Value | Usage |
|----------|------------|------------|-------|
| `--card-bg` | `#ffffff` | `#1e293b` | Card and panel backgrounds |
| `--card-border` | `#e2e8f0` | `rgba(255,255,255,0.1)` | Card borders |
| `--content-bg` | `#f8fafc` | `#0f172a` | Page content area |
| `--hero-bg` | `#1e293b` | `#0B0F1A` | Hero section background |
| `--text-primary` | `#0f172a` | `#f8fafc` | Primary text |
| `--text-secondary` | `#475569` | `#cbd5e1` | Secondary text |
| `--text-muted` | `#94a3b8` | `#64748b` | Muted/disabled text |

### Brand Colour System

The application supports a dynamic brand colour (set via the [Theme admin page](/admin-guide/theme)). The CSS variable `--color-brand` propagates through buttons, links, active sidebar indicators, and accent elements in both light and dark modes.

## Visual Comparison

### Home Page

| Light Mode | Dark Mode |
|:---:|:---:|
| ![Light mode home page](/img/theme-audit/light-mode-home.png) | ![Dark mode home page](/img/theme-audit/dark-mode-home.png) |

### Data Processing

| Light Mode | Dark Mode |
|:---:|:---:|
| ![Light mode data processing](/img/theme-audit/light-mode-data-processing.png) | ![Dark mode data processing](/img/theme-audit/dark-mode-data-processing.png) |

## Toggling Modes

Click the **sun/moon icon** in the top-right corner of the sidebar to switch between light and dark modes. The preference is stored in `localStorage` and persists across sessions.

## Design Patterns

Every UI element follows the **light-first, dark-override** pattern:

```html
<!-- Background -->
<div class="bg-white dark:bg-slate-800">

<!-- Text -->
<span class="text-gray-900 dark:text-white">

<!-- Borders -->
<div class="border-gray-200 dark:border-white/10">

<!-- Hover states -->
<button class="hover:bg-black/5 dark:hover:bg-white/5">
```

### Intentional Exceptions

Some elements are intentionally dark in both modes:

- **Hero gradient** at the top of the workflow pages — always uses a dark gradient background
- **Toast notifications** — the info variant uses a dark background for contrast
- **Tooltips** — dark background ensures readability regardless of page theme

## Audit Coverage

The theme system has been systematically audited across all application components:

| Audit Phase | Files | Violations Fixed | Tests |
|-------------|-------|-----------------|-------|
| [Core Components](/admin-guide/theming/core-components) | 19 | All resolved | 329 |
| [Workflow Pages](/admin-guide/theming/workflow-pages) | 8 | 6 (SatelliteModel) | 120 |
| [Admin & Secondary Pages](/admin-guide/theming/admin-secondary-pages) | 10 | 28 | 160 |
| [Data Mapping Module](/admin-guide/theming/data-mapping-theming) | 8 | 6 | 128 |
| **Total** | **45** | **~40+** | **737** |

A suite of 17 automated scanner patterns detects theme violations in CI, preventing regressions.

## Accessibility

- All text meets WCAG 2.1 AA contrast requirements in both modes
- Interactive elements have visible focus indicators in both themes
- The theme toggle is keyboard-accessible
