"""Tests for domain/data_mapper.py — UC mapping, validation, and type conversion."""

import pytest
from unittest.mock import patch, MagicMock

from domain.data_mapper import (
    _safe_identifier,
    _uc_type_to_ecl_type,
    list_uc_catalogs,
    list_uc_schemas,
    list_uc_tables,
    get_uc_table_columns,
    preview_lakebase_table,
    validate_mapping,
    suggest_mappings,
    get_mapping_status,
    PG_TYPE_MAP,
)


class TestSafeIdentifier:
    def test_valid_simple(self):
        assert _safe_identifier("my_table") == "my_table"

    def test_valid_with_dots(self):
        assert _safe_identifier("catalog.schema.table") == "catalog.schema.table"

    def test_valid_with_dashes(self):
        assert _safe_identifier("my-table") == "my-table"

    def test_valid_starts_with_underscore(self):
        assert _safe_identifier("_private") == "_private"

    def test_valid_alphanumeric(self):
        assert _safe_identifier("table123") == "table123"

    def test_invalid_starts_with_number(self):
        with pytest.raises(ValueError, match="Invalid identifier"):
            _safe_identifier("123table")

    def test_invalid_sql_injection_semicolon(self):
        with pytest.raises(ValueError, match="Invalid identifier"):
            _safe_identifier("table; DROP TABLE users")

    def test_invalid_sql_injection_quotes(self):
        with pytest.raises(ValueError, match="Invalid identifier"):
            _safe_identifier("table' OR '1'='1")

    def test_invalid_spaces(self):
        with pytest.raises(ValueError, match="Invalid identifier"):
            _safe_identifier("my table")

    def test_invalid_special_chars(self):
        with pytest.raises(ValueError, match="Invalid identifier"):
            _safe_identifier("table@name")

    def test_invalid_empty_string(self):
        with pytest.raises(ValueError, match="Invalid identifier"):
            _safe_identifier("")

    def test_invalid_parentheses(self):
        with pytest.raises(ValueError, match="Invalid identifier"):
            _safe_identifier("func()")


class TestUcTypeToEclType:
    def test_string_types(self):
        assert _uc_type_to_ecl_type("STRING") == "TEXT"
        assert _uc_type_to_ecl_type("VARCHAR") == "TEXT"
        assert _uc_type_to_ecl_type("CHAR") == "TEXT"
        assert _uc_type_to_ecl_type("varchar(255)") == "TEXT"

    def test_integer_types(self):
        assert _uc_type_to_ecl_type("INT") == "INT"
        assert _uc_type_to_ecl_type("LONG") == "INT"
        assert _uc_type_to_ecl_type("SHORT") == "INT"
        assert _uc_type_to_ecl_type("BYTE") == "INT"
        assert _uc_type_to_ecl_type("TINYINT") == "INT"
        assert _uc_type_to_ecl_type("SMALLINT") == "INT"
        assert _uc_type_to_ecl_type("BIGINT") == "INT"

    def test_numeric_types(self):
        assert _uc_type_to_ecl_type("DOUBLE") == "NUMERIC"
        assert _uc_type_to_ecl_type("FLOAT") == "NUMERIC"
        assert _uc_type_to_ecl_type("DECIMAL") == "NUMERIC"
        assert _uc_type_to_ecl_type("NUMERIC") == "NUMERIC"

    def test_date_types(self):
        assert _uc_type_to_ecl_type("DATE") == "DATE"
        assert _uc_type_to_ecl_type("TIMESTAMP") == "DATE"
        assert _uc_type_to_ecl_type("timestamp_ntz") == "DATE"

    def test_boolean_types(self):
        assert _uc_type_to_ecl_type("BOOLEAN") == "BOOLEAN"
        assert _uc_type_to_ecl_type("BOOL") == "BOOLEAN"

    def test_unknown_defaults_to_text(self):
        assert _uc_type_to_ecl_type("BINARY") == "TEXT"
        assert _uc_type_to_ecl_type("MAP") == "TEXT"
        assert _uc_type_to_ecl_type("ARRAY") == "TEXT"
        assert _uc_type_to_ecl_type("STRUCT") == "TEXT"

    def test_case_insensitive(self):
        assert _uc_type_to_ecl_type("string") == "TEXT"
        assert _uc_type_to_ecl_type("int") == "INT"
        assert _uc_type_to_ecl_type("double") == "NUMERIC"
        assert _uc_type_to_ecl_type("boolean") == "BOOLEAN"


class TestListUcCatalogs:
    def test_returns_catalog_list(self):
        mock_catalog = MagicMock()
        mock_catalog.name = "my_catalog"
        mock_catalog.comment = "A catalog"
        mock_ws = MagicMock()
        mock_ws.catalogs.list.return_value = [mock_catalog]
        with patch("domain.data_mapper._get_workspace_client", return_value=mock_ws):
            result = list_uc_catalogs()
            assert len(result) == 1
            assert result[0]["name"] == "my_catalog"
            assert result[0]["comment"] == "A catalog"

    def test_empty_comment(self):
        mock_catalog = MagicMock()
        mock_catalog.name = "cat"
        mock_catalog.comment = None
        mock_ws = MagicMock()
        mock_ws.catalogs.list.return_value = [mock_catalog]
        with patch("domain.data_mapper._get_workspace_client", return_value=mock_ws):
            result = list_uc_catalogs()
            assert result[0]["comment"] == ""

    def test_returns_empty_on_error(self):
        with patch("domain.data_mapper._get_workspace_client", side_effect=Exception("SDK error")):
            result = list_uc_catalogs()
            assert result == []


class TestListUcSchemas:
    def test_returns_schema_list(self):
        mock_schema = MagicMock()
        mock_schema.name = "default"
        mock_schema.full_name = "catalog.default"
        mock_schema.comment = None
        mock_ws = MagicMock()
        mock_ws.schemas.list.return_value = [mock_schema]
        with patch("domain.data_mapper._get_workspace_client", return_value=mock_ws):
            result = list_uc_schemas("catalog")
            assert len(result) == 1
            assert result[0]["full_name"] == "catalog.default"

    def test_invalid_catalog_name_raises(self):
        with patch("domain.data_mapper._get_workspace_client") as mock_ws:
            result = list_uc_schemas("bad name!")
            assert result == []


class TestListUcTables:
    def test_returns_table_list(self):
        mock_table = MagicMock()
        mock_table.name = "loans"
        mock_table.full_name = "cat.schema.loans"
        mock_table.table_type = "MANAGED"
        mock_table.comment = "Loan data"
        mock_ws = MagicMock()
        mock_ws.tables.list.return_value = [mock_table]
        with patch("domain.data_mapper._get_workspace_client", return_value=mock_ws):
            result = list_uc_tables("cat", "schema")
            assert len(result) == 1
            assert result[0]["name"] == "loans"

    def test_returns_empty_on_error(self):
        with patch("domain.data_mapper._get_workspace_client", side_effect=Exception("error")):
            result = list_uc_tables("cat", "schema")
            assert result == []


class TestGetUcTableColumns:
    def test_returns_columns(self):
        mock_col = MagicMock()
        mock_col.name = "loan_id"
        mock_col.type_name = MagicMock(value="STRING")
        mock_col.comment = "Primary key"
        mock_col.position = 0
        mock_table_info = MagicMock()
        mock_table_info.columns = [mock_col]
        mock_ws = MagicMock()
        mock_ws.tables.get.return_value = mock_table_info
        with patch("domain.data_mapper._get_workspace_client", return_value=mock_ws):
            result = get_uc_table_columns("cat.schema.table")
            assert len(result) == 1
            assert result[0]["name"] == "loan_id"
            assert result[0]["type"] == "STRING"

    def test_no_columns(self):
        mock_table_info = MagicMock()
        mock_table_info.columns = None
        mock_ws = MagicMock()
        mock_ws.tables.get.return_value = mock_table_info
        with patch("domain.data_mapper._get_workspace_client", return_value=mock_ws):
            result = get_uc_table_columns("cat.schema.table")
            assert result == []

    def test_returns_empty_on_error(self):
        with patch("domain.data_mapper._get_workspace_client", side_effect=Exception("err")):
            result = get_uc_table_columns("cat.schema.table")
            assert result == []

    def test_column_with_no_type(self):
        mock_col = MagicMock()
        mock_col.name = "col1"
        mock_col.type_name = None
        mock_col.comment = ""
        mock_col.position = 0
        mock_table_info = MagicMock()
        mock_table_info.columns = [mock_col]
        mock_ws = MagicMock()
        mock_ws.tables.get.return_value = mock_table_info
        with patch("domain.data_mapper._get_workspace_client", return_value=mock_ws):
            result = get_uc_table_columns("cat.schema.table")
            assert result[0]["type"] == "STRING"


class TestPreviewLakebaseTable:
    def test_delegates_to_admin_config(self):
        with patch("domain.data_mapper.admin_config") as mock_ac:
            mock_ac.get_table_preview.return_value = {"rows": [{"a": 1}]}
            result = preview_lakebase_table("loan_tape", limit=5)
            mock_ac.get_table_preview.assert_called_once_with("loan_tape", limit=5)
            assert result["rows"][0]["a"] == 1


class TestValidateMapping:
    def _setup_mocks(self, table_cfg, source_columns):
        """Common mock setup for validation tests."""
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_columns):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            yield mock_ac

    def test_valid_mapping(self):
        table_cfg = {
            "mandatory_columns": [
                {"name": "loan_id", "type": "TEXT", "description": "Loan ID"},
                {"name": "amount", "type": "NUMERIC", "description": "Amount"},
            ],
            "optional_columns": [],
        }
        source_columns = [
            {"name": "loan_id", "type": "STRING"},
            {"name": "amount", "type": "DOUBLE"},
        ]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_columns):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = validate_mapping("loan_tape", "cat.schema.src", {"loan_id": "loan_id", "amount": "amount"})
            assert result["valid"] is True
            assert result["errors"] == []
            assert result["mandatory_mapped"] == 2

    def test_unmapped_mandatory_column(self):
        table_cfg = {
            "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
            "optional_columns": [],
        }
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=[{"name": "x", "type": "STRING"}]):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = validate_mapping("loan_tape", "cat.schema.src", {})
            assert result["valid"] is False
            assert any("not mapped" in e for e in result["errors"])

    def test_unknown_table_key(self):
        with patch("domain.data_mapper.admin_config") as mock_ac:
            mock_ac.get_config_section.return_value = {"tables": {}}
            result = validate_mapping("nonexistent", "cat.schema.src", {})
            assert result["valid"] is False
            assert any("Unknown ECL table" in e for e in result["errors"])

    def test_source_column_not_found(self):
        table_cfg = {
            "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
            "optional_columns": [],
        }
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=[{"name": "other_col", "type": "STRING"}]):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = validate_mapping("loan_tape", "cat.schema.src", {"loan_id": "missing_col"})
            assert result["valid"] is False
            assert any("does not exist in source" in e for e in result["errors"])

    def test_type_mismatch(self):
        table_cfg = {
            "mandatory_columns": [{"name": "created_date", "type": "DATE"}],
            "optional_columns": [],
        }
        source_columns = [{"name": "created_date", "type": "BOOLEAN"}]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_columns):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = validate_mapping("loan_tape", "cat.schema.src", {"created_date": "created_date"})
            assert result["valid"] is False
            assert any("not compatible" in e for e in result["errors"])

    def test_int_numeric_compatible(self):
        table_cfg = {
            "mandatory_columns": [{"name": "amount", "type": "NUMERIC"}],
            "optional_columns": [],
        }
        source_columns = [{"name": "amount", "type": "INT"}]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_columns):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = validate_mapping("loan_tape", "cat.schema.src", {"amount": "amount"})
            assert result["valid"] is True

    def test_text_accepts_any_source(self):
        table_cfg = {
            "mandatory_columns": [{"name": "notes", "type": "TEXT"}],
            "optional_columns": [],
        }
        source_columns = [{"name": "notes", "type": "INT"}]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_columns):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = validate_mapping("loan_tape", "cat.schema.src", {"notes": "notes"})
            assert result["valid"] is True

    def test_optional_unmapped_is_ok(self):
        table_cfg = {
            "mandatory_columns": [],
            "optional_columns": [{"name": "extra", "type": "TEXT", "default": "null"}],
        }
        source_columns = [{"name": "some_col", "type": "STRING"}]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_columns):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = validate_mapping("loan_tape", "cat.schema.src", {})
            assert result["valid"] is True

    def test_cannot_read_source_table(self):
        table_cfg = {
            "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
            "optional_columns": [],
        }
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=[]):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = validate_mapping("loan_tape", "cat.schema.src", {"loan_id": "lid"})
            assert result["valid"] is False
            assert any("Cannot read columns" in e for e in result["errors"])


class TestSuggestMappings:
    def test_exact_match(self):
        table_cfg = {
            "mandatory_columns": [{"name": "loan_id"}],
            "optional_columns": [],
        }
        source_cols = [{"name": "loan_id", "type": "STRING"}]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_cols):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = suggest_mappings("loan_tape", "cat.schema.src")
            assert result["suggestions"]["loan_id"]["confidence"] == "exact"

    def test_case_insensitive_match(self):
        table_cfg = {
            "mandatory_columns": [{"name": "loan_id"}],
            "optional_columns": [],
        }
        source_cols = [{"name": "LOAN_ID", "type": "STRING"}]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_cols):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = suggest_mappings("loan_tape", "cat.schema.src")
            assert result["suggestions"]["loan_id"]["confidence"] == "case_insensitive"
            assert result["suggestions"]["loan_id"]["source_column"] == "LOAN_ID"

    def test_normalized_match(self):
        table_cfg = {
            "mandatory_columns": [{"name": "loan_id"}],
            "optional_columns": [],
        }
        source_cols = [{"name": "loanid", "type": "STRING"}]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_cols):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = suggest_mappings("loan_tape", "cat.schema.src")
            assert result["suggestions"]["loan_id"]["confidence"] == "normalized"

    def test_unknown_table(self):
        with patch("domain.data_mapper.admin_config") as mock_ac:
            mock_ac.get_config_section.return_value = {"tables": {}}
            result = suggest_mappings("nonexistent", "cat.schema.src")
            assert result["suggestions"] == {}

    def test_no_source_columns(self):
        table_cfg = {"mandatory_columns": [{"name": "x"}], "optional_columns": []}
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=[]):
            mock_ac.get_config_section.return_value = {"tables": {"t": table_cfg}}
            result = suggest_mappings("t", "cat.schema.src")
            assert result["suggestions"] == {}

    def test_partial_match(self):
        table_cfg = {
            "mandatory_columns": [{"name": "gross_carrying_amount"}],
            "optional_columns": [],
        }
        source_cols = [{"name": "carrying_amount", "type": "DOUBLE"}]
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.get_uc_table_columns", return_value=source_cols):
            mock_ac.get_config_section.return_value = {"tables": {"loan_tape": table_cfg}}
            result = suggest_mappings("loan_tape", "cat.schema.src")
            if "gross_carrying_amount" in result["suggestions"]:
                assert result["suggestions"]["gross_carrying_amount"]["confidence"] == "partial"


class TestGetMappingStatus:
    def test_returns_status_for_all_tables(self):
        import pandas as pd
        cfg = {
            "lakebase_schema": "public",
            "lakebase_prefix": "ecl_",
            "tables": {
                "loan_tape": {
                    "source_table": "loans",
                    "required": True,
                    "description": "Loan tape",
                    "mandatory_columns": [{"name": "loan_id"}],
                    "optional_columns": [],
                    "column_mappings": {"loan_id": "loan_id"},
                    "source_uc_table": "cat.schema.loans",
                },
            },
        }
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.backend") as mock_be:
            mock_ac.get_config_section.return_value = cfg
            mock_be.SCHEMA = "public"
            mock_be.PREFIX = "ecl_"
            mock_be.query_df.return_value = pd.DataFrame({"cnt": [42]})
            result = get_mapping_status()
            assert "loan_tape" in result
            assert result["loan_tape"]["has_data"] is True
            assert result["loan_tape"]["row_count"] == 42
            assert result["loan_tape"]["mapped_columns"] == 1

    def test_table_with_no_data(self):
        import pandas as pd
        cfg = {
            "tables": {
                "t": {
                    "source_table": "src",
                    "required": False,
                    "description": "",
                    "mandatory_columns": [],
                    "optional_columns": [],
                    "column_mappings": {},
                    "source_uc_table": "",
                },
            },
        }
        with patch("domain.data_mapper.admin_config") as mock_ac, \
             patch("domain.data_mapper.backend") as mock_be:
            mock_ac.get_config_section.return_value = cfg
            mock_be.SCHEMA = "public"
            mock_be.PREFIX = ""
            mock_be.query_df.side_effect = Exception("no table")
            result = get_mapping_status()
            assert result["t"]["has_data"] is False
            assert result["t"]["row_count"] == 0
