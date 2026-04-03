---
sidebar_position: 1
title: Installation
---

# Installation

Deploy the IFRS 9 ECL application on Databricks Apps.

## Prerequisites

- **Databricks Workspace** with Unity Catalog enabled
- **Lakebase instance** (managed PostgreSQL) provisioned in the workspace
- **Unity Catalog** catalog and schema containing your loan data
- Python 3.11+ (managed by Databricks Apps)

## Deploy on Databricks Apps

### 1. Clone the repository

```bash
git clone <repository-url>
cd expected-credit-losses
```

### 2. Configure `app.yaml`

The deployment configuration is in `app/app.yaml`:

```yaml
command:
  - python
  - app.py
env:
  - name: LAKEBASE_INSTANCE_NAME
    value: "${LAKEBASE_INSTANCE_NAME}"
  - name: LAKEBASE_DATABASE
    value: databricks_postgres
  - name: DATABRICKS_APP_NAME
    value: "${DATABRICKS_APP_NAME}"
resources:
  - name: lakebase-db
    lakebase:
      instance_name: "${LAKEBASE_INSTANCE_NAME}"
      permission: CAN_USE
```

Replace `${LAKEBASE_INSTANCE_NAME}` with your Lakebase instance name.

### 3. Deploy

```bash
databricks apps deploy expected-credit-losses --source-code-path app/
```

Or push to a connected Git repository for automatic deployment.

### 4. Verify

Open the Databricks Apps URL in your browser. You should see the ECL Workflow landing page.

## First-Time Setup

After deployment, an administrator must:

1. **Configure data sources** — Map Unity Catalog tables to the application ([Data Mapping](/admin-guide/data-mapping))
2. **Set model parameters** — Configure satellite models, LGD assumptions, SICR thresholds ([Model Config](/admin-guide/model-config))
3. **Configure scenarios** — Set macroeconomic scenario weights ([App Settings](/admin-guide/app-settings))
4. **Provision jobs** — Set up Databricks Jobs for batch processing ([Jobs & Pipelines](/admin-guide/jobs-pipelines))

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LAKEBASE_INSTANCE_NAME` | Lakebase PostgreSQL instance | Required |
| `LAKEBASE_DATABASE` | Database name | `databricks_postgres` |
| `DATABRICKS_APP_NAME` | App name for identification | `expected-credit-losses` |
| `PORT` | HTTP server port | `8000` |
