---
sidebar_position: 6
title: "Theme Customization"
description: "Customizing the platform appearance with color presets, dark mode, and brand colors."
---

# Theme Customization

The IFRS 9 ECL Platform provides a flexible theming system that supports light and dark modes, eight built-in color presets, and fully custom brand colors. Theme preferences are applied instantly and persisted per-user in the browser.

:::info Who Should Read This
System administrators responsible for configuring the platform's visual appearance and ensuring it aligns with organizational brand guidelines.
:::

## Overview

The theme system has three configurable dimensions:

| Setting | Options | Description |
|---------|---------|-------------|
| **Mode** | Light or Dark | Controls the overall appearance — light backgrounds with dark text, or dark backgrounds with light text. |
| **Color Preset** | 8 built-in presets | A professionally designed color palette applied to buttons, links, accents, and highlights. |
| **Custom Colors** | Any hex color | Override the preset with your organization's exact brand colors. |

The default configuration is **Emerald** preset in **Light** mode — a finance-oriented green that conveys stability and professionalism.

## Switching Between Light and Dark Mode

Users can toggle between light and dark mode using the theme toggle in the application header. The change takes effect immediately without a page reload.

- **Light mode**: White backgrounds, dark text — suitable for well-lit office environments and printed reports
- **Dark mode**: Dark backgrounds, light text — reduces eye strain during extended analysis sessions

:::tip
Dark mode works well for analysts who spend long periods reviewing ECL dashboards and charts. Light mode is generally preferred for presentations and screen-sharing with auditors.
:::

## Built-in Color Presets

Eight professionally designed color presets are available. Each preset defines a harmonized set of primary, dark, and light color variants used throughout the platform for buttons, links, charts, and highlighted areas.

| Preset | Primary Color | Recommended Use Case |
|--------|--------------|---------------------|
| **Emerald** (default) | Green (`#00D09C`) | Finance-oriented. Conveys stability — ideal for credit risk platforms. |
| **Blue** | Blue (`#3B82F6`) | Corporate blue. Suitable for conservative institutions and central banks. |
| **Purple** | Purple (`#8B5CF6`) | Modern aesthetic. Good for innovation-focused teams and fintech. |
| **Rose** | Red-pink (`#F43F5E`) | Bold and attention-grabbing. Use with caution in audit contexts. |
| **Amber** | Yellow (`#F59E0B`) | Warm tone. Works well for warning-oriented dashboards. |
| **Indigo** | Deep blue (`#6366F1`) | Strong contrast. Effective for data-dense analytical views. |
| **Cyan** | Teal (`#06B6D4`) | Cool tone. Good for analytical and reporting interfaces. |
| **Orange** | Orange (`#F97316`) | Energetic. Useful for development or staging environments to distinguish from production. |

To change the preset, navigate to **Settings > Theme** in the application and select the desired preset from the color palette grid. The change is applied immediately across all pages.

## Custom Brand Colors

When the built-in presets do not match your organization's brand guidelines, you can define custom colors. The platform uses three color values:

| Color Role | Where It Appears | Example |
|-----------|-----------------|---------|
| **Primary brand** | Buttons, links, active navigation tabs, chart accents | Your main corporate color |
| **Brand dark** | Hover states, focused elements, emphasis borders | A darker shade of your primary color |
| **Brand light** | Subtle backgrounds, highlighted panels, notification backgrounds | A very light tint of your primary color |

To apply custom colors, navigate to **Settings > Theme**, select **Custom**, and enter the three hex color values. The platform validates that all values are valid 6-digit hex colors before applying.

:::tip
When choosing custom colors, ensure sufficient contrast between text and background elements. The primary brand color should be legible as text on both white and dark backgrounds. A good rule of thumb: the dark variant should be 10-20% darker than the primary, and the light variant should be a very pale tint (90-95% white).
:::

## How Theme Preferences Are Stored

Theme preferences are stored locally in each user's web browser. This means:

- Each user can have their own preferred theme without affecting others
- Preferences persist across browser sessions (closing and reopening the browser)
- Preferences are **not** synchronized across devices — a user's laptop and desktop may have different themes
- Clearing browser data resets the theme to the organizational default

:::caution
Theme preferences are per-browser, per-user. They are not stored on the server. If you need a consistent appearance across all users (for example, during a regulatory audit), coordinate with your team to use the same preset, or set the organizational default as described below.
:::

## Setting Organizational Defaults

To change the default theme for all new users (and any user who has not customized their theme), the frontend must be rebuilt with an updated default configuration. This is a deployment-level change.

**Steps:**

1. Identify the desired default mode (light or dark) and preset (or custom colors)
2. Request a frontend rebuild with the updated default configuration from your development team
3. Redeploy the application

After redeployment, any user who has not previously customized their theme will see the new defaults. Existing users who have already set a preference are not affected — their stored preference takes precedence.

:::info
Changing organizational defaults requires a frontend rebuild and redeployment. It cannot be done through the admin UI alone. For details on the frontend build process, see the [Developer Reference](../developer/architecture).
:::

## Troubleshooting Theme Issues

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Theme resets on every page load | Browser `localStorage` is blocked or full | Check the browser's privacy settings. Ensure the platform's domain is not blocked from storing data. Clear browser storage and retry. |
| Dark mode flickers briefly on load | Theme is applied after the initial page render | This is a known cosmetic issue during page loads. It does not affect functionality. |
| Colors do not match the selected preset | A previous custom color selection is overriding the preset | Re-select the desired preset from the theme settings. This clears any custom color override. |
| Custom colors are not saving | Invalid hex color values | Ensure all three color values are valid 6-digit hex strings starting with `#` (e.g., `#1A5276`). |
| Different users see different themes | Theme preferences are per-browser | This is expected behavior. Each user's preference is independent. Coordinate with users if a consistent appearance is required. |

## What's Next?

- [App Settings](app-settings) — Configure organization name, currency, scenarios, and governance structure
- [System Administration](system-administration) — Monitor platform health and manage database connections
- [Troubleshooting](troubleshooting) — Resolve common platform issues
