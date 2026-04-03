# Sprint 3 Contract: RBAC Enforcement & Governance
STATUS: AGREED

## Scope
Add real RBAC enforcement to all state-changing API endpoints. Implement segregation of duties (user who ran simulation cannot sign off). Add immutability for signed-off ECL runs with cryptographic hash verification.

## Acceptance Criteria
1. [ ] Auth middleware extracts user identity from request headers or Databricks OAuth
2. [ ] All state-changing endpoints check user role before allowing action
3. [ ] Segregation of duties: simulation runner cannot sign off same project
4. [ ] Signed-off projects reject all mutations with 403
5. [ ] SHA-256 hash of ECL results stored at sign-off, verification endpoint available
6. [ ] Audit log entries include authenticated user identity
7. [ ] Unit tests for RBAC middleware and permission checks
