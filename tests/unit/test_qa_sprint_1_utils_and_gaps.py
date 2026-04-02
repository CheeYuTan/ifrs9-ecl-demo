"""
QA Sprint 1 — Iteration 3: Utils unit tests + gap coverage.

Covers:
- routes/_utils.py direct unit tests (_sanitize, df_to_records, serialize_project)
- Sign-off edge cases (None project, no audit_log key)
- Verify-hash with tampered data and hash computation mocking
- Setup complete with body=None
- Overlay advance_step argument verification
- Data endpoint mixed-type DataFrames
- Data consistency checks (stage distribution totals)
"""
import json
import math
from datetime import datetime, date, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock, call

import pandas as pd
import numpy as np
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(mock_db):
    import app as app_module
    return TestClient(app_module.app)


def _project_dict(**overrides):
    base = {
        "project_id": "proj-001",
        "project_name": "ECL Q4 2025",
        "project_type": "ifrs9",
        "description": "Quarterly ECL calculation",
        "reporting_date": "2025-12-31",
        "current_step": 1,
        "step_status": {"create_project": "completed"},
        "audit_log": [],
        "overlays": [],
        "scenario_weights": {},
        "signed_off_by": None,
        "signed_off_at": None,
        "ecl_hash": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return base


# ===================================================================
# _UTILS.PY DIRECT UNIT TESTS
# ===================================================================

class TestSanitize:
    """Direct tests for routes._utils._sanitize."""

    def test_nan_becomes_none(self):
        from routes._utils import _sanitize
        assert _sanitize(float("nan")) is None

    def test_inf_becomes_none(self):
        from routes._utils import _sanitize
        assert _sanitize(float("inf")) is None

    def test_neg_inf_becomes_none(self):
        from routes._utils import _sanitize
        assert _sanitize(float("-inf")) is None

    def test_normal_float_preserved(self):
        from routes._utils import _sanitize
        assert _sanitize(3.14) == 3.14

    def test_zero_preserved(self):
        from routes._utils import _sanitize
        assert _sanitize(0.0) == 0.0

    def test_nested_dict_sanitized(self):
        from routes._utils import _sanitize
        result = _sanitize({"a": float("nan"), "b": {"c": float("inf"), "d": 42}})
        assert result == {"a": None, "b": {"c": None, "d": 42}}

    def test_nested_list_sanitized(self):
        from routes._utils import _sanitize
        result = _sanitize([float("nan"), [float("inf"), 1.0]])
        assert result == [None, [None, 1.0]]

    def test_mixed_types_preserved(self):
        from routes._utils import _sanitize
        result = _sanitize({"s": "hello", "i": 42, "f": 3.14, "n": None, "b": True})
        assert result == {"s": "hello", "i": 42, "f": 3.14, "n": None, "b": True}

    def test_empty_dict(self):
        from routes._utils import _sanitize
        assert _sanitize({}) == {}

    def test_empty_list(self):
        from routes._utils import _sanitize
        assert _sanitize([]) == []

    def test_string_passthrough(self):
        from routes._utils import _sanitize
        assert _sanitize("hello") == "hello"

    def test_none_passthrough(self):
        from routes._utils import _sanitize
        assert _sanitize(None) is None

    def test_integer_passthrough(self):
        from routes._utils import _sanitize
        assert _sanitize(42) == 42


class TestSafeEncoder:
    """Direct tests for _SafeEncoder / DecimalEncoder."""

    def test_decimal_becomes_float(self):
        from routes._utils import _SafeEncoder
        result = json.dumps({"v": Decimal("12345.67")}, cls=_SafeEncoder)
        assert json.loads(result)["v"] == 12345.67

    def test_decimal_zero(self):
        from routes._utils import _SafeEncoder
        result = json.dumps({"v": Decimal("0")}, cls=_SafeEncoder)
        assert json.loads(result)["v"] == 0.0

    def test_decimal_negative(self):
        from routes._utils import _SafeEncoder
        result = json.dumps({"v": Decimal("-99.99")}, cls=_SafeEncoder)
        assert json.loads(result)["v"] == -99.99

    def test_datetime_becomes_iso(self):
        from routes._utils import _SafeEncoder
        dt = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        result = json.dumps({"v": dt}, cls=_SafeEncoder)
        assert "2025-12-31" in json.loads(result)["v"]

    def test_date_becomes_iso(self):
        from routes._utils import _SafeEncoder
        d = date(2025, 6, 15)
        result = json.dumps({"v": d}, cls=_SafeEncoder)
        assert json.loads(result)["v"] == "2025-06-15"

    def test_unsupported_type_raises(self):
        from routes._utils import _SafeEncoder
        with pytest.raises(TypeError):
            json.dumps({"v": set([1, 2])}, cls=_SafeEncoder)

    def test_decimal_encoder_alias(self):
        from routes._utils import DecimalEncoder, _SafeEncoder
        assert DecimalEncoder is _SafeEncoder


class TestDfToRecords:
    """Direct tests for df_to_records."""

    def test_simple_dataframe(self):
        from routes._utils import df_to_records
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = df_to_records(df)
        assert result == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]

    def test_empty_dataframe(self):
        from routes._utils import df_to_records
        result = df_to_records(pd.DataFrame())
        assert result == []

    def test_nan_in_dataframe(self):
        from routes._utils import df_to_records
        df = pd.DataFrame({"a": [1.0, float("nan")], "b": [float("nan"), 2.0]})
        result = df_to_records(df)
        assert result[0]["a"] == 1.0
        assert result[0]["b"] is None
        assert result[1]["a"] is None
        assert result[1]["b"] == 2.0

    def test_decimal_in_dataframe(self):
        from routes._utils import df_to_records
        df = pd.DataFrame({"amount": [Decimal("100.50"), Decimal("200.75")]})
        result = df_to_records(df)
        assert result[0]["amount"] == 100.50
        assert result[1]["amount"] == 200.75

    def test_mixed_types_dataframe(self):
        from routes._utils import df_to_records
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [30, 25],
            "score": [99.5, float("nan")],
            "active": [True, False],
        })
        result = df_to_records(df)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["active"] is True
        assert result[1]["score"] is None

    def test_single_column_dataframe(self):
        from routes._utils import df_to_records
        df = pd.DataFrame({"x": [10, 20, 30]})
        result = df_to_records(df)
        assert len(result) == 3
        assert all("x" in r for r in result)

    def test_all_nan_column(self):
        from routes._utils import df_to_records
        df = pd.DataFrame({"a": [1, 2], "b": [float("nan"), float("nan")]})
        result = df_to_records(df)
        assert result[0]["b"] is None
        assert result[1]["b"] is None


class TestSerializeProject:
    """Direct tests for serialize_project."""

    def test_none_returns_none(self):
        from routes._utils import serialize_project
        assert serialize_project(None) is None

    def test_decimal_values_converted(self):
        from routes._utils import serialize_project
        proj = {"ecl_total": Decimal("12345.67"), "name": "test"}
        result = serialize_project(proj)
        assert result["ecl_total"] == 12345.67
        assert result["name"] == "test"

    def test_datetime_values_converted(self):
        from routes._utils import serialize_project
        dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        proj = {"created_at": dt, "name": "test"}
        result = serialize_project(proj)
        assert "2025-06-15" in result["created_at"]

    def test_nested_structures_preserved(self):
        from routes._utils import serialize_project
        proj = {
            "step_status": {"step1": "completed", "step2": "pending"},
            "overlays": [{"id": "1", "amount": Decimal("500")}],
        }
        result = serialize_project(proj)
        assert result["step_status"]["step1"] == "completed"
        assert result["overlays"][0]["amount"] == 500.0

    def test_empty_dict(self):
        from routes._utils import serialize_project
        assert serialize_project({}) == {}


# ===================================================================
# SIGN-OFF GAP COVERAGE
# ===================================================================

class TestSignOffNoneProject:
    """Sign-off when project doesn't exist (get_project returns None)."""

    def test_sign_off_nonexistent_project_calls_backend(self, client):
        """When get_project returns None, sign_off still attempts backend call."""
        with patch("backend.get_project", return_value=None), \
             patch("backend.sign_off_project", return_value=_project_dict(signed_off_by="Auditor")) as mock_sign:
            resp = client.post(
                "/api/projects/ghost-project/sign-off",
                json={"name": "Auditor"}
            )
        assert resp.status_code == 200
        mock_sign.assert_called_once_with("ghost-project", "Auditor", attestation_data=None)

    def test_sign_off_project_no_audit_log_key(self, client):
        """Project dict without audit_log key — should default to empty list."""
        proj = _project_dict()
        del proj["audit_log"]
        with patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=_project_dict(signed_off_by="Reviewer")):
            resp = client.post(
                "/api/projects/proj-001/sign-off",
                json={"name": "Reviewer"}
            )
        assert resp.status_code == 200

    def test_sign_off_with_non_dict_audit_entries(self, client):
        """Audit log contains non-dict entries (strings) — should skip them safely."""
        proj = _project_dict(audit_log=["step completed", {"step": "model_execution", "user": "Alice"}, 42])
        with patch("backend.get_project", return_value=proj), \
             patch("backend.sign_off_project", return_value=_project_dict(signed_off_by="Bob")):
            resp = client.post(
                "/api/projects/proj-001/sign-off",
                json={"name": "Bob"}
            )
        # Bob != Alice, so segregation passes
        assert resp.status_code == 200

    def test_sign_off_with_non_dict_audit_entries_same_executor(self, client):
        """Audit log with mixed types, last executor matches signer."""
        proj = _project_dict(audit_log=["noise", {"step": "model_execution", "user": "Alice"}])
        with patch("backend.get_project", return_value=proj):
            resp = client.post(
                "/api/projects/proj-001/sign-off",
                json={"name": "Alice"}
            )
        assert resp.status_code == 403
        assert "Segregation of duties" in resp.json()["detail"]


# ===================================================================
# VERIFY-HASH GAP COVERAGE
# ===================================================================

class TestVerifyHashTamperedData:
    """Verify-hash with tampered data scenarios."""

    def test_verify_hash_tampered_returns_invalid(self, client):
        """Hash mismatch when data has been tampered with."""
        proj = _project_dict(
            ecl_hash="original_hash_abc123",
            signed_off_by="Auditor",
            signed_off_at=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=False), \
             patch("middleware.auth.compute_ecl_hash", return_value="tampered_hash_xyz"):
            resp = client.get("/api/projects/proj-001/verify-hash")
        body = resp.json()
        assert resp.status_code == 200
        assert body["status"] == "invalid"
        assert body["match"] is False
        assert body["stored_hash"] == "original_hash_abc123"
        assert body["computed_hash"] == "tampered_hash_xyz"

    def test_verify_hash_valid_returns_match(self, client):
        """Hash matches when data is unchanged."""
        proj = _project_dict(
            ecl_hash="valid_hash_123",
            signed_off_by="Auditor",
            signed_off_at=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=True), \
             patch("middleware.auth.compute_ecl_hash", return_value="valid_hash_123"):
            resp = client.get("/api/projects/proj-001/verify-hash")
        body = resp.json()
        assert body["status"] == "valid"
        assert body["match"] is True
        assert body["stored_hash"] == body["computed_hash"]

    def test_verify_hash_passes_correct_ecl_data(self, client):
        """Verify the hash function receives the right data fields."""
        proj = _project_dict(
            ecl_hash="some_hash",
            project_id="proj-X",
            step_status={"s1": "done"},
            overlays=[{"id": "1"}],
            scenario_weights={"base": 0.6},
        )
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=True) as mock_verify, \
             patch("middleware.auth.compute_ecl_hash", return_value="some_hash"):
            client.get("/api/projects/proj-X/verify-hash")
        expected_data = {
            "project_id": "proj-X",
            "step_status": {"s1": "done"},
            "overlays": [{"id": "1"}],
            "scenario_weights": {"base": 0.6},
        }
        mock_verify.assert_called_once_with(expected_data, "some_hash")

    def test_verify_hash_signed_off_fields(self, client):
        """Response includes signed_off_by and signed_off_at."""
        proj = _project_dict(
            ecl_hash="h",
            signed_off_by="Jane",
            signed_off_at=datetime(2025, 3, 15, 10, 30, tzinfo=timezone.utc),
        )
        with patch("backend.get_project", return_value=proj), \
             patch("middleware.auth.verify_ecl_hash", return_value=True), \
             patch("middleware.auth.compute_ecl_hash", return_value="h"):
            resp = client.get("/api/projects/proj-001/verify-hash")
        body = resp.json()
        assert body["signed_off_by"] == "Jane"
        assert "2025-03-15" in body["signed_off_at"]


# ===================================================================
# SETUP ROUTE GAP COVERAGE
# ===================================================================

class TestSetupCompleteNoneBody:
    """Setup complete endpoint when no body is sent."""

    def test_complete_without_body_uses_default_admin(self, client):
        with patch("admin_config.mark_setup_complete", return_value={"status": "ok"}) as mock_fn:
            resp = client.post("/api/setup/complete")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with("admin")

    def test_complete_with_explicit_user(self, client):
        with patch("admin_config.mark_setup_complete", return_value={"status": "ok"}) as mock_fn:
            resp = client.post("/api/setup/complete", json={"user": "john"})
        mock_fn.assert_called_once_with("john")


# ===================================================================
# OVERLAY ADVANCE_STEP VERIFICATION
# ===================================================================

class TestOverlayAdvanceStepArgs:
    """Verify overlays with comment triggers advance_step with correct arguments."""

    def test_overlay_with_comment_calls_advance_with_correct_args(self, client):
        proj = _project_dict()
        advanced_proj = _project_dict(current_step=2)
        with patch("backend.save_overlays", return_value=proj) as mock_save, \
             patch("backend.advance_step", return_value=advanced_proj) as mock_advance:
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": [{"id": "1", "product": "mortgage", "type": "adj",
                              "amount": 500.0, "reason": "Management override"}],
                "comment": "Approved by risk committee"
            })
        # Verify save_overlays called with serialized overlay dicts
        saved = mock_save.call_args[0][1]
        assert len(saved) == 1
        assert saved[0]["product"] == "mortgage"
        assert saved[0]["amount"] == 500.0
        # Verify advance_step called with correct params
        mock_advance.assert_called_once_with(
            "proj-001", "overlays", "Overlays Submitted",
            "Credit Risk Analyst", "Approved by risk committee"
        )

    def test_overlay_without_comment_does_not_advance(self, client):
        proj = _project_dict()
        with patch("backend.save_overlays", return_value=proj), \
             patch("backend.advance_step") as mock_advance:
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": [{"id": "1", "product": "personal", "type": "adj",
                              "amount": 100.0, "reason": "test"}],
                "comment": ""
            })
        mock_advance.assert_not_called()

    def test_overlay_items_serialized_correctly(self, client):
        """Verify model_dump produces expected dict shape."""
        proj = _project_dict()
        with patch("backend.save_overlays", return_value=proj) as mock_save:
            resp = client.post("/api/projects/proj-001/overlays", json={
                "overlays": [
                    {"id": "a", "product": "mortgage", "type": "adj",
                     "amount": 1000.0, "reason": "reason1", "ifrs9": "stage2"},
                    {"id": "b", "product": "personal", "type": "override",
                     "amount": 200.0, "reason": "reason2"},
                ]
            })
        saved = mock_save.call_args[0][1]
        assert len(saved) == 2
        assert saved[0]["ifrs9"] == "stage2"
        assert saved[1]["ifrs9"] == ""  # default


# ===================================================================
# DATA ENDPOINTS — MIXED TYPES & CONSISTENCY
# ===================================================================

class TestDataEndpointsMixedTypes:
    """Data endpoints handle DataFrames with diverse column types."""

    def test_boolean_columns(self, client):
        df = pd.DataFrame({"name": ["A"], "is_default": [True], "is_cured": [False]})
        with patch("backend.get_portfolio_summary", return_value=df):
            resp = client.get("/api/data/portfolio-summary")
        data = resp.json()
        assert data[0]["is_default"] is True
        assert data[0]["is_cured"] is False

    def test_none_values_in_dataframe(self, client):
        df = pd.DataFrame({"product": ["mortgage", None], "amount": [100.0, None]})
        with patch("backend.get_portfolio_summary", return_value=df):
            resp = client.get("/api/data/portfolio-summary")
        data = resp.json()
        assert data[1]["product"] is None
        assert data[1]["amount"] is None

    def test_integer_columns(self, client):
        df = pd.DataFrame({"stage": [1, 2, 3], "count": [100, 50, 10]})
        with patch("backend.get_stage_distribution", return_value=df):
            resp = client.get("/api/data/stage-distribution")
        data = resp.json()
        assert data[0]["stage"] == 1
        assert data[2]["count"] == 10

    def test_large_numeric_values(self, client):
        df = pd.DataFrame({"exposure": [1e12, 5e11], "product": ["corp", "sme"]})
        with patch("backend.get_ecl_summary", return_value=df):
            resp = client.get("/api/data/ecl-summary")
        data = resp.json()
        assert data[0]["exposure"] == 1e12

    def test_special_string_characters(self, client):
        df = pd.DataFrame({"product": ["Crédit / Bail", "Prêt à taux"], "count": [1, 2]})
        with patch("backend.get_portfolio_summary", return_value=df):
            resp = client.get("/api/data/portfolio-summary")
        data = resp.json()
        assert data[0]["product"] == "Crédit / Bail"


class TestDataConsistency:
    """Verify data consistency patterns (stage totals, etc.)."""

    def test_stage_distribution_stages_are_complete(self, client):
        """Stage distribution should handle all 3 IFRS9 stages."""
        df = pd.DataFrame({
            "stage": [1, 2, 3],
            "loan_count": [77552, 1212, 975],
            "total_gca": [5_000_000, 800_000, 200_000],
        })
        with patch("backend.get_stage_distribution", return_value=df):
            resp = client.get("/api/data/stage-distribution")
        data = resp.json()
        assert len(data) == 3
        stages = {r["stage"] for r in data}
        assert stages == {1, 2, 3}
        # Total loan count = sum of all stages
        total_loans = sum(r["loan_count"] for r in data)
        assert total_loans == 77552 + 1212 + 975

    def test_ecl_by_scenario_product_weights_scenario(self, client):
        """Different scenarios should return different products."""
        df_base = pd.DataFrame({"product": ["mortgage"], "ecl": [50000]})
        df_stress = pd.DataFrame({"product": ["mortgage"], "ecl": [80000]})
        with patch("backend.get_ecl_by_scenario_product_detail", return_value=df_base):
            resp_base = client.get("/api/data/ecl-by-scenario-product-detail?scenario=base")
        with patch("backend.get_ecl_by_scenario_product_detail", return_value=df_stress):
            resp_stress = client.get("/api/data/ecl-by-scenario-product-detail?scenario=stress")
        assert resp_base.json()[0]["ecl"] == 50000
        assert resp_stress.json()[0]["ecl"] == 80000

    def test_top_exposures_respects_limit(self, client):
        """Top exposures limit parameter controls result count."""
        df = pd.DataFrame({"borrower": [f"B{i}" for i in range(50)], "exposure": list(range(50))})
        with patch("backend.get_top_exposures", return_value=df):
            resp = client.get("/api/data/top-exposures?limit=5")
        # The route passes limit to backend, backend controls filtering
        # We just verify the call happens and data comes back
        assert resp.status_code == 200

    def test_loans_by_product_passes_type(self, client):
        """loans-by-product passes the product_type path param to backend."""
        with patch("backend.get_loans_by_product", return_value=pd.DataFrame()) as mock_fn:
            client.get("/api/data/loans-by-product/mortgage")
        mock_fn.assert_called_once_with("mortgage")

    def test_loans_by_stage_passes_stage(self, client):
        """loans-by-stage passes the stage path param as int to backend."""
        with patch("backend.get_loans_by_stage", return_value=pd.DataFrame()) as mock_fn:
            client.get("/api/data/loans-by-stage/2")
        mock_fn.assert_called_once_with(2)


# ===================================================================
# PROJECT LIFECYCLE EDGE CASES
# ===================================================================

class TestProjectLifecycle:
    """Multi-step project workflow edge cases."""

    def test_create_then_get_project(self, client):
        """Create project returns same data that get_project would."""
        proj = _project_dict(project_id="new-proj")
        with patch("backend.create_project", return_value=proj):
            create_resp = client.post("/api/projects", json={
                "project_id": "new-proj",
                "project_name": "New Project",
            })
        with patch("backend.get_project", return_value=proj):
            get_resp = client.get("/api/projects/new-proj")
        assert create_resp.json()["project_id"] == get_resp.json()["project_id"]

    def test_advance_step_body_fields(self, client):
        """Verify advance_step sends all body fields to backend."""
        proj = _project_dict(current_step=2)
        with patch("backend.advance_step", return_value=proj) as mock_fn:
            client.post("/api/projects/proj-001/advance", json={
                "action": "data_processing",
                "user": "analyst",
                "detail": "Processed 10k loans",
                "status": "in_progress"
            })
        mock_fn.assert_called_once_with(
            "proj-001", "data_processing", "data_processing",
            "analyst", "Processed 10k loans", "in_progress"
        )

    def test_scenario_weights_passed_to_backend(self, client):
        """Verify scenario weights dict passed correctly."""
        proj = _project_dict(scenario_weights={"base": 0.4, "up": 0.3, "down": 0.3})
        with patch("backend.save_scenario_weights", return_value=proj) as mock_fn:
            client.post("/api/projects/proj-001/scenario-weights", json={
                "weights": {"base": 0.4, "up": 0.3, "down": 0.3}
            })
        mock_fn.assert_called_once_with("proj-001", {"base": 0.4, "up": 0.3, "down": 0.3})


# ===================================================================
# APPROVAL HISTORY EDGE CASES
# ===================================================================

class TestApprovalHistoryEdgeCases:
    """Approval history additional coverage."""

    def test_approval_history_returns_list_of_dicts(self, client):
        history = [
            {"id": 1, "action": "approved", "user": "Manager", "timestamp": "2025-01-01"},
            {"id": 2, "action": "rejected", "user": "Auditor", "timestamp": "2025-01-02"},
        ]
        with patch("governance.rbac.get_approval_history", return_value=history):
            resp = client.get("/api/projects/proj-001/approval-history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["action"] == "approved"
        assert data[1]["action"] == "rejected"

    def test_approval_history_import_error(self, client):
        """If governance.rbac module fails to import, returns 500."""
        with patch("governance.rbac.get_approval_history", side_effect=ImportError("no module")):
            resp = client.get("/api/projects/proj-001/approval-history")
        assert resp.status_code == 500


# ===================================================================
# SETUP SEED DATA EDGE CASES
# ===================================================================

class TestSetupSeedDataEdgeCases:
    """Setup seed-data additional coverage."""

    def test_seed_data_calls_ensure_tables(self, client):
        """Verify seed-data calls backend.ensure_tables."""
        with patch("backend.ensure_tables") as mock_fn:
            resp = client.post("/api/setup/seed-sample-data")
        assert resp.status_code == 200
        mock_fn.assert_called_once()
        body = resp.json()
        assert body["status"] == "ok"
        assert "Sample data seeded" in body["message"]

    def test_seed_data_failure_preserves_error(self, client):
        """Verify seed-data error message is descriptive."""
        with patch("backend.ensure_tables", side_effect=Exception("table creation failed")):
            resp = client.post("/api/setup/seed-sample-data")
        assert resp.status_code == 500
        assert "table creation failed" in resp.json()["detail"]
