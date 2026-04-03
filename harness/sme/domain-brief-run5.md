# IFRS 9 ECL Platform — Domain SME Audit (Run 5)

**Audit Date:** 2026-03-30
**Auditor:** IFRS 9 / Basel III SME Consultant
**Application:** IFRS 9 Expected Credit Loss Platform
**Stack:** FastAPI + React + Databricks Lakebase (PostgreSQL)

---

## Executive Summary

This audit evaluates the IFRS 9 ECL platform from 10 distinct user personas covering the full lifecycle: installation, configuration, data ingestion, modelling, simulation, approval, audit, reporting, operations, and validation. The application demonstrates **strong domain coverage** for a mid-stage product, with a well-structured 8-step workflow, real Monte Carlo simulation, regulatory reporting (IFRS 7.35F-36), and a governance layer with RBAC and approval workflows. However, critical gaps remain in **authentication enforcement**, **period-over-period comparison**, **true EAD modelling**, and **audit immutability** that would block production deployment at a regulated institution.

---

## Persona Summary Table

| # | Persona | Rating | Key Finding |
|---|---------|--------|-------------|
| 1 | Installation | **PARTIAL** | `install.sh` exists and is well-structured, but Lakebase provisioning is manual; no Terraform/DAB for infrastructure |
| 2 | Initial Configuration | **PARTIAL** | Rich Admin UI with scenarios, LGD, SICR thresholds; missing currency config, discount curve setup, reporting period management |
| 3 | Data Mapping / ETL | **PARTIAL** | Full data mapper with UC browsing, auto-suggest, validation; missing incremental load, data lineage, reconciliation controls |
| 4 | Model (PD/LGD/EAD) | **PARTIAL** | Model registry with lifecycle (draft→active→retired), champion/challenger; missing true EAD model, model documentation templates |
| 5 | Monte Carlo / Simulation | **PARTIAL** | Real vectorized MC engine with Cholesky decomposition, SSE streaming; missing run comparison, seed-based reproducibility, convergence diagnostics |
| 6 | Approval / Sign-off | **PARTIAL** | RBAC with 4 roles, approval requests, segregation of duties check; missing multi-level approval chains, escalation, SLA tracking |
| 7 | Audit | **PARTIAL** | Workflow audit log, model registry audit trail, GL journal audit; missing tamper-proof storage, parameter change tracking, data snapshot versioning |
| 8 | Reporting / Disclosure | **PARTIAL** | IFRS 7.35F-M and 7.36 sections generated; missing PDF/Excel export, prior-period comparatives, IFRS 7.35J (write-offs), board-ready formatting |
| 9 | Maintenance / BAU | **MINIMAL** | Databricks Jobs integration exists; missing period-end close workflow, pipeline health dashboard, scheduling UI, monitoring alerts |
| 10 | Backtesting / Validation | **PARTIAL** | Real PD backtesting (AUC/Gini/KS/HL/Binomial/Jeffreys), LGD backtesting, traffic lights; missing out-of-time validation, validation report generation, trend alerting |

---

## Detailed Findings by Persona

### 1. Installation Persona — IT Admin

**Rating: PARTIAL**

**What exists:**
- `install.sh` (root) — Well-structured bash script with prerequisite checks (Python 3.10+, Node.js 18+), venv creation, pip install, frontend build, `.env` template copy, Lakebase connection test, and unit test execution
- `deploy.sh` — Deploys to Databricks Apps via CLI with frontend build and bundle preparation
- `app/app.yaml` — Databricks App manifest with Lakebase resource declaration
- `app/requirements.txt` — 7 dependencies with version floors
- `.env.example` — Documented template with all required environment variables

**What works well:**
- `install.sh` lines 21-25: Python version validation with clear error messages
- `install.sh` lines 88-118: Automatic Lakebase connection verification
- `install.sh` lines 122-125: Runs unit tests as part of install validation
- `deploy.sh` lines 37-55: Clean deploy bundle preparation excluding dev artifacts

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| I-1 | HIGH | No infrastructure-as-code | Lakebase instance must be manually provisioned. No Terraform, DAB, or CloudFormation template. An IT admin cannot deploy end-to-end without manual Databricks console steps. |
| I-2 | HIGH | No database schema migration tool | Tables are created via `ensure_*_table()` calls at startup (`app/domain/workflow.py:24-44`). No versioned migration system (Alembic, Flyway). Schema changes risk data loss — see `_migrate_model_registry_columns()` which DROPs and recreates (`app/domain/model_registry.py:56-95`). |
| I-3 | MEDIUM | Missing scipy in requirements.txt | `app/domain/backtesting.py:19` imports `scipy.stats` but `scipy` is not in `app/requirements.txt`. Only installed via `install.sh` line 51 as a test dependency. Will fail in production deployment. |
| I-4 | MEDIUM | No Docker/container support | No Dockerfile for containerized deployment. Databricks Apps is the only deployment target. |
| I-5 | LOW | No health check for dependent services | `/api/health` (`app/app.py:65-71`) only checks Lakebase. Does not verify Unity Catalog access, SQL Warehouse availability, or Databricks Jobs API connectivity. |

---

### 2. Initial Configuration Persona — Risk Manager

**Rating: PARTIAL**

**What exists:**
- `app/admin_config.py` — 886-line configuration module with comprehensive defaults stored in Lakebase
- `app/frontend/src/pages/Admin.tsx` — Full admin UI with tabs for Data Sources, Model Config, Scenarios, SICR Thresholds, Jobs, and Theme
- `app/routes/admin.py` — REST API for config CRUD
- `app/components/SetupWizard.tsx` — First-run setup wizard

**What works well:**
- `admin_config.py` lines 20-100: Exhaustive `DATA_SOURCE_CONFIG` with mandatory/optional column definitions, types, descriptions, examples, and constraints for each ECL table (loan_tape, borrower_master, payment_history, macroeconomic_scenarios, historical_defaults)
- `admin_config.py`: 8 pre-configured macroeconomic scenarios (baseline, optimistic, mild_downturn, adverse, severely_adverse, stagflation, rapid_recovery, tail_risk) with PD/LGD multipliers
- SICR thresholds configurable: DPD threshold, PD ratio threshold, 30-day rebuttable presumption, restructuring trigger, alt-data score drop trigger
- LGD assumptions per product type with cure rates

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| C-1 | CRITICAL | No reporting period management | No concept of "reporting date" at the system level beyond per-project `reporting_date`. Cannot manage multiple concurrent reporting periods (e.g., monthly close vs quarterly disclosure). No period lock/unlock mechanism. |
| C-2 | HIGH | No currency configuration | `admin_config.py` has no currency settings. All amounts are implicitly single-currency. Multi-currency portfolios (common in IFRS 9) have no FX rate configuration, no functional currency declaration per IFRS 9.B5.7.2. |
| C-3 | HIGH | No discount rate / yield curve setup | ECL discounting uses loan-level EIR (`effective_interest_rate`). No facility to configure risk-free rate curves, credit-adjusted discount rates, or yield curve term structures per IAS 39 / IFRS 9.B5.5.44. |
| C-4 | HIGH | No EAD configuration | LGD assumptions are configurable per product, but EAD methodology is hardcoded. No Credit Conversion Factor (CCF) configuration for off-balance-sheet exposures per IFRS 9.B5.5.31. The `advanced.py` CCF module exists but is not integrated into the main ECL engine. |
| C-5 | MEDIUM | Scenario weights not validated against regulatory guidance | While `validation_rules.py` checks weights sum to 1.0 (D1) and no single scenario > 50% (M-R5b), there is no guidance enforcement for minimum number of scenarios (IFRS 9.B5.5.42 requires "at least" base, upside, downside). |
| C-6 | MEDIUM | No config versioning/history | `admin_config.py` overwrites config in-place. No history of who changed what parameter when. Critical for audit trail of assumption changes. |

---

### 3. Data Mapping / ETL Persona — Data Engineer

**Rating: PARTIAL**

**What exists:**
- `app/domain/data_mapper.py` — Full data mapping module: UC catalog/schema/table browsing, column preview, auto-suggest mappings, validation, and apply (ingest to Lakebase)
- `app/frontend/src/pages/DataMapping.tsx` — UI for browsing UC, mapping columns, previewing data, validating, and applying
- `app/routes/data_mapping.py` — REST API for all mapping operations
- `scripts/01_generate_data.py` — Synthetic data generator for demo/testing
- `scripts/02_run_data_processing.py` — Data processing pipeline (staging, enrichment)

**What works well:**
- `data_mapper.py` lines 213-374: Thorough `validate_mapping()` with mandatory/optional column checks, type compatibility validation, and detailed error/warning reporting
- `data_mapper.py` lines 377-427: `suggest_mappings()` with exact, case-insensitive, normalized, and partial matching
- `data_mapper.py` lines 433-553: `apply_mapping()` with validation gate, batch insert (500 rows), and config persistence
- `admin_config.py` lines 20-100: Rich schema documentation with examples, constraints, and descriptions for every column

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| E-1 | CRITICAL | No incremental/delta load | `apply_mapping()` (`data_mapper.py:510`) only supports `overwrite` (TRUNCATE) or `append`. No merge/upsert, no change data capture, no SCD Type 2 for historical tracking. Each run destroys prior data. |
| E-2 | HIGH | No data reconciliation controls | No row count reconciliation between source (UC) and target (Lakebase). No checksum validation. No completeness checks (e.g., all loan_ids in payment_history exist in loan_tape). |
| E-3 | HIGH | No data lineage tracking | No record of which source table/version was used for each ECL run. Cannot trace "this ECL number came from this specific data snapshot." |
| E-4 | HIGH | Missing data quality profiling | `scripts/02_run_data_processing.py` generates DQ results, but there is no in-app data profiling (null rates, distribution checks, outlier detection) visible in the Data Mapping UI. |
| E-5 | MEDIUM | No scheduling for data refresh | Data ingestion is manual (click "Apply" in UI). No automated refresh schedule. The `jobs.py` module handles Databricks Jobs but not data ingestion jobs. |
| E-6 | MEDIUM | SQL injection risk in preview | `data_mapper.py:118-126` validates table names but the regex `r'^[a-zA-Z_][a-zA-Z0-9_.\-]*$'` allows dots and hyphens, which could be exploited in crafted UC table names. |

---

### 4. Model Persona — Quantitative Analyst

**Rating: PARTIAL**

**What exists:**
- `app/domain/model_registry.py` — Full model registry with lifecycle management (draft → pending_review → approved → active → retired)
- `app/frontend/src/pages/ModelRegistry.tsx` — UI for registering, comparing, promoting champion models
- `app/frontend/src/pages/SatelliteModel.tsx` — Satellite model comparison and selection UI
- `scripts/models/` — 8 satellite model implementations (linear, logistic, polynomial, ridge, random_forest, elastic_net, gradient_boosting, xgboost)
- `scripts/03a_satellite_model.py` — Satellite model training pipeline
- `app/domain/model_registry.py:304-350` — Auto-generated model cards with methodology, assumptions, limitations

**What works well:**
- `model_registry.py` lines 101-108: Proper status transition validation (cannot skip states)
- `model_registry.py` lines 111: Valid model types: PD, LGD, EAD, Staging
- `model_registry.py` lines 235-257: Champion/challenger promotion with automatic demotion of prior champion
- `model_registry.py` lines 279-301: Full audit trail for every model action
- `model_registry.py` lines 395-437: Sensitivity analysis with parameter perturbation
- `model_registry.py` lines 440-474: Recalibration due checker based on model age

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| M-1 | CRITICAL | No true EAD model | `VALID_MODEL_TYPES` includes "EAD" (`model_registry.py:111`) but no EAD model implementation exists. The ECL engine (`ecl_engine.py:30-46`) uses hardcoded amortization with prepayment adjustment. No CCF for revolving facilities. |
| M-2 | HIGH | No model training from UI | Models are trained via `scripts/03a_satellite_model.py` (Databricks notebook). The ModelRegistry UI only registers pre-trained models. A quant analyst cannot train, tune, or cross-validate models from the application. |
| M-3 | HIGH | No model versioning with artifact storage | `model_registry.py` stores metadata (parameters, metrics) but not the actual model artifacts (coefficients, pickled models). No link to MLflow Model Registry. Cannot reproduce a model run. |
| M-4 | HIGH | Satellite models are PD-only | All 8 satellite models in `scripts/models/` predict PD. No satellite models for LGD or EAD. IFRS 9 requires forward-looking adjustment for all risk parameters. |
| M-5 | MEDIUM | No out-of-sample validation | `model_registry.py:339` notes `validation_type: in_sample` as default. No train/test split enforcement, no k-fold cross-validation tracking, no out-of-time validation. |
| M-6 | MEDIUM | Model card is auto-generated, not editable | `generate_model_card()` (`model_registry.py:304-350`) produces a static card. No facility for quants to add custom methodology notes, override assumptions, or attach documentation. |

---

### 5. Monte Carlo / Simulation Persona — Risk Analyst

**Rating: PARTIAL**

**What exists:**
- `app/ecl_engine.py` — 612-line vectorized Monte Carlo ECL engine with:
  - 8 macro scenarios with product-specific PD/LGD multipliers
  - Correlated PD-LGD draws via Cholesky decomposition
  - PD term structure (flat hazard Stage 1, increasing hazard Stage 2/3)
  - Amortizing EAD with prepayment adjustment
  - Quarterly discounting at EIR
  - Stage 1 → 12-month horizon, Stage 2/3 → remaining life
- `app/routes/simulation.py` — REST API with SSE streaming progress, pre-calculation validation, parameter validation
- `app/frontend/src/components/SimulationPanel.tsx` — UI for configuring and running simulations
- `app/frontend/src/components/SimulationResults.tsx` — Results visualization

**What works well:**
- `ecl_engine.py` lines 1-14: Clear methodology documentation matching IFRS 9 requirements
- `routes/simulation.py` lines 64-95: Pre-calculation validation runs 23 domain rules before simulation
- `routes/simulation.py` lines 157-212: SSE streaming for real-time progress updates during long simulations
- `routes/simulation.py` lines 215-253: Parameter validation with warnings for extreme values
- `ecl_engine.py` lines 30-46: Product-specific LGD and satellite coefficients (PD-LGD correlation, prepayment rates, LGD std dev)

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| S-1 | HIGH | No run reproducibility | No random seed parameter. Cannot reproduce a specific simulation run. `ecl_engine.py` uses `np.random` without seed control. Critical for audit — regulators require reproducible results. |
| S-2 | HIGH | No run comparison | Cannot compare two simulation runs side-by-side. No run history beyond what's stored in `model_runs` table. No "what changed between Run A and Run B" analysis. |
| S-3 | HIGH | No convergence diagnostics | `validation_rules.py` checks CV < 5% (M-R4) but the simulation engine does not compute or report convergence metrics (running mean, running std, confidence interval width vs. simulation count). |
| S-4 | MEDIUM | Simulation cap at 5000 | `routes/simulation.py:227` caps at 5,000 simulations. For large portfolios with tail risk, 10,000-50,000 may be needed for stable VaR/CVaR estimates. |
| S-5 | MEDIUM | No importance sampling or variance reduction | Pure Monte Carlo without variance reduction techniques (antithetic variates, importance sampling, stratified sampling). Increases required simulation count for convergence. |
| S-6 | MEDIUM | PD term structure is simplified | `ecl_engine.py` uses flat hazard (Stage 1) and increasing hazard (Stage 2/3). No Nelson-Siegel, Svensson, or other parametric term structure models. No calibration to observed default term structures. |

---

### 6. Approval / Sign-off Persona — Senior Risk Officer / CFO

**Rating: PARTIAL**

**What exists:**
- `app/governance/rbac.py` — 4-role RBAC system (analyst, reviewer, approver, admin) with granular permissions
- `app/frontend/src/pages/ApprovalWorkflow.tsx` — Approval dashboard with pending queue, history, user management
- `app/frontend/src/pages/SignOff.tsx` — Final sign-off page with attestation checkboxes, ECL summary, attribution waterfall
- `app/domain/workflow.py` — 8-step workflow with step-level approve/reject
- `app/middleware/auth.py` — Authentication middleware with Databricks OAuth support
- `app/domain/validation_rules.py:312-319` — Segregation of duties check (G-R1)

**What works well:**
- `rbac.py` lines 12-35: Well-defined role hierarchy with specific permissions per role
- `rbac.py` lines 182-213: Approve/reject with permission checks and status validation
- `workflow.py` lines 136-149: Sign-off locks the project (prevents further modifications)
- `validation_rules.py` lines 312-319: G-R1 checks that executor ≠ signoff user
- `SignOff.tsx` lines 57-58: 4 attestation checkboxes required before sign-off

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| A-1 | CRITICAL | Authentication is bypassed in local dev | `middleware/auth.py:72-79`: If no auth header is present, RBAC is completely bypassed and anonymous user gets analyst permissions. In production (Databricks Apps), OAuth is enforced, but there is no configuration to require auth in all environments. |
| A-2 | HIGH | No multi-level approval chains | Single-level approve/reject only. No support for "analyst submits → reviewer validates → approver signs off → CFO final approval." Real ECL governance requires 3-4 approval levels. |
| A-3 | HIGH | No approval delegation | No mechanism for an approver to delegate authority during absence. No deputy/proxy approval. |
| A-4 | HIGH | No SLA tracking on approvals | `rbac_approval_requests` has `due_date` column but no enforcement, no escalation on overdue, no SLA dashboard. |
| A-5 | HIGH | Sign-off attestations are not persisted | `SignOff.tsx` line 57: Attestation state is local React state only. Not stored in the database. An auditor cannot verify what the signer attested to. |
| A-6 | MEDIUM | No digital signature | Sign-off stores `signed_off_by` (text name) and `signed_off_at` (timestamp). No cryptographic signature, no certificate-based signing. The `compute_ecl_hash()` in `auth.py:115-118` exists but is not called during sign-off. |

---

### 7. Audit Persona — Internal/External Auditor

**Rating: PARTIAL**

**What exists:**
- `app/domain/workflow.py` — Workflow audit log (JSON array in `ecl_workflow.audit_log` column) tracking every step action with timestamp, user, action, detail
- `app/domain/model_registry.py` — Dedicated `model_registry_audit` table with action, old_status, new_status, performed_by, comment
- `app/reporting/gl_journals.py` — GL journal entries with draft/posted status, posted_by, posted_at
- `app/middleware/auth.py:115-123` — ECL hash computation and verification functions
- `app/domain/validation_rules.py` — 23 validation rules with structured results

**What works well:**
- `workflow.py` lines 76-85, 89-103: Every workflow action is appended to an immutable-style audit log with ISO timestamps
- `model_registry.py` lines 279-301: Dedicated audit table for model lifecycle events
- `gl_journals.py`: Journal entries track created_by, posted_by, posted_at with draft→posted lifecycle
- `validation_rules.py`: 23 rules across 3 categories (Data Integrity D1-D10, Model Reasonableness M-R1-R8, Governance G-R1-G-R5)

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| AU-1 | CRITICAL | Audit log is mutable | `workflow.py` stores audit_log as a JSON text column in `ecl_workflow`. Any user with DB access can modify it. No write-once/append-only storage. No hash chain or blockchain-style immutability. |
| AU-2 | CRITICAL | No data snapshot versioning | Cannot answer "what was the portfolio data at the time of this ECL calculation?" No point-in-time data snapshots. ECL results cannot be traced back to the exact input data. |
| AU-3 | HIGH | No parameter change tracking | `admin_config.py` overwrites config in-place. No history of scenario weight changes, LGD assumption changes, SICR threshold changes. Auditors cannot see "who changed the adverse scenario weight from 20% to 15% on March 15." |
| AU-4 | HIGH | ECL hash not used in practice | `auth.py:115-123` has `compute_ecl_hash()` and `verify_ecl_hash()` but they are never called in the sign-off flow (`workflow.py:136-149`). ECL results can be modified after sign-off without detection. |
| AU-5 | HIGH | No export of audit trail | No API endpoint or UI to export the complete audit trail for a project. Auditors must query the database directly. |
| AU-6 | MEDIUM | No user session logging | No record of who logged in when, what pages they viewed, what API calls they made. Only explicit actions (approve, reject, sign-off) are logged. |

---

### 8. Reporting / Disclosure Persona — Regulatory Reporting Team

**Rating: PARTIAL**

**What exists:**
- `app/reporting/reports.py` — 5 report types: IFRS 7 Disclosure, ECL Movement, Stage Migration, Sensitivity Analysis, Concentration Risk
- `app/frontend/src/pages/RegulatoryReports.tsx` — Report generation UI with section-level data tables, CSV export
- `app/routes/reports.py` — REST API for report generation, listing, finalization, CSV export
- `app/reporting/gl_journals.py` — GL chart of accounts, journal generation, posting, trial balance

**What works well:**
- `reports.py` lines 36-234: Comprehensive IFRS 7 disclosure with sections 35F (credit risk by grade), 35H (loss allowance by stage), 35I (loss allowance reconciliation via attribution), 35K (GCA by product/stage), 35L (modified assets), 35M (collateral), 36 (sensitivity)
- `reports.py` lines 628-634: Report finalization (draft → final lock)
- `reports.py` lines 637-657: CSV export with section flattening
- `gl_journals.py`: Proper double-entry accounting with chart of accounts, stage-specific provision accounts, overlay accounts, write-off accounts

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| R-1 | CRITICAL | No prior-period comparatives | All IFRS 7 disclosures show current period only. IFRS 7.35H explicitly requires "reconciliation from opening to closing balance." The attribution module provides this, but reports do not show prior period columns side-by-side. |
| R-2 | HIGH | No PDF export | `export_report_csv()` exists but no PDF generation. Regulatory submissions and board presentations require formatted PDF output. |
| R-3 | HIGH | Missing IFRS 7.35J — Write-offs | No dedicated write-off disclosure section. IFRS 7.35J requires disclosure of contractual amounts outstanding on financial assets that were written off during the period and are still subject to enforcement activity. |
| R-4 | HIGH | No Excel export with formatting | CSV export loses all formatting. Banks typically submit IFRS 7 disclosures as formatted Excel workbooks with multiple tabs. |
| R-5 | HIGH | Sensitivity analysis is linear approximation | `reports.py` lines 196-209: Sensitivity is computed as `base_ecl * pd_mult * lgd_mult`. This is a first-order linear approximation. Real sensitivity should re-run the ECL engine with stressed parameters. |
| R-6 | MEDIUM | No report approval workflow | Reports go from draft → final with a single `finalize_report()` call. No review/approval step for regulatory reports before submission. |
| R-7 | MEDIUM | No FINREP/COREP template mapping | European banks must map IFRS 7 disclosures to specific FINREP templates (F 12.01, F 12.02). No template mapping or regulatory format export. |

---

### 9. Maintenance / BAU Persona — Operations Team

**Rating: MINIMAL**

**What exists:**
- `app/jobs.py` — Databricks Jobs integration for running pipeline scripts (data generation, processing, model training, ECL calculation, Lakebase sync)
- `app/routes/jobs.py` — REST API for listing, running, and monitoring Databricks Jobs
- `scripts/` — 7 pipeline scripts covering the full data-to-ECL flow
- `app/frontend/src/pages/Admin.tsx` — Jobs configuration tab with script path settings

**What works well:**
- `jobs.py` lines 39-60: Auto-detection of workspace script paths
- `jobs.py`: Job provisioning with proper cluster configuration
- Pipeline scripts are numbered sequentially (01→02→03a→03b→04) indicating a clear execution order

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| B-1 | CRITICAL | No period-end close workflow | No automated "month-end close" process that: (1) snapshots data, (2) runs DQ checks, (3) executes models, (4) generates ECL, (5) produces reports, (6) routes for approval. Each step is manual. |
| B-2 | HIGH | No pipeline health dashboard | No UI showing: last successful run, next scheduled run, pipeline duration trends, failure alerts. The Jobs page shows Databricks Job status but not ECL-specific pipeline health. |
| B-3 | HIGH | No scheduling UI | Jobs can be triggered manually but there is no in-app scheduling configuration. Must configure Databricks Job schedules externally. |
| B-4 | HIGH | No data freshness monitoring | No check for "when was the loan tape last refreshed?" No staleness alerts. An operations team could unknowingly run ECL on stale data. |
| B-5 | MEDIUM | No runbook/playbook | No operational documentation for: "How to run month-end ECL," "What to do when a job fails," "How to handle late data." |
| B-6 | MEDIUM | No environment management | No concept of DEV/UAT/PROD environments. No promotion workflow for config changes from test to production. |

---

### 10. Backtesting / Validation Persona — Model Validation Team

**Rating: PARTIAL**

**What exists:**
- `app/domain/backtesting.py` — Comprehensive backtesting engine with:
  - PD discrimination: AUC-ROC, Gini (Accuracy Ratio), KS statistic
  - PD calibration: Binomial test (EBA/GL/2017/16 §71), Jeffreys test (§72), Hosmer-Lemeshow (§74), Spiegelhalter
  - Population stability: PSI
  - LGD backtesting: MAE, RMSE, Mean Bias, product-level analysis
  - Traffic light system (Green/Amber/Red) per EBA guidelines
- `app/frontend/src/pages/Backtesting.tsx` — UI with metric cards, traffic lights, trend charts, cohort analysis
- `app/routes/backtesting.py` — REST API for running backtests, listing history, trend analysis

**What works well:**
- `backtesting.py` lines 87-99: Well-calibrated metric thresholds matching industry standards (AUC green ≥ 0.70, Gini green ≥ 0.40, PSI green ≤ 0.10)
- `backtesting.py` lines 186-238: Proper implementation of Binomial and Jeffreys tests with confidence intervals
- `backtesting.py` lines 241-295: Hosmer-Lemeshow with decile grouping and chi-squared test
- `backtesting.py` lines 329-438: Real LGD backtesting from historical defaults with product-level granularity
- `backtesting.py` lines 637-663: Historical trend tracking for metric degradation monitoring

**Gaps:**

| ID | Severity | Gap | Detail |
|----|----------|-----|--------|
| V-1 | HIGH | No out-of-time validation | Backtesting uses current portfolio data (`model_ready_loans`) as both training and test set. No temporal holdout. Cannot assess model performance on truly unseen data. |
| V-2 | HIGH | No validation report generation | Backtest results are stored in DB and shown in UI, but no formal validation report (PDF/Word) can be generated for model governance documentation. |
| V-3 | HIGH | No EAD backtesting | Only PD and LGD backtesting implemented. No EAD backtesting (predicted vs actual drawdown at default). |
| V-4 | HIGH | No automated trigger for re-validation | `model_registry.py:440-474` has `check_recalibration_due()` but it is not called automatically. No scheduled check, no alert when a model exceeds its validation period. |
| V-5 | MEDIUM | No traffic light trend alerting | `get_backtest_trend()` returns historical data but no alerting when a metric degrades from Green to Amber or Red across consecutive runs. |
| V-6 | MEDIUM | Backtest uses cross-sectional default proxy | `backtesting.py:455-456`: Default is defined as `days_past_due >= 90 OR assessed_stage = 3` at a point in time. This is a cross-sectional proxy, not a true outcome-based default observation over a 12-month outcome window. |

---

## Prioritized Gap List

### CRITICAL (Must fix before production)

| ID | Persona | Gap | Regulatory Reference |
|----|---------|-----|---------------------|
| AU-1 | Audit | Audit log is mutable (JSON in regular table) | IAS 8, SOX Section 302 |
| AU-2 | Audit | No data snapshot versioning | IFRS 9.B5.5.49 (data used in estimates) |
| R-1 | Reporting | No prior-period comparatives in IFRS 7 disclosures | IFRS 7.35H (reconciliation requirement) |
| A-1 | Approval | Authentication bypassed without auth headers | Basel III Pillar 2 (operational risk) |
| B-1 | BAU | No period-end close workflow | Bank operational risk management |
| E-1 | ETL | No incremental/delta load (TRUNCATE on each run) | Data integrity, operational risk |
| C-1 | Config | No reporting period management | IAS 1.36 (reporting period) |
| I-2 | Install | No database schema migration tool | Operational risk, data integrity |

### HIGH (Should fix before UAT)

| ID | Persona | Gap | Regulatory Reference |
|----|---------|-----|---------------------|
| M-1 | Model | No true EAD model implementation | IFRS 9.B5.5.31 (EAD estimation) |
| S-1 | Simulation | No run reproducibility (no random seed) | EBA/GL/2017/16 (model reproducibility) |
| AU-3 | Audit | No parameter change tracking | IFRS 9.B5.5.52 (changes in estimates) |
| AU-4 | Audit | ECL hash not used in sign-off flow | Data integrity |
| R-2 | Reporting | No PDF export | Regulatory submission requirements |
| R-3 | Reporting | Missing IFRS 7.35J write-off disclosure | IFRS 7.35J |
| A-2 | Approval | No multi-level approval chains | Basel III Pillar 2 governance |
| A-5 | Approval | Sign-off attestations not persisted | SOX Section 302 |
| M-2 | Model | No model training from UI | Operational efficiency |
| M-3 | Model | No model artifact storage | EBA/GL/2017/16 (model documentation) |
| M-4 | Model | Satellite models PD-only (no LGD/EAD) | IFRS 9.B5.5.4 (forward-looking for all parameters) |
| V-1 | Validation | No out-of-time validation | EBA/GL/2017/16 §66 |
| V-2 | Validation | No validation report generation | EBA/GL/2017/16 §82 |
| V-3 | Validation | No EAD backtesting | EBA/GL/2017/16 §150 |
| S-2 | Simulation | No run comparison | Model governance |
| E-2 | ETL | No data reconciliation controls | Data integrity |
| E-3 | ETL | No data lineage tracking | BCBS 239 (data governance) |
| B-2 | BAU | No pipeline health dashboard | Operational risk |
| C-2 | Config | No currency configuration | IFRS 9.B5.7.2 (multi-currency) |
| C-3 | Config | No discount rate / yield curve setup | IFRS 9.B5.5.44 |
| C-4 | Config | No EAD configuration (CCF) | IFRS 9.B5.5.31 |
| I-1 | Install | No infrastructure-as-code | Operational risk |
| R-5 | Reporting | Sensitivity is linear approximation | IFRS 7.36 (sensitivity methodology) |

### MEDIUM

| ID | Persona | Gap |
|----|---------|-----|
| C-5 | Config | Scenario weights not validated against minimum scenario count |
| C-6 | Config | No config versioning/history |
| S-3 | Simulation | No convergence diagnostics |
| S-4 | Simulation | Simulation cap at 5,000 |
| S-5 | Simulation | No variance reduction techniques |
| S-6 | Simulation | Simplified PD term structure |
| A-3 | Approval | No approval delegation |
| A-4 | Approval | No SLA tracking on approvals |
| A-6 | Approval | No digital signature |
| AU-5 | Audit | No export of audit trail |
| AU-6 | Audit | No user session logging |
| R-4 | Reporting | No Excel export with formatting |
| R-6 | Reporting | No report approval workflow |
| R-7 | Reporting | No FINREP/COREP template mapping |
| B-3 | BAU | No scheduling UI |
| B-4 | BAU | No data freshness monitoring |
| B-5 | BAU | No runbook/playbook |
| B-6 | BAU | No environment management |
| V-4 | Validation | No automated re-validation trigger |
| V-5 | Validation | No traffic light trend alerting |
| V-6 | Validation | Cross-sectional default proxy |
| M-5 | Model | No out-of-sample validation tracking |
| M-6 | Model | Model card not editable |
| E-4 | ETL | No in-app data profiling |
| E-5 | ETL | No scheduling for data refresh |
| I-3 | Install | Missing scipy in requirements.txt |
| I-4 | Install | No Docker support |

### LOW

| ID | Persona | Gap |
|----|---------|-----|
| I-5 | Install | Health check doesn't verify all dependencies |
| E-6 | ETL | SQL injection risk in table name regex |

---

## Missing Domain Validation Rules

The existing 23 validation rules (`validation_rules.py`) are well-structured but missing these IFRS 9-specific checks:

| Rule ID | Category | Description | IFRS 9 Reference |
|---------|----------|-------------|-----------------|
| D-11 | Data Integrity | Loan-level PD must be monotonically increasing with DPD bucket | IFRS 9.5.5.9 |
| D-12 | Data Integrity | Stage 2 loans must have SICR trigger documented (PD ratio, DPD, restructuring, or qualitative) | IFRS 9.5.5.3 |
| D-13 | Data Integrity | Write-off loans must have Stage 3 history | IFRS 9.5.4.4 |
| M-R9 | Model | Lifetime PD must be ≥ 12-month PD for all loans | Mathematical constraint |
| M-R10 | Model | ECL for Stage 1 must use 12-month horizon; Stage 2/3 must use lifetime | IFRS 9.5.5.3/5.5.5 |
| M-R11 | Model | Weighted average LGD must be higher under adverse scenarios than baseline | IFRS 9.B5.5.28 |
| M-R12 | Model | Total ECL must be ≥ sum of individual loan ECLs (no diversification benefit in ECL) | IFRS 9.B5.5.40 |
| G-R6 | Governance | Management overlay must not exceed 25% of base ECL without board approval | Industry best practice |
| G-R7 | Governance | Model must have been backtested within last 90 days before use in ECL calculation | EBA/GL/2017/16 |
| G-R8 | Governance | At least 3 macroeconomic scenarios must be used | IFRS 9.B5.5.42 |

---

## Terminology Issues Found

| Location | Current Term | Correct IFRS 9 Term | Note |
|----------|-------------|---------------------|------|
| `workflow.py:10-18` | `STEPS` array uses `model_execution` | Should reference "ECL Calculation" or "ECL Measurement" | "Model execution" is ambiguous — could mean model training or ECL computation |
| `ecl_engine.py:8` | "8 macro scenarios" | "Probability-weighted scenarios" | IFRS 9.5.5.17 uses "probability-weighted" not just "macro" |
| `admin_config.py` column `current_lifetime_pd` | "current lifetime PD" | "Lifetime PD" or "Cumulative PD" | "Current" is redundant and could confuse with "current period" |
| `backtesting.py:454` | `defaulted` defined as `DPD >= 90 OR Stage 3` | Should be "credit-impaired" per IFRS 9 | IFRS 9.B5.5.37 defines credit-impaired, not "defaulted" (which is a Basel term) |
| `queries.py:14` | `assessed_stage` | Acceptable, but "IFRS 9 Stage" or "ECL Stage" is more precise | "Assessed" could imply subjective assessment only |
| `admin_config.py` | `cure_rate` in LGD assumptions | "Cure rate" is correct but should be labeled "Stage 3 to Stage 2 cure rate" | Cure can mean different things (Stage 3→2, Stage 2→1, DPD cure) |
| `ecl_engine.py:9` | "Correlated PD-LGD draws" | "Joint PD-LGD simulation with systematic risk factor" | More precise per Basel/IFRS 9 methodology |
| `reports.py:51-55` | Credit grades mapped from PD ranges | Should reference "Internal Rating Grade" per IFRS 7.35F | The mapping is reasonable but should be configurable, not hardcoded |
| `validation_rules.py:47` | "D1: Scenario weights must sum to 1.0" | "Probability weights" per IFRS 9.5.5.18 | "Scenario weights" is acceptable but "probability weights" is the standard term |

---

## Architectural Strengths

1. **Clean separation of concerns**: Domain logic in `app/domain/`, routes in `app/routes/`, reporting in `app/reporting/`, governance in `app/governance/`
2. **Comprehensive data schema**: `admin_config.py` defines 5 input tables with 60+ columns, each with type, description, example, and constraints
3. **Real statistical tests**: Backtesting implements actual EBA-referenced tests (Binomial, Jeffreys, Hosmer-Lemeshow, Spiegelhalter) — not stubs
4. **Proper GL accounting**: Double-entry journal system with chart of accounts, stage-specific provision accounts, and trial balance
5. **Validation rules engine**: 23 rules across 3 categories with structured results, severity levels, and aggregate pass/fail
6. **Modern UI**: React with lazy loading, dark mode, SSE streaming, responsive design, accessibility (ARIA labels, keyboard navigation)

---

## Recommendations (Priority Order)

1. **Implement immutable audit log** — Move audit trail to append-only table with hash chain. Add `compute_ecl_hash()` to sign-off flow.
2. **Add data snapshot versioning** — Snapshot input data at each ECL run. Store snapshot ID in `model_runs` table.
3. **Build period-end close workflow** — Orchestrate the full ECL cycle as a single automated pipeline with gates.
4. **Add prior-period comparatives to IFRS 7** — Store prior period ECL results and generate comparative disclosures.
5. **Implement EAD model** — Integrate CCF from `advanced.py` into the main ECL engine. Add revolving facility support.
6. **Add random seed to simulation** — Make every run reproducible. Store seed in run metadata.
7. **Enforce authentication in all environments** — Remove anonymous fallback or make it configurable.
8. **Add PDF/Excel report export** — Use a library like WeasyPrint or openpyxl for formatted output.
9. **Implement incremental data load** — Add merge/upsert capability to data mapper.
10. **Add config change tracking** — Version all configuration changes with user, timestamp, and diff.

---

*End of SME Domain Audit — Run 5*
