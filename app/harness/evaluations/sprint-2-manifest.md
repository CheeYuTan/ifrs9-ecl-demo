# Sprint 2 Interaction Manifest — User Guide Workflow Steps 1-4 (Iteration 5)

**Sprint**: 2 (Docs Transformation)
**Iteration**: 5 (final)
**Date**: 2026-04-04
**Test Method**: HTTP verification (curl, port 3000) + static build verification + source markdown audit + sitemap check
**Build**: `npm run build` — 0 errors, 0 warnings (verified fresh build)
**Dev Server**: http://localhost:3000/docs/ (Docusaurus dev server, confirmed running on port 3000)

## Pages Tested

| Page | URL | HTTP | Lines | Target | Status |
|------|-----|------|-------|--------|--------|
| Step 1: Create Project | /docs/user-guide/step-1-create-project | 200 | 151 | ≥150 | TESTED |
| Step 2: Data Processing | /docs/user-guide/step-2-data-processing | 200 | 153 | ≥150 | TESTED |
| Step 3: Data Control | /docs/user-guide/step-3-data-control | 200 | 153 | ≥150 | TESTED |
| Step 4: Satellite Models | /docs/user-guide/step-4-satellite-model | 200 | 176 | ≥150 | TESTED |

## Regression Check — Sprint 1 Pages

| Page | URL | HTTP | Status |
|------|-----|------|--------|
| Overview | /docs/overview | 200 | TESTED |
| Quick Start | /docs/quick-start | 200 | TESTED |
| Workflow Overview | /docs/user-guide/workflow-overview | 200 | TESTED |

## Rendered HTML Element Counts (Source Audit)

| Page | Admonitions | Tables | H2 | H3 | Images | Status |
|------|-------------|--------|----|----|--------|--------|
| Step 1 | 6 | 3 | 7 | 5 | 1 | TESTED |
| Step 2 | 8 | 4 | 5 | 7 | 2 | TESTED |
| Step 3 | 7 | 5 | 5 | 5 | 2 | TESTED |
| Step 4 | 7 | 3 | 5 | 7 | 2 | TESTED |

## Required Sections Audit (per User Guide template)

| Section | Step 1 | Step 2 | Step 3 | Step 4 |
|---------|--------|--------|--------|--------|
| Frontmatter (title, description, sidebar_position) | TESTED | TESTED | TESTED | TESTED |
| Prerequisites (:::info) | TESTED | TESTED | TESTED | TESTED |
| What You'll Do | TESTED | TESTED | TESTED | TESTED |
| Step-by-Step Instructions | TESTED | TESTED | TESTED | TESTED |
| Understanding the Results | TESTED | TESTED | TESTED | TESTED |
| Tips & Best Practices | TESTED | TESTED | TESTED | TESTED |
| What's Next? | TESTED | TESTED | TESTED | TESTED |

## Navigation & Cross-References

| Element | Action | Result | Status |
|---------|--------|--------|--------|
| Sidebar: Getting Started (2 items) | Render | overview, quick-start | TESTED |
| Sidebar: User Guide (18 items) | Render | All workflow steps + feature pages | TESTED |
| Sidebar: Admin Guide (collapsed) | Render | Present | TESTED |
| Sidebar: Developer Reference (collapsed) | Render | Present | TESTED |
| Navbar: Color Mode Toggle | Button | Present | TESTED |
| Navbar: User Guide link | Link | href="/docs/overview" | TESTED |
| Navbar: Admin Guide link | Link | href="/docs/admin-guide/setup-installation" | TESTED |
| Navbar: Developer Reference link | Link | href="/docs/developer/architecture" | TESTED |
| Step 1 → Step 2 (What's Next) | Link | step-2-data-processing (200) | TESTED |
| Step 2 → Step 3 (What's Next) | Link | step-3-data-control (200) | TESTED |
| Step 3 → Step 4 (What's Next) | Link | step-4-satellite-model (200) | TESTED |
| Step 4 → Step 5 (What's Next) | Link | step-5-model-execution (200) | TESTED |
| Step 1 ← Quick Start (Prereq) | Link | /docs/quick-start (200) | TESTED |
| Step 2 ← Step 1 (Prereq) | Link | step-1-create-project (200) | TESTED |
| Step 3 ← Step 2 (Prereq) | Link | step-2-data-processing (200) | TESTED |
| Step 4 ← Step 3 (Prereq) | Link | step-3-data-control (200) | TESTED |
| Step 4: Admin Guide cross-ref | Link | admin-guide/model-configuration (200) | TESTED |
| Pagination: All 4 pages | Nav | prev+next present | TESTED |
| Sitemap: All 4 step pages | XML | Present in sitemap.xml | TESTED |

## Images

| Image | Page | File Exists | Type | Status |
|-------|------|-------------|------|--------|
| step-1-create-project.png | Step 1 | YES | Placeholder | TESTED |
| step-2-stage-distribution.png | Step 2 | YES | Placeholder | TESTED |
| portfolio-dashboard.png | Step 2 | YES | Real screenshot (248KB) | TESTED |
| step-3-data-control.png | Step 3 | YES | Placeholder | TESTED |
| step-3-approval-form.png | Step 3 | YES | Placeholder | TESTED |
| step-4-run-pipeline.png | Step 4 | YES | Placeholder | TESTED |
| step-4-model-comparison.png | Step 4 | YES | Placeholder | TESTED |

Note: 6 of 7 images are placeholder grey rectangles. Known limitation — real screenshots to be captured during documentation batch.

## Persona Compliance (Zero Violations)

| Check | Step 1 | Step 2 | Step 3 | Step 4 |
|-------|--------|--------|--------|--------|
| No Python/JSON code blocks | PASS | PASS | PASS | PASS |
| No API endpoints | PASS | PASS | PASS | PASS |
| No test file references | PASS | PASS | PASS | PASS |
| Business-language only | PASS | PASS | PASS | PASS |

## IFRS 9 Terminology Audit

| Term | Step 1 | Step 2 | Step 3 | Step 4 |
|------|--------|--------|--------|--------|
| ECL | 13 | 9 | 5 | 4 |
| PD | — | 11 | 5 | 3 |
| LGD | — | — | 2 | 3 |
| EAD | — | — | — | — |
| SICR | — | 2 | — | — |
| Stage 1/2/3 | — | 13 | 2 | — |
| IFRS 9 | 3 | 3 | 1 | 1 |
| Incorrect terms found | 0 | 0 | 0 | 0 |

No instances of incorrect generic terms ("risk score", "loss amount", "loan balance", "risk category").

## Iteration 2 Additions Verified (Carried Forward)

| Addition | Page | Description | Status |
|----------|------|-------------|--------|
| Resuming an Existing Project | Step 1 | 5-step subsection for resuming in-progress projects | TESTED |
| Common Project ID Patterns | Step 1 | Tip with 3 naming convention examples | TESTED |
| State-transition narrative | Step 1 | Pending → Completed → Rejected → rework cycle | TESTED |
| Reading the Charts | Step 2 | Step 6 explaining bar heights, colors, drill-down, anomaly patterns | TESTED |
| Bookmark Key Observations | Step 2 | Tip admonition | TESTED |
| Zero or Missing Values | Step 2 | Caution admonition on PD=0 and EIR=0 implications | TESTED |
| 3-decision framework | Step 3 | Decision 1 (Critical?) → Decision 2 (DQ Score?) → Decision 3 (Explainable?) | TESTED |
| Audit Expectations | Step 3 | Caution admonition on auditor expectations | TESTED |

## Dark Mode

| Check | Result | Status |
|-------|--------|--------|
| Dark mode config | `respectPrefersColorScheme: true` in docusaurus.config.ts | TESTED |
| Color mode toggle | Present in navbar | TESTED |

## Build Verification

| Check | Result | Status |
|-------|--------|--------|
| `npm run build` | 0 errors, 0 warnings | TESTED |
| All internal links resolve | Verified via build + HTTP 200 checks | TESTED |
| Sidebar position ordering | Sequential (2, 3, 4, 5) for steps 1-4 | TESTED |
| Static build output | Generated to docs_site/ | TESTED |
| Sitemap includes all 4 pages | Verified in sitemap.xml | TESTED |

## Summary

| Status | Count |
|--------|-------|
| **TESTED** | **89** |
| **BUG** | **0** |
| **SKIPPED** | **0** |
| **PENDING** | **0** |
