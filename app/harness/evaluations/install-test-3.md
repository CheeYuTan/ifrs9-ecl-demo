# Installation Test 3 — Clean Install Verification

**Date**: 2026-04-02
**Tester**: Installation Agent
**Verdict**: **PASS** (with advisory notes)

---

## 1. Clean Install — Dependency Resolution

### Pre-clean
Removed: `.venv/`, `__pycache__/`, `frontend/node_modules/`, `.pytest_cache/`

### Python Dependencies
- **Method**: `python3 -m venv --system-site-packages .venv` (PyPI unreachable from test environment; system Python has all required packages)
- **Result**: All 9 packages in `requirements.txt` resolved successfully
- **Verification**:

| Package | Required | Installed | Status |
|---------|----------|-----------|--------|
| fastapi | >=0.115.0 | 0.129.0 | OK |
| uvicorn[standard] | >=0.34.0 | 0.41.0 | OK |
| numpy | >=1.26.0 | 1.26.4 | OK |
| pandas | >=2.0.0 | 2.3.3 | OK |
| psycopg2-binary | >=2.9.0 | 2.9.9 | OK |
| databricks-sdk | >=0.56.0 | 0.85.0 | OK |
| requests | >=2.31.0 | 2.32.4 | OK |
| scipy | >=1.11.0 | 1.16.3 | OK |
| fpdf2 | >=2.7.0 | 2.8.7 | OK |

### Frontend Dependencies
- **Method**: `npm install` in `frontend/`
- **Result**: 426 packages installed in 3s, exit code 0
- **TypeScript compilation**: `tsc -b` passed (exit code 0)
- **Frontend build**: `vite build` completed in 1.98s, output to `static/`

---

## 2. Test Suite Results After Clean Install

### Backend (pytest)
- **Command**: `python -m pytest --tb=short -q`
- **Result**: **3046 passed, 61 skipped, 0 failures** (78.15s)
- **Exit code**: 0
- No regressions from clean install

### Frontend (vitest)
- **Command**: `npm run test`
- **Result**: **11 test files, 103 tests passed** (2.48s)
- **Exit code**: 0

### Total: 3149 tests passed, 0 failures

---

## 3. Application Startup Verification

- **Port**: 8001 (dynamically found free port)
- **Command**: `DATABRICKS_APP_PORT=8001 python app.py`
- **Startup**: App initialized, Lakebase pool connected

### Health Check (`/api/health`)
```json
{"status": "healthy", "lakebase": "connected", "rows": 1}
```
**Result**: PASS

### Detailed Health Check (`/api/health/detailed`)
- Lakebase: connected, healthy
- Tables: `model_ready_loans` (79,739 rows), `loan_level_ecl` (717,651 rows), `loan_ecl_weighted` (79,739 rows) present
- Some optional tables missing (`ecl_workflow`, `app_config`) — expected for fresh state
- **Result**: PASS (degraded status is expected without full data setup)

### Frontend Serving (`/`)
- HTTP 200 returned
- Valid HTML with React SPA shell (`<!doctype html>`, React app mount)
- **Result**: PASS

---

## 4. Deploy Artifacts Validation

### app.yaml
- **Command**: `python app.py` — correct
- **Environment variables**: `LAKEBASE_INSTANCE_NAME`, `LAKEBASE_DATABASE`, `DATABRICKS_APP_NAME` — defined
- **Resources**: Lakebase resource with `CAN_USE` permission — correct
- **Result**: PASS

### Port Handling
- `app.py` uses `os.environ.get("DATABRICKS_APP_PORT", 8000)` — correct, no hardcoded ports
- No hardcoded `localhost:NNNN` in application Python files
- **Result**: PASS

### No Hardcoded Secrets
- Grep for `api_key`, `secret`, `token`, `password` patterns in `*.py` — no matches in app code
- All credentials come from environment variables or Databricks CLI auth
- **Result**: PASS

---

## 5. Missing Artifacts (Advisory)

| Artifact | Status | Impact |
|----------|--------|--------|
| `install.sh` | **MISSING** | No one-command installer for new developers |
| `.env.example` | **MISSING** | New developers don't know which env vars to set |
| `deploy.sh` | **MISSING** | No deployment automation script |

### Environment Variables Used (should be in `.env.example`)
- `DATABRICKS_APP_PORT` — app listening port (default: 8000)
- `DATABRICKS_APP_NAME` — Databricks Apps app name
- `LAKEBASE_INSTANCE_NAME` — Lakebase instance (default: ifrs9-ecl-demo-db)
- `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGPORT` — direct Postgres connection
- `DATABRICKS_HOST` — workspace URL
- `DATABRICKS_WORKSPACE_ID` — workspace ID
- `DATABRICKS_CONFIG_PROFILE` — CLI profile (default: lakemeter)
- `DATABRICKS_SERVICE_PRINCIPAL_ID` — for job execution
- `DATABRICKS_SQL_WAREHOUSE_ID` — for data mapping queries
- `DATABRICKS_SOURCE_CODE_PATH` — for deployed app source

---

## 6. Verdict

### **PASS**

**Core installation works correctly:**
- All Python and frontend dependencies resolve without errors
- Full test suite (3149 tests) passes after clean install with zero failures
- Application starts, health endpoint responds healthy, frontend serves correctly
- `app.yaml` is valid for Databricks Apps deployment
- No hardcoded secrets or ports in application code

**Advisory items (not blocking):**
- Missing `install.sh` — manual install steps work fine but no automation
- Missing `.env.example` — env vars are documented in `app.yaml` partially, but a complete example file would help onboarding
- Missing `deploy.sh` — deployment is via Databricks Apps CLI, but a wrapper script would standardize the process

These advisory items do not block functionality but would improve developer onboarding experience.
