---
sidebar_position: 2
title: Configuration
---

# Configuration

The application stores configuration in Lakebase, persisting across app restarts. All settings are managed through the **Admin Panel**.

## Configuration Sections

| Section | Purpose | Admin Tab |
|---------|---------|-----------|
| Data Sources | Unity Catalog table mappings | Data Mapping |
| Model | Satellite models, LGD, SICR thresholds | Model Config |
| Jobs | Databricks workspace, job IDs, compute | Jobs & Pipelines |
| App Settings | Organization, currency, scenarios, governance | App Settings |

## Default Values

The application ships with sensible defaults for a bank using USD:

- **Organization**: Horizon Bank
- **Currency**: USD ($)
- **Reporting Period**: Quarterly
- **ECL Framework**: IFRS 9
- **Monte Carlo**: 1,000 simulations, 0.30 PD-LGD correlation
- **SICR Thresholds**: Stage 1 max DPD = 30, Stage 2 max DPD = 90

## Configuration Priority

1. Admin panel settings (stored in Lakebase) — highest priority
2. `admin_config_defaults.py` — fallback defaults
3. Environment variables — deployment-level overrides

## Import / Export

Administrators can export the full configuration as JSON and import it into another environment via the **Admin > System** tab. This enables consistent configuration across development, staging, and production.

See the [Admin Guide](/admin-guide/overview) for detailed configuration instructions.
