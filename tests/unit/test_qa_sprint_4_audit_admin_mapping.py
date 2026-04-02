"""
QA Sprint 4 — Audit, Admin, Data Mapping Endpoints.

Tests routes/audit.py (5 endpoints), routes/admin.py (16 endpoints),
and routes/data_mapping.py (9 endpoints) with mocked backend/domain modules.
"""
import json
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


# ===================================================================
# AUDIT ROUTES — /api/audit/*
# ===================================================================

class TestAuditConfigChanges:
    """GET /api/audit/config/changes"""

    def test_get_config_changes(self, client):
        changes = [
            {"id": 1, "section": "model_config", "config_key": "lgd",
             "old_value": {"default": 0.4}, "new_value": {"default": 0.35},
             "changed_by": "admin", "changed_at": "2025-12-01T00:00:00"},
        ]
        with patch("routes.audit.get_config_audit_log", return_value=changes):
            resp = client.get("/api/audit/config/changes")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_config_changes_with_section(self, client):
        with patch("routes.audit.get_config_audit_log", return_value=[]) as mock:
            resp = client.get("/api/audit/config/changes?section=model_config")
        assert resp.status_code == 200
        mock.assert_called_once_with("model_config", 100)

    def test_config_changes_with_limit(self, client):
        with patch("routes.audit.get_config_audit_log", return_value=[]) as mock:
            resp = client.get("/api/audit/config/changes?limit=50")
        mock.assert_called_once_with(None, 50)

    def test_config_changes_empty(self, client):
        with patch("routes.audit.get_config_audit_log", return_value=[]):
            resp = client.get("/api/audit/config/changes")
        assert resp.status_code == 200
        assert resp.json() == []


class TestAuditConfigDiff:
    """GET /api/audit/config/diff"""

    def test_config_diff(self, client):
        diffs = [
            {"section": "model_config", "config_key": "lgd",
             "old_value": 0.4, "new_value": 0.35,
             "changed_by": "admin", "changed_at": "2025-12-01T00:00:00"},
        ]
        with patch("routes.audit.get_config_diff", return_value=diffs):
            resp = client.get("/api/audit/config/diff?start=2025-01-01&end=2025-12-31")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_config_diff_with_section(self, client):
        with patch("routes.audit.get_config_diff", return_value=[]) as mock:
            resp = client.get("/api/audit/config/diff?start=2025-01-01&section=model_config")
        mock.assert_called_once_with("2025-01-01", None, "model_config")

    def test_config_diff_start_and_end(self, client):
        with patch("routes.audit.get_config_diff", return_value=[]) as mock:
            resp = client.get("/api/audit/config/diff?start=2025-01-01&end=2025-06-30")
        mock.assert_called_once_with("2025-01-01", "2025-06-30", None)


class TestAuditProjectTrail:
    """GET /api/audit/{project_id}"""

    def test_project_audit_trail(self, client):
        entries = [
            {"id": 1, "project_id": "proj-001", "event_type": "workflow",
             "entity_type": "project", "entity_id": "proj-001", "action": "created",
             "performed_by": "user1", "detail": {}, "previous_hash": "GENESIS",
             "entry_hash": "abc123", "created_at": "2025-01-01T00:00:00"},
        ]
        verification = {"valid": True, "entries": 1, "message": "Audit chain is intact"}
        with patch("routes.audit.get_audit_trail", return_value=entries), \
             patch("routes.audit.verify_audit_chain", return_value=verification):
            resp = client.get("/api/audit/proj-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["chain_verification"]["valid"] is True

    def test_project_trail_empty(self, client):
        with patch("routes.audit.get_audit_trail", return_value=[]):
            resp = client.get("/api/audit/proj-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["chain_verification"]["valid"] is True

    def test_project_trail_pagination(self, client):
        entries = [{"id": i, "project_id": "proj-001", "event_type": "workflow",
                    "entity_type": "project", "entity_id": "proj-001", "action": f"step_{i}",
                    "performed_by": "user1", "detail": {}, "previous_hash": "x",
                    "entry_hash": f"hash_{i}", "created_at": "2025-01-01"}
                   for i in range(20)]
        verification = {"valid": True, "entries": 20}
        with patch("routes.audit.get_audit_trail", return_value=entries), \
             patch("routes.audit.verify_audit_chain", return_value=verification):
            resp = client.get("/api/audit/proj-001?offset=5&limit=3")
        data = resp.json()
        assert data["total"] == 20
        assert data["offset"] == 5
        assert data["limit"] == 3
        assert len(data["entries"]) == 3

    def test_invalid_project_id_returns_400(self, client):
        # The route regex rejects project IDs with special chars like spaces or quotes
        resp = client.get("/api/audit/proj id with spaces!")
        assert resp.status_code == 400
        assert "Invalid project_id" in resp.json()["detail"]


class TestAuditVerifyChain:
    """GET /api/audit/{project_id}/verify"""

    def test_verify_intact_chain(self, client):
        with patch("routes.audit.verify_audit_chain",
                   return_value={"valid": True, "entries": 5, "message": "Audit chain is intact"}):
            resp = client.get("/api/audit/proj-001/verify")
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_verify_broken_chain(self, client):
        with patch("routes.audit.verify_audit_chain",
                   return_value={"valid": False, "entries": 5, "broken_at_index": 3,
                                 "message": "Hash chain broken at entry 3"}):
            resp = client.get("/api/audit/proj-001/verify")
        assert resp.status_code == 200
        assert resp.json()["valid"] is False
        assert resp.json()["broken_at_index"] == 3

    def test_verify_invalid_id(self, client):
        resp = client.get("/api/audit/; DROP TABLE/verify")
        assert resp.status_code == 400


class TestAuditExport:
    """GET /api/audit/{project_id}/export"""

    def test_export_audit_package(self, client):
        package = {
            "project_id": "proj-001",
            "export_timestamp": "2025-12-31T00:00:00",
            "chain_verification": {"valid": True, "entries": 3},
            "audit_entries": [{"id": 1}, {"id": 2}, {"id": 3}],
            "config_changes": [],
        }
        with patch("routes.audit.export_audit_package", return_value=package):
            resp = client.get("/api/audit/proj-001/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "proj-001"
        assert len(data["audit_entries"]) == 3
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_export_exception(self, client):
        with patch("routes.audit.export_audit_package", side_effect=RuntimeError("fail")):
            resp = client.get("/api/audit/proj-001/export")
        assert resp.status_code == 500

    def test_export_invalid_id(self, client):
        resp = client.get("/api/audit/proj!invalid/export")
        assert resp.status_code == 400


# ===================================================================
# ADMIN ROUTES — /api/admin/*
# ===================================================================

class TestAdminGetConfig:
    """GET /api/admin/config"""

    def test_get_config(self, client):
        cfg = {"model_config": {"lgd_assumptions": {}}, "app_settings": {"scenarios": []}}
        with patch("admin_config.get_config", return_value=cfg):
            resp = client.get("/api/admin/config")
        assert resp.status_code == 200
        assert "model_config" in resp.json()

    def test_get_config_exception(self, client):
        with patch("admin_config.get_config", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/config")
        assert resp.status_code == 500


class TestAdminSaveConfig:
    """PUT /api/admin/config"""

    def test_save_config(self, client):
        with patch("admin_config.save_config", return_value={"status": "saved"}):
            resp = client.put("/api/admin/config", json={"model_config": {"lgd": 0.35}})
        assert resp.status_code == 200

    def test_save_config_exception(self, client):
        with patch("admin_config.save_config", side_effect=RuntimeError("fail")):
            resp = client.put("/api/admin/config", json={"x": 1})
        assert resp.status_code == 500


class TestAdminGetSection:
    """GET /api/admin/config/{section}"""

    def test_get_section(self, client):
        with patch("admin_config.get_config_section", return_value={"lgd": 0.35}):
            resp = client.get("/api/admin/config/model_config")
        assert resp.status_code == 200

    def test_get_section_exception(self, client):
        with patch("admin_config.get_config_section", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/config/missing_section")
        assert resp.status_code == 500


class TestAdminSaveSection:
    """PUT /api/admin/config/{section}"""

    def test_save_section(self, client):
        with patch("admin_config.save_config_section", return_value={"status": "saved"}):
            resp = client.put("/api/admin/config/model_config", json={"lgd": 0.35})
        assert resp.status_code == 200

    def test_save_section_exception(self, client):
        with patch("admin_config.save_config_section", side_effect=RuntimeError("fail")):
            resp = client.put("/api/admin/config/model_config", json={"x": 1})
        assert resp.status_code == 500


class TestAdminValidateMapping:
    """POST /api/admin/validate-mapping"""

    def test_validate_mapping(self, client):
        result = {"valid": True, "missing": [], "extra": []}
        with patch("admin_config.validate_column_mapping", return_value=result):
            resp = client.post("/api/admin/validate-mapping",
                               json={"table_key": "loans", "mappings": {"col_a": "col_b"}})
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_validate_mapping_exception(self, client):
        with patch("admin_config.validate_column_mapping", side_effect=RuntimeError("fail")):
            resp = client.post("/api/admin/validate-mapping",
                               json={"table_key": "loans", "mappings": {}})
        assert resp.status_code == 500


class TestAdminAvailableTables:
    """GET /api/admin/available-tables"""

    def test_available_tables(self, client):
        tables = ["model_ready_loans", "loan_level_ecl", "loan_ecl_weighted"]
        with patch("admin_config.get_available_tables", return_value=tables):
            resp = client.get("/api/admin/available-tables")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_tables_exception(self, client):
        with patch("admin_config.get_available_tables", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/available-tables")
        assert resp.status_code == 500


class TestAdminTableColumns:
    """GET /api/admin/table-columns/{table}"""

    def test_table_columns(self, client):
        cols = [{"name": "loan_id", "type": "TEXT"}, {"name": "gca", "type": "NUMERIC"}]
        with patch("admin_config.get_table_columns", return_value=cols):
            resp = client.get("/api/admin/table-columns/model_ready_loans")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_columns_exception(self, client):
        with patch("admin_config.get_table_columns", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/table-columns/x")
        assert resp.status_code == 500


class TestAdminTestConnection:
    """POST /api/admin/test-connection"""

    def test_connection_success(self, client):
        with patch("admin_config.test_connection", return_value={"status": "connected"}):
            resp = client.post("/api/admin/test-connection")
        assert resp.status_code == 200
        assert resp.json()["status"] == "connected"

    def test_connection_failure(self, client):
        with patch("admin_config.test_connection", side_effect=RuntimeError("timeout")):
            resp = client.post("/api/admin/test-connection")
        assert resp.status_code == 500


class TestAdminSeedDefaults:
    """POST /api/admin/seed-defaults"""

    def test_seed_defaults(self, client):
        with patch("admin_config.seed_defaults", return_value={"status": "seeded"}):
            resp = client.post("/api/admin/seed-defaults")
        assert resp.status_code == 200

    def test_seed_exception(self, client):
        with patch("admin_config.seed_defaults", side_effect=RuntimeError("fail")):
            resp = client.post("/api/admin/seed-defaults")
        assert resp.status_code == 500


class TestAdminSchemas:
    """GET /api/admin/schemas"""

    def test_schemas(self, client):
        with patch("admin_config.get_available_schemas", return_value=["public", "ecl"]):
            resp = client.get("/api/admin/schemas")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_schemas_exception(self, client):
        with patch("admin_config.get_available_schemas", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/schemas")
        assert resp.status_code == 500


class TestAdminTablePreview:
    """GET /api/admin/table-preview/{table}"""

    def test_preview(self, client):
        preview = {"columns": ["loan_id", "gca"], "rows": [["LN-001", 5000]]}
        with patch("admin_config.get_table_preview", return_value=preview):
            resp = client.get("/api/admin/table-preview/model_ready_loans")
        assert resp.status_code == 200
        assert "rows" in resp.json()

    def test_preview_with_schema_and_limit(self, client):
        with patch("admin_config.get_table_preview", return_value={}) as mock:
            resp = client.get("/api/admin/table-preview/loans?schema=ecl&limit=10")
        mock.assert_called_once_with("loans", "ecl", 10)

    def test_preview_limit_capped_at_20(self, client):
        with patch("admin_config.get_table_preview", return_value={}) as mock:
            resp = client.get("/api/admin/table-preview/loans?limit=50")
        mock.assert_called_once_with("loans", None, 20)

    def test_preview_exception(self, client):
        with patch("admin_config.get_table_preview", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/table-preview/x")
        assert resp.status_code == 500


class TestAdminValidateMappingTyped:
    """POST /api/admin/validate-mapping-typed"""

    def test_validate_typed(self, client):
        result = {"valid": True, "type_errors": []}
        with patch("admin_config.validate_column_mapping_with_types", return_value=result):
            resp = client.post("/api/admin/validate-mapping-typed",
                               json={"table_key": "loans", "mappings": {"col_a": "col_b"}})
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_validate_typed_exception(self, client):
        with patch("admin_config.validate_column_mapping_with_types", side_effect=RuntimeError("fail")):
            resp = client.post("/api/admin/validate-mapping-typed",
                               json={"table_key": "loans", "mappings": {}})
        assert resp.status_code == 500


class TestAdminSuggestMappings:
    """GET /api/admin/suggest-mappings/{table_key}"""

    def test_suggest(self, client):
        suggestions = {"loan_id": "LoanID", "gca": "GrossAmount"}
        with patch("admin_config.suggest_column_mappings", return_value=suggestions):
            resp = client.get("/api/admin/suggest-mappings/loans")
        assert resp.status_code == 200
        assert "loan_id" in resp.json()

    def test_suggest_exception(self, client):
        with patch("admin_config.suggest_column_mappings", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/suggest-mappings/loans")
        assert resp.status_code == 500


class TestAdminAutoDetect:
    """GET /api/admin/auto-detect-workspace"""

    def test_auto_detect(self, client):
        result = {"catalog": "main", "schema": "default", "tables": ["loans"]}
        with patch("admin_config.auto_detect_workspace", return_value=result):
            resp = client.get("/api/admin/auto-detect-workspace")
        assert resp.status_code == 200
        assert resp.json()["catalog"] == "main"

    def test_auto_detect_exception(self, client):
        with patch("admin_config.auto_detect_workspace", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/auto-detect-workspace")
        assert resp.status_code == 500


class TestAdminDiscoverProducts:
    """GET /api/admin/discover-products"""

    def test_discover(self, client):
        products = ["mortgage", "personal_loan", "credit_card"]
        with patch("admin_config.discover_products", return_value=products):
            resp = client.get("/api/admin/discover-products")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_discover_exception(self, client):
        with patch("admin_config.discover_products", side_effect=RuntimeError("fail")):
            resp = client.get("/api/admin/discover-products")
        assert resp.status_code == 500


class TestAdminAutoSetupLgd:
    """POST /api/admin/auto-setup-lgd"""

    def test_auto_setup(self, client):
        result = {"status": "configured", "products": 5}
        with patch("admin_config.auto_setup_lgd_from_data", return_value=result):
            resp = client.post("/api/admin/auto-setup-lgd")
        assert resp.status_code == 200
        assert resp.json()["status"] == "configured"

    def test_auto_setup_exception(self, client):
        with patch("admin_config.auto_setup_lgd_from_data", side_effect=RuntimeError("fail")):
            resp = client.post("/api/admin/auto-setup-lgd")
        assert resp.status_code == 500


# ===================================================================
# DATA MAPPING ROUTES — /api/data-mapping/*
# ===================================================================

class TestDataMappingCatalogs:
    """GET /api/data-mapping/catalogs"""

    def test_list_catalogs(self, client):
        catalogs = [{"name": "main", "comment": "Main catalog"}]
        with patch("routes.data_mapping.list_uc_catalogs", return_value=catalogs):
            resp = client.get("/api/data-mapping/catalogs")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_catalogs_exception(self, client):
        with patch("routes.data_mapping.list_uc_catalogs", side_effect=RuntimeError("fail")):
            resp = client.get("/api/data-mapping/catalogs")
        assert resp.status_code == 500


class TestDataMappingSchemas:
    """GET /api/data-mapping/schemas/{catalog}"""

    def test_list_schemas(self, client):
        schemas = [{"name": "default", "full_name": "main.default", "comment": ""}]
        with patch("routes.data_mapping.list_uc_schemas", return_value=schemas):
            resp = client.get("/api/data-mapping/schemas/main")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_schemas_exception(self, client):
        with patch("routes.data_mapping.list_uc_schemas", side_effect=RuntimeError("fail")):
            resp = client.get("/api/data-mapping/schemas/main")
        assert resp.status_code == 500


class TestDataMappingTables:
    """GET /api/data-mapping/tables/{catalog}/{schema}"""

    def test_list_tables(self, client):
        tables = [{"name": "loans", "full_name": "main.default.loans"}]
        with patch("routes.data_mapping.list_uc_tables", return_value=tables):
            resp = client.get("/api/data-mapping/tables/main/default")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_tables_exception(self, client):
        with patch("routes.data_mapping.list_uc_tables", side_effect=RuntimeError("fail")):
            resp = client.get("/api/data-mapping/tables/main/default")
        assert resp.status_code == 500


class TestDataMappingColumns:
    """GET /api/data-mapping/columns/{catalog}/{schema}/{table}"""

    def test_get_columns(self, client):
        cols = [{"name": "loan_id", "type": "STRING"}, {"name": "amount", "type": "DOUBLE"}]
        with patch("routes.data_mapping.get_uc_table_columns", return_value=cols) as mock:
            resp = client.get("/api/data-mapping/columns/main/default/loans")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        mock.assert_called_once_with("main.default.loans")

    def test_columns_exception(self, client):
        with patch("routes.data_mapping.get_uc_table_columns", side_effect=RuntimeError("fail")):
            resp = client.get("/api/data-mapping/columns/main/default/loans")
        assert resp.status_code == 500


class TestDataMappingPreview:
    """POST /api/data-mapping/preview"""

    def test_preview_success(self, client):
        result = {"columns": ["loan_id", "amount"], "rows": [["LN-001", 5000]]}
        with patch("routes.data_mapping.preview_uc_table", return_value=result):
            resp = client.post("/api/data-mapping/preview",
                               json={"source_table": "main.default.loans", "limit": 5})
        assert resp.status_code == 200
        assert "columns" in resp.json()

    def test_preview_error_result_returns_400(self, client):
        with patch("routes.data_mapping.preview_uc_table",
                   return_value={"error": "Table not found"}):
            resp = client.post("/api/data-mapping/preview",
                               json={"source_table": "missing.table"})
        assert resp.status_code == 400

    def test_preview_exception(self, client):
        with patch("routes.data_mapping.preview_uc_table", side_effect=RuntimeError("fail")):
            resp = client.post("/api/data-mapping/preview",
                               json={"source_table": "x"})
        assert resp.status_code == 500


class TestDataMappingValidate:
    """POST /api/data-mapping/validate"""

    def test_validate(self, client):
        result = {"valid": True, "errors": []}
        with patch("routes.data_mapping.validate_mapping", return_value=result):
            resp = client.post("/api/data-mapping/validate", json={
                "table_key": "loans", "source_table": "main.default.loans",
                "mappings": {"loan_id": "LoanID"},
            })
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_validate_exception(self, client):
        with patch("routes.data_mapping.validate_mapping", side_effect=RuntimeError("fail")):
            resp = client.post("/api/data-mapping/validate", json={
                "table_key": "loans", "source_table": "x", "mappings": {},
            })
        assert resp.status_code == 500


class TestDataMappingSuggest:
    """POST /api/data-mapping/suggest"""

    def test_suggest(self, client):
        suggestions = {"loan_id": "LoanID", "gca": "GrossAmount"}
        with patch("routes.data_mapping.suggest_mappings", return_value=suggestions):
            resp = client.post("/api/data-mapping/suggest",
                               json={"table_key": "loans", "source_table": "main.default.loans"})
        assert resp.status_code == 200
        assert "loan_id" in resp.json()

    def test_suggest_exception(self, client):
        with patch("routes.data_mapping.suggest_mappings", side_effect=RuntimeError("fail")):
            resp = client.post("/api/data-mapping/suggest",
                               json={"table_key": "loans", "source_table": "x"})
        assert resp.status_code == 500


class TestDataMappingApply:
    """POST /api/data-mapping/apply"""

    def test_apply_success(self, client):
        result = {"status": "success", "message": "Imported 500 rows", "rows_imported": 500}
        with patch("routes.data_mapping.apply_mapping", return_value=result):
            resp = client.post("/api/data-mapping/apply", json={
                "table_key": "loans", "source_table": "main.default.loans",
                "mappings": {"loan_id": "LoanID"}, "mode": "overwrite",
            })
        assert resp.status_code == 200
        assert resp.json()["rows_imported"] == 500

    def test_apply_error_result_returns_400(self, client):
        result = {"status": "error", "message": "Invalid mapping"}
        with patch("routes.data_mapping.apply_mapping", return_value=result):
            resp = client.post("/api/data-mapping/apply", json={
                "table_key": "loans", "source_table": "x",
                "mappings": {}, "mode": "overwrite",
            })
        assert resp.status_code == 400

    def test_apply_exception(self, client):
        with patch("routes.data_mapping.apply_mapping", side_effect=RuntimeError("fail")):
            resp = client.post("/api/data-mapping/apply", json={
                "table_key": "loans", "source_table": "x",
                "mappings": {}, "mode": "overwrite",
            })
        assert resp.status_code == 500

    def test_apply_default_mode(self, client):
        with patch("routes.data_mapping.apply_mapping",
                   return_value={"status": "success", "message": "ok"}) as mock:
            resp = client.post("/api/data-mapping/apply", json={
                "table_key": "loans", "source_table": "x",
                "mappings": {"a": "b"},
            })
        assert resp.status_code == 200
        call_kwargs = mock.call_args
        assert call_kwargs.kwargs.get("mode", call_kwargs[1].get("mode")) == "overwrite"


class TestDataMappingStatus:
    """GET /api/data-mapping/status"""

    def test_status(self, client):
        status = {"loans": {"mapped": True, "rows": 500}, "ecl": {"mapped": False, "rows": 0}}
        with patch("routes.data_mapping.get_mapping_status", return_value=status):
            resp = client.get("/api/data-mapping/status")
        assert resp.status_code == 200
        assert "loans" in resp.json()

    def test_status_exception(self, client):
        with patch("routes.data_mapping.get_mapping_status", side_effect=RuntimeError("fail")):
            resp = client.get("/api/data-mapping/status")
        assert resp.status_code == 500
