"""
Route handler tests for under-tested routes — Sprint 4 coverage push.

Covers: admin, advanced, gl_journals, hazard, markov, backtesting, rbac, satellite.
Each test mocks the underlying domain/backend function and asserts status code + shape.
"""
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_db):
    """FastAPI TestClient with backend fully mocked."""
    import app as app_module
    return TestClient(app_module.app)


# ---------------------------------------------------------------------------
# Admin routes — /api/admin/*
# ---------------------------------------------------------------------------

class TestAdminGetConfig:
    def test_get_config_success(self, client):
        with patch("admin_config.get_config", return_value={"app_settings": {}, "model_config": {}}):
            resp = client.get("/api/admin/config")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_get_config_error_returns_500(self, client):
        with patch("admin_config.get_config", side_effect=Exception("disk error")):
            resp = client.get("/api/admin/config")
        assert resp.status_code == 500


class TestAdminSaveConfig:
    def test_save_config_success(self, client):
        with patch("admin_config.save_config", return_value={"saved": True}):
            resp = client.put("/api/admin/config", json={"app_settings": {}})
        assert resp.status_code == 200

    def test_save_config_error_returns_500(self, client):
        with patch("admin_config.save_config", side_effect=Exception("write error")):
            resp = client.put("/api/admin/config", json={})
        assert resp.status_code == 500


class TestAdminGetSection:
    def test_get_section_success(self, client):
        with patch("admin_config.get_config_section", return_value={"pd_floor": 0.001}):
            resp = client.get("/api/admin/config/model_config")
        assert resp.status_code == 200

    def test_get_section_error_returns_500(self, client):
        with patch("admin_config.get_config_section", side_effect=Exception("not found")):
            resp = client.get("/api/admin/config/unknown_section")
        assert resp.status_code == 500


class TestAdminSaveSection:
    def test_save_section_success(self, client):
        with patch("admin_config.save_config_section", return_value={"saved": True}):
            resp = client.put("/api/admin/config/model_config", json={"pd_floor": 0.001})
        assert resp.status_code == 200

    def test_save_section_error_returns_500(self, client):
        with patch("admin_config.save_config_section", side_effect=Exception("write error")):
            resp = client.put("/api/admin/config/model_config", json={})
        assert resp.status_code == 500


class TestAdminValidateMapping:
    def test_validate_mapping_success(self, client):
        with patch("admin_config.validate_column_mapping", return_value={"valid": True, "errors": []}):
            resp = client.post("/api/admin/validate-mapping", json={
                "table_key": "loans",
                "mappings": {"loan_id": "id", "gca": "amount"},
            })
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_validate_mapping_error_returns_500(self, client):
        with patch("admin_config.validate_column_mapping", side_effect=Exception("bad table")):
            resp = client.post("/api/admin/validate-mapping", json={
                "table_key": "nonexistent",
                "mappings": {},
            })
        assert resp.status_code == 500


class TestAdminAvailableTables:
    def test_available_tables_success(self, client):
        with patch("admin_config.get_available_tables", return_value=["loans", "portfolio"]):
            resp = client.get("/api/admin/available-tables")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_available_tables_error_returns_500(self, client):
        with patch("admin_config.get_available_tables", side_effect=Exception("db error")):
            resp = client.get("/api/admin/available-tables")
        assert resp.status_code == 500


class TestAdminTableColumns:
    def test_table_columns_success(self, client):
        with patch("admin_config.get_table_columns", return_value=["loan_id", "gca", "pd"]):
            resp = client.get("/api/admin/table-columns/loans")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_table_columns_error_returns_500(self, client):
        with patch("admin_config.get_table_columns", side_effect=Exception("table missing")):
            resp = client.get("/api/admin/table-columns/missing")
        assert resp.status_code == 500


class TestAdminTestConnection:
    def test_test_connection_success(self, client):
        with patch("admin_config.test_connection", return_value={"connected": True}):
            resp = client.post("/api/admin/test-connection")
        assert resp.status_code == 200

    def test_test_connection_error_returns_500(self, client):
        with patch("admin_config.test_connection", side_effect=Exception("timeout")):
            resp = client.post("/api/admin/test-connection")
        assert resp.status_code == 500


class TestAdminSeedDefaults:
    def test_seed_defaults_success(self, client):
        with patch("admin_config.seed_defaults", return_value={"seeded": True}):
            resp = client.post("/api/admin/seed-defaults")
        assert resp.status_code == 200

    def test_seed_defaults_error_returns_500(self, client):
        with patch("admin_config.seed_defaults", side_effect=Exception("already seeded")):
            resp = client.post("/api/admin/seed-defaults")
        assert resp.status_code == 500


class TestAdminSchemas:
    def test_schemas_success(self, client):
        with patch("admin_config.get_available_schemas", return_value=["main", "ecl"]):
            resp = client.get("/api/admin/schemas")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_schemas_error_returns_500(self, client):
        with patch("admin_config.get_available_schemas", side_effect=Exception("db error")):
            resp = client.get("/api/admin/schemas")
        assert resp.status_code == 500


class TestAdminTablePreview:
    def test_table_preview_success(self, client):
        with patch("admin_config.get_table_preview", return_value=[{"loan_id": "LN-001"}]):
            resp = client.get("/api/admin/table-preview/loans")
        assert resp.status_code == 200

    def test_table_preview_with_limit(self, client):
        with patch("admin_config.get_table_preview", return_value=[]) as mock_fn:
            resp = client.get("/api/admin/table-preview/loans?limit=10")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("loans", None, 10)

    def test_table_preview_error_returns_500(self, client):
        with patch("admin_config.get_table_preview", side_effect=Exception("table not found")):
            resp = client.get("/api/admin/table-preview/missing")
        assert resp.status_code == 500


class TestAdminValidateMappingTyped:
    def test_validate_mapping_typed_success(self, client):
        with patch("admin_config.validate_column_mapping_with_types", return_value={"valid": True}):
            resp = client.post("/api/admin/validate-mapping-typed", json={
                "table_key": "loans",
                "mappings": {"loan_id": "id"},
            })
        assert resp.status_code == 200

    def test_validate_mapping_typed_error_returns_500(self, client):
        with patch("admin_config.validate_column_mapping_with_types", side_effect=Exception("type error")):
            resp = client.post("/api/admin/validate-mapping-typed", json={
                "table_key": "loans",
                "mappings": {},
            })
        assert resp.status_code == 500


class TestAdminSuggestMappings:
    def test_suggest_mappings_success(self, client):
        with patch("admin_config.suggest_column_mappings", return_value={"loan_id": "id"}):
            resp = client.get("/api/admin/suggest-mappings/loans")
        assert resp.status_code == 200

    def test_suggest_mappings_error_returns_500(self, client):
        with patch("admin_config.suggest_column_mappings", side_effect=Exception("table not found")):
            resp = client.get("/api/admin/suggest-mappings/missing")
        assert resp.status_code == 500


class TestAdminAutoDetectWorkspace:
    def test_auto_detect_workspace_success(self, client):
        with patch("admin_config.auto_detect_workspace", return_value={"workspace_url": "https://example.com"}):
            resp = client.get("/api/admin/auto-detect-workspace")
        assert resp.status_code == 200

    def test_auto_detect_workspace_error_returns_500(self, client):
        with patch("admin_config.auto_detect_workspace", side_effect=Exception("env not set")):
            resp = client.get("/api/admin/auto-detect-workspace")
        assert resp.status_code == 500


class TestAdminDiscoverProducts:
    def test_discover_products_success(self, client):
        with patch("admin_config.discover_products", return_value=["credit_builder", "personal_loan"]):
            resp = client.get("/api/admin/discover-products")
        assert resp.status_code == 200

    def test_discover_products_error_returns_500(self, client):
        with patch("admin_config.discover_products", side_effect=Exception("db error")):
            resp = client.get("/api/admin/discover-products")
        assert resp.status_code == 500


class TestAdminAutoSetupLgd:
    def test_auto_setup_lgd_success(self, client):
        with patch("admin_config.auto_setup_lgd_from_data", return_value={"updated": 3}):
            resp = client.post("/api/admin/auto-setup-lgd")
        assert resp.status_code == 200

    def test_auto_setup_lgd_error_returns_500(self, client):
        with patch("admin_config.auto_setup_lgd_from_data", side_effect=Exception("insufficient data")):
            resp = client.post("/api/admin/auto-setup-lgd")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Advanced routes — /api/advanced/*
# ---------------------------------------------------------------------------

class TestAdvancedCureRates:
    def test_compute_cure_rates_success(self, client):
        with patch("backend.compute_cure_rates", return_value={"cure_rate": 0.12, "analysis_id": "cr-001"}):
            resp = client.post("/api/advanced/cure-rates/compute", json={})
        assert resp.status_code == 200
        assert "analysis_id" in resp.json()

    def test_compute_cure_rates_with_product(self, client):
        with patch("backend.compute_cure_rates", return_value={"cure_rate": 0.08}) as mock_fn:
            resp = client.post("/api/advanced/cure-rates/compute", json={"product_type": "personal_loan"})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("personal_loan")

    def test_compute_cure_rates_no_product_passes_none(self, client):
        with patch("backend.compute_cure_rates", return_value={"cure_rate": 0.08}) as mock_fn:
            resp = client.post("/api/advanced/cure-rates/compute", json={})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_compute_cure_rates_error_returns_500(self, client):
        with patch("backend.compute_cure_rates", side_effect=Exception("no data")):
            resp = client.post("/api/advanced/cure-rates/compute", json={})
        assert resp.status_code == 500

    def test_list_cure_analyses_success(self, client):
        with patch("backend.list_cure_analyses", return_value=[{"analysis_id": "cr-001", "cure_rate": 0.12}]):
            resp = client.get("/api/advanced/cure-rates")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_cure_analyses_error_returns_500(self, client):
        with patch("backend.list_cure_analyses", side_effect=Exception("db error")):
            resp = client.get("/api/advanced/cure-rates")
        assert resp.status_code == 500

    def test_get_cure_analysis_found(self, client):
        with patch("backend.get_cure_analysis", return_value={"analysis_id": "cr-001", "cure_rate": 0.12}):
            resp = client.get("/api/advanced/cure-rates/cr-001")
        assert resp.status_code == 200
        assert resp.json()["analysis_id"] == "cr-001"

    def test_get_cure_analysis_not_found(self, client):
        with patch("backend.get_cure_analysis", return_value=None):
            resp = client.get("/api/advanced/cure-rates/nonexistent")
        assert resp.status_code == 404

    def test_get_cure_analysis_error_returns_500(self, client):
        with patch("backend.get_cure_analysis", side_effect=Exception("db error")):
            resp = client.get("/api/advanced/cure-rates/cr-001")
        assert resp.status_code == 500


class TestAdvancedCcf:
    def test_compute_ccf_success(self, client):
        with patch("backend.compute_ccf", return_value={"ccf": 0.75, "analysis_id": "ccf-001"}):
            resp = client.post("/api/advanced/ccf/compute", json={})
        assert resp.status_code == 200

    def test_compute_ccf_with_product(self, client):
        with patch("backend.compute_ccf", return_value={"ccf": 0.80}) as mock_fn:
            resp = client.post("/api/advanced/ccf/compute", json={"product_type": "credit_card"})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("credit_card")

    def test_compute_ccf_no_product_passes_none(self, client):
        with patch("backend.compute_ccf", return_value={"ccf": 0.75}) as mock_fn:
            resp = client.post("/api/advanced/ccf/compute", json={})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_compute_ccf_error_returns_500(self, client):
        with patch("backend.compute_ccf", side_effect=Exception("calculation error")):
            resp = client.post("/api/advanced/ccf/compute", json={})
        assert resp.status_code == 500

    def test_list_ccf_analyses_success(self, client):
        with patch("backend.list_ccf_analyses", return_value=[{"analysis_id": "ccf-001"}]):
            resp = client.get("/api/advanced/ccf")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_ccf_analyses_error_returns_500(self, client):
        with patch("backend.list_ccf_analyses", side_effect=Exception("db error")):
            resp = client.get("/api/advanced/ccf")
        assert resp.status_code == 500

    def test_get_ccf_analysis_found(self, client):
        with patch("backend.get_ccf_analysis", return_value={"analysis_id": "ccf-001", "ccf": 0.75}):
            resp = client.get("/api/advanced/ccf/ccf-001")
        assert resp.status_code == 200

    def test_get_ccf_analysis_not_found(self, client):
        with patch("backend.get_ccf_analysis", return_value=None):
            resp = client.get("/api/advanced/ccf/missing")
        assert resp.status_code == 404

    def test_get_ccf_analysis_error_returns_500(self, client):
        with patch("backend.get_ccf_analysis", side_effect=Exception("db error")):
            resp = client.get("/api/advanced/ccf/ccf-001")
        assert resp.status_code == 500


class TestAdvancedCollateral:
    def test_compute_collateral_success(self, client):
        with patch("backend.compute_collateral_haircuts", return_value={"haircut": 0.20, "analysis_id": "col-001"}):
            resp = client.post("/api/advanced/collateral/compute", json={})
        assert resp.status_code == 200

    def test_compute_collateral_with_product(self, client):
        with patch("backend.compute_collateral_haircuts", return_value={"haircut": 0.15}) as mock_fn:
            resp = client.post("/api/advanced/collateral/compute", json={"product_type": "mortgage"})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("mortgage")

    def test_compute_collateral_no_product_passes_none(self, client):
        with patch("backend.compute_collateral_haircuts", return_value={"haircut": 0.20}) as mock_fn:
            resp = client.post("/api/advanced/collateral/compute", json={})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_compute_collateral_error_returns_500(self, client):
        with patch("backend.compute_collateral_haircuts", side_effect=Exception("no collateral data")):
            resp = client.post("/api/advanced/collateral/compute", json={})
        assert resp.status_code == 500

    def test_list_collateral_analyses_success(self, client):
        with patch("backend.list_collateral_analyses", return_value=[{"analysis_id": "col-001"}]):
            resp = client.get("/api/advanced/collateral")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_collateral_analyses_error_returns_500(self, client):
        with patch("backend.list_collateral_analyses", side_effect=Exception("db error")):
            resp = client.get("/api/advanced/collateral")
        assert resp.status_code == 500

    def test_get_collateral_analysis_found(self, client):
        with patch("backend.get_collateral_analysis", return_value={"analysis_id": "col-001", "haircut": 0.20}):
            resp = client.get("/api/advanced/collateral/col-001")
        assert resp.status_code == 200

    def test_get_collateral_analysis_not_found(self, client):
        with patch("backend.get_collateral_analysis", return_value=None):
            resp = client.get("/api/advanced/collateral/missing")
        assert resp.status_code == 404

    def test_get_collateral_analysis_error_returns_500(self, client):
        with patch("backend.get_collateral_analysis", side_effect=Exception("db error")):
            resp = client.get("/api/advanced/collateral/col-001")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GL Journal routes — /api/gl/*
# ---------------------------------------------------------------------------

class TestGlJournals:
    def test_generate_journals_success(self, client):
        journal = {"journal_id": "jnl-001", "project_id": "proj-001", "entries": []}
        with patch("backend.generate_ecl_journals", return_value=journal):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "analyst"})
        assert resp.status_code == 200
        assert resp.json()["journal_id"] == "jnl-001"

    def test_generate_journals_default_user(self, client):
        with patch("backend.generate_ecl_journals", return_value={"journal_id": "jnl-001"}) as mock_fn:
            resp = client.post("/api/gl/generate/proj-001", json={})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("proj-001", "system")

    def test_generate_journals_value_error_returns_400(self, client):
        with patch("backend.generate_ecl_journals", side_effect=ValueError("ECL not computed")):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "analyst"})
        assert resp.status_code == 400

    def test_generate_journals_error_returns_500(self, client):
        with patch("backend.generate_ecl_journals", side_effect=Exception("db error")):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "analyst"})
        assert resp.status_code == 500

    def test_list_journals_success(self, client):
        with patch("backend.list_journals", return_value=[{"journal_id": "jnl-001"}]):
            resp = client.get("/api/gl/journals/proj-001")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_journals_error_returns_500(self, client):
        with patch("backend.list_journals", side_effect=Exception("db error")):
            resp = client.get("/api/gl/journals/proj-001")
        assert resp.status_code == 500

    def test_get_journal_found(self, client):
        with patch("backend.get_journal", return_value={"journal_id": "jnl-001", "status": "draft"}):
            resp = client.get("/api/gl/journal/jnl-001")
        assert resp.status_code == 200
        assert resp.json()["journal_id"] == "jnl-001"

    def test_get_journal_not_found(self, client):
        with patch("backend.get_journal", return_value=None):
            resp = client.get("/api/gl/journal/missing")
        assert resp.status_code == 404

    def test_get_journal_error_returns_500(self, client):
        with patch("backend.get_journal", side_effect=Exception("db error")):
            resp = client.get("/api/gl/journal/jnl-001")
        assert resp.status_code == 500

    def test_post_journal_success(self, client):
        with patch("backend.post_journal", return_value={"journal_id": "jnl-001", "status": "posted"}):
            resp = client.post("/api/gl/journal/jnl-001/post", json={"user": "cfo"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "posted"

    def test_post_journal_value_error_returns_400(self, client):
        with patch("backend.post_journal", side_effect=ValueError("already posted")):
            resp = client.post("/api/gl/journal/jnl-001/post", json={"user": "cfo"})
        assert resp.status_code == 400

    def test_post_journal_error_returns_500(self, client):
        with patch("backend.post_journal", side_effect=Exception("db error")):
            resp = client.post("/api/gl/journal/jnl-001/post", json={"user": "cfo"})
        assert resp.status_code == 500

    def test_reverse_journal_success(self, client):
        with patch("backend.reverse_journal", return_value={"journal_id": "jnl-001", "status": "reversed"}):
            resp = client.post("/api/gl/journal/jnl-001/reverse", json={"user": "cfo", "reason": "correction"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "reversed"

    def test_reverse_journal_value_error_returns_400(self, client):
        with patch("backend.reverse_journal", side_effect=ValueError("cannot reverse draft")):
            resp = client.post("/api/gl/journal/jnl-001/reverse", json={"user": "cfo", "reason": ""})
        assert resp.status_code == 400

    def test_reverse_journal_error_returns_500(self, client):
        with patch("backend.reverse_journal", side_effect=Exception("db error")):
            resp = client.post("/api/gl/journal/jnl-001/reverse", json={"user": "cfo", "reason": ""})
        assert resp.status_code == 500

    def test_trial_balance_success(self, client):
        with patch("backend.get_gl_trial_balance", return_value={"debit": 1000000, "credit": 1000000}):
            resp = client.get("/api/gl/trial-balance/proj-001")
        assert resp.status_code == 200

    def test_trial_balance_error_returns_500(self, client):
        with patch("backend.get_gl_trial_balance", side_effect=Exception("no journals")):
            resp = client.get("/api/gl/trial-balance/proj-001")
        assert resp.status_code == 500

    def test_chart_of_accounts_success(self, client):
        with patch("backend.get_gl_chart", return_value=[{"account_code": "1001", "name": "Loss Allowance"}]):
            resp = client.get("/api/gl/chart-of-accounts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_chart_of_accounts_error_returns_500(self, client):
        with patch("backend.get_gl_chart", side_effect=Exception("db error")):
            resp = client.get("/api/gl/chart-of-accounts")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Hazard model routes — /api/hazard/*
# ---------------------------------------------------------------------------

class TestHazardRoutes:
    def test_hazard_estimate_success(self, client):
        result = {"model_id": "hm-001", "model_type": "cox", "coefficients": {}}
        with patch("backend.estimate_hazard_model", return_value=result):
            resp = client.post("/api/hazard/estimate", json={"model_type": "cox"})
        assert resp.status_code == 200
        assert resp.json()["model_id"] == "hm-001"

    def test_hazard_estimate_with_product_and_segment(self, client):
        with patch("backend.estimate_hazard_model", return_value={"model_id": "hm-002"}) as mock_fn:
            resp = client.post("/api/hazard/estimate", json={
                "model_type": "weibull",
                "product_type": "personal_loan",
                "segment": "high_risk",
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("weibull", "personal_loan", "high_risk")

    def test_hazard_estimate_no_optionals_passes_none(self, client):
        with patch("backend.estimate_hazard_model", return_value={"model_id": "hm-003"}) as mock_fn:
            resp = client.post("/api/hazard/estimate", json={"model_type": "cox"})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("cox", None, None)

    def test_hazard_estimate_value_error_returns_400(self, client):
        with patch("backend.estimate_hazard_model", side_effect=ValueError("unknown model type")):
            resp = client.post("/api/hazard/estimate", json={"model_type": "invalid"})
        assert resp.status_code == 400

    def test_hazard_estimate_error_returns_500(self, client):
        with patch("backend.estimate_hazard_model", side_effect=Exception("fitting error")):
            resp = client.post("/api/hazard/estimate", json={"model_type": "cox"})
        assert resp.status_code == 500

    def test_hazard_list_models_success(self, client):
        with patch("backend.list_hazard_models", return_value=[{"model_id": "hm-001", "model_type": "cox"}]):
            resp = client.get("/api/hazard/models")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_hazard_list_models_with_filters(self, client):
        with patch("backend.list_hazard_models", return_value=[]) as mock_fn:
            resp = client.get("/api/hazard/models?model_type=cox&product_type=personal_loan")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("cox", "personal_loan")

    def test_hazard_list_models_no_filters_passes_none(self, client):
        with patch("backend.list_hazard_models", return_value=[]) as mock_fn:
            resp = client.get("/api/hazard/models")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None, None)

    def test_hazard_list_models_error_returns_500(self, client):
        with patch("backend.list_hazard_models", side_effect=Exception("db error")):
            resp = client.get("/api/hazard/models")
        assert resp.status_code == 500

    def test_hazard_get_model_found(self, client):
        with patch("backend.get_hazard_model", return_value={"model_id": "hm-001", "model_type": "cox"}):
            resp = client.get("/api/hazard/model/hm-001")
        assert resp.status_code == 200
        assert resp.json()["model_id"] == "hm-001"

    def test_hazard_get_model_not_found(self, client):
        with patch("backend.get_hazard_model", return_value=None):
            resp = client.get("/api/hazard/model/missing")
        assert resp.status_code == 404

    def test_hazard_get_model_error_returns_500(self, client):
        with patch("backend.get_hazard_model", side_effect=Exception("db error")):
            resp = client.get("/api/hazard/model/hm-001")
        assert resp.status_code == 500

    def test_hazard_survival_curve_success(self, client):
        result = {"model_id": "hm-001", "survival": [1.0, 0.95, 0.90]}
        with patch("backend.compute_survival_curve", return_value=result):
            resp = client.post("/api/hazard/survival-curve", json={"model_id": "hm-001"})
        assert resp.status_code == 200
        assert "survival" in resp.json()

    def test_hazard_survival_curve_with_covariates(self, client):
        with patch("backend.compute_survival_curve", return_value={"survival": []}) as mock_fn:
            resp = client.post("/api/hazard/survival-curve", json={
                "model_id": "hm-001",
                "covariates": {"age": 35, "income": 50000},
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("hm-001", {"age": 35, "income": 50000})

    def test_hazard_survival_curve_value_error_returns_400(self, client):
        with patch("backend.compute_survival_curve", side_effect=ValueError("model not found")):
            resp = client.post("/api/hazard/survival-curve", json={"model_id": "bad-id"})
        assert resp.status_code == 400

    def test_hazard_survival_curve_error_returns_500(self, client):
        with patch("backend.compute_survival_curve", side_effect=Exception("numerical error")):
            resp = client.post("/api/hazard/survival-curve", json={"model_id": "hm-001"})
        assert resp.status_code == 500

    def test_hazard_term_structure_success(self, client):
        result = {"model_id": "hm-001", "pd_term_structure": [0.01, 0.02, 0.03]}
        with patch("backend.compute_term_structure_pd", return_value=result):
            resp = client.get("/api/hazard/term-structure/hm-001")
        assert resp.status_code == 200

    def test_hazard_term_structure_default_max_months(self, client):
        with patch("backend.compute_term_structure_pd", return_value={}) as mock_fn:
            resp = client.get("/api/hazard/term-structure/hm-001")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("hm-001", 60)

    def test_hazard_term_structure_with_max_months(self, client):
        with patch("backend.compute_term_structure_pd", return_value={}) as mock_fn:
            resp = client.get("/api/hazard/term-structure/hm-001?max_months=36")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("hm-001", 36)

    def test_hazard_term_structure_value_error_returns_400(self, client):
        with patch("backend.compute_term_structure_pd", side_effect=ValueError("model not found")):
            resp = client.get("/api/hazard/term-structure/missing")
        assert resp.status_code == 400

    def test_hazard_term_structure_error_returns_500(self, client):
        with patch("backend.compute_term_structure_pd", side_effect=Exception("computation error")):
            resp = client.get("/api/hazard/term-structure/hm-001")
        assert resp.status_code == 500

    def test_hazard_compare_success(self, client):
        result = {"comparison": [{"model_id": "hm-001"}, {"model_id": "hm-002"}]}
        with patch("backend.compare_hazard_models", return_value=result):
            resp = client.post("/api/hazard/compare", json={"model_ids": ["hm-001", "hm-002"]})
        assert resp.status_code == 200

    def test_hazard_compare_error_returns_500(self, client):
        with patch("backend.compare_hazard_models", side_effect=Exception("comparison error")):
            resp = client.post("/api/hazard/compare", json={"model_ids": ["hm-001", "hm-002"]})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Markov chain routes — /api/markov/*
# ---------------------------------------------------------------------------

class TestMarkovRoutes:
    def test_markov_estimate_success(self, client):
        result = {"matrix_id": "mx-001", "matrix": [[0.9, 0.08, 0.02], [0.05, 0.90, 0.05], [0.0, 0.0, 1.0]]}
        with patch("backend.estimate_transition_matrix", return_value=result):
            resp = client.post("/api/markov/estimate", json={})
        assert resp.status_code == 200
        assert "matrix_id" in resp.json()

    def test_markov_estimate_with_product_and_segment(self, client):
        with patch("backend.estimate_transition_matrix", return_value={"matrix_id": "mx-002"}) as mock_fn:
            resp = client.post("/api/markov/estimate", json={"product_type": "mortgage", "segment": "retail"})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("mortgage", "retail")

    def test_markov_estimate_no_args_passes_none(self, client):
        with patch("backend.estimate_transition_matrix", return_value={"matrix_id": "mx-001"}) as mock_fn:
            resp = client.post("/api/markov/estimate", json={})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None, None)

    def test_markov_estimate_error_returns_500(self, client):
        with patch("backend.estimate_transition_matrix", side_effect=Exception("insufficient data")):
            resp = client.post("/api/markov/estimate", json={})
        assert resp.status_code == 500

    def test_markov_list_matrices_success(self, client):
        with patch("backend.list_transition_matrices", return_value=[{"matrix_id": "mx-001"}]):
            resp = client.get("/api/markov/matrices")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_markov_list_matrices_with_product_filter(self, client):
        with patch("backend.list_transition_matrices", return_value=[]) as mock_fn:
            resp = client.get("/api/markov/matrices?product_type=mortgage")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("mortgage")

    def test_markov_list_matrices_no_filter_passes_none(self, client):
        with patch("backend.list_transition_matrices", return_value=[]) as mock_fn:
            resp = client.get("/api/markov/matrices")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_markov_list_matrices_error_returns_500(self, client):
        with patch("backend.list_transition_matrices", side_effect=Exception("db error")):
            resp = client.get("/api/markov/matrices")
        assert resp.status_code == 500

    def test_markov_get_matrix_found(self, client):
        mat = {"matrix_id": "mx-001", "matrix": [[0.9, 0.1], [0.0, 1.0]]}
        with patch("backend.get_transition_matrix", return_value=mat):
            resp = client.get("/api/markov/matrix/mx-001")
        assert resp.status_code == 200
        assert resp.json()["matrix_id"] == "mx-001"

    def test_markov_get_matrix_not_found(self, client):
        with patch("backend.get_transition_matrix", return_value=None):
            resp = client.get("/api/markov/matrix/missing")
        assert resp.status_code == 404

    def test_markov_get_matrix_error_returns_500(self, client):
        with patch("backend.get_transition_matrix", side_effect=Exception("db error")):
            resp = client.get("/api/markov/matrix/mx-001")
        assert resp.status_code == 500

    def test_markov_forecast_success(self, client):
        result = {"matrix_id": "mx-001", "forecast": [[0.8, 0.15, 0.05]]}
        with patch("backend.forecast_stage_distribution", return_value=result):
            resp = client.post("/api/markov/forecast", json={
                "matrix_id": "mx-001",
                "initial_distribution": [0.85, 0.10, 0.05],
                "horizon_months": 24,
            })
        assert resp.status_code == 200
        assert "forecast" in resp.json()

    def test_markov_forecast_default_horizon(self, client):
        with patch("backend.forecast_stage_distribution", return_value={"forecast": []}) as mock_fn:
            resp = client.post("/api/markov/forecast", json={
                "matrix_id": "mx-001",
                "initial_distribution": [1.0, 0.0, 0.0],
            })
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("mx-001", [1.0, 0.0, 0.0], 60)

    def test_markov_forecast_value_error_returns_404(self, client):
        with patch("backend.forecast_stage_distribution", side_effect=ValueError("matrix mx-999 not found")):
            resp = client.post("/api/markov/forecast", json={
                "matrix_id": "mx-999",
                "initial_distribution": [1.0, 0.0, 0.0],
            })
        assert resp.status_code == 404

    def test_markov_forecast_error_returns_500(self, client):
        with patch("backend.forecast_stage_distribution", side_effect=Exception("numpy error")):
            resp = client.post("/api/markov/forecast", json={
                "matrix_id": "mx-001",
                "initial_distribution": [1.0, 0.0, 0.0],
            })
        assert resp.status_code == 500

    def test_markov_lifetime_pd_success(self, client):
        result = {"matrix_id": "mx-001", "lifetime_pd": 0.18}
        with patch("backend.compute_lifetime_pd", return_value=result):
            resp = client.get("/api/markov/lifetime-pd/mx-001")
        assert resp.status_code == 200
        assert "lifetime_pd" in resp.json()

    def test_markov_lifetime_pd_default_max_months(self, client):
        with patch("backend.compute_lifetime_pd", return_value={"lifetime_pd": 0.18}) as mock_fn:
            resp = client.get("/api/markov/lifetime-pd/mx-001")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("mx-001", 60)

    def test_markov_lifetime_pd_with_max_months(self, client):
        with patch("backend.compute_lifetime_pd", return_value={"lifetime_pd": 0.12}) as mock_fn:
            resp = client.get("/api/markov/lifetime-pd/mx-001?max_months=36")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("mx-001", 36)

    def test_markov_lifetime_pd_value_error_returns_404(self, client):
        with patch("backend.compute_lifetime_pd", side_effect=ValueError("matrix not found")):
            resp = client.get("/api/markov/lifetime-pd/missing")
        assert resp.status_code == 404

    def test_markov_lifetime_pd_error_returns_500(self, client):
        with patch("backend.compute_lifetime_pd", side_effect=Exception("computation error")):
            resp = client.get("/api/markov/lifetime-pd/mx-001")
        assert resp.status_code == 500

    def test_markov_compare_success(self, client):
        result = {"comparison": [{"matrix_id": "mx-001"}, {"matrix_id": "mx-002"}]}
        with patch("backend.compare_matrices", return_value=result):
            resp = client.post("/api/markov/compare", json={"matrix_ids": ["mx-001", "mx-002"]})
        assert resp.status_code == 200

    def test_markov_compare_single_id_returns_422(self, client):
        resp = client.post("/api/markov/compare", json={"matrix_ids": ["mx-001"]})
        assert resp.status_code == 422

    def test_markov_compare_error_returns_500(self, client):
        with patch("backend.compare_matrices", side_effect=Exception("comparison failed")):
            resp = client.post("/api/markov/compare", json={"matrix_ids": ["mx-001", "mx-002"]})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Backtesting routes — /api/backtest/*
# ---------------------------------------------------------------------------

class TestBacktestingRoutes:
    def test_run_backtest_success(self, client):
        result = {"backtest_id": "bt-001", "model_type": "PD", "auc": 0.78}
        with patch("backend.run_backtest", return_value=result):
            resp = client.post("/api/backtest/run", json={"model_type": "PD", "config": {}})
        assert resp.status_code == 200
        assert resp.json()["backtest_id"] == "bt-001"

    def test_run_backtest_default_model_type(self, client):
        with patch("backend.run_backtest", return_value={"backtest_id": "bt-002"}) as mock_fn:
            resp = client.post("/api/backtest/run", json={})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("PD", {})

    def test_run_backtest_lgd_model(self, client):
        with patch("backend.run_backtest", return_value={"backtest_id": "bt-003", "model_type": "LGD"}) as mock_fn:
            resp = client.post("/api/backtest/run", json={"model_type": "LGD", "config": {"threshold": 0.5}})
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("LGD", {"threshold": 0.5})

    def test_run_backtest_value_error_returns_400(self, client):
        with patch("backend.run_backtest", side_effect=ValueError("unsupported model type")):
            resp = client.post("/api/backtest/run", json={"model_type": "INVALID"})
        assert resp.status_code == 400

    def test_run_backtest_error_returns_500(self, client):
        with patch("backend.run_backtest", side_effect=Exception("scoring failed")):
            resp = client.post("/api/backtest/run", json={"model_type": "PD"})
        assert resp.status_code == 500

    def test_list_backtests_success(self, client):
        with patch("backend.list_backtests", return_value=[{"backtest_id": "bt-001", "model_type": "PD"}]):
            resp = client.get("/api/backtest/results")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_backtests_no_filter_passes_none(self, client):
        with patch("backend.list_backtests", return_value=[]) as mock_fn:
            resp = client.get("/api/backtest/results")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_list_backtests_with_model_type_filter(self, client):
        with patch("backend.list_backtests", return_value=[]) as mock_fn:
            resp = client.get("/api/backtest/results?model_type=LGD")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("LGD")

    def test_list_backtests_error_returns_500(self, client):
        with patch("backend.list_backtests", side_effect=Exception("db error")):
            resp = client.get("/api/backtest/results")
        assert resp.status_code == 500

    def test_backtest_trend_success(self, client):
        trend = {"model_type": "PD", "trend": [{"date": "2024-01", "auc": 0.78}]}
        with patch("backend.get_backtest_trend", return_value=trend):
            resp = client.get("/api/backtest/trend/PD")
        assert resp.status_code == 200
        assert resp.json()["model_type"] == "PD"

    def test_backtest_trend_error_returns_500(self, client):
        with patch("backend.get_backtest_trend", side_effect=Exception("no trend data")):
            resp = client.get("/api/backtest/trend/PD")
        assert resp.status_code == 500

    def test_get_backtest_found(self, client):
        with patch("backend.get_backtest", return_value={"backtest_id": "bt-001", "auc": 0.78}):
            resp = client.get("/api/backtest/bt-001")
        assert resp.status_code == 200
        assert resp.json()["backtest_id"] == "bt-001"

    def test_get_backtest_not_found(self, client):
        with patch("backend.get_backtest", return_value=None):
            resp = client.get("/api/backtest/missing-bt")
        assert resp.status_code == 404

    def test_get_backtest_error_returns_500(self, client):
        with patch("backend.get_backtest", side_effect=Exception("db error")):
            resp = client.get("/api/backtest/bt-001")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# RBAC routes — /api/rbac/*
# ---------------------------------------------------------------------------

class TestRbacRoutes:
    def test_list_users_success(self, client):
        users = [{"user_id": "u1", "role": "analyst"}, {"user_id": "u2", "role": "approver"}]
        with patch("backend.list_users", return_value=users):
            resp = client.get("/api/rbac/users")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 2

    def test_list_users_no_filter_passes_none(self, client):
        with patch("backend.list_users", return_value=[]) as mock_fn:
            resp = client.get("/api/rbac/users")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_list_users_with_role_filter(self, client):
        with patch("backend.list_users", return_value=[]) as mock_fn:
            resp = client.get("/api/rbac/users?role=approver")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("approver")

    def test_list_users_error_returns_500(self, client):
        with patch("backend.list_users", side_effect=Exception("db error")):
            resp = client.get("/api/rbac/users")
        assert resp.status_code == 500

    def test_get_user_found(self, client):
        user = {"user_id": "u1", "role": "analyst", "permissions": ["read", "run_model"]}
        with patch("backend.get_user", return_value=user):
            resp = client.get("/api/rbac/users/u1")
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "u1"

    def test_get_user_not_found(self, client):
        with patch("backend.get_user", return_value=None):
            resp = client.get("/api/rbac/users/missing")
        assert resp.status_code == 404

    def test_get_user_error_returns_500(self, client):
        with patch("backend.get_user", side_effect=Exception("db error")):
            resp = client.get("/api/rbac/users/u1")
        assert resp.status_code == 500

    def test_list_approvals_success(self, client):
        approvals = [{"request_id": "ar-001", "status": "pending"}]
        with patch("backend.list_approval_requests", return_value=approvals):
            resp = client.get("/api/rbac/approvals")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_approvals_with_filters(self, client):
        with patch("backend.list_approval_requests", return_value=[]) as mock_fn:
            resp = client.get("/api/rbac/approvals?status=pending&assigned_to=u2&type=sign_off")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("pending", "u2", "sign_off")

    def test_list_approvals_no_filters_passes_none(self, client):
        with patch("backend.list_approval_requests", return_value=[]) as mock_fn:
            resp = client.get("/api/rbac/approvals")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None, None, None)

    def test_list_approvals_error_returns_500(self, client):
        with patch("backend.list_approval_requests", side_effect=Exception("db error")):
            resp = client.get("/api/rbac/approvals")
        assert resp.status_code == 500

    def test_create_approval_success(self, client):
        created = {"request_id": "ar-001", "status": "pending", "request_type": "sign_off"}
        with patch("backend.create_approval_request", return_value=created):
            resp = client.post("/api/rbac/approvals", json={
                "request_type": "sign_off",
                "entity_id": "proj-001",
                "requested_by": "analyst1",
            })
        assert resp.status_code == 200
        assert resp.json()["request_id"] == "ar-001"

    def test_create_approval_error_returns_500(self, client):
        with patch("backend.create_approval_request", side_effect=Exception("db error")):
            resp = client.post("/api/rbac/approvals", json={
                "request_type": "sign_off",
                "entity_id": "proj-001",
                "requested_by": "analyst1",
            })
        assert resp.status_code == 500

    def test_approve_request_success(self, client):
        approved = {"request_id": "ar-001", "status": "approved"}
        with patch("backend.approve_request", return_value=approved):
            resp = client.post("/api/rbac/approvals/ar-001/approve", json={"user_id": "approver1", "comment": "LGTM"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_approve_request_value_error_returns_400(self, client):
        with patch("backend.approve_request", side_effect=ValueError("already approved")):
            resp = client.post("/api/rbac/approvals/ar-001/approve", json={"user_id": "approver1"})
        assert resp.status_code == 400

    def test_approve_request_error_returns_500(self, client):
        with patch("backend.approve_request", side_effect=Exception("db error")):
            resp = client.post("/api/rbac/approvals/ar-001/approve", json={"user_id": "approver1"})
        assert resp.status_code == 500

    def test_reject_request_success(self, client):
        rejected = {"request_id": "ar-001", "status": "rejected"}
        with patch("backend.reject_request", return_value=rejected):
            resp = client.post("/api/rbac/approvals/ar-001/reject", json={"user_id": "approver1", "comment": "needs rework"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_reject_request_value_error_returns_400(self, client):
        with patch("backend.reject_request", side_effect=ValueError("cannot reject closed request")):
            resp = client.post("/api/rbac/approvals/ar-001/reject", json={"user_id": "approver1"})
        assert resp.status_code == 400

    def test_reject_request_error_returns_500(self, client):
        with patch("backend.reject_request", side_effect=Exception("db error")):
            resp = client.post("/api/rbac/approvals/ar-001/reject", json={"user_id": "approver1"})
        assert resp.status_code == 500

    def test_approval_history_success(self, client):
        history = [{"request_id": "ar-001", "status": "approved", "entity_id": "proj-001"}]
        with patch("backend.get_approval_history", return_value=history):
            resp = client.get("/api/rbac/approvals/history/proj-001")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_approval_history_error_returns_500(self, client):
        with patch("backend.get_approval_history", side_effect=Exception("db error")):
            resp = client.get("/api/rbac/approvals/history/proj-001")
        assert resp.status_code == 500

    def test_check_permissions_found(self, client):
        user = {"user_id": "u1", "role": "analyst", "permissions": ["read", "run_model"]}
        with patch("backend.get_user", return_value=user):
            resp = client.get("/api/rbac/permissions/u1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "u1"
        assert data["role"] == "analyst"
        assert "permissions" in data

    def test_check_permissions_user_not_found(self, client):
        with patch("backend.get_user", return_value=None):
            resp = client.get("/api/rbac/permissions/missing")
        assert resp.status_code == 404

    def test_check_permissions_error_returns_500(self, client):
        with patch("backend.get_user", side_effect=Exception("db error")):
            resp = client.get("/api/rbac/permissions/u1")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Satellite routes — /api/model-runs, /api/data/cohort-summary, etc.
# ---------------------------------------------------------------------------

class TestSatelliteRoutes:
    def test_satellite_model_selected_success(self, client):
        df = pd.DataFrame({"product_type": ["personal_loan"], "model_type": ["linear_regression"], "r_squared": [0.85]})
        with patch("backend.get_satellite_model_selected", return_value=df):
            resp = client.get("/api/data/satellite-model-selected")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1

    def test_satellite_model_selected_with_run_id(self, client):
        df = pd.DataFrame({"product_type": ["personal_loan"]})
        with patch("backend.get_satellite_model_selected", return_value=df) as mock_fn:
            resp = client.get("/api/data/satellite-model-selected?run_id=2025-01-01")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("2025-01-01")

    def test_satellite_model_selected_no_run_id_passes_none(self, client):
        df = pd.DataFrame({"product_type": []})
        with patch("backend.get_satellite_model_selected", return_value=df) as mock_fn:
            resp = client.get("/api/data/satellite-model-selected")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_satellite_model_selected_error_returns_500(self, client):
        with patch("backend.get_satellite_model_selected", side_effect=Exception("db error")):
            resp = client.get("/api/data/satellite-model-selected")
        assert resp.status_code == 500

    def test_list_model_runs_success(self, client):
        df = pd.DataFrame({
            "run_id": ["run-001"],
            "run_type": ["satellite_model"],
            "models_used": ['["linear_regression"]'],
            "products": ['["personal_loan"]'],
            "best_model_summary": ['{}'],
        })
        with patch("backend.list_model_runs", return_value=df):
            resp = client.get("/api/model-runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_model_runs_parses_json_fields(self, client):
        df = pd.DataFrame({
            "run_id": ["run-001"],
            "run_type": ["satellite_model"],
            "models_used": ['["lr", "ridge"]'],
            "products": ['["loan_a"]'],
            "best_model_summary": ['{"model": "lr"}'],
        })
        with patch("backend.list_model_runs", return_value=df):
            resp = client.get("/api/model-runs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data[0]["models_used"], list)
        assert isinstance(data[0]["best_model_summary"], dict)

    def test_list_model_runs_with_run_type_filter(self, client):
        df = pd.DataFrame({"run_id": [], "run_type": [], "models_used": [], "products": [], "best_model_summary": []})
        with patch("backend.list_model_runs", return_value=df) as mock_fn:
            resp = client.get("/api/model-runs?run_type=satellite_model")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("satellite_model")

    def test_list_model_runs_no_filter_passes_none(self, client):
        df = pd.DataFrame({"run_id": [], "run_type": [], "models_used": [], "products": [], "best_model_summary": []})
        with patch("backend.list_model_runs", return_value=df) as mock_fn:
            resp = client.get("/api/model-runs")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None)

    def test_list_model_runs_error_returns_500(self, client):
        with patch("backend.list_model_runs", side_effect=Exception("db error")):
            resp = client.get("/api/model-runs")
        assert resp.status_code == 500

    def test_get_model_run_found(self, client):
        run = {"run_id": "run-001", "run_type": "satellite_model", "models_used": []}
        with patch("backend.get_model_run", return_value=run):
            resp = client.get("/api/model-runs/run-001")
        assert resp.status_code == 200

    def test_get_model_run_not_found(self, client):
        with patch("backend.get_model_run", return_value=None):
            resp = client.get("/api/model-runs/missing")
        assert resp.status_code == 404

    def test_get_model_run_error_returns_500(self, client):
        with patch("backend.get_model_run", side_effect=Exception("db error")):
            resp = client.get("/api/model-runs/run-001")
        assert resp.status_code == 500

    def test_save_model_run_success(self, client):
        saved = {"run_id": "run-002", "run_type": "satellite_model", "total_cohorts": 5}
        with patch("backend.save_model_run", return_value=saved):
            resp = client.post("/api/model-runs", json={
                "run_id": "run-002",
                "run_type": "satellite_model",
                "models_used": ["linear_regression"],
                "products": ["personal_loan"],
                "total_cohorts": 5,
            })
        assert resp.status_code == 200
        assert resp.json()["run_id"] == "run-002"

    def test_save_model_run_error_returns_500(self, client):
        with patch("backend.save_model_run", side_effect=Exception("db error")):
            resp = client.post("/api/model-runs", json={
                "run_id": "run-002",
                "run_type": "satellite_model",
            })
        assert resp.status_code == 500

    def test_cohort_summary_success(self, client):
        df = pd.DataFrame({"product_type": ["personal_loan", "mortgage"], "cohort_count": [100, 50]})
        with patch("backend.get_cohort_summary", return_value=df):
            resp = client.get("/api/data/cohort-summary")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_cohort_summary_error_returns_500(self, client):
        with patch("backend.get_cohort_summary", side_effect=Exception("db error")):
            resp = client.get("/api/data/cohort-summary")
        assert resp.status_code == 500

    def test_cohort_summary_by_product_success(self, client):
        df = pd.DataFrame({"product_type": ["personal_loan"], "cohort_count": [100]})
        with patch("backend.get_cohort_summary_by_product", return_value=df) as mock_fn:
            resp = client.get("/api/data/cohort-summary/personal_loan")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("personal_loan")

    def test_cohort_summary_by_product_error_returns_500(self, client):
        with patch("backend.get_cohort_summary_by_product", side_effect=Exception("db error")):
            resp = client.get("/api/data/cohort-summary/personal_loan")
        assert resp.status_code == 500

    def test_drill_down_dimensions_success(self, client):
        with patch("backend.get_drill_down_dimensions", return_value=["risk_band", "region", "vintage"]):
            resp = client.get("/api/data/drill-down-dimensions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_drill_down_dimensions_with_product(self, client):
        with patch("backend.get_drill_down_dimensions", return_value=["risk_band"]) as mock_fn:
            resp = client.get("/api/data/drill-down-dimensions?product=personal_loan")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("personal_loan")

    def test_drill_down_dimensions_default_product(self, client):
        with patch("backend.get_drill_down_dimensions", return_value=[]) as mock_fn:
            resp = client.get("/api/data/drill-down-dimensions")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("any")

    def test_drill_down_dimensions_error_returns_500(self, client):
        with patch("backend.get_drill_down_dimensions", side_effect=Exception("db error")):
            resp = client.get("/api/data/drill-down-dimensions")
        assert resp.status_code == 500

    def test_ecl_by_cohort_success(self, client):
        df = pd.DataFrame({"product": ["personal_loan"], "risk_band": ["high"], "ecl": [50000]})
        with patch("backend.get_ecl_by_cohort", return_value=df) as mock_fn:
            resp = client.get("/api/data/ecl-by-cohort?product=personal_loan&dimension=risk_band")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("personal_loan", "risk_band")

    def test_ecl_by_cohort_default_dimension(self, client):
        df = pd.DataFrame({"product": ["personal_loan"]})
        with patch("backend.get_ecl_by_cohort", return_value=df) as mock_fn:
            resp = client.get("/api/data/ecl-by-cohort?product=personal_loan")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("personal_loan", "risk_band")

    def test_ecl_by_cohort_error_returns_500(self, client):
        with patch("backend.get_ecl_by_cohort", side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-by-cohort?product=personal_loan")
        assert resp.status_code == 500

    def test_stage_by_cohort_success(self, client):
        df = pd.DataFrame({"product": ["personal_loan"], "stage": [1], "count": [100]})
        with patch("backend.get_stage_by_cohort", return_value=df) as mock_fn:
            resp = client.get("/api/data/stage-by-cohort?product=personal_loan")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("personal_loan")

    def test_stage_by_cohort_error_returns_500(self, client):
        with patch("backend.get_stage_by_cohort", side_effect=Exception("db error")):
            resp = client.get("/api/data/stage-by-cohort?product=personal_loan")
        assert resp.status_code == 500

    def test_portfolio_by_cohort_success(self, client):
        df = pd.DataFrame({"product": ["personal_loan"], "risk_band": ["low"], "gca": [1000000]})
        with patch("backend.get_portfolio_by_dimension", return_value=df) as mock_fn:
            resp = client.get("/api/data/portfolio-by-cohort?product=personal_loan&dimension=risk_band")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("personal_loan", "risk_band")

    def test_portfolio_by_cohort_default_dimension(self, client):
        df = pd.DataFrame({"product": ["personal_loan"]})
        with patch("backend.get_portfolio_by_dimension", return_value=df) as mock_fn:
            resp = client.get("/api/data/portfolio-by-cohort?product=personal_loan")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("personal_loan", "risk_band")

    def test_portfolio_by_cohort_error_returns_500(self, client):
        with patch("backend.get_portfolio_by_dimension", side_effect=Exception("db error")):
            resp = client.get("/api/data/portfolio-by-cohort?product=personal_loan")
        assert resp.status_code == 500

    def test_ecl_by_product_drilldown_success(self, client):
        df = pd.DataFrame({"product": ["personal_loan", "mortgage"], "total_ecl": [500000, 800000]})
        with patch("backend.get_ecl_by_product_drilldown", return_value=df):
            resp = client.get("/api/data/ecl-by-product-drilldown")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_ecl_by_product_drilldown_error_returns_500(self, client):
        with patch("backend.get_ecl_by_product_drilldown", side_effect=Exception("db error")):
            resp = client.get("/api/data/ecl-by-product-drilldown")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Simulation routes — /api/simulate, /api/simulation-defaults, /api/simulation/compare
# ---------------------------------------------------------------------------

class TestSimulationRunRoutes:
    """Tests for POST /simulate and GET /simulation/compare."""

    def test_run_simulation_success(self, client):
        raw = {
            "stage_summary": [{"stage": 1, "total_gca": 1000000, "total_ecl": 50000}],
            "scenario_results": [{"scenario": "baseline", "weight": 0.60, "total_ecl": 50000}],
            "portfolio_summary": [{"product_type": "personal_loan", "loan_count": 100, "total_gca": 1000000, "total_ecl": 50000}],
            "product_scenario": [],
            "run_metadata": {},
        }
        with patch("domain.validation_rules.run_all_pre_calculation_checks", return_value=[]), \
             patch("domain.validation_rules.has_critical_failures", return_value=False), \
             patch("ecl_engine.run_simulation", return_value=raw), \
             patch("routes.simulation._persist_simulation_run"):
            resp = client.post("/api/simulate", json={"n_simulations": 1000})
        assert resp.status_code == 200
        data = resp.json()
        assert "ecl_by_product" in data
        assert "scenario_summary" in data
        assert "loss_allowance_by_stage" in data

    def test_run_simulation_critical_validation_failure_returns_400(self, client):
        checks = [{"check": "pd_values", "status": "FAIL", "severity": "critical", "message": "no PD data"}]
        with patch("domain.validation_rules.run_all_pre_calculation_checks", return_value=checks), \
             patch("domain.validation_rules.has_critical_failures", return_value=True):
            resp = client.post("/api/simulate", json={"n_simulations": 1000})
        assert resp.status_code == 400

    def test_run_simulation_engine_error_returns_500(self, client):
        with patch("domain.validation_rules.run_all_pre_calculation_checks", return_value=[]), \
             patch("domain.validation_rules.has_critical_failures", return_value=False), \
             patch("ecl_engine.run_simulation", side_effect=Exception("numpy crash")):
            resp = client.post("/api/simulate", json={"n_simulations": 1000})
        assert resp.status_code == 500

    def test_simulation_defaults_error_returns_500(self, client):
        with patch("ecl_engine.get_defaults", side_effect=Exception("config missing")):
            resp = client.get("/api/simulation-defaults")
        assert resp.status_code == 500

    def test_compare_simulation_runs_success(self, client):
        run_a = {"run_id": "r-001", "run_type": "satellite_model", "run_timestamp": "2025-01-01",
                 "products": ["personal_loan"], "best_model_summary": {"total_ecl": 1000000, "weighted_ecl": 950000}}
        run_b = {"run_id": "r-002", "run_type": "satellite_model", "run_timestamp": "2025-02-01",
                 "products": ["personal_loan"], "best_model_summary": {"total_ecl": 1100000, "weighted_ecl": 1050000}}
        with patch("domain.model_runs.get_model_run", side_effect=[run_a, run_b]):
            resp = client.get("/api/simulation/compare?run_a=r-001&run_b=r-002")
        assert resp.status_code == 200
        data = resp.json()
        assert "deltas" in data
        assert "run_a" in data
        assert "run_b" in data

    def test_compare_simulation_runs_missing_returns_404(self, client):
        with patch("domain.model_runs.get_model_run", side_effect=[None, None]):
            resp = client.get("/api/simulation/compare?run_a=missing-a&run_b=missing-b")
        assert resp.status_code == 404

    def test_compare_simulation_runs_error_returns_500(self, client):
        with patch("domain.model_runs.get_model_run", side_effect=Exception("db error")):
            resp = client.get("/api/simulation/compare?run_a=r-001&run_b=r-002")
        assert resp.status_code == 500
