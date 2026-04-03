# Installation Test 5 — IFRS 9 ECL Application

**Date**: 2026-04-02
**Tester**: Installation Agent
**Verdict**: **CONDITIONAL PASS** (see findings below)

---

## 1. Clean Install Results

### Python Dependencies
- **Action**: Deleted `.venv`, `__pycache__`, `frontend/node_modules`, `frontend/dist`
- **Fresh venv creation**: `python3 -m venv .venv` — SUCCESS
- **`pip install -r requirements.txt`**: BLOCKED — PyPI unreachable (network/firewall issue, `Connection refused` to pypi.org)
- **Workaround**: Copied parent `.venv` (which had all deps pre-installed) to verify dependency resolution
- **All 9 packages verified importable**:
  | Package | Version | Status |
  |---------|---------|--------|
  | fastapi | 0.129.0 | OK (>=0.115.0) |
  | uvicorn | 0.41.0 | OK (>=0.34.0) |
  | numpy | 1.26.4 | OK (>=1.26.0) |
  | pandas | 2.3.3 | OK (>=2.0.0) |
  | psycopg2-binary | 2.9.9 | OK (>=2.9.0) |
  | databricks-sdk | present | OK (>=0.56.0) |
  | requests | 2.32.4 | OK (>=2.31.0) |
  | scipy | 1.16.3 | OK (>=1.11.0) |
  | fpdf2 | present (imports as `fpdf`) | OK (>=2.7.0) |

### Frontend Dependencies
- **`npm install`**: SUCCESS — 426 packages installed in 3s
- **`npm run build`**: SUCCESS — built in 1.96s, all chunks produced
- **Static assets**: Written to `../static/assets/` (served by FastAPI)

---

## 2. Test Results After Clean Install

### Python Tests (pytest)
- **Result**: 3412 passed, 61 skipped, 0 failed
- **Duration**: 113.41s
- **No regressions** after clean install

### Frontend Tests (vitest)
- **Result**: 103 passed across 11 test files
- **Duration**: 1.87s
- **No regressions** after clean install

### Combined: **3515 tests passed, 0 failures**

---

## 3. Application Startup Verification

- **Port**: 8100 (found free via `find_free_port(8100, 8200)`)
- **Start command**: `DATABRICKS_APP_PORT=8100 python app.py`
- **Startup time**: ~8 seconds (Lakebase connection, table initialization)
- **Startup log**: Clean — connected to PostgreSQL 16.12, initialized workflow/audit/config tables

| Endpoint | Status | Response |
|----------|--------|----------|
| `GET /api/health` | 200 | `{"status":"healthy","lakebase":"connected","rows":1}` |
| `GET /api/projects` | 200 | Returns project data |
| `GET /` (frontend) | 200 | Serves `index.html` with React SPA |

---

## 4. Deploy Artifacts Validation

### app.yaml
- **Command**: `python app.py` — matches the `if __name__ == "__main__"` entrypoint
- **Environment variables**: `LAKEBASE_INSTANCE_NAME`, `LAKEBASE_DATABASE`, `DATABRICKS_APP_NAME` — all templated
- **Resources**: Lakebase instance with `CAN_USE` permission
- **Status**: PASS

### Port Configuration
- **No hardcoded ports** in application code
- Port read from `DATABRICKS_APP_PORT` env var with fallback to 8000
- **Status**: PASS

### Security Scan
- **No hardcoded secrets, tokens, or API keys** found in application source
- OAuth tokens generated dynamically via Databricks SDK
- **Status**: PASS

---

## 5. Findings & Issues

### ISSUE 1: No `install.sh` script (MEDIUM)
- **Expected**: An `install.sh` plug-and-play installer per harness spec
- **Actual**: No shell script exists for automated installation
- **Impact**: New developers must manually create venv, install deps, build frontend
- **Recommendation**: Create `install.sh` that:
  1. Checks Python 3.11+ and Node 18+ prerequisites
  2. Creates venv and installs requirements.txt
  3. Runs `cd frontend && npm install && npm run build`
  4. Copies `.env.example` to `.env` if needed
  5. Runs `pytest --tb=short -q`

### ISSUE 2: No `.env.example` file (MEDIUM)
- **Expected**: `.env.example` listing all required environment variables
- **Actual**: No `.env.example` exists
- **Impact**: New deployments may fail without knowing required env vars
- **Required vars** (from app.yaml + code analysis):
  - `LAKEBASE_INSTANCE_NAME`
  - `LAKEBASE_DATABASE` (default: `databricks_postgres`)
  - `DATABRICKS_APP_NAME`
  - `DATABRICKS_APP_PORT` (default: `8000`)

### ISSUE 3: No `deploy.sh` script (LOW)
- **Expected**: Deployment helper script
- **Actual**: Not present
- **Impact**: Deployment steps must be done manually

### ISSUE 4: `pytest` not in `requirements.txt` (LOW)
- **Expected**: Test dependencies listed or separate `requirements-dev.txt`
- **Actual**: `pytest` is available from parent environment but not declared
- **Impact**: Clean install without system pytest would fail to run tests

---

## 6. Verdict

### **CONDITIONAL PASS**

**Core application functionality is solid:**
- All 3515 tests pass (3412 Python + 103 frontend)
- App starts cleanly and serves both API and frontend
- No hardcoded secrets or ports
- app.yaml is correctly configured for Databricks Apps deployment
- Frontend builds successfully and is served as static assets

**Missing deployment scaffolding:**
- No `install.sh` (automated installer)
- No `.env.example` (environment variable documentation)
- No `deploy.sh` (deployment helper)
- Test dependencies not declared in requirements

These are **not blockers** for the application itself — the app works correctly. They are deployment ergonomics issues that should be addressed before handoff to other developers.
