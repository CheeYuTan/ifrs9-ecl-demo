---
sidebar_position: 4
title: Operational & Governance Features
---

# GL Journals, Reports, RBAC, Audit, Admin & Advanced Analytics

The platform includes a full suite of operational, governance, and administrative features required for production IFRS 9 ECL workflows — from general ledger posting to regulatory report generation, role-based access control, and period-close orchestration.

## Overview

These features span eight route modules (67 endpoints) organized into three functional areas:

1. **Financial Operations** — GL journal generation, regulatory reports, period close pipeline
2. **Governance & Compliance** — RBAC, approval workflows, immutable audit trails
3. **Administration** — Database configuration, data mapping, advanced analytics (cure rates, CCF, collateral)

![GL Journals Page](/img/guides/gl-journals-page.png)
*GL Journals page showing journal generation and posting controls*

## GL Journals

General ledger journals translate ECL provisions into accounting entries that can be posted to the ERP system.

### Generating Journals

**API**: `POST /api/gl-journals/generate`

Generates double-entry journal lines for a project's ECL results. Every generated journal guarantees:
- **Double-entry integrity**: Total debits = total credits for every journal
- **Idempotent posting**: Posting the same journal twice does not create duplicate entries

### Key Endpoints

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Generate journals | `/api/gl-journals/generate` | POST |
| List journals | `/api/gl-journals` | GET |
| Get journal | `/api/gl-journals/{id}` | GET |
| Post to GL | `/api/gl-journals/{id}/post` | POST |
| Reverse journal | `/api/gl-journals/{id}/reverse` | POST |
| Trial balance | `/api/gl-journals/trial-balance` | GET |
| Chart of accounts | `/api/gl-journals/chart-of-accounts` | GET |

### Trial Balance

**API**: `GET /api/gl-journals/trial-balance`

Returns the trial balance for all posted journals. The platform enforces that **total debits always equal total credits** — a fundamental accounting invariant.

### Journal Reversal

Reversals create an offsetting journal that nets the original to zero. The original journal is marked as reversed and cannot be re-posted.

## Regulatory Reports

The platform generates IFRS 7 disclosure reports required under sections 35H through 35N of the standard.

![Reports Page](/img/guides/reports-page.png)
*Regulatory Reports page with report generation and export options*

### Report Types

| Report | IFRS 7 Section | Content |
|--------|---------------|---------|
| **ECL Summary** | 35H | Gross carrying amounts and loss allowances by stage |
| **Stage Migration** | 35I | Reconciliation of loss allowance movements (originations, derecognitions, transfers, remeasurements) |
| **Credit Quality** | 35J | Credit quality analysis using historical default data |
| **Sensitivity** | 35K | Sensitivity of ECL to changes in key assumptions |
| **Collateral** | 35L | Collateral and credit enhancements held |

### Generating a Report

**API**: `POST /api/reports/generate/{project_id}`

```json
{
  "report_type": "ecl_summary",
  "as_of_date": "2025-12-31"
}
```

### Export Formats

Reports can be exported in two formats:

- **CSV**: `GET /api/reports/{report_id}/export` — tabular data for spreadsheet analysis
- **PDF**: `GET /api/reports/{report_id}/export/pdf` — formatted document for regulatory submission

### Finalizing Reports

**API**: `POST /api/reports/{report_id}/finalize`

Finalized reports are locked and cannot be modified. This provides an audit trail for regulatory submissions.

## Role-Based Access Control (RBAC)

The RBAC system enforces segregation of duties — a core IFRS 9 governance requirement ensuring that the person calculating ECL is not the same person approving it.

![Approval Workflow](/img/guides/approval-workflow-page.png)
*Approval workflow showing pending requests and approval history*

### User Management

| Operation | Endpoint | Method |
|-----------|----------|--------|
| List users | `/api/rbac/users` | GET |
| Get user | `/api/rbac/users/{user_id}` | GET |
| Get permissions | `/api/rbac/permissions/{user_id}` | GET |

### Approval Workflow

The maker-checker-approver pattern ensures proper oversight:

1. **Create request**: `POST /api/rbac/approvals` — a user submits a change for approval
2. **Review**: Approvers see pending requests with full context
3. **Approve/Reject**: `POST /api/rbac/approvals/{request_id}/approve` or `/reject`
4. **History**: `GET /api/rbac/approvals/history/{entity_id}` — complete audit trail

**Segregation of duties**: The system prevents the request creator from approving their own request.

## Audit Trail

An immutable, hash-chained audit trail tracks every action for regulatory compliance.

### Audit Endpoints

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Config changes | `GET /api/audit/config/changes` | GET |
| Config diff | `GET /api/audit/config/diff` | GET |
| Project trail | `GET /api/audit/{project_id}` | GET |
| Verify chain | `GET /api/audit/{project_id}/verify` | GET |
| Export | `GET /api/audit/{project_id}/export` | GET |

### Hash Chain Verification

**API**: `GET /api/audit/{project_id}/verify`

Each audit entry includes a cryptographic hash of its contents plus the previous entry's hash, creating a tamper-evident chain. The verify endpoint checks that every link in the chain is intact.

### Config Change Tracking

**API**: `GET /api/audit/config/diff`

Returns a structured diff showing exactly what changed between two configuration versions — field by field.

## Admin Console

The admin console provides database configuration, table management, and auto-discovery capabilities.

![Admin Page](/img/guides/admin-page.png)
*Admin console showing database configuration and table management*

### Configuration Management

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Get config | `GET /api/admin/config` | GET |
| Get section | `GET /api/admin/config/{section}` | GET |
| Save config | `POST /api/admin/config` | POST |
| Test connection | `POST /api/admin/test-connection` | POST |
| Seed defaults | `POST /api/admin/seed-defaults` | POST |

Configuration is persisted and round-trip consistent — saving then retrieving returns identical values.

### Data Discovery

| Operation | Endpoint | Description |
|-----------|----------|-------------|
| Auto-detect workspace | `GET /api/admin/auto-detect-workspace` | Discover available Unity Catalog assets |
| Available tables | `GET /api/admin/available-tables` | List all accessible tables |
| Table columns | `GET /api/admin/table-columns/{table}` | Inspect column schema |
| Table preview | `GET /api/admin/table-preview/{table}` | Preview first N rows |
| Discover products | `GET /api/admin/discover-products` | Auto-identify product types in data |
| Auto-setup LGD | `POST /api/admin/auto-setup-lgd` | Configure LGD parameters from data |

### Schema Validation

**API**: `POST /api/admin/validate-mapping`

Validates that the current column mapping configuration is consistent with the actual table schemas in the database.

## Data Mapping

The data mapping system connects Unity Catalog tables to the ECL platform's expected schema.

![Data Mapping Page](/img/guides/data-mapping-page.png)
*Data Mapping page showing schema discovery and column mapping interface*

### Mapping Workflow

1. **Discover**: Browse catalogs, schemas, and tables via the discovery endpoints
2. **Suggest**: `POST /api/data-mapping/suggest` — AI-assisted column mapping suggestions
3. **Validate**: `POST /api/data-mapping/validate` — check mapping consistency
4. **Apply**: `POST /api/data-mapping/apply` — activate the mapping configuration
5. **Status**: `GET /api/data-mapping/status` — verify current mapping health

### Key Endpoints

| Operation | Endpoint | Method |
|-----------|----------|--------|
| List catalogs | `GET /api/data-mapping/catalogs` | GET |
| List schemas | `GET /api/data-mapping/schemas/{catalog}` | GET |
| List tables | `GET /api/data-mapping/tables/{catalog}/{schema}` | GET |
| List columns | `GET /api/data-mapping/columns/{catalog}/{schema}/{table}` | GET |
| Preview data | `POST /api/data-mapping/preview` | POST |
| Suggest mapping | `POST /api/data-mapping/suggest` | POST |
| Validate | `POST /api/data-mapping/validate` | POST |
| Apply mapping | `POST /api/data-mapping/apply` | POST |
| Check status | `GET /api/data-mapping/status` | GET |

## Advanced Analytics

Advanced analytics provide cure rate estimation, credit conversion factors, and collateral analysis.

![Advanced Features](/img/guides/advanced-page.png)
*Advanced analytics page with cure rates, CCF, and collateral panels*

### Cure Rates

Cure rates measure the probability of a defaulted borrower (Stage 3) returning to performing status.

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Compute | `POST /api/advanced/cure-rates/compute` | POST |
| List | `GET /api/advanced/cure-rates` | GET |
| Get detail | `GET /api/advanced/cure-rates/{id}` | GET |

Cure rate values are bounded in [0, 1].

### Credit Conversion Factors (CCF)

CCF estimates the proportion of undrawn credit that will be drawn at the time of default — essential for revolving credit exposures.

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Compute | `POST /api/advanced/ccf/compute` | POST |
| List | `GET /api/advanced/ccf` | GET |
| Get detail | `GET /api/advanced/ccf/{id}` | GET |

CCF values are bounded in [0, 1].

### Collateral Analysis

Collateral haircut analysis adjusts LGD based on the value of collateral held against each exposure.

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Compute | `POST /api/advanced/collateral/compute` | POST |
| List | `GET /api/advanced/collateral` | GET |
| Get detail | `GET /api/advanced/collateral/{id}` | GET |

## Period Close Pipeline

The period-close pipeline orchestrates the end-of-period ECL calculation and reporting workflow.

### Pipeline Steps

The pipeline executes steps in a defined order with dependency management:

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Start pipeline | `POST /api/period-close/start` | POST |
| List steps | `GET /api/period-close/steps` | GET |
| Get run status | `GET /api/period-close/run` | GET |
| Execute step | `POST /api/period-close/execute-step` | POST |
| Complete | `POST /api/period-close/complete` | POST |
| Health check | `GET /api/period-close/health` | GET |
| Run all | `POST /api/period-close/run-all` | POST |

### Run-All Behavior

`POST /api/period-close/run-all` executes all pipeline steps sequentially. If any step fails, the pipeline **stops immediately** — it does not skip failed steps.

## Test Coverage

Sprint 4 of the QA audit added **225 tests** across all 67 endpoints:
- GL journal double-entry integrity validation
- All 5 IFRS 7 report types with structure verification
- Maker-checker segregation of duties enforcement
- Audit hash chain integrity with tamper detection
- Admin config save/retrieve round-trip consistency
- Data mapping suggest → validate → apply pipeline
- Period close step ordering and failure handling
- 3 bug fixes with 11 regression tests (audit timestamp serialization, IFRS 7.35I reconciliation column, historical defaults table error handling)
