---
sidebar_position: 4
title: Admin & Secondary Page Theming
---

# Admin & Secondary Page Theming

This guide covers the theme audit results for the 10 admin and secondary workflow pages audited in Sprint 3. These pages include GL Journals, Admin settings, Hazard Models, Advanced Features, Model Registry, Backtesting, Markov Chains, Approval Workflow, Attribution, and Regulatory Reports.

## Pages Audited

| Page | File | Violations Found | Status |
|------|------|-----------------|--------|
| GL Journals | `GLJournals.tsx` | 3 fixes | PASS |
| Admin | `Admin.tsx` | 3 fixes | PASS |
| Hazard Models | `HazardModels.tsx` | 4 fixes | PASS |
| Advanced Features | `AdvancedFeatures.tsx` | 3 fixes | PASS |
| Model Registry | `ModelRegistry.tsx` | 5 fixes | PASS |
| Backtesting | `Backtesting.tsx` | 1 fix | PASS |
| Markov Chains | `MarkovChains.tsx` | 1 fix | PASS |
| Approval Workflow | `ApprovalWorkflow.tsx` | 8 fixes | PASS |
| Attribution | `Attribution.tsx` | 0 (already clean) | PASS |
| Regulatory Reports | `RegulatoryReports.tsx` | 0 (already clean) | PASS |

**Total: 28 violations fixed across 8 files.** Two files (Attribution, Regulatory Reports) were already fully compliant.

## GL Journals

| Light Mode | Dark Mode |
|:---:|:---:|
| ![GL Journals light](/img/theme-audit/gl-journals-light.png) | ![GL Journals dark](/img/theme-audit/gl-journals-dark.png) |

The GL Journals page displays journal entry reconciliation tables. Three violations were fixed:

1. **Totals row background** — bare `bg-slate-800` on the totals row was invisible in light mode. Added a light-mode pair.
2. **Hover text on interactive elements** — bare `hover:text-slate-700` missing dark-mode hover pair.
3. **Row hover background** — bare `hover:bg-slate-200` missing dark-mode pair.

## Admin Settings

| Light Mode | Dark Mode |
|:---:|:---:|
| ![Admin light](/img/theme-audit/admin-light.png) | ![Admin dark](/img/theme-audit/admin-dark.png) |

The Admin page contains configuration tabs for system settings. Three violations were fixed:

1. **Tab bar border** — `border-white/60` was invisible in light mode. Replaced with `border-gray-200 dark:border-white/60`.
2. **Tab hover background** — `hover:bg-white/80` produced no visible hover in light mode.
3. **Tab hover text** — bare `hover:text-slate-700` missing dark-mode pair.

## Hazard Models

| Light Mode | Dark Mode |
|:---:|:---:|
| ![Hazard Models light](/img/theme-audit/hazard-models-light.png) | ![Hazard Models dark](/img/theme-audit/hazard-models-dark.png) |

The Hazard Models page displays term structure data and model comparison views. Four violations were fixed:

1. **Tab hover background** — `hover:bg-white/50` without light pair.
2. **Tab hover text** — bare `hover:text-slate-700` without dark pair.
3. **Active tab background** — `bg-white/50` without light pair.
4. **Row border** (BUG-S3-001) — `border-slate-50` was nearly invisible against white backgrounds. Changed to `border-slate-100 dark:border-slate-700`.

### BUG-S3-001: The `slate-50` Scanner Gap

During Sprint 3 evaluation, a previously undetected pattern was discovered: `border-slate-50`, `bg-slate-50`, and `ring-slate-50` classes without `dark:` pairs. These are nearly white on white backgrounds in light mode — technically "visible" but with insufficient contrast.

This led to the creation of a **17th scanner** (`find_bare_slate_50`) added to the regression test suite. The scanner discovered 4 additional violations beyond the initial report:

- `ModelRegistry.tsx`: Draft status badge `bg-slate-50`
- `ApprovalWorkflow.tsx`: Normal priority badge, inactive status badge, and pending request hover — all using `bg-slate-50`

## Model Registry

| Light Mode | Dark Mode |
|:---:|:---:|
| ![Model Registry light](/img/theme-audit/models-light.png) | ![Model Registry dark](/img/theme-audit/models-dark.png) |

Five violations were fixed in the Model Registry:

1. **Close button hover** (x2) — `hover:bg-slate-100` on modal close buttons without dark hover pair.
2. **Performance metrics gradient** — gradient header missing dark-mode pair for visibility.
3. **Border visibility** — a border was invisible in one mode.
4. **Draft badge** — `bg-slate-50` draft status badge invisible against light backgrounds in dark mode. Added `dark:bg-slate-800`.

## Approval Workflow

| Light Mode | Dark Mode |
|:---:|:---:|
| ![Approval light](/img/theme-audit/approval-light.png) | ![Approval dark](/img/theme-audit/approval-dark.png) |

The Approval Workflow had the most violations of any page in this sprint — 8 total:

1. **Close button hover** — `hover:bg-slate-100` without dark pair
2. **Tab hover text** — `hover:text-slate-700` without dark pair
3. **XCircle icon** — icon colour missing dark-mode pair
4. **Border divider** — section divider invisible in one mode
5. **Priority badge** — Normal priority `bg-slate-50` invisible in dark mode
6. **Status badge** — Inactive status `bg-slate-50` invisible in dark mode
7. **Pending request hover** — `hover:bg-slate-50` invisible in dark mode
8. Additional hover state fixes

## Backtesting & Markov Chains

| Backtesting Light | Markov Chains Light |
|:---:|:---:|
| ![Backtesting](/img/theme-audit/backtesting-light.png) | ![Markov Chains](/img/theme-audit/markov-light.png) |

Both pages required minimal fixes:

- **Backtesting**: 1 fix — `hover:bg-slate-100` on a close button without dark pair.
- **Markov Chains**: 1 fix — `hover:text-slate-700` on an inactive tab without dark pair.

## Advanced Features

| Light Mode | Dark Mode |
|:---:|:---:|
| ![Advanced light](/img/theme-audit/advanced-light.png) | ![Advanced dark](/img/theme-audit/advanced-dark.png) |

Three violations fixed, all in the tab navigation:

1. `hover:bg-white/50` — tab hover background without light pair
2. `hover:text-slate-700` — tab hover text without dark pair
3. `bg-white/50` — active tab background without light pair

## Testing

**160 automated tests** (16 scanners x 10 files) verify zero theme violations across all admin and secondary pages, plus the new 17th scanner (`find_bare_slate_50`) was added to the Sprint 1 regression suite.

```bash
# Run Sprint 3 theme tests
pytest tests/unit/test_theme_audit_sprint3.py -v

# Run all theme tests (Sprint 1 + 2 + 3 regression)
pytest tests/unit/test_theme_audit_sprint1.py tests/unit/test_theme_audit_sprint2.py tests/unit/test_theme_audit_sprint3.py -v
```

## Troubleshooting

### Badge text is invisible in dark mode

Badges using `bg-slate-50` (very light grey) need a dark-mode override:

```diff
- <span class="bg-slate-50 text-slate-600 ...">Draft</span>
+ <span class="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 ...">Draft</span>
```

### Tab borders disappear in light mode

Tab navigation using `border-white/N` opacity borders are invisible on white backgrounds:

```diff
- <div class="border-b border-white/60">
+ <div class="border-b border-gray-200 dark:border-white/60">
```
