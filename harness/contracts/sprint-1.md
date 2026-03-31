# Sprint 1 Contract: ECL Attribution Analysis Frontend
STATUS: AGREED

## Scope
Build the Attribution Analysis frontend page with waterfall chart visualization, 
period-over-period comparison, and stage-level breakdown. The backend engine, 
API routes, and API client already exist. This sprint adds the visual layer.

## Acceptance Criteria
1. [ ] New `Attribution.tsx` page with waterfall chart (recharts BarChart)
2. [ ] Stage-level breakdown table showing all 10 IFRS 7.35I components
3. [ ] Reconciliation status card showing materiality check
4. [ ] "Compute Attribution" button to trigger fresh computation
5. [ ] Attribution history list with date selector
6. [ ] Data gap indicators when components are unavailable
7. [ ] Sidebar navigation entry under "Analytics" group
8. [ ] App.tsx routing for the attribution view
9. [ ] Dark mode support consistent with existing pages
10. [ ] Loading/error states on all async operations
11. [ ] Frontend builds successfully (`npm run build`)
12. [ ] All existing tests pass (0 new failures)

## API Contract (already implemented)
- `GET /api/data/attribution/{project_id}` → full attribution with waterfall
- `POST /api/data/attribution/{project_id}/compute` → recompute
- `GET /api/data/attribution/{project_id}/history` → historical attributions

## Test Plan
- Existing unit tests for attribution engine (test_attribution.py) must still pass
- Frontend build must succeed with zero errors

## Production Readiness Items
- Loading skeletons on data fetch
- Error boundary wrapping
- Dark mode via Tailwind dark: classes and CSS variables
