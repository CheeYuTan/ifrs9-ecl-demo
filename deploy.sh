#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${DATABRICKS_APP_NAME:-ifrs9-ecl-platform}"
DEPLOY_DIR="_deploy"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; exit 1; }
info() { echo -e "  ${BLUE}→${NC} $1"; }

echo ""
echo -e "${BLUE}Deploying $APP_NAME to Databricks Apps...${NC}"
echo ""

# ── Prerequisites ────────────────────────────────────────────────────────────

command -v databricks &>/dev/null || fail "Databricks CLI not found. Install: pip install databricks-cli"
databricks auth describe &>/dev/null || fail "Not authenticated. Run: databricks configure"
ok "Databricks CLI authenticated"

# ── Build Frontend ───────────────────────────────────────────────────────────

if [ -f "app/frontend/package.json" ]; then
    info "Building frontend..."
    (cd app/frontend && npm install --silent && npm run build 2>&1 | tail -3)
    ok "Frontend built"
fi

# ── Prepare Deploy Bundle ────────────────────────────────────────────────────

info "Preparing deployment bundle..."
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

cp app/app.py "$DEPLOY_DIR/"
cp app/backend.py "$DEPLOY_DIR/"
cp app/ecl_engine.py "$DEPLOY_DIR/"
cp app/admin_config.py "$DEPLOY_DIR/"
cp app/admin_config_defaults.py "$DEPLOY_DIR/"
cp app/admin_config_schema.py "$DEPLOY_DIR/"
cp app/admin_config_setup.py "$DEPLOY_DIR/"
cp app/jobs.py "$DEPLOY_DIR/"
cp app/requirements.txt "$DEPLOY_DIR/"
cp app/app.yaml "$DEPLOY_DIR/"

cp -r app/db "$DEPLOY_DIR/"
cp -r app/domain "$DEPLOY_DIR/"
cp -r app/ecl "$DEPLOY_DIR/"
cp -r app/governance "$DEPLOY_DIR/"
cp -r app/reporting "$DEPLOY_DIR/"
cp -r app/routes "$DEPLOY_DIR/"
cp -r app/middleware "$DEPLOY_DIR/"

if [ -d "app/static" ]; then
    cp -r app/static "$DEPLOY_DIR/"
    ok "Static assets included"
fi

ok "Deploy bundle ready ($DEPLOY_DIR/)"

# ── Deploy ───────────────────────────────────────────────────────────────────

info "Deploying to Databricks Apps..."
databricks apps deploy "$APP_NAME" --source-code-path "$DEPLOY_DIR"

echo ""
echo -e "  ${GREEN}Deployed!${NC}"
echo "  App URL: Check your Databricks workspace → Apps → $APP_NAME"
echo ""
