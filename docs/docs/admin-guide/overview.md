---
sidebar_position: 1
title: Overview
---

# Admin Guide

Configure and manage the IFRS 9 ECL application through the Admin Panel.

## Accessing the Admin Panel

Navigate to **Admin** in the sidebar. The panel has six tabs:

| Tab | Purpose | Page |
|-----|---------|------|
| Data Mapping | Map Unity Catalog / Lakebase tables and columns | [Data Mapping](data-mapping) |
| Model Config | Satellite models, Monte Carlo, SICR, LGD assumptions | [Model Config](model-config) |
| Jobs & Pipelines | Databricks workspace, job IDs, compute settings | [Jobs & Pipelines](jobs-pipelines) |
| App Settings | Organization, currency, scenarios, governance | [App Settings](app-settings) |
| Theme | Dark/light mode, colour presets | [Theme](theme) |
| System | Import/export config, reset, connection test | [System](system) |

## Configuration Storage

All configuration is stored in **Lakebase** (managed PostgreSQL) as a single JSON document with four sections: `data_sources`, `model`, `jobs`, `app_settings`. Changes persist across app restarts.

## Configuration Priority

1. **Admin panel settings** (stored in Lakebase) — highest priority
2. **`admin_config_defaults.py`** — fallback defaults
3. **Environment variables** — deployment-level overrides

## Save Behaviour

Changes are saved when you click **Save** at the top of the Admin panel. The following validations are enforced:

| Validation | Severity |
|-----------|----------|
| Organization name must not be blank | Error (blocks save) |
| Scenario weights must sum to 100% (±1%) | Error (blocks save) |
| LGD values must be between 0 and 1 | Error (blocks save) |
| Cure rates must be between 0 and 1 | Error (blocks save) |
| Workspace URL should not be blank | Warning (saves with notice) |
| At least one satellite model should be enabled | Warning (saves with notice) |

An unsaved-changes guard prevents accidentally navigating away with unsaved modifications.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/config` | Load full configuration |
| `PUT` | `/api/admin/config` | Save full configuration |
| `GET` | `/api/admin/config/{section}` | Load one section |
| `PUT` | `/api/admin/config/{section}` | Save one section |
