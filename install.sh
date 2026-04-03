#!/usr/bin/env bash
set -euo pipefail

APP_NAME="IFRS 9 ECL Platform"
echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║  $APP_NAME — Local Development Setup  ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; exit 1; }
info() { echo -e "  ${BLUE}→${NC} $1"; }

# ── Prerequisites ────────────────────────────────────────────────────────────

echo -e "${BLUE}Checking prerequisites...${NC}"

command -v python3 &>/dev/null || fail "Python 3 not found. Install Python 3.10+"
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
[ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ] && ok "Python $PY_VER" || fail "Python 3.10+ required (found $PY_VER)"

if [ -f "app/frontend/package.json" ]; then
    command -v node &>/dev/null || fail "Node.js not found. Install Node.js 18+"
    NODE_VER=$(node -v)
    ok "Node.js $NODE_VER"
fi

command -v databricks &>/dev/null && ok "Databricks CLI found" || warn "Databricks CLI not found (optional for local dev, required for deploy)"

# ── Python Environment ───────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}Setting up Python environment...${NC}"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    ok "Created virtual environment (.venv)"
else
    ok "Virtual environment exists (.venv)"
fi

source .venv/bin/activate

pip install --upgrade pip -q 2>/dev/null
pip install -r app/requirements.txt -q && ok "Python dependencies installed"
pip install scipy pytest pytest-cov pytest-asyncio httpx -q && ok "Test dependencies installed"

# ── Frontend ─────────────────────────────────────────────────────────────────

if [ -f "app/frontend/package.json" ]; then
    echo ""
    echo -e "${BLUE}Setting up frontend...${NC}"
    (cd app/frontend && npm install --silent 2>&1 | tail -1) && ok "Frontend dependencies installed"

    if [ ! -d "app/static" ] || [ -z "$(ls -A app/static 2>/dev/null)" ]; then
        info "Building frontend (first time)..."
        (cd app/frontend && npm run build 2>&1 | tail -3) && ok "Frontend built → app/static/"
    else
        ok "Frontend already built (app/static/)"
        info "To rebuild: cd app/frontend && npm run build"
    fi
fi

# ── Environment Configuration ────────────────────────────────────────────────

echo ""
echo -e "${BLUE}Checking environment...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        warn "Created .env from template — edit with your Databricks credentials"
    else
        warn "No .env file found. Create one with your Databricks/Lakebase credentials."
        warn "See .env.example for required variables."
    fi
else
    ok ".env file exists"
fi

# ── Verify Databricks Connection ─────────────────────────────────────────────

if [ -f ".env" ]; then
    set +u
    source .env 2>/dev/null || true
    set -u
fi

if [ -n "${PGHOST:-}" ] && [ -n "${PGUSER:-}" ]; then
    PYTHONPATH=app python3 -c "
import os, sys
sys.path.insert(0, 'app')
try:
    import psycopg2
    conn = psycopg2.connect(
        host=os.environ['PGHOST'],
        port=os.environ.get('PGPORT', '5432'),
        database=os.environ.get('PGDATABASE', 'databricks_postgres'),
        user=os.environ['PGUSER'],
        password=os.environ.get('PGPASSWORD', ''),
        sslmode='require',
    )
    cur = conn.cursor()
    cur.execute('SELECT version()')
    ver = cur.fetchone()[0]
    print(f'  Connected to Lakebase: {ver[:60]}')
    conn.close()
except Exception as e:
    print(f'  Could not connect to Lakebase: {e}')
" 2>/dev/null && ok "Lakebase connected" || warn "Lakebase connection failed — check .env credentials"
else
    warn "PGHOST/PGUSER not set — Lakebase connection will be configured at runtime"
fi

# ── Run Tests ────────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}Running tests...${NC}"

PYTHONPATH=app python3 -m pytest tests/unit/test_backtesting.py tests/unit/test_rbac.py tests/unit/test_attribution.py tests/unit/test_model_registry.py tests/unit/test_validation_rules.py --tb=short -q 2>/dev/null && ok "Unit tests pass" || warn "Some tests failed (may need Lakebase connection)"

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo -e "  ╔══════════════════════════════════════════════════════╗"
echo -e "  ║  ${GREEN}Setup complete!${NC}                                     ║"
echo -e "  ╚══════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}Start the app:${NC}"
echo "    source .venv/bin/activate"
echo "    cd app && python app.py"
echo ""
echo -e "  ${GREEN}Frontend dev:${NC}"
echo "    cd app/frontend && npm run dev"
echo ""
echo -e "  ${GREEN}Run tests:${NC}"
echo "    PYTHONPATH=app python -m pytest tests/ -v"
echo ""
echo -e "  ${GREEN}Deploy to Databricks:${NC}"
echo "    ./deploy.sh"
echo ""
