.PHONY: lint test test-backend test-frontend build dev clean

lint:
	ruff check app/
	cd app/frontend && npx eslint src/ --max-warnings 50

test: test-backend test-frontend

test-backend:
	RATE_LIMIT_DISABLED=1 python -m pytest tests/ -q --tb=short

test-frontend:
	cd app/frontend && npx vitest run

build:
	cd app/frontend && npm run build

dev:
	cd app/frontend && npm run dev &
	PYTHONPATH=app python -m uvicorn app:app --reload --port 8000 --app-dir app

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf app/static/ app/frontend/node_modules/.vite
