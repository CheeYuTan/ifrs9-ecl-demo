"""
Shared fixtures for the IFRS 9 ECL test suite.

Provides mock database connections, realistic loan/portfolio/scenario DataFrames,
a FastAPI test client, and macro data for satellite model testing.
"""
import sys
import os
import json
import unittest.mock
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(PROJECT_ROOT, "app")
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
MODELS_DIR = os.path.join(SCRIPTS_DIR, "models")

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

for p in (APP_DIR, SCRIPTS_DIR, MODELS_DIR, TESTS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# Import the real backend first (it doesn't connect at import time), then
# temporarily swap it for a mock so admin_config can resolve backend.SCHEMA
# at module level without a live DB.  Restore the real module immediately
# after so test_backend.py (and any other test that needs the real module)
# continues to work.
import backend as _real_backend  # noqa: E402 — real module, no DB call at import

_mock_backend = unittest.mock.MagicMock()
_mock_backend.SCHEMA = _real_backend.SCHEMA
_mock_backend.PREFIX = _real_backend.PREFIX
sys.modules['backend'] = _mock_backend

import admin_config  # noqa: E402

sys.modules['backend'] = _real_backend
admin_config.backend = _real_backend

# Derive from admin config defaults so tests adapt when config changes
PRODUCT_TYPES = list(admin_config.MODEL_CONFIG["lgd_assumptions"].keys())
SCENARIOS = [s["key"] for s in admin_config.APP_SETTINGS["scenarios"]]
MODEL_KEYS = list(admin_config.MODEL_CONFIG["satellite_models"].keys())


@pytest.fixture
def sample_loans_df():
    """Dynamic-length DataFrame matching the model_ready_loans schema."""
    rng = np.random.default_rng(42)
    n = max(20, len(PRODUCT_TYPES) * 4)
    return pd.DataFrame({
        "loan_id": [f"LN-{i:05d}" for i in range(1, n + 1)],
        "product_type": rng.choice(PRODUCT_TYPES, n).tolist(),
        "assessed_stage": rng.choice([1, 1, 1, 2, 3], n).tolist(),
        "gross_carrying_amount": np.round(rng.uniform(500, 25000, n), 2).tolist(),
        "effective_interest_rate": np.round(rng.uniform(0.05, 0.35, n), 4).tolist(),
        "current_lifetime_pd": np.round(rng.uniform(0.005, 0.40, n), 6).tolist(),
        "remaining_months": rng.integers(3, 60, n).tolist(),
    })


@pytest.fixture
def sample_portfolio_df():
    """Portfolio summary data grouped by product_type."""
    rng = np.random.default_rng(99)
    n = len(PRODUCT_TYPES)
    return pd.DataFrame({
        "product_type": PRODUCT_TYPES,
        "loan_count": rng.integers(10000, 20000, n).tolist(),
        "total_gca": np.round(rng.uniform(5_000_000, 50_000_000, n), 2).tolist(),
        "avg_eir_pct": np.round(rng.uniform(10, 35, n), 1).tolist(),
        "avg_dpd": np.round(rng.uniform(2, 20, n), 1).tolist(),
        "stage_1_count": rng.integers(8000, 17000, n).tolist(),
        "stage_2_count": rng.integers(1000, 4000, n).tolist(),
        "stage_3_count": rng.integers(500, 2000, n).tolist(),
    })


@pytest.fixture
def sample_scenarios_df():
    """Scenario data matching mc_ecl_distribution schema, derived from admin config."""
    rng = np.random.default_rng(77)
    n = len(SCENARIOS)
    scenario_defs = admin_config.APP_SETTINGS["scenarios"]
    weights = [s["weight"] for s in scenario_defs]
    pd_mults = [s["pd_multiplier"] for s in scenario_defs]
    lgd_mults = [s["lgd_multiplier"] for s in scenario_defs]
    ecl_means = np.round(rng.uniform(1_500_000, 9_000_000, n), 2).tolist()
    return pd.DataFrame({
        "scenario": SCENARIOS,
        "weight": weights,
        "ecl_mean": ecl_means,
        "ecl_p50": [e * 0.95 for e in ecl_means],
        "ecl_p75": [e * 1.10 for e in ecl_means],
        "ecl_p95": [e * 1.35 for e in ecl_means],
        "ecl_p99": [e * 1.55 for e in ecl_means],
        "avg_pd_multiplier": pd_mults,
        "avg_lgd_multiplier": lgd_mults,
        "pd_vol": np.round(rng.uniform(0.02, 0.15, n), 3).tolist(),
        "lgd_vol": np.round(rng.uniform(0.01, 0.10, n), 3).tolist(),
        "n_simulations": [1000] * n,
    })


@pytest.fixture
def mock_db():
    """Patch backend.query_df and backend.execute to avoid real DB calls.

    Returns a dict with the mock objects so tests can configure return values.
    """
    admin_config._initialized = False
    with patch("backend._pool", new=MagicMock()), \
         patch("backend.init_pool"), \
         patch("backend.query_df") as mock_query, \
         patch("backend.execute") as mock_exec:
        mock_query.return_value = pd.DataFrame()
        yield {"query_df": mock_query, "execute": mock_exec}
    admin_config._initialized = False


@pytest.fixture
def fastapi_client(mock_db):
    """FastAPI TestClient with backend fully mocked."""
    from fastapi.testclient import TestClient
    import app as app_module
    return TestClient(app_module.app)


@pytest.fixture
def macro_data():
    """Synthetic macro-economic data for satellite model testing.

    Returns X (20x3 numpy array) and y (20-element numpy array).
    Features: unemployment_rate, gdp_growth_rate, inflation_rate.
    Target: observed_default_rate.
    """
    rng = np.random.default_rng(123)
    n = 20
    unemployment = rng.uniform(3.0, 12.0, n)
    gdp_growth = rng.uniform(-3.0, 5.0, n)
    inflation = rng.uniform(1.0, 8.0, n)
    X = np.column_stack([unemployment, gdp_growth, inflation])
    noise = rng.normal(0, 0.005, n)
    y = np.clip(0.02 + 0.008 * unemployment - 0.003 * gdp_growth + 0.002 * inflation + noise, 0.005, 0.50)
    return X, y


@pytest.fixture
def macro_data_minimal():
    """Minimum viable data (5 rows) for edge-case model testing."""
    rng = np.random.default_rng(999)
    n = 5
    X = rng.uniform(0, 10, (n, 3))
    y = np.clip(0.05 + 0.01 * X[:, 0] - 0.005 * X[:, 1] + rng.normal(0, 0.002, n), 0.01, 0.50)
    return X, y


@pytest.fixture
def macro_data_constant_y():
    """Data where target y is constant — tests model robustness."""
    rng = np.random.default_rng(777)
    X = rng.uniform(0, 10, (20, 3))
    y = np.full(20, 0.05)
    return X, y


@pytest.fixture
def macro_data_correlated():
    """Highly correlated features — tests regularization models."""
    rng = np.random.default_rng(555)
    n = 20
    base = rng.uniform(3, 10, n)
    X = np.column_stack([base, base + rng.normal(0, 0.1, n), base * 0.5 + rng.normal(0, 0.05, n)])
    y = np.clip(0.01 * base + rng.normal(0, 0.002, n), 0.005, 0.50)
    return X, y


def _make_workflow_project(project_id="test-proj-001", step=1, signed=False):
    """Helper to build a realistic workflow project dict."""
    from backend import STEPS
    step_status = {s: "pending" for s in STEPS}
    step_status["create_project"] = "completed"
    audit = [{"ts": datetime.now(timezone.utc).isoformat(), "user": "Test User",
              "action": "Project Created", "detail": "Test project", "step": "create_project"}]
    proj = {
        "project_id": project_id,
        "project_name": "Test ECL Project",
        "project_type": "ifrs9",
        "description": "Automated test project",
        "reporting_date": "2025-12-31",
        "current_step": step,
        "step_status": step_status,
        "audit_log": audit,
        "overlays": [],
        "scenario_weights": {},
        "signed_off_by": "Auditor" if signed else None,
        "signed_off_at": datetime.now(timezone.utc).isoformat() if signed else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return proj
