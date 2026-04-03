---
sidebar_position: 7
title: System
---

# System

Import/export configuration, reset to defaults, and verify system health.

## Connection Status

On load, the System tab automatically tests the Lakebase connection and displays:

- **Connected** / **Disconnected** badge
- Schema name and table prefix

## Configuration Management

### Export Configuration

Click **Export Config** to download the current configuration as a JSON file named `ecl-config-YYYY-MM-DD.json`. This includes all four sections:

- `data_sources` — Table mappings and connection settings
- `model` — Satellite models, Monte Carlo, SICR, LGD
- `jobs` — Workspace URL, job IDs, compute settings
- `app_settings` — Organization, scenarios, governance

### Import Configuration

Click **Import Config** to upload a previously exported JSON file. The system validates that the file contains all four required sections before applying. This is useful for:

- Migrating configuration between environments (dev → staging → production)
- Restoring a known-good configuration
- Sharing configuration across teams

### Re-run Setup Wizard

Resets the setup state and reloads the initial configuration wizard. This calls `POST /api/setup/reset`.

### Reset to Defaults

Resets all configuration to factory defaults defined in `admin_config_defaults.py`. This calls `POST /api/admin/seed-defaults`.

:::warning
Resetting to defaults will overwrite all custom configuration. Export your current configuration first if you want to preserve it.
:::

## Audit Trail

The system maintains two audit subsystems:

### Configuration Audit

Track all changes to admin configuration:

- `GET /api/audit/config/changes` — View the change log (filterable by section)
- `GET /api/audit/config/diff` — Compare configuration between two timestamps

### Project Audit

Each project has its own audit trail with cryptographic chain verification:

- `GET /api/audit/{project_id}` — Paginated audit trail
- `GET /api/audit/{project_id}/verify` — Verify chain integrity (tamper detection)
- `GET /api/audit/{project_id}/export` — Download full audit package as JSON

The audit chain uses SHA-256 hashing to ensure immutability. Any tampering is detected by the verification endpoint.
