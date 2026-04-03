---
sidebar_position: 2
title: Getting Started
---

# Getting Started

Get the IFRS 9 ECL Platform running in under 5 minutes.

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm 9+
- Access to a Databricks workspace with Lakebase

## Installation

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repo-url> && cd "Expected Credit Losses/app"

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Build the frontend
cd frontend && npm install && npm run build && cd ..
```

### 2. Configure Environment

Set the required environment variables for Lakebase connectivity:

```bash
export LAKEBASE_INSTANCE_NAME="your-instance"
export LAKEBASE_DATABASE="databricks_postgres"
```

### 3. Start the Application

```bash
uvicorn app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## First Steps

### 1. Run Setup Wizard

On first launch, the Setup Wizard guides you through database configuration:

1. **Validate Tables** — Checks that the required Lakebase tables exist
2. **Seed Data** — Populates reference data and sample portfolios
3. **Complete Setup** — Marks the workspace as ready

### 2. Create Your First ECL Project

1. Click **Create Project** in the sidebar or stepper
2. Enter a project name, reporting date, and base currency
3. The project opens at Step 1 of the 8-step workflow

### 3. Walk Through the Workflow

The platform guides you through 8 sequential steps:

| Step | Name | What Happens |
|------|------|-------------|
| 1 | Create Project | Define project metadata |
| 2 | Data Processing | Import and process portfolio data |
| 3 | Data Control | Quality checks and validation |
| 4 | Satellite Model | Select macroeconomic models |
| 5 | Monte Carlo | Run ECL simulation |
| 6 | Stress Testing | Apply stress scenarios |
| 7 | Overlays | Management adjustments |
| 8 | Sign Off | Approval and lock |

Each step must be completed (or explicitly skipped) before advancing to the next.

## Deploy to Databricks Apps

The application is configured for Databricks Apps deployment via `app.yaml`:

```bash
# Deploy using Databricks CLI
databricks apps deploy ecl-platform --source-code-path .
```

The app reads `DATABRICKS_APP_PORT` automatically in production. See the [Architecture](./architecture) page for deployment details.

## API Documentation

The platform includes built-in API docs:

- **Swagger UI**: [http://localhost:8000/api/swagger](http://localhost:8000/api/swagger)
- **ReDoc**: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)
- **OpenAPI JSON**: [http://localhost:8000/api/openapi.json](http://localhost:8000/api/openapi.json)
