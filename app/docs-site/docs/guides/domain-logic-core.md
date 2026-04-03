---
sidebar_position: 6
title: Domain Logic — Workflow, Queries & Validation
---

# Domain Logic: Workflow, Queries, Attribution & Validation

The platform's domain logic layer (`domain/`) implements the core business rules for IFRS 9 ECL workflows — state machine management, portfolio query generation, ECL attribution decomposition, and pre/post-calculation validation.

## Overview

Eight domain modules handle the business logic between the API routes and the database layer:

| Module | Purpose | Tests |
|--------|---------|-------|
| `domain/workflow.py` | Project state machine, step validation, audit events | 27 |
| `domain/queries.py` | 27 portfolio/ECL aggregation query builders | 30 |
| `domain/attribution.py` | ECL waterfall decomposition (IFRS 7.35I) | 20 |
| `domain/validation_rules.py` | 23 pre/post-calculation validation checks | 39 |
| `domain/data_mapper.py` | Column mapping logic, auto-suggest, status | 22 |
| `domain/model_runs.py` | Run history, cohort queries, ECL drill-down | 10 |
| `domain/audit_trail.py` | Immutable event logging, chain verification | 7 |
| `domain/config_audit.py` | Config change tracking, diff computation | 10 |

![ECL Workflow Overview](/img/guides/ecl-workflow-overview.png)
*ECL workflow stepper showing the 8-step project lifecycle*

## Workflow State Machine

The `workflow.py` module manages the 8-step project lifecycle as a strict state machine. Each step must be explicitly advanced before the next becomes available.

### Step Advancement

```python
# Valid advancement: step N → step N+1
advance_project_step(project_id, status="completed")

# Invalid: skipping steps raises WorkflowError
advance_project_step(project_id, status="completed")  # at step 3, cannot jump to step 5
```

### State Transitions

| Action | Effect | Validation |
|--------|--------|------------|
| **Create** | Initializes project at Step 1 | Name + reporting date required |
| **Advance** | Moves to next step | Current step must be completed |
| **Reset** | Returns to a prior step | Clears all downstream data |
| **Sign-off** | Locks project permanently | Segregation of duties enforced |

### Audit Events

Every state transition generates an immutable audit event with:
- Timestamp, user identity, action type
- Before/after state
- Cryptographic hash linking to the previous event

### Table Initialization

The `ensure_workflow_table()` function initializes all required database tables at startup. It lazily imports and calls 7 specialized ensure functions:

- `ensure_backtesting_table`
- `ensure_model_registry_table`
- `ensure_markov_table`
- `ensure_hazard_table`
- `ensure_advanced_table`
- `ensure_period_close_table`
- `ensure_health_table`

Each function is imported with `try/except ImportError` to handle missing modules gracefully, then called with `try/except Exception` for runtime errors — ensuring that one failed initialization does not block the others.

## Portfolio Queries

The `queries.py` module provides 27 query-builder functions that generate SQL for portfolio analytics. Every query function:

- Accepts a `project_id` parameter for scoping
- Returns structured column sets verified by tests
- Uses parameterized SQL (no string interpolation) to prevent injection

### Key Query Functions

| Function | Returns | SQL Patterns |
|----------|---------|-------------|
| `get_portfolio_summary` | Total exposure, weighted-average PD, loan count | Aggregate with GROUP BY |
| `get_stage_distribution` | Exposure breakdown by Stage 1/2/3 | GROUP BY stage |
| `get_ecl_summary` | ECL by stage and product | Multi-level GROUP BY |
| `get_vintage_by_product` | Vintage analysis by origination year | GROUP BY vintage, product |
| `get_concentration_by_product_stage` | Concentration by product and stage | GROUP BY product, stage |
| `get_ecl_by_scenario_product` | ECL by scenario and product | GROUP BY scenario, product |
| `get_dq_results` | Data quality check results | JOIN with DQ rules |
| `get_dq_summary` | Aggregated DQ summary | GROUP BY severity |
| `get_gl_reconciliation` | GL reconciliation data | ORDER BY account |

![Portfolio Dashboard](/img/guides/portfolio-dashboard.png)
*Portfolio summary displaying stage distribution and key metrics*

## ECL Attribution (IFRS 7.35I)

The `attribution.py` module decomposes the change in ECL between two reporting periods into its component drivers — a mandatory disclosure under IFRS 7 paragraph 35I.

### Waterfall Components

The attribution waterfall breaks the total ECL change into:

| Component | Description |
|-----------|-------------|
| **New Originations** | ECL from newly originated loans |
| **Derecognitions** | ECL reduction from repaid/written-off loans |
| **Stage Transfers** | ECL change due to stage migration |
| **Remeasurements** | ECL change from updated risk parameters |
| **Model Changes** | ECL change from model methodology updates |
| **Overlays** | Management overlay adjustments |

### Sum-to-Total Guarantee

The waterfall components **must** sum to the total ECL change:

```
ECL_change = New_Originations + Derecognitions + Stage_Transfers
           + Remeasurements + Model_Changes + Overlays
```

This invariant is enforced by validation and verified by tests. Any residual difference is tracked against a 5% materiality threshold and flagged as `within_materiality` (boolean).

### Prior Period Handling

When no prior period exists (first ECL calculation), the attribution returns `None` for prior values and sets opening == closing amounts.

## Validation Rules

The `validation_rules.py` module implements 23 pre- and post-calculation checks organized by domain:

### Data Quality Validations (D-series)

| Rule | Check | Failure |
|------|-------|---------|
| D-7 | PD values in [0, 1] | Reject loans with invalid PD |
| D-8 | LGD values in [0, 1] | Reject loans with invalid LGD |
| D-9 | EAD values ≥ 0 | Reject negative exposure |
| D-10 | Required fields non-null | Flag incomplete records |

### Domain Accuracy Validations (DA-series)

| Rule | Check | Failure |
|------|-------|---------|
| DA-1 | Scenario weights sum to 1.0 | Reject with tolerance ±0.001 |
| DA-2 | Stage 3 implies default flag | Flag inconsistent staging |
| DA-3 | ECL ≥ 0 (no negative provisions) | Reject negative ECL |
| DA-4 | Coverage ratio in reasonable range | Warning if > 100% |
| DA-5 | Stage distribution sums to total | Reject inconsistency |
| DA-6 | Discount factor in (0, 1] | Reject invalid DF |

### Model Risk Validations (M-R series)

| Rule | Check |
|------|-------|
| M-R3 | Model version matches approved champion |
| M-R7 | Backtesting metrics within acceptable range |

### Governance Validations (G-R series)

| Rule | Check |
|------|-------|
| G-R4 | Approval workflow complete before sign-off |

### Boundary Conditions

All validation rules are tested with:
- **Passing input**: Known-good values
- **Failing input**: Values that should trigger the rule
- **Boundary input**: Values at the exact threshold (e.g., PD = 0.0, PD = 1.0, scenario weights = 0.999 vs 1.001)

## Data Mapper

The `data_mapper.py` module maps Unity Catalog table columns to the platform's expected schema.

### Mapping Functions

| Function | Purpose |
|----------|---------|
| `_safe_identifier` | Sanitize column names for SQL safety |
| `validate_mapping` | Check that mapped columns exist in source table |
| `suggest_mapping` | AI-assisted column name matching |
| `get_mapping_status` | Health check of current mapping configuration |

### Type Mapping

The mapper automatically converts between Unity Catalog types and the platform's internal types:

| Source Type | Target Type |
|------------|-------------|
| `string`, `varchar` | `TEXT` |
| `int`, `bigint`, `long` | `INTEGER` |
| `float`, `double`, `decimal` | `NUMERIC` |
| `date`, `timestamp` | `TIMESTAMP` |
| `boolean` | `BOOLEAN` |

### Error Handling

`get_mapping_status` returns a dictionary with status counts and handles database errors gracefully — returning a degraded status rather than throwing an exception.

## Audit Trail & Config Audit

### Immutable Audit Trail

The `audit_trail.py` module implements a hash-chained, append-only audit log:

1. **Hash computation**: Each entry hashes its content + the previous entry's hash
2. **Chain verification**: `verify_chain()` walks the entire chain and detects any tampering
3. **Multi-entry support**: Chains with 1, 10, or 1000 entries are all verified correctly

If any entry in the chain is modified after creation, the verification fails — providing tamper-evident logging for regulatory compliance.

### Config Change Tracking

The `config_audit.py` module tracks configuration changes with:

- **Time-range filtering**: Query changes within a date range
- **JSON parsing**: Config values stored as JSON are parsed for structured diffs
- **Timestamp conversion**: All timestamps normalized to UTC for consistent comparison

## Test Coverage

Sprint 6 of the QA audit added **196 tests** across all 8 domain modules with 2 iterations:

- Workflow state machine: valid transitions, invalid transitions, sign-off, reset, audit events
- All 27 query functions with SQL keyword assertions (GROUP BY, table names, ORDER BY)
- Attribution waterfall: components sum to total ECL change (IFRS 7.35I compliance)
- All 23 validation rules with positive, negative, and boundary test cases
- Data mapper: safe identifiers, type mapping, suggest, validate, status
- Audit trail: hash computation, chain verification, tamper detection
- Config audit: diff computation, time ranges, JSON parsing
