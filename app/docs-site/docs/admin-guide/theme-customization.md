---
sidebar_position: 6
title: "Theme Customization"
description: "Customizing the platform appearance with color presets, dark mode, and brand colors."
---

# Theme Customization

The IFRS 9 ECL Platform provides a flexible theming system that supports light and dark modes, eight built-in color presets, and fully custom brand colors. Theme preferences are persisted per-user in the browser and applied instantly without a page reload.

:::info Who Should Read This
System administrators responsible for platform appearance, and developers extending the frontend with custom components that need to respect the active theme.
:::

## Theme Configuration Model

The theme system is driven by a `ThemeConfig` object with three properties:

| Property | Type | Description |
|----------|------|-------------|
| `mode` | `'light' \| 'dark'` | Controls whether the UI renders in light or dark mode. |
| `colors` | `ThemeColors` | An object with `brand`, `brandDark`, and `brandLight` hex values. |
| `preset` | `string` | The name of the active preset (e.g., `'emerald'`), or `'custom'` for user-defined colors. |

The `ThemeColors` interface defines the three color channels used throughout the platform:

```typescript
interface ThemeColors {
  brand: string;      // Primary brand color (buttons, links, active states)
  brandDark: string;  // Darker variant (hover states, focused elements)
  brandLight: string; // Light variant (backgrounds, subtle highlights)
}
```

The default configuration ships with:

```typescript
const DEFAULT_THEME: ThemeConfig = {
  mode: 'light',
  colors: PRESETS.emerald,
  preset: 'emerald',
};
```

## Built-in Color Presets

Eight professionally designed color presets are available out of the box. Each preset defines a harmonized triad of brand, dark, and light variants.

| Preset | Brand | Dark | Light | Use Case |
|--------|-------|------|-------|----------|
| **emerald** | `#00D09C` | `#00B386` | `#E6FBF5` | Default. Finance-oriented green conveying stability. |
| **blue** | `#3B82F6` | `#2563EB` | `#EFF6FF` | Corporate blue. Suitable for conservative institutions. |
| **purple** | `#8B5CF6` | `#7C3AED` | `#F5F3FF` | Modern aesthetic for innovation-focused teams. |
| **rose** | `#F43F5E` | `#E11D48` | `#FFF1F2` | Bold and attention-grabbing. Use with caution in audit contexts. |
| **amber** | `#F59E0B` | `#D97706` | `#FFFBEB` | Warm tone. Works well for warning-oriented dashboards. |
| **indigo** | `#6366F1` | `#4F46E5` | `#EEF2FF` | Deep blue-purple. Strong contrast for data-dense views. |
| **cyan** | `#06B6D4` | `#0891B2` | `#ECFEFF` | Cool tone. Good for analytical and reporting interfaces. |
| **orange** | `#F97316` | `#EA580C` | `#FFF7ED` | Energetic. Useful for development or staging environments. |

To apply a preset programmatically:

```typescript
const { setPreset } = useTheme();
setPreset('blue');
```

## The `useTheme` Hook

All theme operations are accessed through the `useTheme` React hook, exported from `src/lib/theme.tsx`. This hook provides the current theme state and mutation functions.

```typescript
const {
  theme,           // Current ThemeConfig object
  setMode,         // (mode: 'light' | 'dark') => void
  toggleMode,      // () => void — switches between light and dark
  setPreset,       // (preset: string) => void — applies a built-in preset
  setCustomColors, // (colors: ThemeColors) => void — applies custom colors
  isDark,          // boolean — shorthand for theme.mode === 'dark'
} = useTheme();
```

### Setting Mode

Switch between light and dark mode explicitly:

```typescript
setMode('dark');   // Force dark mode
setMode('light');  // Force light mode
toggleMode();      // Toggle from current to opposite
```

### Applying Custom Colors

When the built-in presets do not match your organization's brand guidelines, you can supply arbitrary hex colors:

```typescript
setCustomColors({
  brand: '#1A5276',
  brandDark: '#154360',
  brandLight: '#EBF5FB',
});
```

When custom colors are applied, the `preset` field is automatically set to `'custom'` to distinguish it from the built-in presets.

## LocalStorage Persistence

Theme preferences are persisted in the browser's `localStorage` under the key **`ecl-theme`**. The stored value is a JSON-serialized `ThemeConfig` object.

On application load, the `ThemeProvider` attempts to read from `localStorage`. If a stored configuration exists, it is merged with the default theme to ensure forward compatibility when new fields are added. If no stored configuration is found, or if the stored JSON is malformed, the default emerald light theme is applied.

```
// Example localStorage entry
localStorage.getItem('ecl-theme')
// → '{"mode":"dark","colors":{"brand":"#3B82F6","brandDark":"#2563EB","brandLight":"#EFF6FF"},"preset":"blue"}'
```

To reset a user's theme to defaults, clear the storage key:

```javascript
localStorage.removeItem('ecl-theme');
location.reload();
```

:::caution
Theme preferences are per-browser, per-user. They are not synchronized across devices or stored server-side. If you need organization-wide defaults, configure the `DEFAULT_THEME` constant in `src/lib/theme.tsx`.
:::

## CSS Variables

When the theme changes, three CSS custom properties are updated on the `document.documentElement` (the `html` root element):

| CSS Variable | Source | Example Value |
|-------------|--------|---------------|
| `--color-brand` | `colors.brand` | `#00D09C` |
| `--color-brand-dark` | `colors.brandDark` | `#00B386` |
| `--color-brand-light` | `colors.brandLight` | `#E6FBF5` |

These variables are set via `style.setProperty()` directly on the root element, ensuring they cascade into all components regardless of CSS specificity.

Use them in custom CSS or inline styles:

```css
.custom-header {
  background-color: var(--color-brand);
  border-bottom: 2px solid var(--color-brand-dark);
}

.highlight-panel {
  background-color: var(--color-brand-light);
}
```

## Dark Mode Implementation

Dark mode is implemented via a `dark` CSS class on the root `html` element. When dark mode is active, the class is added; when light mode is active, it is removed.

```javascript
// Internal implementation
if (mode === 'dark') {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}
```

This approach is fully compatible with Tailwind CSS's dark mode variant system. The platform's Tailwind configuration uses `darkMode: 'class'`, which means any utility prefixed with `dark:` will activate when the `dark` class is present on the root `html` element.

## Tailwind CSS Integration

All platform components use Tailwind CSS utility classes that respond to the theme configuration.

### Using Brand Colors in Tailwind

The CSS variables are mapped to Tailwind's color system via the `tailwind.config.js` file. Components can reference brand colors as standard Tailwind utilities:

```html
<!-- These classes resolve to the active theme's brand color -->
<button class="bg-brand hover:bg-brand-dark text-white">
  Run Backtest
</button>

<div class="bg-brand-light border border-brand rounded-lg p-4">
  Highlighted content area
</div>
```

### Dark Mode Variants

Write dark-mode-aware styles using Tailwind's `dark:` prefix:

```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  <h2 class="text-brand dark:text-brand-light">ECL Summary</h2>
</div>
```

### Common Patterns

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Page background | `bg-white` | `dark:bg-gray-900` |
| Card background | `bg-gray-50` | `dark:bg-gray-800` |
| Primary text | `text-gray-900` | `dark:text-gray-100` |
| Secondary text | `text-gray-600` | `dark:text-gray-400` |
| Borders | `border-gray-200` | `dark:border-gray-700` |
| Brand accent | `text-brand` | `dark:text-brand-light` |

## ThemeProvider Setup

The `ThemeProvider` component must wrap the entire application to make the `useTheme` hook available. This is already configured in the platform's root layout, but if you are embedding platform components in another application, ensure the provider is present:

```tsx
import { ThemeProvider } from '@/lib/theme';

function App() {
  return (
    <ThemeProvider>
      {/* All child components can use useTheme() */}
      <YourApplicationLayout />
    </ThemeProvider>
  );
}
```

The provider initializes the theme from `localStorage` on mount, applies it to the DOM, and re-applies on every change. The `useEffect` inside the provider ensures that both the CSS variables and the `dark` class are kept in sync with the React state.

## Organizational Defaults

To change the default theme for all new users in your organization, modify the `DEFAULT_THEME` constant in `frontend/src/lib/theme.tsx`:

```typescript
const DEFAULT_THEME: ThemeConfig = {
  mode: 'dark',               // Organization prefers dark mode
  colors: PRESETS.blue,        // Corporate blue
  preset: 'blue',
};
```

After rebuilding and redeploying the frontend, any user who has not previously customized their theme will see the new defaults. Existing users who have a stored preference in `localStorage` are not affected.

## Troubleshooting Theme Issues

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Theme resets on every page load | `localStorage` is blocked or full | Check browser privacy settings; clear storage and retry. |
| Dark mode flickers on load | Theme is applied after initial render | Ensure `ThemeProvider` is at the root of the component tree, not lazy-loaded. |
| CSS variables not updating | Component uses hardcoded colors | Replace hardcoded hex values with `var(--color-brand)` references. |
| Custom colors not persisting | `setCustomColors` called with invalid hex | Ensure all three color values are valid 6-digit hex strings. |
| Tailwind dark styles not applying | `darkMode` not set to `'class'` in config | Verify `tailwind.config.js` contains `darkMode: 'class'`. |
