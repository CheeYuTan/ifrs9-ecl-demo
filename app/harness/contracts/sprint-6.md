# Sprint 6 Contract: Admin Guide — Complete (9 Pages)

## Overview

All 9 admin guide pages exist with substantial content. This sprint ensures persona compliance (no developer code in admin pages), template consistency, cross-referencing, and quality to meet the 9.5/10 target.

## Acceptance Criteria

### Persona Compliance (Critical)
- [ ] No Python code snippets in any admin guide page
- [ ] No TypeScript/JavaScript code snippets in any admin guide page
- [ ] No CSS/Tailwind code examples in any admin guide page
- [ ] No SQL DDL statements (CREATE TABLE) in admin guide pages
- [ ] API endpoints shown with plain-language descriptions only where relevant
- [ ] JSON config examples allowed ONLY for admin-facing configuration format

### Template Compliance
- [ ] Every page has frontmatter with sidebar_position, title, description
- [ ] Every page has "Who Should Read This" info admonition
- [ ] Every page uses admonitions (tip, warning, caution, danger) appropriately
- [ ] Tables used for structured data presentation
- [ ] Every page has a "What's Next?" section with cross-references

### Content Completeness
- [ ] 6.1 Setup & Installation — deployment, app.yaml, environment vars, first-run
- [ ] 6.2 Data Mapping — Unity Catalog wizard, column mapping, required tables
- [ ] 6.3 Model Configuration — satellite models, SICR thresholds, LGD assumptions
- [ ] 6.4 App Settings — organization config, scenarios, governance
- [ ] 6.5 Jobs & Pipelines — job types, triggering, monitoring, period-end close
- [ ] 6.6 Theme Customization — presets, dark mode, organizational defaults
- [ ] 6.7 System Administration — health checks, token refresh, audit trail
- [ ] 6.8 User Management — RBAC, roles, permissions, approval workflow
- [ ] 6.9 Troubleshooting — common issues organized by subsystem

### Build Verification
- [ ] `npm run build` succeeds with 0 errors
- [ ] Deployed to `docs_site/`

## Pages Requiring Changes

| Page | Issues | Action |
|------|--------|--------|
| data-mapping.md | JSON request/response bodies, API-centric steps | Rewrite to admin wizard walkthrough |
| model-configuration.md | JSON config OK, but API override example dev-focused | Light cleanup |
| app-settings.md | SQL DDL, heavy JSON, dev-facing API reference | Major rewrite — settings-focused |
| theme-customization.md | TypeScript, CSS, JavaScript throughout | Major rewrite — admin perspective |
| system-administration.md | JSON responses OK, developer-ish tone | Light cleanup, add cross-refs |
| user-management.md | Python code snippets, SQL DDL | Rewrite to remove code |
| troubleshooting.md | JSON config snippets, grep commands | Light cleanup |
| setup-installation.md | Comprehensive already, YAML OK | Light cleanup, add What's Next |
| jobs-pipelines.md | JSON request/response bodies | Moderate cleanup |

## Test Plan
- Build: `cd docs-site && npm run build` with 0 errors
- Links: All internal cross-references resolve (onBrokenLinks: 'throw')
- Persona audit: No Python/TS/CSS/SQL code blocks in admin pages
