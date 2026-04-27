"""Dedicated tests for admin_config_defaults.py — configuration constants and data schema."""
import pytest

from admin_config_defaults import DATA_SOURCE_CONFIG, DEFAULT_CONFIG


class TestDataSourceConfig:
    def test_has_catalog(self):
        assert "catalog" in DATA_SOURCE_CONFIG

    def test_has_schema(self):
        assert "schema" in DATA_SOURCE_CONFIG

    def test_has_lakebase_schema(self):
        assert "lakebase_schema" in DATA_SOURCE_CONFIG

    def test_has_lakebase_prefix(self):
        assert "lakebase_prefix" in DATA_SOURCE_CONFIG

    def test_has_tables(self):
        assert "tables" in DATA_SOURCE_CONFIG
        assert isinstance(DATA_SOURCE_CONFIG["tables"], dict)

    def test_has_eight_tables(self):
        assert len(DATA_SOURCE_CONFIG["tables"]) == 8

    def test_expected_tables_present(self):
        expected = {"loan_tape", "borrower_master", "payment_history",
                    "historical_defaults", "macro_scenarios", "general_ledger",
                    "collateral_register", "model_ready_loans"}
        assert set(DATA_SOURCE_CONFIG["tables"].keys()) == expected

    def test_loan_tape_is_required(self):
        assert DATA_SOURCE_CONFIG["tables"]["loan_tape"]["required"] is True

    def test_borrower_master_is_required(self):
        assert DATA_SOURCE_CONFIG["tables"]["borrower_master"]["required"] is True

    def test_all_tables_have_source_table(self):
        for name, cfg in DATA_SOURCE_CONFIG["tables"].items():
            assert "source_table" in cfg, f"{name} missing source_table"

    def test_all_tables_have_required_flag(self):
        for name, cfg in DATA_SOURCE_CONFIG["tables"].items():
            assert "required" in cfg, f"{name} missing required"

    def test_all_tables_have_description(self):
        for name, cfg in DATA_SOURCE_CONFIG["tables"].items():
            assert "description" in cfg, f"{name} missing description"
            assert len(cfg["description"]) > 0

    def test_all_tables_have_mandatory_columns(self):
        for name, cfg in DATA_SOURCE_CONFIG["tables"].items():
            assert "mandatory_columns" in cfg, f"{name} missing mandatory_columns"
            assert isinstance(cfg["mandatory_columns"], list)

    def test_loan_tape_has_loan_id_column(self):
        cols = DATA_SOURCE_CONFIG["tables"]["loan_tape"]["mandatory_columns"]
        col_names = [c["name"] for c in cols]
        assert "loan_id" in col_names

    def test_loan_tape_has_gca_column(self):
        cols = DATA_SOURCE_CONFIG["tables"]["loan_tape"]["mandatory_columns"]
        col_names = [c["name"] for c in cols]
        assert "gross_carrying_amount" in col_names

    def test_all_columns_have_required_fields(self):
        for table_name, cfg in DATA_SOURCE_CONFIG["tables"].items():
            for col in cfg["mandatory_columns"]:
                assert "name" in col, f"{table_name} column missing name"
                assert "type" in col, f"{table_name}.{col.get('name', '?')} missing type"
                assert "description" in col, f"{table_name}.{col.get('name', '?')} missing description"

    def test_column_types_are_valid(self):
        valid_types = {"TEXT", "NUMERIC", "INT", "DATE", "BOOLEAN", "TIMESTAMP"}
        for table_name, cfg in DATA_SOURCE_CONFIG["tables"].items():
            for col in cfg["mandatory_columns"]:
                assert col["type"] in valid_types, \
                    f"{table_name}.{col['name']} has invalid type: {col['type']}"

    def test_loan_tape_columns_count(self):
        cols = DATA_SOURCE_CONFIG["tables"]["loan_tape"]["mandatory_columns"]
        assert len(cols) >= 8

    def test_borrower_master_has_borrower_id(self):
        cols = DATA_SOURCE_CONFIG["tables"]["borrower_master"]["mandatory_columns"]
        col_names = [c["name"] for c in cols]
        assert "borrower_id" in col_names


class TestDefaultConfig:
    def test_has_four_sections(self):
        assert len(DEFAULT_CONFIG) == 4

    def test_has_data_sources(self):
        assert "data_sources" in DEFAULT_CONFIG

    def test_has_model(self):
        assert "model" in DEFAULT_CONFIG

    def test_has_jobs(self):
        assert "jobs" in DEFAULT_CONFIG

    def test_has_app_settings(self):
        assert "app_settings" in DEFAULT_CONFIG

    def test_model_has_lgd_assumptions(self):
        assert "lgd_assumptions" in DEFAULT_CONFIG["model"]

    def test_lgd_assumptions_not_empty(self):
        lgd = DEFAULT_CONFIG["model"]["lgd_assumptions"]
        assert len(lgd) > 0

    def test_app_settings_has_scenarios(self):
        assert "scenarios" in DEFAULT_CONFIG["app_settings"]

    def test_scenarios_is_list(self):
        assert isinstance(DEFAULT_CONFIG["app_settings"]["scenarios"], list)

    def test_scenarios_not_empty(self):
        assert len(DEFAULT_CONFIG["app_settings"]["scenarios"]) > 0

    def test_each_scenario_has_key_and_name(self):
        for sc in DEFAULT_CONFIG["app_settings"]["scenarios"]:
            assert "key" in sc, f"Scenario missing key: {sc}"
            assert "name" in sc, f"Scenario missing name: {sc}"

    def test_data_sources_matches_data_source_config(self):
        ds = DEFAULT_CONFIG["data_sources"]
        assert ds == DATA_SOURCE_CONFIG

    def test_lgd_has_product_entries(self):
        lgd = DEFAULT_CONFIG["model"]["lgd_assumptions"]
        for product, vals in lgd.items():
            assert "lgd" in vals, f"{product} missing lgd"
            assert 0 < vals["lgd"] < 1, f"{product} has invalid lgd: {vals['lgd']}"

    def test_jobs_section_exists(self):
        assert isinstance(DEFAULT_CONFIG["jobs"], dict)
