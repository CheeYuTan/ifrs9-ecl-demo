"""Tests for admin_config module — configuration CRUD and validation."""
import json
import pytest
from unittest.mock import patch, MagicMock, call
import pandas as pd

import admin_config


class TestDefaultConfig:
    """Verify the default configuration structure is complete and valid."""

    def test_default_config_has_all_sections(self):
        assert set(admin_config.DEFAULT_CONFIG.keys()) == {"data_sources", "model", "jobs", "app_settings"}

    def test_data_sources_has_required_tables(self):
        tables = admin_config.DATA_SOURCE_CONFIG["tables"]
        assert "loan_tape" in tables
        assert "borrower_master" in tables
        assert "payment_history" in tables
        assert "historical_defaults" in tables
        assert "macro_scenarios" in tables

    def test_raw_tables_marked_required_or_optional(self):
        tables = admin_config.DATA_SOURCE_CONFIG["tables"]
        required_tables = ["loan_tape", "borrower_master", "payment_history", "historical_defaults", "macro_scenarios"]
        optional_tables = ["general_ledger", "collateral_register"]
        for t in required_tables:
            assert tables[t].get("required") is True, f"{t} should be required"
        for t in optional_tables:
            assert tables[t].get("required") is False, f"{t} should be optional"

    def test_loan_tape_mandatory_columns(self):
        cols = admin_config.DATA_SOURCE_CONFIG["tables"]["loan_tape"]["mandatory_columns"]
        col_names = [c["name"] for c in cols]
        for required in ["loan_id", "borrower_id", "product_type", "gross_carrying_amount",
                         "effective_interest_rate", "current_lifetime_pd", "remaining_months",
                         "days_past_due", "origination_date", "maturity_date"]:
            assert required in col_names, f"Missing mandatory column: {required}"

    def test_columns_have_rich_metadata(self):
        cols = admin_config.DATA_SOURCE_CONFIG["tables"]["loan_tape"]["mandatory_columns"]
        for col in cols:
            assert "description" in col, f"{col['name']} missing description"
            assert "example" in col, f"{col['name']} missing example"
            assert "constraints" in col, f"{col['name']} missing constraints"

    def test_governance_config_exists(self):
        gov = admin_config.APP_SETTINGS.get("governance")
        assert gov is not None
        assert "cfo_name" in gov
        assert "cro_name" in gov
        assert "approval_workflow" in gov
        assert "external_auditor_firm" in gov

    def test_all_satellite_models_defined(self):
        models = admin_config.MODEL_CONFIG["satellite_models"]
        assert len(models) >= 8
        for key, val in models.items():
            assert "enabled" in val
            assert "label" in val

    def test_scenarios_weights_sum_to_one(self):
        scenarios = admin_config.APP_SETTINGS["scenarios"]
        total = sum(s["weight"] for s in scenarios)
        assert abs(total - 1.0) < 0.01, f"Scenario weights sum to {total}, expected ~1.0"

    def test_each_scenario_has_required_fields(self):
        for sc in admin_config.APP_SETTINGS["scenarios"]:
            assert "key" in sc
            assert "name" in sc
            assert "weight" in sc
            assert "pd_multiplier" in sc
            assert "lgd_multiplier" in sc
            assert "color" in sc

    def test_job_config_has_job_ids_key(self):
        assert "job_ids" in admin_config.JOB_CONFIG
        assert isinstance(admin_config.JOB_CONFIG["job_ids"], dict)

    def test_lgd_assumptions_have_required_fields(self):
        for product, vals in admin_config.MODEL_CONFIG["lgd_assumptions"].items():
            assert "lgd" in vals, f"{product} missing lgd"
            assert "cure_rate" in vals, f"{product} missing cure_rate"
            assert 0 <= vals["lgd"] <= 1, f"{product} lgd out of range"
            assert 0 <= vals["cure_rate"] <= 1, f"{product} cure_rate out of range"


class TestGetConfig:
    """Test get_config() retrieves and merges config correctly."""

    def test_returns_all_sections(self, mock_db):
        mock_db["query_df"].side_effect = [
            pd.DataFrame({"cnt": [0]}),
            pd.DataFrame({"config_key": [], "config_value": []}),
        ]
        result = admin_config.get_config()
        assert "data_sources" in result
        assert "model" in result
        assert "jobs" in result
        assert "app_settings" in result

    def test_returns_stored_values_when_present(self, mock_db):
        custom_settings = {"organization_name": "Test Bank"}
        mock_db["query_df"].side_effect = [
            pd.DataFrame({"cnt": [1]}),
            pd.DataFrame({
                "config_key": ["app_settings"],
                "config_value": [json.dumps(custom_settings)],
            }),
        ]
        result = admin_config.get_config()
        assert result["app_settings"] == custom_settings
        assert result["data_sources"] == admin_config.DATA_SOURCE_CONFIG


class TestSaveConfig:
    """Test save_config() persists correctly."""

    def test_calls_execute_for_each_section(self, mock_db):
        config_df = pd.DataFrame({"config_key": ["test"], "config_value": [json.dumps({"a": 1})]})
        def qdf_side_effect(*args, **kwargs):
            q = args[0] if args else ""
            if "COUNT" in str(q):
                return pd.DataFrame({"cnt": [1]})
            return config_df
        mock_db["query_df"].side_effect = qdf_side_effect
        admin_config.save_config({"test": {"a": 1}})
        assert mock_db["execute"].call_count >= 1


class TestSeedDefaults:
    """Test seed_defaults() resets to factory config."""

    def test_deletes_and_reinserts(self, mock_db):
        mock_db["query_df"].side_effect = [
            pd.DataFrame({"cnt": [0]}),                                # init() -> _seed_defaults_if_empty (seeds defaults)
            pd.DataFrame({"config_key": [], "config_value": []}),      # get_config() -> SELECT config
        ]
        admin_config.seed_defaults()
        delete_calls = [c for c in mock_db["execute"].call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) >= 1


class TestValidateColumnMapping:
    """Test validate_column_mapping() checks against actual schema."""

    def test_valid_mapping_returns_valid(self, mock_db):
        mock_db["query_df"].side_effect = [
            pd.DataFrame({"cnt": [1]}),
            pd.DataFrame({"config_value": [json.dumps(admin_config.DATA_SOURCE_CONFIG)]}),
            pd.DataFrame({"column_name": ["borrower_id", "segment", "age",
                                           "monthly_income", "income_source",
                                           "employment_tenure_months", "education_level",
                                           "formal_credit_score", "alt_data_composite_score",
                                           "country", "region", "dependents"]}),
        ]
        result = admin_config.validate_column_mapping("borrower_master", {})
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_missing_mandatory_column_returns_invalid(self, mock_db):
        mock_db["query_df"].side_effect = [
            pd.DataFrame({"cnt": [1]}),
            pd.DataFrame({"config_value": [json.dumps(admin_config.DATA_SOURCE_CONFIG)]}),
            pd.DataFrame({"column_name": ["borrower_id"]}),
        ]
        result = admin_config.validate_column_mapping("borrower_master", {})
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_unknown_table_returns_invalid(self, mock_db):
        mock_db["query_df"].side_effect = [
            pd.DataFrame({"cnt": [1]}),
            pd.DataFrame({"config_value": [json.dumps(admin_config.DATA_SOURCE_CONFIG)]}),
        ]
        result = admin_config.validate_column_mapping("nonexistent_table", {})
        assert result["valid"] is False


class TestTestConnection:
    """Test test_connection() reports status."""

    def test_successful_connection(self, mock_db):
        mock_db["query_df"].return_value = pd.DataFrame({
            "version": ["PostgreSQL 15.4"],
            "server_time": ["2025-12-31 12:00:00"],
        })
        result = admin_config.test_connection()
        assert result["connected"] is True
        assert "version" in result

    def test_failed_connection(self, mock_db):
        mock_db["query_df"].side_effect = Exception("Connection refused")
        result = admin_config.test_connection()
        assert result["connected"] is False
        assert "error" in result
