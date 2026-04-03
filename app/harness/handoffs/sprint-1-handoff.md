# Sprint 1 Handoff: Foundation — Restructure & Getting Started

## What Was Built

### Directory Restructure
- Created persona-based directory structure: `docs/user-guide/`, `docs/admin-guide/`, `docs/developer/`
- Removed old flat structure: `docs/guides/` directory (8 files), `docs/getting-started.md`, `docs/architecture.md`, `docs/faq.md`
- Created 30 stub pages across all persona directories to support the full sidebar

### Sidebar Configuration (sidebars.ts)
- Rewrote from flat single-category layout to 4 persona-based categories:
  - **Getting Started** (2 pages): overview, quick-start
  - **User Guide** (18 pages): workflow-overview + 8 step pages + 9 feature pages
  - **Admin Guide** (9 pages): setup through troubleshooting
  - **Developer Reference** (5 pages): architecture through testing

### Navigation (docusaurus.config.ts)
- Navbar: 3 persona links (User Guide, Admin Guide, Developer Reference)
- Footer: 4 columns organized by persona with key page links
- Homepage CTA updated to point to overview

### Content Pages (3 fully written pages)
1. **overview.md** — "What is IFRS 9 ECL?" — business-language, zero code, explains platform capabilities, user roles, key stats
2. **quick-start.md** — "Your First ECL Project" — login, create project, run simulation, sign off — with screenshot placeholders referencing existing images
3. **user-guide/workflow-overview.md** — "The 8-Step ECL Workflow" — ASCII flow diagram, step summaries with descriptions and links, post-workflow actions, tips

### Build & Deploy
- `npm run build` succeeds with 0 errors
- Built output deployed to `docs_site/`

## How to Test

```bash
# Build the docs site
cd docs-site && npm run build

# Serve locally
npm run serve
# Navigate to http://localhost:3000/docs/
```

**Pages to verify:**
- http://localhost:3000/docs/overview — full content, business language, no code
- http://localhost:3000/docs/quick-start — step-by-step with screenshots
- http://localhost:3000/docs/user-guide/workflow-overview — ASCII diagram, step links
- Sidebar: all 4 categories visible, all pages link correctly
- Navbar: User Guide, Admin Guide, Developer Reference links work
- Footer: all 4 columns with correct links

## Test Results

```
npm run build: SUCCESS — 0 errors, 0 warnings
All 34 pages generated successfully
```

## Known Limitations
- Stub pages contain placeholder text ("This page will be completed in Sprint N")
- Screenshots reference existing images in `/img/guides/` — not all pages have matching screenshots yet
- Homepage features section still shows stock Docusaurus content (will be redesigned in Sprint 8)

## Files Changed

### New Files (30)
- `docs/quick-start.md`
- `docs/user-guide/workflow-overview.md`
- `docs/user-guide/step-1-create-project.md` through `step-8-sign-off.md` (8 files)
- `docs/user-guide/model-registry.md`, `backtesting.md`, `regulatory-reports.md`, `gl-journals.md`, `approval-workflow.md`, `attribution.md`, `markov-hazard.md`, `advanced-features.md`, `faq.md` (9 files)
- `docs/admin-guide/setup-installation.md` through `troubleshooting.md` (9 files)
- `docs/developer/architecture.md` through `testing.md` (5 files)

### Modified Files (3)
- `docs/overview.md` — complete rewrite for business audience
- `sidebars.ts` — persona-based category structure
- `docusaurus.config.ts` — navbar + footer persona links

### Deleted Files (12)
- `docs/getting-started.md` (replaced by `quick-start.md`)
- `docs/architecture.md` (moved to `developer/architecture.md`)
- `docs/faq.md` (moved to `user-guide/faq.md`)
- `docs/guides/core-workflow-data.md`
- `docs/guides/simulation-engine.md`
- `docs/guides/model-analytics.md`
- `docs/guides/operational-governance.md`
- `docs/guides/ecl-engine.md`
- `docs/guides/domain-logic-core.md`
- `docs/guides/domain-logic-analytical.md`
- `docs/guides/frontend-testing.md`
- `src/pages/markdown-page.md`
