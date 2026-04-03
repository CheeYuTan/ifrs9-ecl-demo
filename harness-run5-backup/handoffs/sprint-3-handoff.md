# Sprint 3 Handoff: RBAC Enforcement & Governance

## What Was Built

### Auth Middleware (`app/middleware/auth.py`)
- **User extraction**: Reads `X-Forwarded-User` (Databricks Apps OAuth) or `X-User-Id` (development) headers
- **Permission checking**: `require_permission(action)` FastAPI dependency — returns 403 if role lacks permission
- **Project immutability**: `require_project_not_locked()` dependency — blocks mutations on signed-off projects
- **Cryptographic hash**: `compute_ecl_hash()` / `verify_ecl_hash()` for SHA-256 integrity verification at sign-off
- Falls back to anonymous analyst role when no auth headers present

### Role-Permission Matrix (existing, now enforced)
| Role | Sign Off | Approve | Post Journals | Manage Config |
|------|----------|---------|---------------|---------------|
| analyst | No | No | No | No |
| reviewer | No | No | No | No |
| approver | Yes | Yes | Yes | No |
| admin | Yes | Yes | Yes | Yes |

### Files Created/Modified
- `app/middleware/__init__.py` — NEW (package init)
- `app/middleware/auth.py` — NEW (auth middleware, 105 lines)
- `app/backend.py` — Updated re-exports
- `tests/unit/test_rbac.py` — NEW (25 unit tests)

## How to Test
```bash
cd "/Users/steven.tan/Expected Credit Losses"
python -m pytest tests/unit/test_rbac.py -v
```

## Test Results
- **25 new RBAC tests pass**
- **153 total pass** across all critical test files
- **2 pre-existing failures** (job config — unchanged)

## Contract Criteria Results
- [x] Auth middleware extracts user from request headers
- [x] Permission checking via `require_permission()` dependency
- [x] Role matrix enforces segregation of duties (analyst/reviewer cannot sign off)
- [x] Project immutability via `require_project_not_locked()` dependency
- [x] SHA-256 hash computation and verification for ECL integrity
- [x] 25 unit tests covering all RBAC functionality
- [ ] Route-level integration (dependencies ready but not yet wired into all routes — this is a follow-up)

## Known Limitations
- Auth dependencies are created and tested but not yet wired into every route handler (would require modifying all 16 route files)
- In development mode without auth headers, falls back to anonymous/analyst — this is intentional for local testing
