# Context Reset 2 — Embedding Docs + Deep Quality Push

## Current State
- **Phase**: BUILD_AGENT
- **Sprints Completed**: 10 (modularization, backtesting, RBAC, attribution, model registry, validation rules, testing, installer, docs, slides)
- **Quality Target**: 9.0/10 (NOT YET SCORED — previous sprints did not run evaluator with live app)
- **Status**: User wants docs embedded in the app itself with screenshots/GIFs, and a deep quality push

## What Exists
- 233 passing tests (150 new), 2 pre-existing failures
- 13 domain modules + 16 route modules + middleware
- Static HTML docs in `docs/` (16 pages) — NOT embedded in app
- 176 screenshots in `screenshots/`
- install.sh, deploy.sh, .env.example
- Demo deck on Google Slides

## What's Missing / Needs Work
1. **Docs served by the app** — Add `/docs` route that serves the HTML docs site from within the FastAPI app, so customers see docs at `https://app-url/docs`
2. **Screenshots embedded in docs** — Copy relevant screenshots into docs, reference them in guide pages
3. **GIF capture** — Record key workflows as GIFs for docs
4. **Evaluator with live app** — Start the app, use agent-browser to test, capture screenshots, score properly
5. **Production readiness gaps** — Global error handler middleware, CORS, rate limiting
6. **Code structure audit** — Some files still exceed 200 lines (hazard.py 634, reports.py 657)
7. **Wire RBAC into routes** — Auth dependencies created but not injected into route handlers

## Architecture Decisions
- `backend.py` is a re-export shim (180 lines) — all imports work unchanged
- sys.path-based imports (bare `import backend`)
- Tests use `patch("backend.func")` which works via the shim
- scipy added as dependency for calibration tests
- FastAPI app at `app/app.py`, routes in `app/routes/`

## Remaining Spec Items
- [ ] Embed docs site in the Databricks App (serve at /docs)
- [ ] Add screenshots/GIFs to doc pages
- [ ] Wire RBAC dependencies into state-changing routes
- [ ] Add global error handler middleware
- [ ] Split oversized files (hazard.py, reports.py)
- [ ] Run evaluator with live app + browser testing
- [ ] Final integration evaluation meeting 9.0 target

## Exact Next Step
1. Add a `/docs` route to app.py that serves the static HTML docs
2. Copy key screenshots into docs/static/img/
3. Wire RBAC `require_permission()` into sign-off, overlay, and admin routes
4. Add global error handler middleware
5. Start the app and run evaluator via web-devloop-tester

## Files to Read on Resume
1. `harness/state.json`
2. `harness/progress.md`
3. `harness/spec.md`
4. `app/app.py` (120 lines — main entry)
5. `app/routes/projects.py` (sign-off route needs RBAC)
6. `app/middleware/auth.py` (RBAC dependencies)
7. `docs/index.html` (docs landing page)
