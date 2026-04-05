# IFRS 9 ECL Permission Model — Progress

## Quality Target: 9.5/10

## Project Summary
Two-layer permission model: existing RBAC (Layer 1) + per-project roles (Layer 2). Both layers must be satisfied. Admin overrides all. Anonymous dev mode bypasses all.

## Sprint Status

| Sprint | Feature | Status | Score | Tests | Iterations | Decision |
|--------|---------|--------|-------|-------|------------|----------|
| 1 | Backend Permission Engine | PENDING | — | — | 0 | — |
| 2 | API Layer + Route Protection | PENDING | — | — | 0 | — |
| 3 | Frontend Permission Infrastructure | PENDING | — | — | 0 | — |
| 4 | Frontend UI Integration | PENDING | — | — | 0 | — |
| 5 | Integration Testing + Deployment | PENDING | — | — | 0 | — |

## Baseline
- Tests at start: 4108 passing

## Key Files
- Spec: `harness/spec.md`
- State: `harness/state.json`
- Existing RBAC: `governance/rbac.py`
- Existing auth: `middleware/auth.py`
- Existing workflow: `domain/workflow.py`
- Existing audit: `domain/audit_trail.py`
