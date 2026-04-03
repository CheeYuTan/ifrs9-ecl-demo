# Context Reset 3 — User Feedback: Deep Quality Push

## User's Specific Feedback (MUST FIX ALL)

### i. Drill-down chart ordering is wrong
Credit grade bars (BBB, A, BB, B, AA, CCC, AAA) are in random order. They MUST be in logical order:
- Credit grades: AAA → AA → A → BBB → BB → B → CCC (best to worst)
- Age groups: ascending order
- DPD buckets: ascending order
- Any categorical axis must have a logical sort order

### ii. Portfolio by product missing drill-down
The user expected ALL charts to have drill-down capability, but portfolio-by-product does not. Every chart that shows aggregated data should support clicking to drill into the next dimension.

### iii. Data generation vs data mapping
The "Full Pipeline" job generates synthetic data. In reality, customers bring their OWN data. The app should use data mapping (Admin → Data Sources) to map customer tables/columns to the expected schema, NOT generate data. The data generation scripts are for DEMO purposes only — the app itself should work with any customer's loan tape via configurable column mapping.

### iv. Model pipeline failed
The satellite model + ECL pipeline failed (aggregate_models task failed). This was NOT caught because no proper evaluator testing was done. The harness REQUIRES exhaustive end-to-end testing — every button clicked, every workflow completed, every pipeline run verified.

## What's Been Built (10 sprints so far)
1. Modularize Backend (13 domain + 16 route modules)
2. Real Backtesting Engine (calibration tests, LGD from data)
3. RBAC Enforcement (auth middleware, permission deps)
4. Attribution Waterfall (no hardcoded fallbacks)
5. Model Registry (model cards, sensitivity, recalibration)
6. Validation Rules (23-rule engine)
7. Testing & Polish (233 tests)
8. Installer (install.sh, deploy.sh, .env.example)
9. Documentation (16 HTML pages, screenshots)
10. Demo Slides (Google Slides deck)

## Remaining Work (from user feedback)
- [ ] Fix drill-down chart ordering (credit grade, age, DPD — all categorical axes)
- [ ] Add drill-down to portfolio-by-product chart
- [ ] Fix model pipeline failure (aggregate_models task)
- [ ] Run FULL end-to-end evaluator testing with live app
- [ ] Verify every single workflow step completes successfully
- [ ] Ensure data mapping (not data generation) is the primary flow

## Architecture
- backend.py is a re-export shim from 13 domain modules
- React frontend at app/frontend/, built to app/static/
- FastAPI serves SPA + docs + API
- Docs embedded at /docs route, Swagger at /api/swagger

## Files to Read
1. harness/state.json
2. harness/progress.md  
3. app/frontend/src/pages/ — chart components with drill-down
4. app/frontend/src/components/ — reusable chart components
5. scripts/03a_aggregate_models.py — the failing pipeline task
6. app/admin_config.py — data mapping configuration
