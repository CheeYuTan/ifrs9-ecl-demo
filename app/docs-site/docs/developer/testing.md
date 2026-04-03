---
sidebar_position: 5
title: "Testing"
description: "Test framework, running tests, and writing new tests for the platform."
---

# Testing

The IFRS 9 ECL Platform maintains a comprehensive test suite covering the backend API, domain logic, ECL engine, and frontend components. This page describes the test framework, how to run tests, key fixtures, and conventions for writing new tests.

## Framework

| Component | Tool |
|-----------|------|
| Backend test runner | pytest |
| Frontend test runner | Vitest |
| Mocking | `unittest.mock` (patch, MagicMock) |
| Coverage | pytest-cov (HTML output in `htmlcov/`) |
| Markers | `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow` |

The pytest configuration is in `app/pytest.ini`:

```ini
[pytest]
testpaths = ../tests
asyncio_mode = auto
markers =
    unit: Unit tests (deselect with '-m "not unit"')
    integration: Integration tests requiring mocked services
    slow: Tests that take more than a few seconds
```

## Directory Structure

```
tests/
├── conftest.py                 # Shared fixtures and test constants
├── __init__.py
├── unit/                       # Unit tests (50+ files)
│   ├── __init__.py
│   ├── test_admin_config.py
│   ├── test_advanced.py
│   ├── test_attestation_sprint4.py
│   ├── test_attribution.py
│   ├── test_attribution_audit_routes_sprint4c.py
│   ├── test_audit_routes.py
│   ├── test_audit_trail.py
│   ├── test_backend.py
│   ├── test_backtesting.py
│   ├── test_config_audit_sprint6.py
│   ├── test_data_models_routes_sprint4b.py
│   ├── test_domain_accuracy_sprint3.py
│   ├── test_ecl_engine.py
│   ├── test_gl_journals.py
│   ├── test_hazard.py
│   ├── test_installation_sprint7.py
│   ├── test_jobs.py
│   ├── test_markov.py
│   ├── test_model_registry.py
│   ├── test_model_runs.py
│   ├── test_models.py
│   ├── test_period_close_sprint5.py
│   ├── test_production_readiness_sprint5.py
│   ├── test_qa_sprint_1_core_routes.py
│   ├── test_qa_sprint_1_iter4_error_paths.py
│   ├── test_qa_sprint_1_iter5_final_gaps.py
│   ├── test_qa_sprint_1_utils_and_gaps.py
│   ├── test_qa_sprint_2_simulation_satellite.py
│   ├── test_qa_sprint_3_models_backtest_markov_hazard.py
│   ├── test_qa_sprint_4_advanced_pipeline.py
│   ├── test_qa_sprint_4_audit_admin_mapping.py
│   ├── test_qa_sprint_4_gl_reports_rbac.py
│   ├── test_qa_sprint_5_ecl_engine.py
│   ├── test_qa_sprint_6_domain_logic.py
│   ├── test_qa_sprint_7_domain_analytical.py
│   ├── test_qa_sprint_7_iter2_domain.py
│   ├── test_qa_sprint_7_iter3_regression.py
│   ├── test_qa_sprint_7_iter4_regression.py
│   ├── test_qa_sprint_9_db_pool.py
│   ├── test_qa_sprint_9_integration_flows.py
│   ├── test_qa_sprint_9_middleware.py
│   ├── test_rbac.py
│   ├── test_reporting_sprint3.py
│   ├── test_reports_routes.py
│   ├── test_route_handlers_sprint4.py
│   ├── test_simulation_seed.py
│   └── test_sprint1_debt_fixes.py
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_api.py             # End-to-end API tests via TestClient
│   └── test_workflow.py        # Workflow lifecycle tests
└── regression/                 # Regression tests for fixed bugs
    └── test_sprint_4_bugs.py
```

## Running Tests

All commands should be run from the `app/` directory.

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest -m unit
```

### Run Integration Tests Only

```bash
pytest -m integration
```

### Run a Specific Test File

```bash
pytest ../tests/unit/test_simulation_seed.py
```

### Run a Specific Test Function

```bash
pytest ../tests/unit/test_simulation_seed.py::test_seed_reproducibility -v
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in a browser
```

### Skip Slow Tests

```bash
pytest -m "not slow"
```

## Key Fixtures

All fixtures are defined in `tests/conftest.py`. The conftest dynamically derives test constants from the admin configuration defaults, so tests automatically adapt when configuration changes.

### Test Constants

```python
PRODUCT_TYPES  # List of product types from admin_config (e.g., ["credit_card", "residential_mortgage", ...])
SCENARIOS      # List of scenario keys from admin_config (e.g., ["baseline", "mild_recovery", ...])
MODEL_KEYS     # List of satellite model keys from admin_config
```

### sample_loans_df

A dynamically-sized DataFrame matching the `lb_model_ready_loans` schema. Generates at least 20 rows (or 4 per product type, whichever is larger) with realistic random values seeded at 42.

| Column | Values |
|--------|--------|
| `loan_id` | `LN-00001` through `LN-NNNNN` |
| `product_type` | Random from `PRODUCT_TYPES` |
| `assessed_stage` | Random from [1, 1, 1, 2, 3] (weighted toward Stage 1) |
| `gross_carrying_amount` | Uniform [500, 25000] |
| `effective_interest_rate` | Uniform [0.05, 0.35] |
| `current_lifetime_pd` | Uniform [0.005, 0.40] |
| `remaining_months` | Integer [3, 60] |

### sample_portfolio_df

Portfolio summary data grouped by product type. One row per product type with aggregated statistics.

| Column | Values |
|--------|--------|
| `product_type` | All `PRODUCT_TYPES` |
| `loan_count` | Random [10000, 20000] |
| `total_gca` | Random [5M, 50M] |
| `avg_eir_pct` | Random [10, 35] |
| `avg_dpd` | Random [2, 20] |
| `stage_1_count`, `stage_2_count`, `stage_3_count` | Realistic per-stage counts |

### sample_scenarios_df

Scenario distribution data matching `mc_ecl_distribution` schema. One row per scenario, derived from admin config scenario definitions.

| Column | Values |
|--------|--------|
| `scenario` | All `SCENARIOS` |
| `weight` | From admin config |
| `ecl_mean` | Random [1.5M, 9M] |
| `ecl_p50`, `ecl_p75`, `ecl_p95`, `ecl_p99` | Percentile multiples of ecl_mean |
| `avg_pd_multiplier`, `avg_lgd_multiplier` | From admin config |
| `pd_vol`, `lgd_vol` | Random volatilities |

### mock_db

Patches `backend._pool`, `backend.init_pool`, `backend.query_df`, and `backend.execute` to avoid real database calls. Returns a dict with the mock objects so tests can configure return values:

```python
def test_something(mock_db):
    mock_db["query_df"].return_value = pd.DataFrame({"col": [1, 2, 3]})
    # ... call function under test ...
    mock_db["query_df"].assert_called_once()
```

## Key Test Files by Domain

### ECL Engine

- **`test_ecl_engine.py`**: Core simulation tests -- parameter handling, result structure, NaN safety.
- **`test_simulation_seed.py`**: Seed reproducibility -- verifies identical seeds produce identical results, different seeds produce different results.
- **`test_qa_sprint_5_ecl_engine.py`**: Extended ECL engine coverage including edge cases (zero loans, extreme parameters, single-scenario runs).

### Backend and Routes

- **`test_backend.py`**: Database layer tests -- `query_df()`, `execute()`, connection pool behavior, retry logic.
- **`test_qa_sprint_1_core_routes.py`**: Core route handler tests for health, projects, data endpoints.
- **`test_route_handlers_sprint4.py`**: Route handler tests for sign-off, overlays, hash verification.
- **`test_qa_sprint_9_middleware.py`**: Middleware tests -- RequestIDMiddleware, ErrorHandlerMiddleware behavior.
- **`test_qa_sprint_9_db_pool.py`**: Connection pool tests -- initialization, token refresh, retry on auth errors.

### Model Governance

- **`test_model_registry.py`**: Model CRUD, status transitions (draft to validated to champion to retired), champion promotion.
- **`test_models.py`**: Model route handler tests.
- **`test_model_runs.py`**: Simulation run persistence and retrieval.

### Statistical Models

- **`test_hazard.py`**: Hazard model estimation (Cox PH, Kaplan-Meier, discrete logistic), survival curves, term structures.
- **`test_markov.py`**: Transition matrix estimation, matrix exponentiation forecasting, lifetime PD computation.
- **`test_backtesting.py`**: Backtest execution, statistical tests (binomial, traffic light), result structure.

### Governance and Reporting

- **`test_rbac.py`**: Role-based access control, permission checks, approval workflows, segregation of duties.
- **`test_audit_trail.py`**: Hash-chained audit trail integrity, chain verification, export.
- **`test_gl_journals.py`**: Journal generation, posting, reversal, trial balance.
- **`test_reports_routes.py`**: Report generation, listing, export (CSV/PDF), finalization.
- **`test_reporting_sprint3.py`**: IFRS 7 disclosure, ECL movement, stage migration report content.

### Configuration and Admin

- **`test_admin_config.py`**: Configuration CRUD, section management, column mapping validation, defaults seeding.
- **`test_config_audit_sprint6.py`**: Configuration change audit logging, diff computation.
- **`test_qa_sprint_4_audit_admin_mapping.py`**: Admin routes, data mapping, audit trail integration.

## Frontend Testing

Frontend tests use Vitest and are located in the `frontend/` directory.

### Running Frontend Tests

```bash
cd frontend
npm run test
```

### Running with Coverage

```bash
cd frontend
npm run test -- --coverage
```

Frontend tests cover React component rendering, user interaction flows, API integration hooks, and chart/visualization components.

## Writing New Tests

### Conventions

1. **File naming**: `test_{module_name}.py` in the appropriate directory (`unit/`, `integration/`, or `regression/`).
2. **Test naming**: `test_{behavior_being_tested}` -- descriptive names that explain what is being verified.
3. **Markers**: Apply `@pytest.mark.unit` for fast, isolated tests; `@pytest.mark.integration` for tests that exercise multiple modules; `@pytest.mark.slow` for tests that take more than a few seconds.
4. **Database isolation**: Always use the `mock_db` fixture to avoid real database calls in unit tests.
5. **Fixture reuse**: Use the shared fixtures (`sample_loans_df`, `sample_portfolio_df`, `sample_scenarios_df`) rather than creating new test DataFrames unless your test requires specific data patterns.

### Example Unit Test

```python
import pytest
import pandas as pd
from unittest.mock import patch

@pytest.mark.unit
class TestPortfolioSummary:
    """Tests for the portfolio summary data endpoint."""

    def test_returns_all_product_types(self, mock_db, sample_portfolio_df):
        """Portfolio summary should include every configured product type."""
        mock_db["query_df"].return_value = sample_portfolio_df

        from routes.data import portfolio_summary
        result = portfolio_summary()

        product_types = {r["product_type"] for r in result}
        from conftest import PRODUCT_TYPES
        assert product_types == set(PRODUCT_TYPES)

    def test_handles_empty_portfolio(self, mock_db):
        """Should return empty list when no portfolio data exists."""
        mock_db["query_df"].return_value = pd.DataFrame()

        from routes.data import portfolio_summary
        result = portfolio_summary()
        assert result == []
```

### Example Integration Test

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
class TestSimulationWorkflow:
    """End-to-end simulation workflow tests."""

    def test_validate_then_simulate(self, mock_db, sample_loans_df):
        """Validation should pass before simulation runs."""
        from app import app
        client = TestClient(app)

        # Step 1: Validate parameters
        response = client.post("/api/simulate-validate", json={
            "n_simulations": 500,
            "pd_lgd_correlation": 0.30,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
```

### Test Data Patterns

When the shared fixtures do not match your test scenario, create targeted data within the test:

```python
def test_stage_3_high_pd(self, mock_db):
    """Stage 3 loans with high PD should produce high coverage ratios."""
    loans = pd.DataFrame({
        "loan_id": ["LN-TEST-001"],
        "product_type": ["commercial_loan"],
        "assessed_stage": [3],
        "gross_carrying_amount": [100000.0],
        "effective_interest_rate": [0.10],
        "current_lifetime_pd": [0.50],
        "remaining_months": [36],
    })
    mock_db["query_df"].return_value = loans
    # ... test logic ...
```

### Mocking Patterns

For tests that need to mock specific backend functions:

```python
from unittest.mock import patch, MagicMock

@patch("backend.get_project")
def test_project_not_found(mock_get, mock_db):
    mock_get.return_value = None
    # ... test that 404 is raised ...

@patch("ecl_engine.run_simulation")
def test_simulation_error_handling(mock_sim, mock_db):
    mock_sim.side_effect = ValueError("No loans found")
    # ... test that 500 is returned with error message ...
```

### Common Pitfalls

- **Import ordering**: The test conftest temporarily swaps `backend` for a mock during import to allow `admin_config` to resolve at module level. If you import `backend` at the top of a test file, ensure it is after conftest runs.
- **Database state**: Never assume tables exist in unit tests. Always mock `query_df` and `execute`.
- **Decimal precision**: Use `pytest.approx()` when comparing floating-point ECL values, as Monte Carlo results have inherent variance.
- **Random seeds**: When testing simulation determinism, always provide an explicit `random_seed` parameter.

## What's Next?

- **[Architecture](architecture)** — System design and module structure that the test suite validates
- **[API Reference](api-reference)** — Endpoint documentation for writing integration tests with `TestClient`
- **[Data Model](data-model)** — Table schemas that `sample_loans_df` and other fixtures mirror
- **[ECL Engine](ecl-engine)** — The simulation engine tested by `test_ecl_engine.py` and `test_simulation_seed.py`
