#!/usr/bin/env bash
set -euo pipefail

echo "=== IFRS 9 ECL Platform — Installation ==="

# Prerequisites check
command -v python3 &>/dev/null || { echo "ERROR: Python 3 required"; exit 1; }
command -v node &>/dev/null || { echo "ERROR: Node.js required"; exit 1; }
command -v npm &>/dev/null || { echo "ERROR: npm required"; exit 1; }

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python: $PYTHON_VERSION"
echo "Node:   $(node --version)"
echo "npm:    $(npm --version)"

# Python virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo "Installing Python dependencies..."
pip install -r requirements.txt -q

# Frontend
echo "Installing frontend dependencies..."
(cd frontend && npm install --silent)
echo "Building frontend..."
(cd frontend && npx vite build)

# Environment file
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "Created .env from .env.example — edit with your credentials."
fi

# Run tests
echo "Running tests..."
python3 -m pytest tests/ -q --tb=short || echo "WARNING: Some tests failed"

echo ""
echo "=== Installation complete ==="
echo "Start the app:  source .venv/bin/activate && python app.py"
echo "Default port:   \$DATABRICKS_APP_PORT or 8000"
