---
sidebar_position: 2
title: Core Component Theming
---

# Core Component Theming

This guide covers how the 19 foundational shared components handle light and dark mode rendering. These components form the building blocks used across every page of the application.

## App Shell Components

### Sidebar

The sidebar adapts its background, text colours, hover states, and active indicators between modes.

![Sidebar in light mode](/img/theme-audit/light-mode-sidebar.png)

*Sidebar in light mode — note the light background, dark text, and brand-coloured active indicator.*

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Background | `bg-white` | `bg-slate-900` |
| Text | `text-gray-700` | `text-white/80` |
| Active item | Brand colour background | Brand colour background |
| Hover | `bg-black/5` | `bg-white/5` |
| Dividers | `border-gray-200` | `border-white/10` |

### Main Layout (App.tsx)

The top-level layout applies the content area background and manages the hero gradient. The hero section at the top of workflow pages is **always dark** — this is intentional, not a theming gap.

## Data Display Components

### DataTable

Tables use gradient headers that adapt to the current mode:

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Header row | `from-gray-100 to-gray-50` | `from-slate-800 to-slate-700` |
| Header text | `text-gray-900` | `text-white` |
| Body rows | `bg-white` | `bg-slate-800` |
| Alternate rows | `bg-gray-50` | `bg-slate-800/50` |
| Hover | `hover:bg-black/5` | `hover:bg-white/5` |

### Cards & KPI Cards

Cards use CSS custom properties for consistent theming:

```css
background: var(--card-bg);
border-color: var(--card-border);
```

KPI cards within the workflow pages follow the same pattern, with accent colours derived from the brand colour system.

### Collapsible Sections

Expandable panels used throughout the workflow (e.g., scenario details, model parameters) adapt their background and chevron colour.

### Charts (DrillDown, ScenarioProduct, ChartTooltip)

Chart containers use `bg-white dark:bg-slate-800` backgrounds. Tooltips are intentionally dark in both modes for readability against varied chart colours.

## Feedback Components

### Help Panel

![Help panel in light mode](/img/theme-audit/light-mode-help-panel.png)

*The help panel slides in from the right with contextual documentation.*

The help panel adapts its overlay, background, and text colours. The close button and section headers respect the current theme.

### Toast Notifications

| Variant | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Success | Green background | Green background |
| Error | Red background | Red background |
| Warning | Amber background | Amber background |
| Info | `bg-slate-800` (always dark) | `bg-slate-800` (always dark) |

The info variant is intentionally always dark — this provides consistent contrast regardless of the page theme.

### Confirm Dialog

Modal dialogs use `bg-white dark:bg-slate-800` with a semi-transparent overlay backdrop. Button styles follow the standard pattern with hover states in both modes.

### Error Boundary & Error Display

Error states display correctly in both modes, with red accent borders and appropriate text contrast.

### Status Badges

Status indicators (Approved, Pending, Rejected, etc.) use semantic colours that work in both modes. The badge background and text colours are theme-aware.

### Locked Banner

The locked banner that appears on completed/locked projects uses a gradient header that adapts between modes, matching the DataTable header pattern.

## Validation Methodology

Each component was validated using 16 automated scanner patterns that detect dark-only CSS classes missing their light-mode counterparts. The scanners check for:

1. Bare `bg-slate-[6-9]00` without `dark:` prefix
2. `bg-white/N` opacity classes without light-mode pairs
3. `border-white/N` without light-mode pairs
4. `text-white/N` muted text without light-mode pairs
5. Hover states without dual-mode pairs
6. Gradient classes without dual-mode pairs
7. Hex colour classes without `dark:` prefix
8. Directional borders, focus states, and more

**329 automated tests** verify zero violations across all 19 core components.
