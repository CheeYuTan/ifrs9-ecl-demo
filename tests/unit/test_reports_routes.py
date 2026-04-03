"""
Unit tests for Reports, Data Mapping, and Setup routes.

Covers:
  - /api/reports/* — generate, list, get, export, finalize
  - /api/data-mapping/* — catalogs, schemas, tables, columns, preview, validate, suggest, apply, status
  - /api/setup/* — status, validate-tables, seed-sample-data, complete, reset
"""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report(report_id="rpt-001", report_type="ifrs7_disclosure", project_id="proj-001"):
    return {
        "report_id": report_id,
        "project_id": project_id,
        "report_type": report_type,
        "status": "draft",
        "generated_at": "2025-12-31T10:00:00Z",
        "generated_by": "analyst",
        "sections": [{"title": "Overview", "content": {"ecl_total": 1_234_567.89}}],
    }


# ===========================================================================
# REPORTS — POST /api/reports/generate/{project_id}
# ===========================================================================

class TestGenerateReport:
    """POST /api/reports/generate/{project_id}"""

    VALID_TYPES = [
        "ifrs7_disclosure",
        "ecl_movement",
        "stage_migration",
        "sensitivity_analysis",
        "concentration_risk",
    ]

    @pytest.mark.parametrize("report_type", VALID_TYPES)
    def test_generate_each_report_type_happy_path(self, fastapi_client, mock_db, report_type):
        """All five report types return 200 when the backend succeeds."""
        backend_fn_map = {
            "ifrs7_disclosure": "backend.generate_ifrs7_disclosure",
            "ecl_movement": "backend.generate_ecl_movement_report",
            "stage_migration": "backend.generate_stage_migration_report",
            "sensitivity_analysis": "backend.generate_sensitivity_report",
            "concentration_risk": "backend.generate_concentration_report",
        }
        fake_report = _make_report(report_type=report_type)
        with patch(backend_fn_map[report_type], return_value=fake_report):
            resp = fastapi_client.post(
                "/api/reports/generate/proj-001",
                json={"report_type": report_type, "user": "analyst"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_type"] == report_type

    def test_generate_passes_project_id_and_user_to_backend(self, fastapi_client, mock_db):
        """project_id and user are forwarded to the backend generator."""
        fake_report = _make_report()
        with patch("backend.generate_ifrs7_disclosure", return_value=fake_report) as mock_gen:
            fastapi_client.post(
                "/api/reports/generate/proj-XYZ",
                json={"report_type": "ifrs7_disclosure", "user": "cfo"},
            )
        mock_gen.assert_called_once_with("proj-XYZ", "cfo")

    def test_generate_unknown_report_type_returns_400(self, fastapi_client, mock_db):
        """Unrecognised report_type returns HTTP 400."""
        resp = fastapi_client.post(
            "/api/reports/generate/proj-001",
            json={"report_type": "unknown_report", "user": "analyst"},
        )
        assert resp.status_code == 400
        assert "Unknown report type" in resp.json()["detail"]

    def test_generate_empty_report_type_returns_400(self, fastapi_client, mock_db):
        """Empty string report_type is unknown — returns 400."""
        resp = fastapi_client.post(
            "/api/reports/generate/proj-001",
            json={"report_type": "", "user": "analyst"},
        )
        assert resp.status_code == 400

    def test_generate_backend_raises_value_error_returns_400(self, fastapi_client, mock_db):
        """ValueError from the backend becomes HTTP 400 (domain validation failure)."""
        with patch("backend.generate_ifrs7_disclosure", side_effect=ValueError("No ECL data found")):
            resp = fastapi_client.post(
                "/api/reports/generate/proj-001",
                json={"report_type": "ifrs7_disclosure", "user": "analyst"},
            )
        assert resp.status_code == 400
        assert "No ECL data found" in resp.json()["detail"]

    def test_generate_backend_raises_runtime_error_returns_500(self, fastapi_client, mock_db):
        """Generic exception from backend becomes HTTP 500."""
        with patch("backend.generate_ecl_movement_report", side_effect=RuntimeError("DB timeout")):
            resp = fastapi_client.post(
                "/api/reports/generate/proj-001",
                json={"report_type": "ecl_movement", "user": "analyst"},
            )
        assert resp.status_code == 500

    def test_generate_default_user_is_system(self, fastapi_client, mock_db):
        """When user is omitted it defaults to 'system'."""
        fake_report = _make_report()
        with patch("backend.generate_ifrs7_disclosure", return_value=fake_report) as mock_gen:
            fastapi_client.post(
                "/api/reports/generate/proj-001",
                json={"report_type": "ifrs7_disclosure"},
            )
        mock_gen.assert_called_once_with("proj-001", "system")

    def test_generate_report_with_decimal_values_serialises_cleanly(self, fastapi_client, mock_db):
        """DecimalEncoder should not cause serialisation errors."""
        from decimal import Decimal
        fake_report = _make_report()
        fake_report["sections"] = [{"ecl": Decimal("1234567.89")}]
        with patch("backend.generate_ifrs7_disclosure", return_value=fake_report):
            resp = fastapi_client.post(
                "/api/reports/generate/proj-001",
                json={"report_type": "ifrs7_disclosure", "user": "analyst"},
            )
        assert resp.status_code == 200

    def test_generate_missing_report_type_field_returns_422(self, fastapi_client, mock_db):
        """Pydantic validation: omitting required field returns 422."""
        resp = fastapi_client.post(
            "/api/reports/generate/proj-001",
            json={"user": "analyst"},
        )
        assert resp.status_code == 422

    def test_generate_non_string_report_type_coerces_or_rejects(self, fastapi_client, mock_db):
        """Pydantic coerces int 42 to '42'; route returns 400 (unknown type)."""
        resp = fastapi_client.post(
            "/api/reports/generate/proj-001",
            json={"report_type": 42},
        )
        assert resp.status_code in (400, 422)


# ===========================================================================
# REPORTS — GET /api/reports
# ===========================================================================

class TestListReports:
    """GET /api/reports"""

    def test_list_all_reports_returns_200(self, fastapi_client, mock_db):
        """No filters: backend.list_reports called with (None, None)."""
        with patch("backend.list_reports", return_value=[_make_report()]) as mock_fn:
            resp = fastapi_client.get("/api/reports")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        mock_fn.assert_called_once_with(None, None)

    def test_list_reports_with_project_id_filter(self, fastapi_client, mock_db):
        """project_id query param forwarded to backend."""
        with patch("backend.list_reports", return_value=[]) as mock_fn:
            resp = fastapi_client.get("/api/reports?project_id=proj-001")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("proj-001", None)

    def test_list_reports_with_type_filter(self, fastapi_client, mock_db):
        """report_type query param forwarded to backend."""
        with patch("backend.list_reports", return_value=[]) as mock_fn:
            resp = fastapi_client.get("/api/reports?report_type=ecl_movement")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(None, "ecl_movement")

    def test_list_reports_with_both_filters(self, fastapi_client, mock_db):
        """Both filters forwarded together."""
        with patch("backend.list_reports", return_value=[_make_report()]) as mock_fn:
            resp = fastapi_client.get("/api/reports?project_id=proj-001&report_type=ifrs7_disclosure")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("proj-001", "ifrs7_disclosure")

    def test_list_reports_empty_result(self, fastapi_client, mock_db):
        """Empty list is a valid response."""
        with patch("backend.list_reports", return_value=[]):
            resp = fastapi_client.get("/api/reports")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_reports_backend_error_returns_500(self, fastapi_client, mock_db):
        """Backend exception propagates as HTTP 500."""
        with patch("backend.list_reports", side_effect=Exception("DB unavailable")):
            resp = fastapi_client.get("/api/reports")
        assert resp.status_code == 500


# ===========================================================================
# REPORTS — GET /api/reports/{report_id}
# ===========================================================================

class TestGetReport:
    """GET /api/reports/{report_id}"""

    def test_get_existing_report_returns_200(self, fastapi_client, mock_db):
        """Found report returns 200 with correct data."""
        with patch("backend.get_report", return_value=_make_report("rpt-001")):
            resp = fastapi_client.get("/api/reports/rpt-001")
        assert resp.status_code == 200
        assert resp.json()["report_id"] == "rpt-001"

    def test_get_report_not_found_returns_404(self, fastapi_client, mock_db):
        """None from backend -> 404."""
        with patch("backend.get_report", return_value=None):
            resp = fastapi_client.get("/api/reports/nonexistent")
        assert resp.status_code == 404

    def test_get_report_backend_error_returns_500(self, fastapi_client, mock_db):
        """Unexpected exception -> 500."""
        with patch("backend.get_report", side_effect=RuntimeError("connection lost")):
            resp = fastapi_client.get("/api/reports/rpt-001")
        assert resp.status_code == 500

    def test_get_report_forwarded_correct_id(self, fastapi_client, mock_db):
        """The exact report_id from the path is passed to backend.get_report."""
        with patch("backend.get_report", return_value=_make_report("rpt-42")) as mock_fn:
            fastapi_client.get("/api/reports/rpt-42")
        mock_fn.assert_called_once_with("rpt-42")


# ===========================================================================
# REPORTS — GET /api/reports/{report_id}/export
# ===========================================================================

class TestExportReport:
    """GET /api/reports/{report_id}/export"""

    def test_export_returns_csv_streaming_response(self, fastapi_client, mock_db):
        """Successful export returns text/csv with correct header."""
        rows = [
            {"stage": "1", "ecl": "100.00", "count": "50"},
            {"stage": "2", "ecl": "500.00", "count": "10"},
        ]
        with patch("backend.export_report_csv", return_value=rows):
            resp = fastapi_client.get("/api/reports/rpt-001/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "rpt-001.csv" in resp.headers["content-disposition"]

    def test_export_csv_content_contains_header_and_rows(self, fastapi_client, mock_db):
        """The streamed body includes column headers and data rows."""
        rows = [{"stage": "1", "ecl": "100.00"}]
        with patch("backend.export_report_csv", return_value=rows):
            resp = fastapi_client.get("/api/reports/rpt-001/export")
        text = resp.text
        assert "stage" in text
        assert "ecl" in text
        assert "100.00" in text

    def test_export_not_found_returns_404(self, fastapi_client, mock_db):
        """None rows -> 404."""
        with patch("backend.export_report_csv", return_value=None):
            resp = fastapi_client.get("/api/reports/rpt-001/export")
        assert resp.status_code == 404

    def test_export_empty_list_returns_404(self, fastapi_client, mock_db):
        """An empty list is also treated as not-found."""
        with patch("backend.export_report_csv", return_value=[]):
            resp = fastapi_client.get("/api/reports/rpt-001/export")
        assert resp.status_code == 404

    def test_export_backend_error_returns_500(self, fastapi_client, mock_db):
        """Backend exception -> 500."""
        with patch("backend.export_report_csv", side_effect=Exception("read error")):
            resp = fastapi_client.get("/api/reports/rpt-001/export")
        assert resp.status_code == 500


# ===========================================================================
# REPORTS — POST /api/reports/{report_id}/finalize
# ===========================================================================

class TestFinalizeReport:
    """POST /api/reports/{report_id}/finalize"""

    def test_finalize_returns_200_with_updated_report(self, fastapi_client, mock_db):
        """Finalized report returned on success."""
        finalized = {**_make_report(), "status": "final"}
        with patch("backend.finalize_report", return_value=finalized):
            resp = fastapi_client.post("/api/reports/rpt-001/finalize")
        assert resp.status_code == 200
        assert resp.json()["status"] == "final"

    def test_finalize_not_found_returns_404(self, fastapi_client, mock_db):
        """None from backend -> 404."""
        with patch("backend.finalize_report", return_value=None):
            resp = fastapi_client.post("/api/reports/rpt-999/finalize")
        assert resp.status_code == 404

    def test_finalize_backend_error_returns_500(self, fastapi_client, mock_db):
        """Unexpected exception -> 500."""
        with patch("backend.finalize_report", side_effect=RuntimeError("lock conflict")):
            resp = fastapi_client.post("/api/reports/rpt-001/finalize")
        assert resp.status_code == 500

    def test_finalize_passes_correct_id_to_backend(self, fastapi_client, mock_db):
        """report_id from path forwarded verbatim."""
        with patch("backend.finalize_report", return_value=_make_report("rpt-007")) as mock_fn:
            fastapi_client.post("/api/reports/rpt-007/finalize")
        mock_fn.assert_called_once_with("rpt-007")


# ===========================================================================
# DATA MAPPING — GET /api/data-mapping/catalogs
# ===========================================================================

class TestGetCatalogs:
    """GET /api/data-mapping/catalogs"""

    _MODULE = "routes.data_mapping"

    def test_returns_catalog_list(self, fastapi_client, mock_db):
        catalogs = [{"name": "lakemeter_catalog"}, {"name": "dev_catalog"}]
        with patch(f"{self._MODULE}.list_uc_catalogs", return_value=catalogs):
            resp = fastapi_client.get("/api/data-mapping/catalogs")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_returns_empty_list_when_no_catalogs(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.list_uc_catalogs", return_value=[]):
            resp = fastapi_client.get("/api/data-mapping/catalogs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.list_uc_catalogs", side_effect=Exception("UC unavailable")):
            resp = fastapi_client.get("/api/data-mapping/catalogs")
        assert resp.status_code == 500


# ===========================================================================
# DATA MAPPING — GET /api/data-mapping/schemas/{catalog}
# ===========================================================================

class TestGetSchemas:
    """GET /api/data-mapping/schemas/{catalog}"""

    _MODULE = "routes.data_mapping"

    def test_returns_schema_list(self, fastapi_client, mock_db):
        schemas = [{"name": "ecl_schema"}, {"name": "raw"}]
        with patch(f"{self._MODULE}.list_uc_schemas", return_value=schemas) as mock_fn:
            resp = fastapi_client.get("/api/data-mapping/schemas/lakemeter_catalog")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        mock_fn.assert_called_once_with("lakemeter_catalog")

    def test_catalog_name_forwarded(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.list_uc_schemas", return_value=[]) as mock_fn:
            fastapi_client.get("/api/data-mapping/schemas/my_catalog")
        mock_fn.assert_called_once_with("my_catalog")

    def test_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.list_uc_schemas", side_effect=Exception("auth failed")):
            resp = fastapi_client.get("/api/data-mapping/schemas/lakemeter_catalog")
        assert resp.status_code == 500


# ===========================================================================
# DATA MAPPING — GET /api/data-mapping/tables/{catalog}/{schema}
# ===========================================================================

class TestGetTables:
    """GET /api/data-mapping/tables/{catalog}/{schema}"""

    _MODULE = "routes.data_mapping"

    def test_returns_table_list(self, fastapi_client, mock_db):
        tables = [{"name": "loan_tape"}, {"name": "borrower_master"}]
        with patch(f"{self._MODULE}.list_uc_tables", return_value=tables) as mock_fn:
            resp = fastapi_client.get("/api/data-mapping/tables/cat/schema")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        mock_fn.assert_called_once_with("cat", "schema")

    def test_catalog_and_schema_forwarded_correctly(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.list_uc_tables", return_value=[]) as mock_fn:
            fastapi_client.get("/api/data-mapping/tables/my_cat/my_schema")
        mock_fn.assert_called_once_with("my_cat", "my_schema")

    def test_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.list_uc_tables", side_effect=Exception("network error")):
            resp = fastapi_client.get("/api/data-mapping/tables/cat/schema")
        assert resp.status_code == 500


# ===========================================================================
# DATA MAPPING — GET /api/data-mapping/columns/{catalog}/{schema}/{table}
# ===========================================================================

class TestGetColumns:
    """GET /api/data-mapping/columns/{catalog}/{schema}/{table}"""

    _MODULE = "routes.data_mapping"

    def test_returns_column_metadata(self, fastapi_client, mock_db):
        columns = [
            {"name": "loan_id", "data_type": "STRING"},
            {"name": "gross_carrying_amount", "data_type": "DOUBLE"},
        ]
        with patch(f"{self._MODULE}.get_uc_table_columns", return_value=columns) as mock_fn:
            resp = fastapi_client.get("/api/data-mapping/columns/cat/schema/loan_tape")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        mock_fn.assert_called_once_with("cat.schema.loan_tape")

    def test_qualified_name_assembled_from_path_parts(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.get_uc_table_columns", return_value=[]) as mock_fn:
            fastapi_client.get("/api/data-mapping/columns/a/b/c")
        mock_fn.assert_called_once_with("a.b.c")

    def test_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.get_uc_table_columns", side_effect=Exception("forbidden")):
            resp = fastapi_client.get("/api/data-mapping/columns/cat/schema/tbl")
        assert resp.status_code == 500


# ===========================================================================
# DATA MAPPING — POST /api/data-mapping/preview
# ===========================================================================

class TestPreviewTable:
    """POST /api/data-mapping/preview"""

    _MODULE = "routes.data_mapping"

    def test_preview_returns_sample_rows(self, fastapi_client, mock_db):
        preview_result = {
            "columns": ["loan_id", "product_type"],
            "rows": [["LN-001", "personal_loan"], ["LN-002", "mortgage"]],
            "total_rows": 2,
        }
        with patch(f"{self._MODULE}.preview_uc_table", return_value=preview_result):
            resp = fastapi_client.post(
                "/api/data-mapping/preview",
                json={"source_table": "cat.schema.loan_tape", "limit": 10},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "columns" in data
        assert len(data["rows"]) == 2

    def test_preview_default_limit_is_10(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.preview_uc_table", return_value={"columns": [], "rows": []}) as mock_fn:
            fastapi_client.post(
                "/api/data-mapping/preview",
                json={"source_table": "cat.schema.tbl"},
            )
        mock_fn.assert_called_once_with("cat.schema.tbl", limit=10)

    def test_preview_custom_limit_forwarded(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.preview_uc_table", return_value={"columns": [], "rows": []}) as mock_fn:
            fastapi_client.post(
                "/api/data-mapping/preview",
                json={"source_table": "cat.schema.tbl", "limit": 50},
            )
        mock_fn.assert_called_once_with("cat.schema.tbl", limit=50)

    def test_preview_error_in_result_returns_400(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.preview_uc_table", return_value={"error": "Table not found"}):
            resp = fastapi_client.post(
                "/api/data-mapping/preview",
                json={"source_table": "cat.schema.missing"},
            )
        assert resp.status_code == 400
        assert "Table not found" in resp.json()["detail"]

    def test_preview_backend_exception_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.preview_uc_table", side_effect=Exception("timeout")):
            resp = fastapi_client.post(
                "/api/data-mapping/preview",
                json={"source_table": "cat.schema.tbl"},
            )
        assert resp.status_code == 500

    def test_preview_missing_source_table_returns_422(self, fastapi_client, mock_db):
        resp = fastapi_client.post("/api/data-mapping/preview", json={"limit": 5})
        assert resp.status_code == 422


# ===========================================================================
# DATA MAPPING — POST /api/data-mapping/validate
# ===========================================================================

class TestValidateMapping:
    """POST /api/data-mapping/validate"""

    _MODULE = "routes.data_mapping"

    _VALID_BODY = {
        "table_key": "loan_tape",
        "source_table": "cat.schema.loan_tape",
        "mappings": {"loan_id": "id", "product_type": "product"},
    }

    def test_valid_mapping_returns_200(self, fastapi_client, mock_db):
        result = {"valid": True, "errors": [], "warnings": []}
        with patch(f"{self._MODULE}.validate_mapping", return_value=result):
            resp = fastapi_client.post("/api/data-mapping/validate", json=self._VALID_BODY)
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_invalid_mapping_returns_200_with_errors(self, fastapi_client, mock_db):
        result = {"valid": False, "errors": ["Missing required column: loan_id"], "warnings": []}
        with patch(f"{self._MODULE}.validate_mapping", return_value=result):
            resp = fastapi_client.post("/api/data-mapping/validate", json=self._VALID_BODY)
        assert resp.status_code == 200
        assert resp.json()["valid"] is False
        assert len(resp.json()["errors"]) == 1

    def test_validate_forwards_correct_arguments(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.validate_mapping", return_value={"valid": True}) as mock_fn:
            fastapi_client.post("/api/data-mapping/validate", json=self._VALID_BODY)
        mock_fn.assert_called_once_with(
            "loan_tape", "cat.schema.loan_tape", {"loan_id": "id", "product_type": "product"}
        )

    def test_empty_mappings_dict_is_valid_request(self, fastapi_client, mock_db):
        body = {**self._VALID_BODY, "mappings": {}}
        with patch(f"{self._MODULE}.validate_mapping", return_value={"valid": False, "errors": ["No mappings"]}):
            resp = fastapi_client.post("/api/data-mapping/validate", json=body)
        assert resp.status_code == 200

    def test_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.validate_mapping", side_effect=Exception("schema mismatch")):
            resp = fastapi_client.post("/api/data-mapping/validate", json=self._VALID_BODY)
        assert resp.status_code == 500

    def test_missing_table_key_returns_422(self, fastapi_client, mock_db):
        body = {"source_table": "cat.schema.tbl", "mappings": {}}
        resp = fastapi_client.post("/api/data-mapping/validate", json=body)
        assert resp.status_code == 422

    def test_missing_source_table_returns_422(self, fastapi_client, mock_db):
        body = {"table_key": "loan_tape", "mappings": {}}
        resp = fastapi_client.post("/api/data-mapping/validate", json=body)
        assert resp.status_code == 422


# ===========================================================================
# DATA MAPPING — POST /api/data-mapping/suggest
# ===========================================================================

class TestSuggestMappings:
    """POST /api/data-mapping/suggest"""

    _MODULE = "routes.data_mapping"

    def test_suggest_returns_suggestions(self, fastapi_client, mock_db):
        suggestions = {"loan_id": "id", "product_type": "product_category", "gross_carrying_amount": "balance"}
        with patch(f"{self._MODULE}.suggest_mappings", return_value=suggestions):
            resp = fastapi_client.post(
                "/api/data-mapping/suggest",
                json={"table_key": "loan_tape", "source_table": "cat.schema.source_loans"},
            )
        assert resp.status_code == 200
        assert resp.json() == suggestions

    def test_suggest_forwards_correct_args(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.suggest_mappings", return_value={}) as mock_fn:
            fastapi_client.post(
                "/api/data-mapping/suggest",
                json={"table_key": "borrower_master", "source_table": "cat.schema.borrowers"},
            )
        mock_fn.assert_called_once_with("borrower_master", "cat.schema.borrowers")

    def test_suggest_no_matches_returns_empty_dict(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.suggest_mappings", return_value={}):
            resp = fastapi_client.post(
                "/api/data-mapping/suggest",
                json={"table_key": "loan_tape", "source_table": "cat.schema.weird_table"},
            )
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_suggest_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.suggest_mappings", side_effect=Exception("UC timeout")):
            resp = fastapi_client.post(
                "/api/data-mapping/suggest",
                json={"table_key": "loan_tape", "source_table": "cat.schema.tbl"},
            )
        assert resp.status_code == 500

    def test_suggest_missing_table_key_returns_422(self, fastapi_client, mock_db):
        resp = fastapi_client.post(
            "/api/data-mapping/suggest",
            json={"source_table": "cat.schema.tbl"},
        )
        assert resp.status_code == 422


# ===========================================================================
# DATA MAPPING — POST /api/data-mapping/apply
# ===========================================================================

class TestApplyMapping:
    """POST /api/data-mapping/apply"""

    _MODULE = "routes.data_mapping"

    _VALID_BODY = {
        "table_key": "loan_tape",
        "source_table": "cat.schema.loan_tape",
        "mappings": {"loan_id": "id", "product_type": "product"},
        "mode": "overwrite",
    }

    def test_successful_apply_returns_200(self, fastapi_client, mock_db):
        result = {"status": "ok", "message": "Ingested 5000 rows", "rows_written": 5000}
        with patch(f"{self._MODULE}.apply_mapping", return_value=result):
            resp = fastapi_client.post("/api/data-mapping/apply", json=self._VALID_BODY)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_apply_error_status_returns_400(self, fastapi_client, mock_db):
        """If domain returns {status: error}, the route raises HTTP 400."""
        error_result = {"status": "error", "message": "Missing required column: loan_id"}
        with patch(f"{self._MODULE}.apply_mapping", return_value=error_result):
            resp = fastapi_client.post("/api/data-mapping/apply", json=self._VALID_BODY)
        assert resp.status_code == 400
        assert "Missing required column" in resp.json()["detail"]

    def test_apply_default_mode_is_overwrite(self, fastapi_client, mock_db):
        body = {k: v for k, v in self._VALID_BODY.items() if k != "mode"}
        with patch(f"{self._MODULE}.apply_mapping", return_value={"status": "ok"}) as mock_fn:
            fastapi_client.post("/api/data-mapping/apply", json=body)
        _, call_kwargs = mock_fn.call_args
        assert call_kwargs.get("mode", "overwrite") == "overwrite"

    def test_apply_append_mode_forwarded(self, fastapi_client, mock_db):
        body = {**self._VALID_BODY, "mode": "append"}
        with patch(f"{self._MODULE}.apply_mapping", return_value={"status": "ok"}) as mock_fn:
            fastapi_client.post("/api/data-mapping/apply", json=body)
        mock_fn.assert_called_once_with(
            table_key="loan_tape",
            source_table="cat.schema.loan_tape",
            mappings={"loan_id": "id", "product_type": "product"},
            mode="append",
        )

    def test_apply_backend_exception_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.apply_mapping", side_effect=Exception("write failed")):
            resp = fastapi_client.post("/api/data-mapping/apply", json=self._VALID_BODY)
        assert resp.status_code == 500

    def test_apply_missing_table_key_returns_422(self, fastapi_client, mock_db):
        body = {k: v for k, v in self._VALID_BODY.items() if k != "table_key"}
        resp = fastapi_client.post("/api/data-mapping/apply", json=body)
        assert resp.status_code == 422

    def test_apply_missing_mappings_returns_422(self, fastapi_client, mock_db):
        body = {k: v for k, v in self._VALID_BODY.items() if k != "mappings"}
        resp = fastapi_client.post("/api/data-mapping/apply", json=body)
        assert resp.status_code == 422


# ===========================================================================
# DATA MAPPING — GET /api/data-mapping/status
# ===========================================================================

class TestMappingStatus:
    """GET /api/data-mapping/status"""

    _MODULE = "routes.data_mapping"

    def test_returns_status_for_all_tables(self, fastapi_client, mock_db):
        status = {
            "loan_tape": {"mapped": True, "row_count": 50000},
            "borrower_master": {"mapped": False, "row_count": 0},
        }
        with patch(f"{self._MODULE}.get_mapping_status", return_value=status):
            resp = fastapi_client.get("/api/data-mapping/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "loan_tape" in data
        assert data["loan_tape"]["mapped"] is True

    def test_returns_empty_status_when_nothing_mapped(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.get_mapping_status", return_value={}):
            resp = fastapi_client.get("/api/data-mapping/status")
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch(f"{self._MODULE}.get_mapping_status", side_effect=Exception("query failed")):
            resp = fastapi_client.get("/api/data-mapping/status")
        assert resp.status_code == 500


# ===========================================================================
# SETUP — GET /api/setup/status
# ===========================================================================

class TestSetupStatus:
    """GET /api/setup/status"""

    def test_returns_setup_status(self, fastapi_client, mock_db):
        status = {
            "setup_complete": False,
            "completed_at": None,
            "completed_by": None,
            "tables_ok": False,
        }
        with patch("admin_config.get_setup_status", return_value=status):
            resp = fastapi_client.get("/api/setup/status")
        assert resp.status_code == 200
        assert resp.json()["setup_complete"] is False

    def test_returns_complete_status(self, fastapi_client, mock_db):
        status = {
            "setup_complete": True,
            "completed_at": "2025-01-01T00:00:00Z",
            "completed_by": "admin",
        }
        with patch("admin_config.get_setup_status", return_value=status):
            resp = fastapi_client.get("/api/setup/status")
        assert resp.status_code == 200
        assert resp.json()["setup_complete"] is True

    def test_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch("admin_config.get_setup_status", side_effect=Exception("config table missing")):
            resp = fastapi_client.get("/api/setup/status")
        assert resp.status_code == 500


# ===========================================================================
# SETUP — POST /api/setup/validate-tables
# ===========================================================================

class TestSetupValidateTables:
    """POST /api/setup/validate-tables"""

    def test_all_tables_valid_returns_200(self, fastapi_client, mock_db):
        result = {
            "valid": True,
            "tables": {
                "loan_tape": {"exists": True, "row_count": 50000},
                "borrower_master": {"exists": True, "row_count": 10000},
            },
        }
        with patch("admin_config.validate_required_tables", return_value=result):
            resp = fastapi_client.post("/api/setup/validate-tables")
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_missing_tables_returns_200_with_valid_false(self, fastapi_client, mock_db):
        result = {
            "valid": False,
            "tables": {
                "loan_tape": {"exists": False},
                "borrower_master": {"exists": True, "row_count": 1000},
            },
            "errors": ["Table loan_tape does not exist"],
        }
        with patch("admin_config.validate_required_tables", return_value=result):
            resp = fastapi_client.post("/api/setup/validate-tables")
        assert resp.status_code == 200
        assert resp.json()["valid"] is False

    def test_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch("admin_config.validate_required_tables", side_effect=Exception("DB error")):
            resp = fastapi_client.post("/api/setup/validate-tables")
        assert resp.status_code == 500


# ===========================================================================
# SETUP — POST /api/setup/seed-sample-data
# ===========================================================================

class TestSetupSeedSampleData:
    """POST /api/setup/seed-sample-data"""

    def test_seed_returns_ok_message(self, fastapi_client, mock_db):
        with patch("backend.ensure_tables", return_value=None):
            resp = fastapi_client.post("/api/setup/seed-sample-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "seeded" in data["message"].lower()

    def test_seed_calls_ensure_tables(self, fastapi_client, mock_db):
        with patch("backend.ensure_tables") as mock_fn:
            fastapi_client.post("/api/setup/seed-sample-data")
        mock_fn.assert_called_once()

    def test_seed_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch("backend.ensure_tables", side_effect=Exception("write permission denied")):
            resp = fastapi_client.post("/api/setup/seed-sample-data")
        assert resp.status_code == 500


# ===========================================================================
# SETUP — POST /api/setup/complete
# ===========================================================================

class TestSetupComplete:
    """POST /api/setup/complete"""

    def test_complete_setup_returns_200(self, fastapi_client, mock_db):
        result = {
            "setup_complete": True,
            "completed_by": "admin",
            "completed_at": "2025-12-31T10:00:00Z",
        }
        with patch("admin_config.mark_setup_complete", return_value=result):
            resp = fastapi_client.post("/api/setup/complete", json={"user": "admin"})
        assert resp.status_code == 200
        assert resp.json()["setup_complete"] is True

    def test_complete_passes_user_to_admin_config(self, fastapi_client, mock_db):
        with patch("admin_config.mark_setup_complete", return_value={"setup_complete": True}) as mock_fn:
            fastapi_client.post("/api/setup/complete", json={"user": "cfo"})
        mock_fn.assert_called_once_with("cfo")

    def test_complete_default_user_is_admin(self, fastapi_client, mock_db):
        """When user field is empty dict body, default 'admin' is used."""
        with patch("admin_config.mark_setup_complete", return_value={"setup_complete": True}) as mock_fn:
            fastapi_client.post("/api/setup/complete", json={})
        mock_fn.assert_called_once_with("admin")

    def test_complete_no_body_uses_default_user(self, fastapi_client, mock_db):
        with patch("admin_config.mark_setup_complete", return_value={"setup_complete": True}) as mock_fn:
            fastapi_client.post("/api/setup/complete")
        mock_fn.assert_called_once_with("admin")

    def test_complete_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch("admin_config.mark_setup_complete", side_effect=Exception("config locked")):
            resp = fastapi_client.post("/api/setup/complete", json={"user": "admin"})
        assert resp.status_code == 500


# ===========================================================================
# SETUP — POST /api/setup/reset
# ===========================================================================

class TestSetupReset:
    """POST /api/setup/reset"""

    def test_reset_returns_200(self, fastapi_client, mock_db):
        result = {"setup_complete": False, "reset_at": "2025-12-31T12:00:00Z"}
        with patch("admin_config.mark_setup_incomplete", return_value=result):
            resp = fastapi_client.post("/api/setup/reset")
        assert resp.status_code == 200
        assert resp.json()["setup_complete"] is False

    def test_reset_calls_mark_setup_incomplete(self, fastapi_client, mock_db):
        with patch("admin_config.mark_setup_incomplete", return_value={"setup_complete": False}) as mock_fn:
            fastapi_client.post("/api/setup/reset")
        mock_fn.assert_called_once()

    def test_reset_backend_error_returns_500(self, fastapi_client, mock_db):
        with patch("admin_config.mark_setup_incomplete", side_effect=Exception("reset blocked")):
            resp = fastapi_client.post("/api/setup/reset")
        assert resp.status_code == 500


# ===========================================================================
# PYDANTIC VALIDATION EDGE CASES
# ===========================================================================

class TestPydanticValidation:
    """Pydantic model validation boundary checks across all three route groups."""

    def test_generate_report_extra_fields_ignored_or_rejected(self, fastapi_client, mock_db):
        """Extra unknown fields should not crash the endpoint."""
        fake = _make_report()
        with patch("backend.generate_ifrs7_disclosure", return_value=fake):
            resp = fastapi_client.post(
                "/api/reports/generate/proj-001",
                json={"report_type": "ifrs7_disclosure", "user": "analyst", "unknown_field": "ignored"},
            )
        assert resp.status_code in (200, 422)

    def test_apply_mapping_non_string_values_coerced_or_rejected(self, fastapi_client, mock_db):
        """mappings dict values should be strings; int value should coerce or reject."""
        body = {
            "table_key": "loan_tape",
            "source_table": "cat.schema.tbl",
            "mappings": {"loan_id": 123},
        }
        with patch("routes.data_mapping.apply_mapping", return_value={"status": "ok"}):
            resp = fastapi_client.post("/api/data-mapping/apply", json=body)
        assert resp.status_code in (200, 422)

    def test_preview_request_limit_must_be_integer(self, fastapi_client, mock_db):
        """Non-numeric limit should fail Pydantic validation."""
        resp = fastapi_client.post(
            "/api/data-mapping/preview",
            json={"source_table": "cat.schema.tbl", "limit": "ten"},
        )
        assert resp.status_code == 422

    def test_setup_complete_user_coerces_to_string(self, fastapi_client, mock_db):
        """Numeric user value should be coerced to string by Pydantic."""
        with patch("admin_config.mark_setup_complete", return_value={"setup_complete": True}):
            resp = fastapi_client.post("/api/setup/complete", json={"user": 42})
        assert resp.status_code in (200, 422)

    def test_validate_request_mappings_must_be_dict(self, fastapi_client, mock_db):
        """If mappings is a list, Pydantic should reject with 422."""
        body = {
            "table_key": "loan_tape",
            "source_table": "cat.schema.tbl",
            "mappings": ["loan_id"],
        }
        resp = fastapi_client.post("/api/data-mapping/validate", json=body)
        assert resp.status_code == 422

    def test_suggest_request_empty_strings_are_valid(self, fastapi_client, mock_db):
        """Empty strings are technically valid Pydantic str fields."""
        with patch("routes.data_mapping.suggest_mappings", return_value={}):
            resp = fastapi_client.post(
                "/api/data-mapping/suggest",
                json={"table_key": "", "source_table": ""},
            )
        assert resp.status_code == 200

    def test_generate_report_body_entirely_absent_returns_422(self, fastapi_client, mock_db):
        """POST with no body at all fails Pydantic (report_type is required)."""
        resp = fastapi_client.post("/api/reports/generate/proj-001")
        assert resp.status_code == 422

    def test_preview_non_string_source_table_coerced_or_rejected(self, fastapi_client, mock_db):
        """source_table as a list should reject with 422."""
        resp = fastapi_client.post(
            "/api/data-mapping/preview",
            json={"source_table": ["cat", "schema", "tbl"]},
        )
        assert resp.status_code == 422
