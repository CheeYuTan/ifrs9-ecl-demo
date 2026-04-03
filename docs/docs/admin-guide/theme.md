---
sidebar_position: 6
title: Theme
---

# Theme

Customise the application's appearance with light/dark mode and colour presets.

## Appearance Mode

Toggle between **Light** and **Dark** mode. The selected mode is stored client-side (browser localStorage) and persists across sessions.

## Colour Presets

Eight pre-built colour themes:

| Preset | Primary Colour |
|--------|---------------|
| Emerald | Green tones |
| Ocean Blue | Blue tones |
| Royal Purple | Purple tones |
| Rose | Pink tones |
| Amber | Orange/amber tones |
| Indigo | Deep blue tones |
| Cyan | Teal tones |
| Sunset | Warm gradient tones |

Click any preset to apply it immediately.

## Custom Colour

Enter a hex colour code or use the colour picker to define a custom brand colour. The system automatically generates:

- **Brand Dark** — Primary colour with −20 brightness
- **Brand Light** — Primary colour with +90 brightness

## Live Preview

A preview panel shows how the selected theme looks on:

- Primary buttons
- Accent text
- Highlighted cards

Changes take effect immediately across the application.

:::note
Theme settings are stored in the browser only and do not affect other users. They are not included in the admin configuration export/import.
:::

## Further Reading

For technical details on how the theme system works across components and pages, see:

- [Light & Dark Mode](/admin-guide/theming/light-dark-mode) — How the dual-theme system works, CSS custom properties, and design patterns
- [Core Component Theming](/admin-guide/theming/core-components) — How the 19 shared components handle light/dark mode
- [Workflow Page Theming](/admin-guide/theming/workflow-pages) — Theme audit results for the 8 ECL workflow pages
- [Admin & Secondary Page Theming](/admin-guide/theming/admin-secondary-pages) — Theme audit for GL Journals, Admin, Hazard Models, Approval Workflow, and more
- [Data Mapping Theming](/admin-guide/theming/data-mapping-theming) — Theme audit for the Data Mapping module
