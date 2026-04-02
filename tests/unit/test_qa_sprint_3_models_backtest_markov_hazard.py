"""
QA Sprint 3: Model Registry, Backtesting, Markov Chain, Hazard Model Endpoints.

Tests routes/models.py (7 endpoints), routes/backtesting.py (4 endpoints),
routes/markov.py (6 endpoints), routes/hazard.py (6 endpoints)
with mocked backend functions.
"""
import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(mock_db):
    import app as app_module
    return TestClient(app_module.app)


# ---------------------------------------------------------------------------
# Helpers — Model Registry
# ---------------------------------------------------------------------------

def _model_dict(**overrides):
    """Build a realistic model registry record."""
    base = {
        "model_id": "mdl-001",
        "model_name": "PD Logistic v1",
        "model_type": "PD",
        "algorithm": "logistic_regression",
        "version": 1,
        "description": "PD model using logistic regression",
        "status": "draft",
        "product_type": "mortgage",
        "cohort": "2024Q1",
        "parameters": {"intercept": -3.2, "unemployment_coeff": 0.45},
        "performance_metrics": {"auc": 0.82, "gini": 0.64, "ks": 0.38},
        "training_data_info": {"sample_size": 50000, "date_range": "2020-2023"},
        "is_champion": False,
        "created_by": "analyst1",
        "created_at": "2025-01-15T10:00:00",
        "approved_by": None,
        "approved_at": None,
        "promoted_by": None,
        "promoted_at": None,
        "retired_by": None,
        "retired_at": None,
        "notes": "",
        "parent_model_id": None,
    }
    base.update(overrides)
    return base


def _audit_entry(**overrides):
    """Build a model audit trail entry."""
    base = {
        "audit_id": "aud-001",
        "model_id": "mdl-001",
        "action": "registered",
        "old_status": None,
        "new_status": "draft",
        "performed_by": "analyst1",
        "performed_at": "2025-01-15T10:00:00",
        "comment": "Model registered",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Helpers — Backtesting
# ---------------------------------------------------------------------------

def _backtest_result(**overrides):
    """Build a realistic backtest result."""
    base = {
        "backtest_id": "BT-PD-20250115-abc123",
        "model_id": None,
        "model_type": "PD",
        "backtest_date": "2025-01-15T10:00:00",
        "observation_window": "12M",
        "outcome_window": "12M",
        "overall_traffic_light": "Green",
        "pass_count": 4,
        "amber_count": 1,
        "fail_count": 0,
        "total_loans": 5000,
        "config": {},
        "created_by": "system",
        "metrics": [
            {"metric_id": "m1", "metric_name": "AUC", "metric_value": 0.85,
             "threshold_green": 0.7, "threshold_amber": 0.6, "pass_fail": "Green", "detail": None},
            {"metric_id": "m2", "metric_name": "Gini", "metric_value": 0.70,
             "threshold_green": 0.4, "threshold_amber": 0.2, "pass_fail": "Green", "detail": None},
            {"metric_id": "m3", "metric_name": "KS", "metric_value": 0.42,
             "threshold_green": 0.3, "threshold_amber": 0.2, "pass_fail": "Green", "detail": None},
            {"metric_id": "m4", "metric_name": "PSI", "metric_value": 0.08,
             "threshold_green": 0.1, "threshold_amber": 0.25, "pass_fail": "Green", "detail": None},
            {"metric_id": "m5", "metric_name": "Brier", "metric_value": 0.12,
             "threshold_green": 0.15, "threshold_amber": 0.25, "pass_fail": "Green", "detail": None},
        ],
        "cohort_results": [
            {"cohort_id": "c1", "cohort_name": "mortgage", "predicted_rate": 0.03, "actual_rate": 0.025, "count": 3000, "abs_diff": 0.005},
            {"cohort_id": "c2", "cohort_name": "personal", "predicted_rate": 0.05, "actual_rate": 0.055, "count": 2000, "abs_diff": 0.005},
        ],
    }
    base.update(overrides)
    return base


def _backtest_list_entry(**overrides):
    """Build a backtest list entry (no metrics/cohorts)."""
    base = {
        "backtest_id": "BT-PD-20250115-abc123",
        "model_type": "PD",
        "backtest_date": "2025-01-15T10:00:00",
        "observation_window": "12M",
        "outcome_window": "12M",
        "overall_traffic_light": "Green",
        "pass_count": 4,
        "amber_count": 1,
        "fail_count": 0,
        "total_loans": 5000,
        "created_by": "system",
    }
    base.update(overrides)
    return base


def _trend_entry(**overrides):
    """Build a backtest trend entry."""
    base = {
        "backtest_id": "BT-PD-20250115-abc123",
        "backtest_date": "2025-01-15",
        "overall_traffic_light": "Green",
        "AUC": 0.85,
        "AUC_light": "Green",
        "Gini": 0.70,
        "Gini_light": "Green",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Helpers — Markov
# ---------------------------------------------------------------------------

def _markov_matrix(**overrides):
    """Build a realistic transition matrix record."""
    base = {
        "matrix_id": "tm-001",
        "model_name": "TM-All-All",
        "estimation_date": "2025-01-15",
        "matrix_data": {
            "states": ["Stage 1", "Stage 2", "Stage 3", "Default"],
            "matrix": [
                [0.90, 0.07, 0.02, 0.01],
                [0.05, 0.80, 0.10, 0.05],
                [0.01, 0.04, 0.70, 0.25],
                [0.00, 0.00, 0.00, 1.00],
            ],
        },
        "matrix_type": "annual",
        "product_type": None,
        "segment": None,
        "methodology": "cohort",
        "n_observations": 10000,
        "computed_at": "2025-01-15T10:00:00",
    }
    base.update(overrides)
    return base


def _markov_list_entry(**overrides):
    """Build a markov list entry (no matrix_data)."""
    base = {
        "matrix_id": "tm-001",
        "model_name": "TM-All-All",
        "estimation_date": "2025-01-15",
        "matrix_type": "annual",
        "product_type": None,
        "segment": None,
        "methodology": "cohort",
        "n_observations": 10000,
        "computed_at": "2025-01-15T10:00:00",
    }
    base.update(overrides)
    return base


def _forecast_result(**overrides):
    """Build a markov forecast result."""
    base = {
        "forecast_id": "fc-001",
        "matrix_id": "tm-001",
        "horizon_months": 12,
        "forecast_data": {
            "initial_distribution": [0.7, 0.2, 0.1, 0.0],
            "horizon_months": 12,
            "points": [
                {"month": 0, "Stage 1": 70.0, "Stage 2": 20.0, "Stage 3": 10.0, "Default": 0.0},
                {"month": 1, "Stage 1": 64.0, "Stage 2": 19.5, "Stage 3": 9.5, "Default": 7.0},
            ],
        },
    }
    base.update(overrides)
    return base


def _lifetime_pd_result(**overrides):
    """Build a markov lifetime PD result."""
    base = {
        "matrix_id": "tm-001",
        "max_months": 60,
        "pd_curves": {
            "Stage 1": [
                {"month": 0, "cumulative_pd": 0.0},
                {"month": 1, "cumulative_pd": 1.0},
                {"month": 2, "cumulative_pd": 1.9},
            ],
            "Stage 2": [
                {"month": 0, "cumulative_pd": 0.0},
                {"month": 1, "cumulative_pd": 5.0},
                {"month": 2, "cumulative_pd": 9.5},
            ],
            "Stage 3": [
                {"month": 0, "cumulative_pd": 0.0},
                {"month": 1, "cumulative_pd": 25.0},
                {"month": 2, "cumulative_pd": 43.75},
            ],
        },
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Helpers — Hazard
# ---------------------------------------------------------------------------

def _hazard_model(**overrides):
    """Build a realistic hazard model record."""
    base = {
        "model_id": "haz_cox_ph_20250115_abc12345",
        "model_type": "cox_ph",
        "estimation_date": "2025-01-15",
        "coefficients": {
            "covariates": [
                {"name": "days_past_due", "coefficient": 0.015, "se": 0.002, "p_value": 0.001},
                {"name": "gross_carrying_amount", "coefficient": -0.0001, "se": 0.00005, "p_value": 0.05},
            ],
        },
        "baseline_hazard": {str(t): round(0.002 * (1 + t * 0.01), 6) for t in range(1, 61)},
        "concordance_index": 0.78,
        "log_likelihood": -4500.5,
        "aic": 9005.0,
        "bic": 9020.0,
        "product_type": None,
        "segment": None,
        "n_observations": 8000,
        "n_events": 400,
        "created_at": "2025-01-15T10:00:00",
        "curves": [
            {
                "curve_id": "crv_001",
                "model_id": "haz_cox_ph_20250115_abc12345",
                "segment": "all",
                "time_points": list(range(1, 61)),
                "survival_probs": [round(0.998 ** t, 6) for t in range(1, 61)],
                "hazard_rates": [round(0.002 * (1 + t * 0.01), 6) for t in range(1, 61)],
            }
        ],
    }
    base.update(overrides)
    return base


def _hazard_list_entry(**overrides):
    """Build a hazard model list entry."""
    base = {
        "model_id": "haz_cox_ph_20250115_abc12345",
        "model_type": "cox_ph",
        "estimation_date": "2025-01-15",
        "concordance_index": 0.78,
        "log_likelihood": -4500.5,
        "aic": 9005.0,
        "bic": 9020.0,
        "product_type": None,
        "segment": None,
        "n_observations": 8000,
        "n_events": 400,
        "created_at": "2025-01-15T10:00:00",
    }
    base.update(overrides)
    return base


def _survival_curve_result(**overrides):
    """Build a survival curve result."""
    base = {
        "model_id": "haz_cox_ph_20250115_abc12345",
        "covariate_values": None,
        "time_points": list(range(1, 61)),
        "survival_probs": [round(0.998 ** t, 6) for t in range(1, 61)],
        "hazard_rates": [round(0.002 * (1 + t * 0.01), 6) for t in range(1, 61)],
        "pd_12_month": 0.023,
        "risk_multiplier": 1.0,
    }
    base.update(overrides)
    return base


def _term_structure_result(**overrides):
    """Build a PD term structure result."""
    base = {
        "model_id": "haz_cox_ph_20250115_abc12345",
        "model_type": "cox_ph",
        "time_points": list(range(1, 61)),
        "marginal_pd": [0.002 * (1 + t * 0.01) for t in range(1, 61)],
        "cumulative_pd": [round(1 - 0.998 ** t, 6) for t in range(1, 61)],
        "forward_pd": [0.01] * 60,
        "pd_12_month": 0.023,
        "pd_lifetime": 0.11,
    }
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════════════════════
# MODEL REGISTRY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestModelRegistryListModels:
    """GET /api/models — list models with optional filters."""

    @patch("backend.list_models")
    def test_list_models_happy(self, mock_list, client):
        mock_list.return_value = [_model_dict(), _model_dict(model_id="mdl-002", model_name="LGD v1", model_type="LGD")]
        resp = client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        mock_list.assert_called_once_with(None, None)

    @patch("backend.list_models")
    def test_list_models_filter_type(self, mock_list, client):
        mock_list.return_value = [_model_dict()]
        resp = client.get("/api/models?model_type=PD")
        assert resp.status_code == 200
        mock_list.assert_called_once_with("PD", None)

    @patch("backend.list_models")
    def test_list_models_filter_status(self, mock_list, client):
        mock_list.return_value = [_model_dict(status="approved")]
        resp = client.get("/api/models?status=approved")
        assert resp.status_code == 200
        mock_list.assert_called_once_with(None, "approved")

    @patch("backend.list_models")
    def test_list_models_both_filters(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/models?model_type=LGD&status=draft")
        assert resp.status_code == 200
        assert resp.json() == []
        mock_list.assert_called_once_with("LGD", "draft")

    @patch("backend.list_models")
    def test_list_models_empty(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/models")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.list_models")
    def test_list_models_500(self, mock_list, client):
        mock_list.side_effect = Exception("DB error")
        resp = client.get("/api/models")
        assert resp.status_code == 500
        assert "Failed to list models" in resp.json()["detail"]

    @patch("backend.list_models")
    def test_list_models_with_decimal_values(self, mock_list, client):
        mock_list.return_value = [_model_dict(performance_metrics={"auc": Decimal("0.85")})]
        resp = client.get("/api/models")
        assert resp.status_code == 200
        assert resp.json()[0]["performance_metrics"]["auc"] == 0.85


class TestModelRegistryGetModel:
    """GET /api/models/{model_id} — get single model."""

    @patch("backend.get_model")
    def test_get_model_found(self, mock_get, client):
        mock_get.return_value = _model_dict()
        resp = client.get("/api/models/mdl-001")
        assert resp.status_code == 200
        assert resp.json()["model_id"] == "mdl-001"

    @patch("backend.get_model")
    def test_get_model_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/models/nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    @patch("backend.get_model")
    def test_get_model_500(self, mock_get, client):
        mock_get.side_effect = Exception("DB error")
        resp = client.get("/api/models/mdl-001")
        assert resp.status_code == 500

    @patch("backend.get_model")
    def test_get_model_returns_all_fields(self, mock_get, client):
        model = _model_dict()
        mock_get.return_value = model
        resp = client.get("/api/models/mdl-001")
        data = resp.json()
        for key in ("model_id", "model_name", "model_type", "algorithm", "version",
                     "status", "parameters", "performance_metrics", "is_champion"):
            assert key in data

    @patch("backend.get_model")
    def test_get_model_with_champion_flag(self, mock_get, client):
        mock_get.return_value = _model_dict(is_champion=True)
        resp = client.get("/api/models/mdl-001")
        assert resp.json()["is_champion"] is True


class TestModelRegistryRegister:
    """POST /api/models — register new model."""

    @patch("backend.register_model")
    def test_register_happy(self, mock_reg, client):
        mock_reg.return_value = _model_dict()
        resp = client.post("/api/models", json={
            "model_name": "PD Logistic v1",
            "model_type": "PD",
            "algorithm": "logistic_regression",
        })
        assert resp.status_code == 200
        mock_reg.assert_called_once()
        call_data = mock_reg.call_args[0][0]
        assert call_data["model_name"] == "PD Logistic v1"
        assert call_data["model_type"] == "PD"

    @patch("backend.register_model")
    def test_register_with_all_fields(self, mock_reg, client):
        mock_reg.return_value = _model_dict()
        payload = {
            "model_name": "PD Logistic v1",
            "model_type": "PD",
            "algorithm": "logistic_regression",
            "version": 2,
            "description": "Updated PD model",
            "product_type": "mortgage",
            "cohort": "2024Q1",
            "parameters": {"intercept": -3.2},
            "performance_metrics": {"auc": 0.82},
            "training_data_info": {"sample_size": 50000},
            "created_by": "analyst1",
            "notes": "Initial registration",
            "parent_model_id": "mdl-000",
        }
        resp = client.post("/api/models", json=payload)
        assert resp.status_code == 200
        call_data = mock_reg.call_args[0][0]
        assert call_data["version"] == 2
        assert call_data["parent_model_id"] == "mdl-000"

    @patch("backend.register_model")
    def test_register_minimal_payload(self, mock_reg, client):
        mock_reg.return_value = _model_dict()
        resp = client.post("/api/models", json={
            "model_name": "Test",
            "model_type": "LGD",
        })
        assert resp.status_code == 200
        call_data = mock_reg.call_args[0][0]
        assert call_data["algorithm"] == "Unknown"
        assert call_data["version"] == 1

    def test_register_missing_required_fields(self, client):
        resp = client.post("/api/models", json={})
        assert resp.status_code == 422

    def test_register_missing_model_name(self, client):
        resp = client.post("/api/models", json={"model_type": "PD"})
        assert resp.status_code == 422

    def test_register_missing_model_type(self, client):
        resp = client.post("/api/models", json={"model_name": "Test"})
        assert resp.status_code == 422

    @patch("backend.register_model")
    def test_register_500(self, mock_reg, client):
        mock_reg.side_effect = Exception("DB insert error")
        resp = client.post("/api/models", json={
            "model_name": "Test", "model_type": "PD",
        })
        assert resp.status_code == 500


class TestModelRegistryUpdateStatus:
    """PUT /api/models/{model_id}/status — status transitions."""

    @patch("backend.update_model_status")
    def test_valid_transition_draft_to_pending(self, mock_update, client):
        mock_update.return_value = _model_dict(status="pending_review")
        resp = client.put("/api/models/mdl-001/status", json={
            "status": "pending_review", "user": "analyst1",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending_review"

    @patch("backend.update_model_status")
    def test_valid_transition_pending_to_approved(self, mock_update, client):
        mock_update.return_value = _model_dict(status="approved", approved_by="reviewer1")
        resp = client.put("/api/models/mdl-001/status", json={
            "status": "approved", "user": "reviewer1", "comment": "Looks good",
        })
        assert resp.status_code == 200

    @patch("backend.update_model_status")
    def test_invalid_transition_returns_400(self, mock_update, client):
        mock_update.side_effect = ValueError("Cannot transition from 'draft' to 'active'")
        resp = client.put("/api/models/mdl-001/status", json={
            "status": "active", "user": "analyst1",
        })
        assert resp.status_code == 400
        assert "Cannot transition" in resp.json()["detail"]

    @patch("backend.update_model_status")
    def test_invalid_transition_draft_to_retired(self, mock_update, client):
        mock_update.side_effect = ValueError("Cannot transition from 'draft' to 'retired'")
        resp = client.put("/api/models/mdl-001/status", json={
            "status": "retired", "user": "admin",
        })
        assert resp.status_code == 400

    @patch("backend.update_model_status")
    def test_model_not_found_returns_400(self, mock_update, client):
        mock_update.side_effect = ValueError("Model xxx not found")
        resp = client.put("/api/models/xxx/status", json={
            "status": "pending_review", "user": "analyst1",
        })
        assert resp.status_code == 400

    def test_missing_status_field(self, client):
        resp = client.put("/api/models/mdl-001/status", json={"user": "analyst1"})
        assert resp.status_code == 422

    def test_missing_user_field(self, client):
        resp = client.put("/api/models/mdl-001/status", json={"status": "pending_review"})
        assert resp.status_code == 422

    @patch("backend.update_model_status")
    def test_update_status_500(self, mock_update, client):
        mock_update.side_effect = Exception("DB error")
        resp = client.put("/api/models/mdl-001/status", json={
            "status": "pending_review", "user": "analyst1",
        })
        assert resp.status_code == 500

    @patch("backend.update_model_status")
    def test_transition_with_comment(self, mock_update, client):
        mock_update.return_value = _model_dict(status="pending_review")
        resp = client.put("/api/models/mdl-001/status", json={
            "status": "pending_review", "user": "analyst1", "comment": "Ready for review",
        })
        assert resp.status_code == 200
        mock_update.assert_called_once_with("mdl-001", "pending_review", "analyst1", "Ready for review")


class TestModelRegistryPromote:
    """POST /api/models/{model_id}/promote — promote champion."""

    @patch("backend.promote_champion")
    def test_promote_happy(self, mock_promote, client):
        mock_promote.return_value = _model_dict(is_champion=True, status="approved")
        resp = client.post("/api/models/mdl-001/promote", json={"user": "admin"})
        assert resp.status_code == 200
        assert resp.json()["is_champion"] is True

    @patch("backend.promote_champion")
    def test_promote_invalid_status_returns_400(self, mock_promote, client):
        mock_promote.side_effect = ValueError("Only approved or active models can be promoted")
        resp = client.post("/api/models/mdl-001/promote", json={"user": "admin"})
        assert resp.status_code == 400
        assert "approved or active" in resp.json()["detail"]

    @patch("backend.promote_champion")
    def test_promote_not_found_returns_400(self, mock_promote, client):
        mock_promote.side_effect = ValueError("Model xxx not found")
        resp = client.post("/api/models/xxx/promote", json={"user": "admin"})
        assert resp.status_code == 400

    def test_promote_missing_user(self, client):
        resp = client.post("/api/models/mdl-001/promote", json={})
        assert resp.status_code == 422

    @patch("backend.promote_champion")
    def test_promote_500(self, mock_promote, client):
        mock_promote.side_effect = Exception("DB error")
        resp = client.post("/api/models/mdl-001/promote", json={"user": "admin"})
        assert resp.status_code == 500


class TestModelRegistryCompare:
    """POST /api/models/compare — side-by-side comparison."""

    @patch("backend.compare_models")
    def test_compare_happy(self, mock_compare, client):
        mock_compare.return_value = [_model_dict(), _model_dict(model_id="mdl-002")]
        resp = client.post("/api/models/compare", json={"model_ids": ["mdl-001", "mdl-002"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @patch("backend.compare_models")
    def test_compare_empty_ids(self, mock_compare, client):
        mock_compare.return_value = []
        resp = client.post("/api/models/compare", json={"model_ids": []})
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.compare_models")
    def test_compare_single_id(self, mock_compare, client):
        mock_compare.return_value = [_model_dict()]
        resp = client.post("/api/models/compare", json={"model_ids": ["mdl-001"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("backend.compare_models")
    def test_compare_500(self, mock_compare, client):
        mock_compare.side_effect = Exception("DB error")
        resp = client.post("/api/models/compare", json={"model_ids": ["mdl-001"]})
        assert resp.status_code == 500

    def test_compare_missing_model_ids(self, client):
        resp = client.post("/api/models/compare", json={})
        assert resp.status_code == 422


class TestModelRegistryAudit:
    """GET /api/models/{model_id}/audit — audit trail."""

    @patch("backend.get_model_audit_trail")
    def test_audit_happy(self, mock_audit, client):
        mock_audit.return_value = [
            _audit_entry(),
            _audit_entry(audit_id="aud-002", action="submitted_for_review", old_status="draft", new_status="pending_review"),
        ]
        resp = client.get("/api/models/mdl-001/audit")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @patch("backend.get_model_audit_trail")
    def test_audit_empty(self, mock_audit, client):
        mock_audit.return_value = []
        resp = client.get("/api/models/mdl-001/audit")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.get_model_audit_trail")
    def test_audit_500(self, mock_audit, client):
        mock_audit.side_effect = Exception("DB error")
        resp = client.get("/api/models/mdl-001/audit")
        assert resp.status_code == 500

    @patch("backend.get_model_audit_trail")
    def test_audit_contains_expected_fields(self, mock_audit, client):
        mock_audit.return_value = [_audit_entry()]
        resp = client.get("/api/models/mdl-001/audit")
        entry = resp.json()[0]
        for key in ("audit_id", "model_id", "action", "performed_by", "performed_at"):
            assert key in entry


# ═══════════════════════════════════════════════════════════════════════════
# BACKTESTING TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestBacktestRun:
    """POST /api/backtest/run — execute backtest."""

    @patch("backend.run_backtest")
    def test_run_pd_happy(self, mock_run, client):
        mock_run.return_value = _backtest_result()
        resp = client.post("/api/backtest/run", json={"model_type": "PD"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_traffic_light"] == "Green"
        mock_run.assert_called_once_with("PD", {})

    @patch("backend.run_backtest")
    def test_run_lgd_happy(self, mock_run, client):
        mock_run.return_value = _backtest_result(model_type="LGD", overall_traffic_light="Amber")
        resp = client.post("/api/backtest/run", json={"model_type": "LGD"})
        assert resp.status_code == 200
        assert resp.json()["model_type"] == "LGD"
        mock_run.assert_called_once_with("LGD", {})

    @patch("backend.run_backtest")
    def test_run_with_config(self, mock_run, client):
        config = {"observation_window": "24M", "created_by": "tester"}
        mock_run.return_value = _backtest_result()
        resp = client.post("/api/backtest/run", json={"model_type": "PD", "config": config})
        assert resp.status_code == 200
        mock_run.assert_called_once_with("PD", config)

    @patch("backend.run_backtest")
    def test_run_default_model_type(self, mock_run, client):
        """Default model_type should be PD."""
        mock_run.return_value = _backtest_result()
        resp = client.post("/api/backtest/run", json={})
        assert resp.status_code == 200
        mock_run.assert_called_once_with("PD", {})

    @patch("backend.run_backtest")
    def test_run_no_data_returns_400(self, mock_run, client):
        mock_run.side_effect = ValueError("No portfolio data available for backtesting")
        resp = client.post("/api/backtest/run", json={"model_type": "PD"})
        assert resp.status_code == 400
        assert "No portfolio data" in resp.json()["detail"]

    @patch("backend.run_backtest")
    def test_run_500(self, mock_run, client):
        mock_run.side_effect = Exception("DB error")
        resp = client.post("/api/backtest/run", json={"model_type": "PD"})
        assert resp.status_code == 500

    @patch("backend.run_backtest")
    def test_run_result_has_metrics(self, mock_run, client):
        mock_run.return_value = _backtest_result()
        resp = client.post("/api/backtest/run", json={"model_type": "PD"})
        data = resp.json()
        assert "metrics" in data
        assert len(data["metrics"]) == 5
        metric_names = {m["metric_name"] for m in data["metrics"]}
        assert "AUC" in metric_names
        assert "Gini" in metric_names

    @patch("backend.run_backtest")
    def test_run_result_has_cohorts(self, mock_run, client):
        mock_run.return_value = _backtest_result()
        resp = client.post("/api/backtest/run", json={"model_type": "PD"})
        data = resp.json()
        assert "cohort_results" in data
        assert len(data["cohort_results"]) == 2

    @patch("backend.run_backtest")
    def test_run_result_traffic_light_counts(self, mock_run, client):
        result = _backtest_result(pass_count=3, amber_count=1, fail_count=1, overall_traffic_light="Amber")
        mock_run.return_value = result
        resp = client.post("/api/backtest/run", json={"model_type": "PD"})
        data = resp.json()
        assert data["pass_count"] == 3
        assert data["amber_count"] == 1
        assert data["fail_count"] == 1
        assert data["overall_traffic_light"] == "Amber"


class TestBacktestList:
    """GET /api/backtest/results — list backtests."""

    @patch("backend.list_backtests")
    def test_list_happy(self, mock_list, client):
        mock_list.return_value = [_backtest_list_entry()]
        resp = client.get("/api/backtest/results")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        mock_list.assert_called_once_with(None)

    @patch("backend.list_backtests")
    def test_list_filter_model_type(self, mock_list, client):
        mock_list.return_value = [_backtest_list_entry()]
        resp = client.get("/api/backtest/results?model_type=PD")
        assert resp.status_code == 200
        mock_list.assert_called_once_with("PD")

    @patch("backend.list_backtests")
    def test_list_empty(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/backtest/results")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.list_backtests")
    def test_list_500(self, mock_list, client):
        mock_list.side_effect = Exception("DB error")
        resp = client.get("/api/backtest/results")
        assert resp.status_code == 500

    @patch("backend.list_backtests")
    def test_list_multiple_entries(self, mock_list, client):
        entries = [
            _backtest_list_entry(backtest_id="BT-PD-1"),
            _backtest_list_entry(backtest_id="BT-PD-2", overall_traffic_light="Amber"),
            _backtest_list_entry(backtest_id="BT-LGD-1", model_type="LGD"),
        ]
        mock_list.return_value = entries
        resp = client.get("/api/backtest/results")
        assert len(resp.json()) == 3


class TestBacktestTrend:
    """GET /api/backtest/trend/{model_type} — metric trend."""

    @patch("backend.get_backtest_trend")
    def test_trend_happy(self, mock_trend, client):
        mock_trend.return_value = [_trend_entry()]
        resp = client.get("/api/backtest/trend/PD")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "AUC" in data[0]
        mock_trend.assert_called_once_with("PD")

    @patch("backend.get_backtest_trend")
    def test_trend_empty(self, mock_trend, client):
        mock_trend.return_value = []
        resp = client.get("/api/backtest/trend/LGD")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.get_backtest_trend")
    def test_trend_multiple(self, mock_trend, client):
        entries = [
            _trend_entry(backtest_id="BT-1", AUC=0.85),
            _trend_entry(backtest_id="BT-2", AUC=0.87),
            _trend_entry(backtest_id="BT-3", AUC=0.83),
        ]
        mock_trend.return_value = entries
        resp = client.get("/api/backtest/trend/PD")
        assert len(resp.json()) == 3

    @patch("backend.get_backtest_trend")
    def test_trend_500(self, mock_trend, client):
        mock_trend.side_effect = Exception("DB error")
        resp = client.get("/api/backtest/trend/PD")
        assert resp.status_code == 500


class TestBacktestGet:
    """GET /api/backtest/{backtest_id} — get single backtest."""

    @patch("backend.get_backtest")
    def test_get_found(self, mock_get, client):
        mock_get.return_value = _backtest_result()
        resp = client.get("/api/backtest/BT-PD-20250115-abc123")
        assert resp.status_code == 200
        assert resp.json()["backtest_id"] == "BT-PD-20250115-abc123"

    @patch("backend.get_backtest")
    def test_get_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/backtest/nonexistent")
        assert resp.status_code == 404

    @patch("backend.get_backtest")
    def test_get_500(self, mock_get, client):
        mock_get.side_effect = Exception("DB error")
        resp = client.get("/api/backtest/BT-PD-1")
        assert resp.status_code == 500

    @patch("backend.get_backtest")
    def test_get_includes_metrics_and_cohorts(self, mock_get, client):
        mock_get.return_value = _backtest_result()
        resp = client.get("/api/backtest/BT-PD-1")
        data = resp.json()
        assert "metrics" in data
        assert "cohort_results" in data

    @patch("backend.get_backtest")
    def test_get_with_decimal_metrics(self, mock_get, client):
        result = _backtest_result()
        result["metrics"][0]["metric_value"] = Decimal("0.85")
        mock_get.return_value = result
        resp = client.get("/api/backtest/BT-PD-1")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# MARKOV CHAIN TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestMarkovEstimate:
    """POST /api/markov/estimate — estimate transition matrix."""

    @patch("backend.estimate_transition_matrix")
    def test_estimate_happy(self, mock_est, client):
        mock_est.return_value = _markov_matrix()
        resp = client.post("/api/markov/estimate", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "matrix_data" in data
        assert data["matrix_data"]["states"] == ["Stage 1", "Stage 2", "Stage 3", "Default"]
        mock_est.assert_called_once_with(None, None)

    @patch("backend.estimate_transition_matrix")
    def test_estimate_with_product_type(self, mock_est, client):
        mock_est.return_value = _markov_matrix(product_type="mortgage")
        resp = client.post("/api/markov/estimate", json={"product_type": "mortgage"})
        assert resp.status_code == 200
        mock_est.assert_called_once_with("mortgage", None)

    @patch("backend.estimate_transition_matrix")
    def test_estimate_with_segment(self, mock_est, client):
        mock_est.return_value = _markov_matrix(segment="retail")
        resp = client.post("/api/markov/estimate", json={"segment": "retail"})
        assert resp.status_code == 200
        mock_est.assert_called_once_with(None, "retail")

    @patch("backend.estimate_transition_matrix")
    def test_estimate_matrix_rows_sum_to_1(self, mock_est, client):
        mock_est.return_value = _markov_matrix()
        resp = client.post("/api/markov/estimate", json={})
        matrix = resp.json()["matrix_data"]["matrix"]
        for row in matrix:
            assert abs(sum(row) - 1.0) < 1e-6

    @patch("backend.estimate_transition_matrix")
    def test_estimate_matrix_non_negative(self, mock_est, client):
        mock_est.return_value = _markov_matrix()
        resp = client.post("/api/markov/estimate", json={})
        matrix = resp.json()["matrix_data"]["matrix"]
        for row in matrix:
            for val in row:
                assert val >= 0

    @patch("backend.estimate_transition_matrix")
    def test_estimate_default_is_absorbing(self, mock_est, client):
        mock_est.return_value = _markov_matrix()
        resp = client.post("/api/markov/estimate", json={})
        matrix = resp.json()["matrix_data"]["matrix"]
        assert matrix[3] == [0.0, 0.0, 0.0, 1.0]

    @patch("backend.estimate_transition_matrix")
    def test_estimate_500(self, mock_est, client):
        mock_est.side_effect = Exception("DB error")
        resp = client.post("/api/markov/estimate", json={})
        assert resp.status_code == 500


class TestMarkovListMatrices:
    """GET /api/markov/matrices — list transition matrices."""

    @patch("backend.list_transition_matrices")
    def test_list_happy(self, mock_list, client):
        mock_list.return_value = [_markov_list_entry()]
        resp = client.get("/api/markov/matrices")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        mock_list.assert_called_once_with(None)

    @patch("backend.list_transition_matrices")
    def test_list_filter_product(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/markov/matrices?product_type=mortgage")
        assert resp.status_code == 200
        mock_list.assert_called_once_with("mortgage")

    @patch("backend.list_transition_matrices")
    def test_list_empty(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/markov/matrices")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.list_transition_matrices")
    def test_list_500(self, mock_list, client):
        mock_list.side_effect = Exception("DB error")
        resp = client.get("/api/markov/matrices")
        assert resp.status_code == 500


class TestMarkovGetMatrix:
    """GET /api/markov/matrix/{matrix_id} — get single matrix."""

    @patch("backend.get_transition_matrix")
    def test_get_found(self, mock_get, client):
        mock_get.return_value = _markov_matrix()
        resp = client.get("/api/markov/matrix/tm-001")
        assert resp.status_code == 200
        assert resp.json()["matrix_id"] == "tm-001"

    @patch("backend.get_transition_matrix")
    def test_get_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/markov/matrix/nonexistent")
        assert resp.status_code == 404

    @patch("backend.get_transition_matrix")
    def test_get_500(self, mock_get, client):
        mock_get.side_effect = Exception("DB error")
        resp = client.get("/api/markov/matrix/tm-001")
        assert resp.status_code == 500

    @patch("backend.get_transition_matrix")
    def test_get_contains_matrix_data(self, mock_get, client):
        mock_get.return_value = _markov_matrix()
        resp = client.get("/api/markov/matrix/tm-001")
        data = resp.json()
        assert "matrix_data" in data
        assert "states" in data["matrix_data"]
        assert "matrix" in data["matrix_data"]
        assert len(data["matrix_data"]["matrix"]) == 4


class TestMarkovForecast:
    """POST /api/markov/forecast — project stage distribution."""

    @patch("backend.forecast_stage_distribution")
    def test_forecast_happy(self, mock_fc, client):
        mock_fc.return_value = _forecast_result()
        resp = client.post("/api/markov/forecast", json={
            "matrix_id": "tm-001",
            "initial_distribution": [0.7, 0.2, 0.1, 0.0],
            "horizon_months": 12,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["horizon_months"] == 12
        assert "forecast_data" in data

    @patch("backend.forecast_stage_distribution")
    def test_forecast_distribution_sums_to_100(self, mock_fc, client):
        """Each forecast point distribution should sum to ~100%."""
        points = []
        for m in range(13):
            s1 = max(0, 70 - m * 2)
            s2 = 20 + m * 0.5
            s3 = 10 + m * 0.5
            default = 100 - s1 - s2 - s3
            points.append({"month": m, "Stage 1": s1, "Stage 2": s2, "Stage 3": s3, "Default": default})
        mock_fc.return_value = _forecast_result(forecast_data={
            "initial_distribution": [0.7, 0.2, 0.1, 0.0],
            "horizon_months": 12,
            "points": points,
        })
        resp = client.post("/api/markov/forecast", json={
            "matrix_id": "tm-001",
            "initial_distribution": [0.7, 0.2, 0.1, 0.0],
            "horizon_months": 12,
        })
        for point in resp.json()["forecast_data"]["points"]:
            total = point["Stage 1"] + point["Stage 2"] + point["Stage 3"] + point["Default"]
            assert abs(total - 100.0) < 0.01

    @patch("backend.forecast_stage_distribution")
    def test_forecast_matrix_not_found(self, mock_fc, client):
        mock_fc.side_effect = ValueError("Matrix xxx not found")
        resp = client.post("/api/markov/forecast", json={
            "matrix_id": "xxx",
            "initial_distribution": [1, 0, 0, 0],
        })
        assert resp.status_code == 404

    @patch("backend.forecast_stage_distribution")
    def test_forecast_default_horizon(self, mock_fc, client):
        mock_fc.return_value = _forecast_result(horizon_months=60)
        resp = client.post("/api/markov/forecast", json={
            "matrix_id": "tm-001",
            "initial_distribution": [1, 0, 0, 0],
        })
        assert resp.status_code == 200
        mock_fc.assert_called_once_with("tm-001", [1, 0, 0, 0], 60)

    @patch("backend.forecast_stage_distribution")
    def test_forecast_500(self, mock_fc, client):
        mock_fc.side_effect = Exception("DB error")
        resp = client.post("/api/markov/forecast", json={
            "matrix_id": "tm-001",
            "initial_distribution": [1, 0, 0, 0],
        })
        assert resp.status_code == 500

    def test_forecast_missing_matrix_id(self, client):
        resp = client.post("/api/markov/forecast", json={
            "initial_distribution": [1, 0, 0, 0],
        })
        assert resp.status_code == 422

    def test_forecast_missing_distribution(self, client):
        resp = client.post("/api/markov/forecast", json={
            "matrix_id": "tm-001",
        })
        assert resp.status_code == 422


class TestMarkovLifetimePD:
    """GET /api/markov/lifetime-pd/{matrix_id} — cumulative PD curves."""

    @patch("backend.compute_lifetime_pd")
    def test_lifetime_pd_happy(self, mock_lpd, client):
        mock_lpd.return_value = _lifetime_pd_result()
        resp = client.get("/api/markov/lifetime-pd/tm-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "pd_curves" in data
        assert "Stage 1" in data["pd_curves"]
        assert "Stage 2" in data["pd_curves"]
        assert "Stage 3" in data["pd_curves"]
        mock_lpd.assert_called_once_with("tm-001", 60)

    @patch("backend.compute_lifetime_pd")
    def test_lifetime_pd_custom_months(self, mock_lpd, client):
        mock_lpd.return_value = _lifetime_pd_result(max_months=120)
        resp = client.get("/api/markov/lifetime-pd/tm-001?max_months=120")
        assert resp.status_code == 200
        mock_lpd.assert_called_once_with("tm-001", 120)

    @patch("backend.compute_lifetime_pd")
    def test_lifetime_pd_monotonic_non_decreasing(self, mock_lpd, client):
        """Cumulative PD should never decrease over time."""
        mock_lpd.return_value = _lifetime_pd_result()
        resp = client.get("/api/markov/lifetime-pd/tm-001")
        for stage, curve in resp.json()["pd_curves"].items():
            for i in range(1, len(curve)):
                assert curve[i]["cumulative_pd"] >= curve[i - 1]["cumulative_pd"], \
                    f"{stage} month {curve[i]['month']}: PD decreased"

    @patch("backend.compute_lifetime_pd")
    def test_lifetime_pd_starts_at_zero(self, mock_lpd, client):
        mock_lpd.return_value = _lifetime_pd_result()
        resp = client.get("/api/markov/lifetime-pd/tm-001")
        for stage, curve in resp.json()["pd_curves"].items():
            assert curve[0]["cumulative_pd"] == 0.0

    @patch("backend.compute_lifetime_pd")
    def test_lifetime_pd_matrix_not_found(self, mock_lpd, client):
        mock_lpd.side_effect = ValueError("Matrix xxx not found")
        resp = client.get("/api/markov/lifetime-pd/xxx")
        assert resp.status_code == 404

    @patch("backend.compute_lifetime_pd")
    def test_lifetime_pd_500(self, mock_lpd, client):
        mock_lpd.side_effect = Exception("DB error")
        resp = client.get("/api/markov/lifetime-pd/tm-001")
        assert resp.status_code == 500


class TestMarkovCompare:
    """POST /api/markov/compare — side-by-side comparison."""

    @patch("backend.compare_matrices")
    def test_compare_happy(self, mock_cmp, client):
        mock_cmp.return_value = [_markov_matrix(), _markov_matrix(matrix_id="tm-002")]
        resp = client.post("/api/markov/compare", json={"matrix_ids": ["tm-001", "tm-002"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @patch("backend.compare_matrices")
    def test_compare_empty(self, mock_cmp, client):
        mock_cmp.return_value = []
        resp = client.post("/api/markov/compare", json={"matrix_ids": []})
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.compare_matrices")
    def test_compare_single(self, mock_cmp, client):
        mock_cmp.return_value = [_markov_matrix()]
        resp = client.post("/api/markov/compare", json={"matrix_ids": ["tm-001"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("backend.compare_matrices")
    def test_compare_500(self, mock_cmp, client):
        mock_cmp.side_effect = Exception("DB error")
        resp = client.post("/api/markov/compare", json={"matrix_ids": ["tm-001"]})
        assert resp.status_code == 500

    def test_compare_missing_matrix_ids(self, client):
        resp = client.post("/api/markov/compare", json={})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# HAZARD MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestHazardEstimate:
    """POST /api/hazard/estimate — estimate hazard model."""

    @patch("backend.estimate_hazard_model")
    def test_estimate_cox_ph(self, mock_est, client):
        mock_est.return_value = _hazard_model()
        resp = client.post("/api/hazard/estimate", json={"model_type": "cox_ph"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_type"] == "cox_ph"
        mock_est.assert_called_once_with("cox_ph", None, None)

    @patch("backend.estimate_hazard_model")
    def test_estimate_discrete_time(self, mock_est, client):
        mock_est.return_value = _hazard_model(model_type="discrete_time")
        resp = client.post("/api/hazard/estimate", json={"model_type": "discrete_time"})
        assert resp.status_code == 200
        assert resp.json()["model_type"] == "discrete_time"

    @patch("backend.estimate_hazard_model")
    def test_estimate_kaplan_meier(self, mock_est, client):
        mock_est.return_value = _hazard_model(model_type="kaplan_meier")
        resp = client.post("/api/hazard/estimate", json={"model_type": "kaplan_meier"})
        assert resp.status_code == 200
        assert resp.json()["model_type"] == "kaplan_meier"

    @patch("backend.estimate_hazard_model")
    def test_estimate_with_product_type(self, mock_est, client):
        mock_est.return_value = _hazard_model(product_type="mortgage")
        resp = client.post("/api/hazard/estimate", json={"model_type": "cox_ph", "product_type": "mortgage"})
        assert resp.status_code == 200
        mock_est.assert_called_once_with("cox_ph", "mortgage", None)

    @patch("backend.estimate_hazard_model")
    def test_estimate_with_segment(self, mock_est, client):
        mock_est.return_value = _hazard_model(segment="retail")
        resp = client.post("/api/hazard/estimate", json={"model_type": "cox_ph", "segment": "retail"})
        assert resp.status_code == 200
        mock_est.assert_called_once_with("cox_ph", None, "retail")

    @patch("backend.estimate_hazard_model")
    def test_estimate_invalid_model_type_returns_400(self, mock_est, client):
        mock_est.side_effect = ValueError("Unknown model type: invalid_type")
        resp = client.post("/api/hazard/estimate", json={"model_type": "invalid_type"})
        assert resp.status_code == 400
        assert "Unknown model type" in resp.json()["detail"]

    @patch("backend.estimate_hazard_model")
    def test_estimate_no_data_returns_400(self, mock_est, client):
        mock_est.side_effect = ValueError("No portfolio data available")
        resp = client.post("/api/hazard/estimate", json={"model_type": "cox_ph"})
        assert resp.status_code == 400

    @patch("backend.estimate_hazard_model")
    def test_estimate_500(self, mock_est, client):
        mock_est.side_effect = Exception("DB error")
        resp = client.post("/api/hazard/estimate", json={"model_type": "cox_ph"})
        assert resp.status_code == 500

    def test_estimate_missing_model_type(self, client):
        resp = client.post("/api/hazard/estimate", json={})
        assert resp.status_code == 422

    @patch("backend.estimate_hazard_model")
    def test_estimate_result_has_curves(self, mock_est, client):
        mock_est.return_value = _hazard_model()
        resp = client.post("/api/hazard/estimate", json={"model_type": "cox_ph"})
        data = resp.json()
        assert "curves" in data
        assert len(data["curves"]) > 0
        curve = data["curves"][0]
        assert "time_points" in curve
        assert "survival_probs" in curve
        assert "hazard_rates" in curve

    @patch("backend.estimate_hazard_model")
    def test_estimate_result_has_goodness_of_fit(self, mock_est, client):
        mock_est.return_value = _hazard_model()
        resp = client.post("/api/hazard/estimate", json={"model_type": "cox_ph"})
        data = resp.json()
        assert "concordance_index" in data
        assert "log_likelihood" in data
        assert "aic" in data
        assert "bic" in data


class TestHazardListModels:
    """GET /api/hazard/models — list hazard models."""

    @patch("backend.list_hazard_models")
    def test_list_happy(self, mock_list, client):
        mock_list.return_value = [_hazard_list_entry()]
        resp = client.get("/api/hazard/models")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        mock_list.assert_called_once_with(None, None)

    @patch("backend.list_hazard_models")
    def test_list_filter_model_type(self, mock_list, client):
        mock_list.return_value = [_hazard_list_entry()]
        resp = client.get("/api/hazard/models?model_type=cox_ph")
        assert resp.status_code == 200
        mock_list.assert_called_once_with("cox_ph", None)

    @patch("backend.list_hazard_models")
    def test_list_filter_product_type(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/hazard/models?product_type=mortgage")
        assert resp.status_code == 200
        mock_list.assert_called_once_with(None, "mortgage")

    @patch("backend.list_hazard_models")
    def test_list_both_filters(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/hazard/models?model_type=cox_ph&product_type=mortgage")
        assert resp.status_code == 200
        mock_list.assert_called_once_with("cox_ph", "mortgage")

    @patch("backend.list_hazard_models")
    def test_list_empty(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/hazard/models")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.list_hazard_models")
    def test_list_500(self, mock_list, client):
        mock_list.side_effect = Exception("DB error")
        resp = client.get("/api/hazard/models")
        assert resp.status_code == 500


class TestHazardGetModel:
    """GET /api/hazard/model/{model_id} — get single hazard model."""

    @patch("backend.get_hazard_model")
    def test_get_found(self, mock_get, client):
        mock_get.return_value = _hazard_model()
        resp = client.get("/api/hazard/model/haz_cox_ph_20250115_abc12345")
        assert resp.status_code == 200
        assert resp.json()["model_id"] == "haz_cox_ph_20250115_abc12345"

    @patch("backend.get_hazard_model")
    def test_get_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/hazard/model/nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    @patch("backend.get_hazard_model")
    def test_get_500(self, mock_get, client):
        mock_get.side_effect = Exception("DB error")
        resp = client.get("/api/hazard/model/haz_1")
        assert resp.status_code == 500

    @patch("backend.get_hazard_model")
    def test_get_has_coefficients(self, mock_get, client):
        mock_get.return_value = _hazard_model()
        resp = client.get("/api/hazard/model/haz_1")
        data = resp.json()
        assert "coefficients" in data
        assert "covariates" in data["coefficients"]

    @patch("backend.get_hazard_model")
    def test_get_has_baseline_hazard(self, mock_get, client):
        mock_get.return_value = _hazard_model()
        resp = client.get("/api/hazard/model/haz_1")
        data = resp.json()
        assert "baseline_hazard" in data
        assert len(data["baseline_hazard"]) == 60


class TestHazardSurvivalCurve:
    """POST /api/hazard/survival-curve — compute survival curve."""

    @patch("backend.compute_survival_curve")
    def test_survival_happy(self, mock_sc, client):
        mock_sc.return_value = _survival_curve_result()
        resp = client.post("/api/hazard/survival-curve", json={"model_id": "haz_1"})
        assert resp.status_code == 200
        data = resp.json()
        assert "survival_probs" in data
        assert "hazard_rates" in data
        assert "pd_12_month" in data

    @patch("backend.compute_survival_curve")
    def test_survival_with_covariates(self, mock_sc, client):
        covariates = {"days_past_due": 30, "gross_carrying_amount": 500000}
        mock_sc.return_value = _survival_curve_result(covariate_values=covariates, risk_multiplier=1.35)
        resp = client.post("/api/hazard/survival-curve", json={
            "model_id": "haz_1", "covariates": covariates,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_multiplier"] == 1.35
        assert data["covariate_values"] == covariates
        mock_sc.assert_called_once_with("haz_1", covariates)

    @patch("backend.compute_survival_curve")
    def test_survival_monotonic_non_increasing(self, mock_sc, client):
        """Survival probabilities should never increase over time."""
        mock_sc.return_value = _survival_curve_result()
        resp = client.post("/api/hazard/survival-curve", json={"model_id": "haz_1"})
        probs = resp.json()["survival_probs"]
        for i in range(1, len(probs)):
            assert probs[i] <= probs[i - 1], f"Survival increased at time {i}"

    @patch("backend.compute_survival_curve")
    def test_survival_model_not_found_400(self, mock_sc, client):
        mock_sc.side_effect = ValueError("Model xxx not found")
        resp = client.post("/api/hazard/survival-curve", json={"model_id": "xxx"})
        assert resp.status_code == 400

    @patch("backend.compute_survival_curve")
    def test_survival_500(self, mock_sc, client):
        mock_sc.side_effect = Exception("DB error")
        resp = client.post("/api/hazard/survival-curve", json={"model_id": "haz_1"})
        assert resp.status_code == 500

    def test_survival_missing_model_id(self, client):
        resp = client.post("/api/hazard/survival-curve", json={})
        assert resp.status_code == 422

    @patch("backend.compute_survival_curve")
    def test_survival_no_covariates_risk_mult_1(self, mock_sc, client):
        mock_sc.return_value = _survival_curve_result(risk_multiplier=1.0)
        resp = client.post("/api/hazard/survival-curve", json={"model_id": "haz_1"})
        assert resp.json()["risk_multiplier"] == 1.0


class TestHazardTermStructure:
    """GET /api/hazard/term-structure/{model_id} — PD term structure."""

    @patch("backend.compute_term_structure_pd")
    def test_term_structure_happy(self, mock_ts, client):
        mock_ts.return_value = _term_structure_result()
        resp = client.get("/api/hazard/term-structure/haz_1")
        assert resp.status_code == 200
        data = resp.json()
        assert "marginal_pd" in data
        assert "cumulative_pd" in data
        assert "forward_pd" in data
        assert "pd_12_month" in data
        assert "pd_lifetime" in data
        mock_ts.assert_called_once_with("haz_1", 60)

    @patch("backend.compute_term_structure_pd")
    def test_term_structure_custom_months(self, mock_ts, client):
        mock_ts.return_value = _term_structure_result()
        resp = client.get("/api/hazard/term-structure/haz_1?max_months=120")
        assert resp.status_code == 200
        mock_ts.assert_called_once_with("haz_1", 120)

    @patch("backend.compute_term_structure_pd")
    def test_term_structure_cumulative_pd_non_decreasing(self, mock_ts, client):
        """Cumulative PD should be monotonically non-decreasing."""
        mock_ts.return_value = _term_structure_result()
        resp = client.get("/api/hazard/term-structure/haz_1")
        cpd = resp.json()["cumulative_pd"]
        for i in range(1, len(cpd)):
            assert cpd[i] >= cpd[i - 1], f"Cumulative PD decreased at time {i}"

    @patch("backend.compute_term_structure_pd")
    def test_term_structure_model_not_found_400(self, mock_ts, client):
        mock_ts.side_effect = ValueError("Model xxx not found")
        resp = client.get("/api/hazard/term-structure/xxx")
        assert resp.status_code == 400

    @patch("backend.compute_term_structure_pd")
    def test_term_structure_500(self, mock_ts, client):
        mock_ts.side_effect = Exception("DB error")
        resp = client.get("/api/hazard/term-structure/haz_1")
        assert resp.status_code == 500

    @patch("backend.compute_term_structure_pd")
    def test_term_structure_pd_12m_within_range(self, mock_ts, client):
        mock_ts.return_value = _term_structure_result(pd_12_month=0.023)
        resp = client.get("/api/hazard/term-structure/haz_1")
        pd_12 = resp.json()["pd_12_month"]
        assert 0 <= pd_12 <= 1.0


class TestHazardCompare:
    """POST /api/hazard/compare — compare hazard models."""

    @patch("backend.compare_hazard_models")
    def test_compare_happy(self, mock_cmp, client):
        mock_cmp.return_value = {
            "models": [
                {"model_id": "haz_1", "model_type": "cox_ph", "concordance_index": 0.78},
                {"model_id": "haz_2", "model_type": "discrete_time", "concordance_index": 0.75},
            ],
            "curves": [
                {"model_id": "haz_1", "model_type": "cox_ph",
                 "time_points": [1, 2, 3], "survival_probs": [0.99, 0.98, 0.97], "hazard_rates": [0.01, 0.01, 0.01]},
            ],
        }
        resp = client.post("/api/hazard/compare", json={"model_ids": ["haz_1", "haz_2"]})
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert len(data["models"]) == 2

    @patch("backend.compare_hazard_models")
    def test_compare_empty(self, mock_cmp, client):
        mock_cmp.return_value = {"models": [], "curves": []}
        resp = client.post("/api/hazard/compare", json={"model_ids": []})
        assert resp.status_code == 200
        assert resp.json()["models"] == []

    @patch("backend.compare_hazard_models")
    def test_compare_single(self, mock_cmp, client):
        mock_cmp.return_value = {
            "models": [{"model_id": "haz_1", "model_type": "cox_ph"}],
            "curves": [],
        }
        resp = client.post("/api/hazard/compare", json={"model_ids": ["haz_1"]})
        assert resp.status_code == 200
        assert len(resp.json()["models"]) == 1

    @patch("backend.compare_hazard_models")
    def test_compare_500(self, mock_cmp, client):
        mock_cmp.side_effect = Exception("DB error")
        resp = client.post("/api/hazard/compare", json={"model_ids": ["haz_1"]})
        assert resp.status_code == 500

    def test_compare_missing_model_ids(self, client):
        resp = client.post("/api/hazard/compare", json={})
        assert resp.status_code == 422

    @patch("backend.compare_hazard_models")
    def test_compare_includes_curves(self, mock_cmp, client):
        mock_cmp.return_value = {
            "models": [{"model_id": "haz_1", "model_type": "cox_ph"}],
            "curves": [
                {"model_id": "haz_1", "model_type": "cox_ph",
                 "time_points": [1], "survival_probs": [0.99], "hazard_rates": [0.01]},
            ],
        }
        resp = client.post("/api/hazard/compare", json={"model_ids": ["haz_1"]})
        data = resp.json()
        assert "curves" in data
        assert len(data["curves"]) == 1


# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN VALIDATION — STATUS TRANSITIONS
# ═══════════════════════════════════════════════════════════════════════════

class TestModelRegistryStatusTransitions:
    """Test all valid and invalid model status transitions via route layer."""

    VALID_TRANSITIONS = [
        ("draft", "pending_review"),
        ("pending_review", "approved"),
        ("pending_review", "draft"),  # rejection
        ("approved", "active"),
        ("active", "retired"),
    ]

    INVALID_TRANSITIONS = [
        ("draft", "approved"),
        ("draft", "active"),
        ("draft", "retired"),
        ("pending_review", "active"),
        ("pending_review", "retired"),
        ("approved", "draft"),
        ("approved", "retired"),
        ("approved", "pending_review"),
        ("active", "draft"),
        ("active", "approved"),
        ("active", "pending_review"),
        ("retired", "draft"),
        ("retired", "pending_review"),
        ("retired", "approved"),
        ("retired", "active"),
    ]

    @pytest.mark.parametrize("from_status,to_status", VALID_TRANSITIONS)
    @patch("backend.update_model_status")
    def test_valid_transition(self, mock_update, from_status, to_status, client):
        mock_update.return_value = _model_dict(status=to_status)
        resp = client.put("/api/models/mdl-001/status", json={
            "status": to_status, "user": "tester",
        })
        assert resp.status_code == 200, f"Valid transition {from_status}→{to_status} should succeed"

    @pytest.mark.parametrize("from_status,to_status", INVALID_TRANSITIONS)
    @patch("backend.update_model_status")
    def test_invalid_transition(self, mock_update, from_status, to_status, client):
        mock_update.side_effect = ValueError(f"Cannot transition from '{from_status}' to '{to_status}'")
        resp = client.put("/api/models/mdl-001/status", json={
            "status": to_status, "user": "tester",
        })
        assert resp.status_code == 400, f"Invalid transition {from_status}→{to_status} should fail"


# ═══════════════════════════════════════════════════════════════════════════
# ADDITIONAL EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

class TestModelRegistryEdgeCases:
    """Additional edge case tests for model registry."""

    @patch("backend.register_model")
    def test_register_with_empty_parameters(self, mock_reg, client):
        mock_reg.return_value = _model_dict(parameters={})
        resp = client.post("/api/models", json={
            "model_name": "Test", "model_type": "PD", "parameters": {},
        })
        assert resp.status_code == 200

    @patch("backend.register_model")
    def test_register_with_nested_parameters(self, mock_reg, client):
        nested = {"intercept": -3.2, "features": {"f1": 0.5, "f2": -0.3}, "hyperparams": {"C": 1.0, "max_iter": 100}}
        mock_reg.return_value = _model_dict(parameters=nested)
        resp = client.post("/api/models", json={
            "model_name": "Test", "model_type": "PD", "parameters": nested,
        })
        assert resp.status_code == 200

    @patch("backend.promote_champion")
    def test_promote_replaces_existing_champion(self, mock_promote, client):
        """When promoting a new champion, the previous champion should be demoted."""
        mock_promote.return_value = _model_dict(model_id="mdl-002", is_champion=True)
        resp = client.post("/api/models/mdl-002/promote", json={"user": "admin"})
        assert resp.status_code == 200
        assert resp.json()["is_champion"] is True

    @patch("backend.compare_models")
    def test_compare_three_models(self, mock_cmp, client):
        mock_cmp.return_value = [
            _model_dict(model_id="m1"), _model_dict(model_id="m2"), _model_dict(model_id="m3"),
        ]
        resp = client.post("/api/models/compare", json={"model_ids": ["m1", "m2", "m3"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    @patch("backend.get_model_audit_trail")
    def test_audit_full_lifecycle(self, mock_audit, client):
        """Audit trail should show full lifecycle: registered → pending → approved → active."""
        mock_audit.return_value = [
            _audit_entry(action="promoted_to_active", old_status="approved", new_status="active"),
            _audit_entry(audit_id="a3", action="approved", old_status="pending_review", new_status="approved"),
            _audit_entry(audit_id="a2", action="submitted_for_review", old_status="draft", new_status="pending_review"),
            _audit_entry(audit_id="a1", action="registered", old_status=None, new_status="draft"),
        ]
        resp = client.get("/api/models/mdl-001/audit")
        assert len(resp.json()) == 4


class TestBacktestingEdgeCases:
    """Additional edge case tests for backtesting."""

    @patch("backend.run_backtest")
    def test_run_red_traffic_light(self, mock_run, client):
        result = _backtest_result(
            overall_traffic_light="Red",
            pass_count=1, amber_count=1, fail_count=3,
        )
        mock_run.return_value = result
        resp = client.post("/api/backtest/run", json={"model_type": "PD"})
        assert resp.json()["overall_traffic_light"] == "Red"
        assert resp.json()["fail_count"] == 3

    @patch("backend.get_backtest")
    def test_get_with_zero_cohorts(self, mock_get, client):
        mock_get.return_value = _backtest_result(cohort_results=[])
        resp = client.get("/api/backtest/bt-1")
        assert resp.json()["cohort_results"] == []

    @patch("backend.run_backtest")
    def test_run_lgd_insufficient_data(self, mock_run, client):
        """LGD backtest with insufficient data still returns a result."""
        result = _backtest_result(
            model_type="LGD",
            metrics=[{"metric_id": "m1", "metric_name": "LGD_Status", "metric_value": 0.0,
                      "threshold_green": 0, "threshold_amber": 0, "pass_fail": "Green",
                      "detail": {"status": "insufficient_data"}}],
        )
        mock_run.return_value = result
        resp = client.post("/api/backtest/run", json={"model_type": "LGD"})
        assert resp.status_code == 200

    @patch("backend.get_backtest_trend")
    def test_trend_with_declining_metrics(self, mock_trend, client):
        entries = [
            _trend_entry(backtest_id="BT-1", AUC=0.85, overall_traffic_light="Green"),
            _trend_entry(backtest_id="BT-2", AUC=0.78, overall_traffic_light="Amber"),
            _trend_entry(backtest_id="BT-3", AUC=0.65, overall_traffic_light="Red"),
        ]
        mock_trend.return_value = entries
        resp = client.get("/api/backtest/trend/PD")
        data = resp.json()
        assert data[0]["AUC"] > data[2]["AUC"]


class TestMarkovEdgeCases:
    """Additional edge case tests for Markov chain routes."""

    @patch("backend.forecast_stage_distribution")
    def test_forecast_all_in_stage_1(self, mock_fc, client):
        """100% in Stage 1 initially."""
        mock_fc.return_value = _forecast_result(forecast_data={
            "initial_distribution": [1.0, 0.0, 0.0, 0.0],
            "horizon_months": 3,
            "points": [
                {"month": 0, "Stage 1": 100.0, "Stage 2": 0.0, "Stage 3": 0.0, "Default": 0.0},
                {"month": 1, "Stage 1": 90.0, "Stage 2": 7.0, "Stage 3": 2.0, "Default": 1.0},
            ],
        })
        resp = client.post("/api/markov/forecast", json={
            "matrix_id": "tm-001",
            "initial_distribution": [1.0, 0.0, 0.0, 0.0],
            "horizon_months": 3,
        })
        assert resp.status_code == 200

    @patch("backend.forecast_stage_distribution")
    def test_forecast_all_in_default(self, mock_fc, client):
        """100% in Default — absorbing state, no change."""
        mock_fc.return_value = _forecast_result(forecast_data={
            "initial_distribution": [0.0, 0.0, 0.0, 1.0],
            "horizon_months": 3,
            "points": [
                {"month": 0, "Stage 1": 0.0, "Stage 2": 0.0, "Stage 3": 0.0, "Default": 100.0},
                {"month": 1, "Stage 1": 0.0, "Stage 2": 0.0, "Stage 3": 0.0, "Default": 100.0},
            ],
        })
        resp = client.post("/api/markov/forecast", json={
            "matrix_id": "tm-001",
            "initial_distribution": [0.0, 0.0, 0.0, 1.0],
            "horizon_months": 3,
        })
        data = resp.json()
        for point in data["forecast_data"]["points"]:
            assert point["Default"] == 100.0

    @patch("backend.compare_matrices")
    def test_compare_three_matrices(self, mock_cmp, client):
        mock_cmp.return_value = [
            _markov_matrix(matrix_id="tm-1"),
            _markov_matrix(matrix_id="tm-2"),
            _markov_matrix(matrix_id="tm-3"),
        ]
        resp = client.post("/api/markov/compare", json={"matrix_ids": ["tm-1", "tm-2", "tm-3"]})
        assert len(resp.json()) == 3

    @patch("backend.estimate_transition_matrix")
    def test_estimate_with_both_filters(self, mock_est, client):
        mock_est.return_value = _markov_matrix(product_type="mortgage", segment="retail")
        resp = client.post("/api/markov/estimate", json={"product_type": "mortgage", "segment": "retail"})
        assert resp.status_code == 200
        mock_est.assert_called_once_with("mortgage", "retail")


class TestHazardEdgeCases:
    """Additional edge case tests for hazard model routes."""

    @patch("backend.compute_survival_curve")
    def test_survival_all_zero_hazard(self, mock_sc, client):
        """Zero hazard rate => survival stays at 1.0."""
        mock_sc.return_value = _survival_curve_result(
            survival_probs=[1.0] * 60,
            hazard_rates=[0.0] * 60,
            pd_12_month=0.0,
        )
        resp = client.post("/api/hazard/survival-curve", json={"model_id": "haz_1"})
        data = resp.json()
        assert all(p == 1.0 for p in data["survival_probs"])
        assert data["pd_12_month"] == 0.0

    @patch("backend.compute_survival_curve")
    def test_survival_high_risk_multiplier(self, mock_sc, client):
        mock_sc.return_value = _survival_curve_result(risk_multiplier=5.0, pd_12_month=0.11)
        resp = client.post("/api/hazard/survival-curve", json={
            "model_id": "haz_1",
            "covariates": {"days_past_due": 120},
        })
        assert resp.json()["risk_multiplier"] == 5.0

    @patch("backend.compute_term_structure_pd")
    def test_term_structure_short_horizon(self, mock_ts, client):
        """12-month horizon."""
        mock_ts.return_value = _term_structure_result(
            time_points=list(range(1, 13)),
            marginal_pd=[0.002] * 12,
            cumulative_pd=[round(1 - 0.998 ** t, 6) for t in range(1, 13)],
            forward_pd=[0.01] * 12,
        )
        resp = client.get("/api/hazard/term-structure/haz_1?max_months=12")
        assert resp.status_code == 200
        mock_ts.assert_called_once_with("haz_1", 12)

    @patch("backend.compare_hazard_models")
    def test_compare_three_models(self, mock_cmp, client):
        mock_cmp.return_value = {
            "models": [
                {"model_id": f"haz_{i}", "model_type": t}
                for i, t in enumerate(["cox_ph", "discrete_time", "kaplan_meier"])
            ],
            "curves": [],
        }
        resp = client.post("/api/hazard/compare", json={"model_ids": ["haz_0", "haz_1", "haz_2"]})
        assert len(resp.json()["models"]) == 3

    @patch("backend.estimate_hazard_model")
    def test_estimate_result_has_n_observations(self, mock_est, client):
        mock_est.return_value = _hazard_model(n_observations=8000, n_events=400)
        resp = client.post("/api/hazard/estimate", json={"model_type": "cox_ph"})
        data = resp.json()
        assert data["n_observations"] == 8000
        assert data["n_events"] == 400

    @patch("backend.get_hazard_model")
    def test_get_model_with_no_curves(self, mock_get, client):
        mock_get.return_value = _hazard_model(curves=[])
        resp = client.get("/api/hazard/model/haz_1")
        assert resp.json()["curves"] == []
