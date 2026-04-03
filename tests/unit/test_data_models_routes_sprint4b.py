"""
Supplementary route handler tests — data and model registry routes.

Adds error-path coverage for routes/data.py and routes/models.py to push
overall coverage above 70%.
"""
import pandas as pd
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_db):
    """FastAPI TestClient with backend fully mocked."""
    import app as app_module
    return TestClient(app_module.app)


_EMPTY_DF = pd.DataFrame()
_ONE_ROW = pd.DataFrame({"col": [1]})


# ---------------------------------------------------------------------------
# Data routes — error paths (happy paths already covered in test_api.py)
# ---------------------------------------------------------------------------

class TestDataRouteErrors:
    """Exercise the except branches in routes/data.py."""

    @pytest.mark.parametrize("endpoint,backend_fn", [
        ("/api/data/stage-distribution", "get_stage_distribution"),
        ("/api/data/borrower-segments", "get_borrower_segment_stats"),
        ("/api/data/vintage-analysis", "get_vintage_analysis"),
        ("/api/data/dpd-distribution", "get_dpd_distribution"),
        ("/api/data/ecl-summary", "get_ecl_summary"),
        ("/api/data/scenario-summary", "get_scenario_summary"),
        ("/api/data/mc-distribution", "get_mc_distribution"),
        ("/api/data/stage-migration", "get_stage_migration"),
        ("/api/data/sensitivity", "get_sensitivity_data"),
    ])
    def test_data_endpoint_500_on_error(self, client, endpoint, backend_fn):
        with patch(f"backend.{backend_fn}", side_effect=Exception("db error")):
            resp = client.get(endpoint)
        assert resp.status_code == 500

    def test_stage_by_product_success(self, client):
        with patch("backend.get_stage_by_product", return_value=_ONE_ROW):
            resp = client.get("/api/data/stage-by-product")
        assert resp.status_code == 200

    def test_stage_by_product_error(self, client):
        with patch("backend.get_stage_by_product", side_effect=Exception("db error")):
            resp = client.get("/api/data/stage-by-product")
        assert resp.status_code == 500

    def test_pd_distribution_success(self, client):
        with patch("backend.get_pd_distribution", return_value=_ONE_ROW):
            resp = client.get("/api/data/pd-distribution")
        assert resp.status_code == 200

    def test_pd_distribution_error(self, client):
        with patch("backend.get_pd_distribution", side_effect=Exception("db error")):
            resp = client.get("/api/data/pd-distribution")
        assert resp.status_code == 500

    def test_dq_results_success(self, client):
        with patch("backend.get_dq_results", return_value=_ONE_ROW):
            resp = client.get("/api/data/dq-results")
        assert resp.status_code == 200

    def test_dq_results_error(self, client):
        with patch("backend.get_dq_results", side_effect=Exception("db error")):
            resp = client.get("/api/data/dq-results")
        assert resp.status_code == 500

    def test_dq_summary_success(self, client):
        with patch("backend.get_dq_summary", return_value=_ONE_ROW):
            resp = client.get("/api/data/dq-summary")
        assert resp.status_code == 200

    def test_dq_summary_error(self, client):
        with patch("backend.get_dq_summary", side_effect=Exception("db error")):
            resp = client.get("/api/data/dq-summary")
        assert resp.status_code == 500

    def test_gl_reconciliation_success(self, client):
        with patch("backend.get_gl_reconciliation", return_value=_ONE_ROW):
            resp = client.get("/api/data/gl-reconciliation")
        assert resp.status_code == 200

    def test_gl_reconciliation_error(self, client):
        with patch("backend.get_gl_reconciliation", side_effect=Exception("db error")):
            resp = client.get("/api/data/gl-reconciliation")
        assert resp.status_code == 500

    def test_ecl_by_product_success(self, client):
        with patch("backend.get_ecl_by_product", return_value=_ONE_ROW):
            resp = client.get("/api/data/ecl-by-product")
        assert resp.status_code == 200

    def test_ecl_by_product_error(self, client):
        with patch("backend.get_ecl_by_product", side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-by-product")
        assert resp.status_code == 500

    def test_ecl_by_scenario_product_success(self, client):
        with patch("backend.get_ecl_by_scenario_product", return_value=_ONE_ROW):
            resp = client.get("/api/data/ecl-by-scenario-product")
        assert resp.status_code == 200

    def test_ecl_by_scenario_product_error(self, client):
        with patch("backend.get_ecl_by_scenario_product", side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-by-scenario-product")
        assert resp.status_code == 500

    def test_ecl_concentration_success(self, client):
        with patch("backend.get_ecl_concentration", return_value=_ONE_ROW):
            resp = client.get("/api/data/ecl-concentration")
        assert resp.status_code == 200

    def test_ecl_concentration_error(self, client):
        with patch("backend.get_ecl_concentration", side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-concentration")
        assert resp.status_code == 500

    def test_credit_risk_exposure_success(self, client):
        with patch("backend.get_credit_risk_exposure", return_value=_ONE_ROW):
            resp = client.get("/api/data/credit-risk-exposure")
        assert resp.status_code == 200

    def test_credit_risk_exposure_error(self, client):
        with patch("backend.get_credit_risk_exposure", side_effect=Exception("db error")):
            resp = client.get("/api/data/credit-risk-exposure")
        assert resp.status_code == 500

    def test_loss_allowance_by_stage_success(self, client):
        with patch("backend.get_loss_allowance_by_stage", return_value=_ONE_ROW):
            resp = client.get("/api/data/loss-allowance-by-stage")
        assert resp.status_code == 200

    def test_loss_allowance_by_stage_error(self, client):
        with patch("backend.get_loss_allowance_by_stage", side_effect=Exception("db error")):
            resp = client.get("/api/data/loss-allowance-by-stage")
        assert resp.status_code == 500

    def test_ecl_by_stage_product_success(self, client):
        with patch("backend.get_ecl_by_stage_product", return_value=_ONE_ROW) as mock_fn:
            resp = client.get("/api/data/ecl-by-stage-product/1")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(1)

    def test_ecl_by_stage_product_error(self, client):
        with patch("backend.get_ecl_by_stage_product", side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-by-stage-product/1")
        assert resp.status_code == 500

    def test_ecl_by_scenario_product_detail_success(self, client):
        with patch("backend.get_ecl_by_scenario_product_detail", return_value=_ONE_ROW) as mock_fn:
            resp = client.get("/api/data/ecl-by-scenario-product-detail?scenario=baseline")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("baseline")

    def test_ecl_by_scenario_product_detail_error(self, client):
        with patch("backend.get_ecl_by_scenario_product_detail", side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-by-scenario-product-detail?scenario=baseline")
        assert resp.status_code == 500

    def test_top_exposures_error(self, client):
        with patch("backend.get_top_exposures", side_effect=Exception("db error")):
            resp = client.get("/api/data/top-exposures")
        assert resp.status_code == 500

    def test_loans_by_product_error(self, client):
        with patch("backend.get_loans_by_product", side_effect=Exception("db error")):
            resp = client.get("/api/data/loans-by-product/personal_loan")
        assert resp.status_code == 500

    def test_loans_by_stage_error(self, client):
        with patch("backend.get_loans_by_stage", side_effect=Exception("db error")):
            resp = client.get("/api/data/loans-by-stage/1")
        assert resp.status_code == 500

    def test_scenario_comparison_success(self, client):
        with patch("backend.get_scenario_comparison", return_value=_ONE_ROW):
            resp = client.get("/api/data/scenario-comparison")
        assert resp.status_code == 200

    def test_scenario_comparison_error(self, client):
        with patch("backend.get_scenario_comparison", side_effect=Exception("db error")):
            resp = client.get("/api/data/scenario-comparison")
        assert resp.status_code == 500

    def test_stress_by_stage_success(self, client):
        with patch("backend.get_stress_by_stage", return_value=_ONE_ROW):
            resp = client.get("/api/data/stress-by-stage")
        assert resp.status_code == 200

    def test_stress_by_stage_error(self, client):
        with patch("backend.get_stress_by_stage", side_effect=Exception("db error")):
            resp = client.get("/api/data/stress-by-stage")
        assert resp.status_code == 500

    def test_vintage_performance_success(self, client):
        with patch("backend.get_vintage_performance", return_value=_ONE_ROW):
            resp = client.get("/api/data/vintage-performance")
        assert resp.status_code == 200

    def test_vintage_performance_error(self, client):
        with patch("backend.get_vintage_performance", side_effect=Exception("db error")):
            resp = client.get("/api/data/vintage-performance")
        assert resp.status_code == 500

    def test_vintage_by_product_success(self, client):
        with patch("backend.get_vintage_by_product", return_value=_ONE_ROW):
            resp = client.get("/api/data/vintage-by-product")
        assert resp.status_code == 200

    def test_vintage_by_product_error(self, client):
        with patch("backend.get_vintage_by_product", side_effect=Exception("db error")):
            resp = client.get("/api/data/vintage-by-product")
        assert resp.status_code == 500

    def test_concentration_by_segment_success(self, client):
        with patch("backend.get_concentration_by_segment", return_value=_ONE_ROW):
            resp = client.get("/api/data/concentration-by-segment")
        assert resp.status_code == 200

    def test_concentration_by_segment_error(self, client):
        with patch("backend.get_concentration_by_segment", side_effect=Exception("db error")):
            resp = client.get("/api/data/concentration-by-segment")
        assert resp.status_code == 500

    def test_concentration_by_product_stage_success(self, client):
        with patch("backend.get_concentration_by_product_stage", return_value=_ONE_ROW):
            resp = client.get("/api/data/concentration-by-product-stage")
        assert resp.status_code == 200

    def test_concentration_by_product_stage_error(self, client):
        with patch("backend.get_concentration_by_product_stage", side_effect=Exception("db error")):
            resp = client.get("/api/data/concentration-by-product-stage")
        assert resp.status_code == 500

    def test_top_concentration_risk_success(self, client):
        with patch("backend.get_top_concentration_risk", return_value=_ONE_ROW):
            resp = client.get("/api/data/top-concentration-risk")
        assert resp.status_code == 200

    def test_top_concentration_risk_error(self, client):
        with patch("backend.get_top_concentration_risk", side_effect=Exception("db error")):
            resp = client.get("/api/data/top-concentration-risk")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Model registry routes — /api/models/*
# ---------------------------------------------------------------------------

class TestModelRegistryRoutes:
    def test_list_models_success(self, client):
        with patch("backend.list_models", return_value=[{"model_id": "m-001", "model_type": "PD"}]):
            resp = client.get("/api/models")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_models_with_filters(self, client):
        with patch("backend.list_models", return_value=[]) as mock_fn:
            resp = client.get("/api/models?model_type=PD&status=champion")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("PD", "champion")

    def test_list_models_no_filters_passes_none(self, client):
        with patch("backend.list_models", return_value=[]) as mock_fn:
            resp = client.get("/api/models")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None, None)

    def test_list_models_error_returns_500(self, client):
        with patch("backend.list_models", side_effect=Exception("db error")):
            resp = client.get("/api/models")
        assert resp.status_code == 500

    def test_get_model_found(self, client):
        with patch("backend.get_model", return_value={"model_id": "m-001", "model_type": "PD"}):
            resp = client.get("/api/models/m-001")
        assert resp.status_code == 200
        assert resp.json()["model_id"] == "m-001"

    def test_get_model_not_found(self, client):
        with patch("backend.get_model", return_value=None):
            resp = client.get("/api/models/missing")
        assert resp.status_code == 404

    def test_get_model_error_returns_500(self, client):
        with patch("backend.get_model", side_effect=Exception("db error")):
            resp = client.get("/api/models/m-001")
        assert resp.status_code == 500

    def test_register_model_success(self, client):
        registered = {"model_id": "m-002", "model_name": "PD Model v2", "status": "draft"}
        with patch("backend.register_model", return_value=registered):
            resp = client.post("/api/models", json={
                "model_name": "PD Model v2",
                "model_type": "PD",
                "algorithm": "logistic_regression",
            })
        assert resp.status_code == 200
        assert resp.json()["model_id"] == "m-002"

    def test_register_model_error_returns_500(self, client):
        with patch("backend.register_model", side_effect=Exception("db error")):
            resp = client.post("/api/models", json={
                "model_name": "PD Model v2",
                "model_type": "PD",
            })
        assert resp.status_code == 500

    def test_update_model_status_success(self, client):
        updated = {"model_id": "m-001", "status": "champion"}
        with patch("backend.update_model_status", return_value=updated):
            resp = client.put("/api/models/m-001/status", json={"status": "champion", "user": "admin"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "champion"

    def test_update_model_status_value_error_returns_400(self, client):
        with patch("backend.update_model_status", side_effect=ValueError("invalid transition")):
            resp = client.put("/api/models/m-001/status", json={"status": "invalid", "user": "admin"})
        assert resp.status_code == 400

    def test_update_model_status_error_returns_500(self, client):
        with patch("backend.update_model_status", side_effect=Exception("db error")):
            resp = client.put("/api/models/m-001/status", json={"status": "champion", "user": "admin"})
        assert resp.status_code == 500

    def test_promote_champion_success(self, client):
        promoted = {"model_id": "m-001", "status": "champion"}
        with patch("backend.promote_champion", return_value=promoted):
            resp = client.post("/api/models/m-001/promote", json={"user": "admin"})
        assert resp.status_code == 200

    def test_promote_champion_value_error_returns_400(self, client):
        with patch("backend.promote_champion", side_effect=ValueError("model not in staging")):
            resp = client.post("/api/models/m-001/promote", json={"user": "admin"})
        assert resp.status_code == 400

    def test_promote_champion_error_returns_500(self, client):
        with patch("backend.promote_champion", side_effect=Exception("db error")):
            resp = client.post("/api/models/m-001/promote", json={"user": "admin"})
        assert resp.status_code == 500

    def test_compare_models_success(self, client):
        compared = [{"model_id": "m-001"}, {"model_id": "m-002"}]
        with patch("backend.compare_models", return_value=compared):
            resp = client.post("/api/models/compare", json={"model_ids": ["m-001", "m-002"]})
        assert resp.status_code == 200

    def test_compare_models_error_returns_500(self, client):
        with patch("backend.compare_models", side_effect=Exception("db error")):
            resp = client.post("/api/models/compare", json={"model_ids": ["m-001", "m-002"]})
        assert resp.status_code == 500

    def test_get_model_audit_success(self, client):
        trail = [{"action": "created", "user": "admin", "ts": "2025-01-01T00:00:00Z"}]
        with patch("backend.get_model_audit_trail", return_value=trail):
            resp = client.get("/api/models/m-001/audit")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_model_audit_error_returns_500(self, client):
        with patch("backend.get_model_audit_trail", side_effect=Exception("db error")):
            resp = client.get("/api/models/m-001/audit")
        assert resp.status_code == 500
