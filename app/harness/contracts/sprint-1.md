# Sprint 1 Contract: Foundation — Restructure & Getting Started

## Acceptance Criteria

### Directory Restructure
- [ ] New directory structure: `docs/user-guide/`, `docs/admin-guide/`, `docs/developer/`
- [ ] Old flat guide files relocated to proper persona directories or removed
- [ ] Stub pages created for ALL sidebar entries so sidebar links resolve

### Sidebar Configuration
- [ ] `sidebars.ts` rewritten with persona-based categories matching spec
- [ ] Getting Started section: overview, quick-start
- [ ] User Guide category with workflow-overview + step stubs + feature page stubs
- [ ] Admin Guide category with all 9 page stubs
- [ ] Developer Reference category with all 5 page stubs

### Navigation
- [ ] `docusaurus.config.ts` navbar has persona links (User Guide, Admin Guide, Developer Reference)
- [ ] Footer updated with persona-organized links
- [ ] Homepage CTA points to correct overview path

### Content Pages (3 real pages this sprint)
- [ ] `overview.md` — business-language, zero code, explains IFRS 9 ECL platform
- [ ] `quick-start.md` — first login, navigating the app, creating first project, screenshot placeholders
- [ ] `user-guide/workflow-overview.md` — 8-step ECL workflow with visual diagram, links to step pages

### Build Verification
- [ ] `cd docs-site && npm run build` succeeds with 0 errors
- [ ] No broken internal links

## Test Plan
- Build: `cd docs-site && npm run build` — 0 errors
- Verify sidebar renders all categories and pages

## Production Readiness Items
- Clean persona-based directory structure
- No broken links in build output
