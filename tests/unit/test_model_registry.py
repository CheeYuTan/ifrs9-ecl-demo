"""
Unit tests for Model Registry & Validation Framework.

Tests:
  - Model lifecycle state machine (Draft → Pending Review → Approved → Active → Retired)
  - Invalid transitions rejected
  - Model card auto-generation
  - Sensitivity analysis
  - Recalibration due checking
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from domain.model_registry import (
    VALID_MODEL_STATUSES,
    VALID_STATUS_TRANSITIONS,
    VALID_MODEL_TYPES,
    _extract_assumptions,
    _extract_limitations,
    generate_model_card,
    compute_sensitivity,
    check_recalibration_due,
)


class TestModelStatuses:
    def test_all_statuses_defined(self):
        assert "draft" in VALID_MODEL_STATUSES
        assert "pending_review" in VALID_MODEL_STATUSES
        assert "approved" in VALID_MODEL_STATUSES
        assert "active" in VALID_MODEL_STATUSES
        assert "retired" in VALID_MODEL_STATUSES

    def test_draft_can_only_go_to_pending(self):
        assert VALID_STATUS_TRANSITIONS["draft"] == ["pending_review"]

    def test_pending_can_go_to_approved_or_draft(self):
        transitions = VALID_STATUS_TRANSITIONS["pending_review"]
        assert "approved" in transitions
        assert "draft" in transitions

    def test_retired_has_no_transitions(self):
        assert VALID_STATUS_TRANSITIONS["retired"] == []

    def test_active_can_only_retire(self):
        assert VALID_STATUS_TRANSITIONS["active"] == ["retired"]


class TestModelTypes:
    def test_pd_is_valid(self):
        assert "PD" in VALID_MODEL_TYPES

    def test_lgd_is_valid(self):
        assert "LGD" in VALID_MODEL_TYPES

    def test_ead_is_valid(self):
        assert "EAD" in VALID_MODEL_TYPES

    def test_staging_is_valid(self):
        assert "Staging" in VALID_MODEL_TYPES


class TestExtractAssumptions:
    def test_pd_model_assumptions(self):
        model = {"model_type": "PD", "algorithm": "logistic_regression"}
        assumptions = _extract_assumptions(model)
        assert any("90+ DPD" in a for a in assumptions)
        assert any("logistic" in a.lower() for a in assumptions)

    def test_lgd_model_assumptions(self):
        model = {"model_type": "LGD", "algorithm": "linear_regression"}
        assumptions = _extract_assumptions(model)
        assert any("recovery" in a.lower() for a in assumptions)

    def test_ensemble_model_warning(self):
        model = {"model_type": "PD", "algorithm": "random_forest"}
        assumptions = _extract_assumptions(model)
        assert any("overfit" in a.lower() for a in assumptions)


class TestExtractLimitations:
    def test_low_r_squared_flagged(self):
        model = {"model_type": "PD", "performance_metrics": {"r_squared": 0.3}}
        limitations = _extract_limitations(model)
        assert any("R²" in l or "explanatory" in l.lower() for l in limitations)

    def test_high_r_squared_not_flagged(self):
        model = {"model_type": "PD", "performance_metrics": {"r_squared": 0.8}}
        limitations = _extract_limitations(model)
        assert not any("R²" in l for l in limitations)

    def test_always_includes_regime_warning(self):
        model = {"model_type": "PD", "performance_metrics": {}}
        limitations = _extract_limitations(model)
        assert any("economic conditions" in l.lower() for l in limitations)


class TestGenerateModelCard:
    @patch("domain.model_registry.get_model")
    @patch("domain.model_registry.get_model_audit_trail")
    def test_card_has_required_sections(self, mock_audit, mock_get):
        mock_get.return_value = {
            "model_id": "m-001", "model_name": "PD Logistic v1",
            "model_type": "PD", "algorithm": "logistic_regression",
            "version": 1, "status": "active", "is_champion": True,
            "description": "PD model using logistic regression",
            "product_type": "credit_card", "cohort": "all",
            "parameters": {"intercept": -2.5, "unemployment_coeff": 0.8},
            "performance_metrics": {"r_squared": 0.65, "auc": 0.78},
            "training_data_info": {"sample_size": 50000, "date_range": "2020-2024"},
            "created_by": "analyst@bank.com", "created_at": "2024-01-15",
            "approved_by": "validator@bank.com", "approved_at": "2024-02-01",
            "notes": "",
        }
        mock_audit.return_value = [{"action": "registered"}, {"action": "approved"}]

        card = generate_model_card("m-001")
        assert "methodology" in card
        assert "training_data" in card
        assert "performance" in card
        assert "governance" in card
        assert "assumptions" in card
        assert "limitations" in card
        assert card["model_type"] == "PD"
        assert card["is_champion"] == True

    @patch("domain.model_registry.get_model")
    def test_card_raises_for_missing_model(self, mock_get):
        mock_get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            generate_model_card("nonexistent")


class TestComputeSensitivity:
    @patch("domain.model_registry.get_model")
    def test_returns_sensitivities(self, mock_get):
        mock_get.return_value = {
            "model_id": "m-001", "model_name": "PD v1",
            "parameters": {
                "intercept": -2.5,
                "unemployment_coeff": 0.8,
                "gdp_coeff": -0.3,
            },
            "performance_metrics": {},
        }
        result = compute_sensitivity("m-001", perturbation_pct=10.0)
        assert len(result["sensitivities"]) == 3
        for s in result["sensitivities"]:
            assert "parameter" in s
            assert "base_value" in s
            assert "perturbed_up" in s
            assert "perturbed_down" in s
            assert abs(s["perturbed_up"]) >= abs(s["base_value"]) or s["base_value"] == 0

    @patch("domain.model_registry.get_model")
    def test_raises_for_missing_model(self, mock_get):
        mock_get.return_value = None
        with pytest.raises(ValueError):
            compute_sensitivity("nonexistent")


class TestRecalibrationDue:
    @patch("domain.model_registry.get_model")
    def test_old_model_is_due(self, mock_get):
        old_date = datetime.now(timezone.utc) - timedelta(days=400)
        mock_get.return_value = {
            "model_id": "m-001", "model_name": "Old PD",
            "status": "active", "created_at": old_date.isoformat(),
            "approved_at": old_date.isoformat(),
        }
        result = check_recalibration_due("m-001", max_age_days=365)
        assert result["recalibration_due"] == True
        assert result["age_days"] > 365

    @patch("domain.model_registry.get_model")
    def test_recent_model_not_due(self, mock_get):
        recent_date = datetime.now(timezone.utc) - timedelta(days=30)
        mock_get.return_value = {
            "model_id": "m-002", "model_name": "New PD",
            "status": "active", "created_at": recent_date.isoformat(),
            "approved_at": recent_date.isoformat(),
        }
        result = check_recalibration_due("m-002", max_age_days=365)
        assert result["recalibration_due"] == False

    @patch("domain.model_registry.get_model")
    def test_raises_for_missing_model(self, mock_get):
        mock_get.return_value = None
        with pytest.raises(ValueError):
            check_recalibration_due("nonexistent")
