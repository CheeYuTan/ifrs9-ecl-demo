"""Tests for Sprint 3: Reporting & Export features.

Covers:
  - IFRS 7.35J write-off disclosure section
  - IFRS 7.35H prior-period comparatives
  - PDF export generation (pdf_export module)
  - PDF export API endpoint
  - Prior-period retrieval helper
"""
import json
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


# ── PDF Export Module Tests ─────────────────────────────────────────────────

class TestPDFExport:
    """Tests for reporting/pdf_export.py"""

    def test_generate_pdf_returns_bytes(self):
        from reporting.pdf_export import generate_report_pdf
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-001",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {},
        }
        result = generate_report_pdf(report)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pdf_starts_with_pdf_header(self):
        from reporting.pdf_export import generate_report_pdf
        report = {
            "report_type": "ecl_movement",
            "project_id": "proj-002",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {"movement": {"title": "ECL Movement", "data": [{"amount": 123.45}]}},
        }
        result = generate_report_pdf(report)
        assert result[:5] == b"%PDF-"

    def test_pdf_handles_unicode_in_titles(self):
        from reporting.pdf_export import generate_report_pdf
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-003",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {
                "s1": {"title": "IFRS 7.35F \u2014 Credit Risk", "data": [{"val": 1}]},
                "s2": {"title": "Section with \u2018quotes\u2019", "data": []},
            },
        }
        result = generate_report_pdf(report)
        assert result[:5] == b"%PDF-"

    def test_pdf_handles_empty_sections(self):
        from reporting.pdf_export import generate_report_pdf
        report = {
            "report_type": "stage_migration",
            "project_id": "proj-004",
            "report_date": "2025-06-30",
            "generated_at": "2025-06-30T10:00:00Z",
            "status": "final",
            "sections": {
                "empty": {"title": "Empty Section", "data": []},
                "error": {"title": "Error Section", "data": [], "error": "DB unavailable"},
            },
        }
        result = generate_report_pdf(report)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pdf_with_summary_and_note(self):
        from reporting.pdf_export import generate_report_pdf
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-005",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {
                "ifrs7_35j": {
                    "title": "IFRS 7.35J - Write-off Disclosure",
                    "data": [{"product_type": "mortgage", "gross_writeoff": 50000}],
                    "summary": {"total_defaults": 10, "total_gross": 100000.50},
                    "note": "Per IFRS 7.35J, amounts written off still subject to enforcement",
                },
            },
        }
        result = generate_report_pdf(report)
        assert result[:5] == b"%PDF-"

    def test_pdf_with_prior_period_flag(self):
        from reporting.pdf_export import generate_report_pdf
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-006",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {
                "ifrs7_35h": {
                    "title": "IFRS 7.35H - Loss Allowance",
                    "data": [{"stage": 1, "ecl_amount": 1000, "prior_ecl_amount": 900}],
                    "has_prior_period": True,
                },
            },
        }
        result = generate_report_pdf(report)
        assert result[:5] == b"%PDF-"

    def test_pdf_all_report_types(self):
        from reporting.pdf_export import generate_report_pdf
        for rtype in ["ifrs7_disclosure", "ecl_movement", "stage_migration",
                       "sensitivity_analysis", "concentration_risk"]:
            report = {
                "report_type": rtype,
                "project_id": "proj-all",
                "report_date": "2025-12-31",
                "generated_at": "2025-12-31T10:00:00Z",
                "status": "draft",
                "sections": {"s1": {"title": f"Section for {rtype}", "data": [{"x": 1}]}},
            }
            result = generate_report_pdf(report)
            assert result[:5] == b"%PDF-", f"Failed for report type: {rtype}"


class TestSanitize:
    """Tests for the _sanitize helper."""

    def test_sanitize_em_dash(self):
        from reporting.pdf_export import _sanitize
        assert _sanitize("test \u2014 value") == "test - value"

    def test_sanitize_smart_quotes(self):
        from reporting.pdf_export import _sanitize
        assert _sanitize("\u201chello\u201d") == '"hello"'

    def test_sanitize_non_string(self):
        from reporting.pdf_export import _sanitize
        assert _sanitize(12345) == "12345"


class TestFmt:
    """Tests for _fmt number formatter."""

    def test_fmt_large_number(self):
        from reporting.pdf_export import _fmt
        assert _fmt(1234567.89) == "1,234,567.89"

    def test_fmt_small_number(self):
        from reporting.pdf_export import _fmt
        result = _fmt(0.0012)
        assert "0.0012" in result

    def test_fmt_none(self):
        from reporting.pdf_export import _fmt
        assert _fmt(None) == "-"

    def test_fmt_zero(self):
        from reporting.pdf_export import _fmt
        assert _fmt(0) == "0.00"


# ── PDF Export Endpoint Tests ───────────────────────────────────────────────

class TestPDFExportEndpoint:
    """Tests for GET /api/reports/{report_id}/export/pdf"""

    def test_pdf_export_happy_path(self, fastapi_client, mock_db):
        fake_report = {
            "report_id": "RPT-001",
            "project_id": "proj-001",
            "report_type": "ifrs7_disclosure",
            "report_date": "2025-12-31",
            "status": "draft",
            "report_data": json.dumps({
                "report_type": "ifrs7_disclosure",
                "project_id": "proj-001",
                "report_date": "2025-12-31",
                "generated_at": "2025-12-31T10:00:00Z",
                "sections": {"s1": {"title": "Test", "data": [{"val": 1}]}},
            }),
        }
        with patch("backend.get_report", return_value=fake_report):
            resp = fastapi_client.get("/api/reports/RPT-001/export/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"

    def test_pdf_export_not_found(self, fastapi_client, mock_db):
        with patch("backend.get_report", return_value=None):
            resp = fastapi_client.get("/api/reports/RPT-999/export/pdf")
        assert resp.status_code == 404

    def test_pdf_export_with_json_report_data(self, fastapi_client, mock_db):
        """report_data stored as dict (not string) should also work."""
        fake_report = {
            "report_id": "RPT-002",
            "project_id": "proj-002",
            "report_type": "ecl_movement",
            "report_date": "2025-06-30",
            "status": "final",
            "report_data": {
                "report_type": "ecl_movement",
                "project_id": "proj-002",
                "report_date": "2025-06-30",
                "generated_at": "2025-06-30T10:00:00Z",
                "sections": {},
            },
        }
        with patch("backend.get_report", return_value=fake_report):
            resp = fastapi_client.get("/api/reports/RPT-002/export/pdf")
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"


# ── IFRS 7.35J Write-off Disclosure Tests ───────────────────────────────────

class TestIFRS735JSection:
    """Tests for the IFRS 7.35J write-off disclosure in the IFRS 7 generator."""

    def test_35j_section_included_in_ifrs7(self, fastapi_client, mock_db):
        """The generate endpoint should produce an ifrs7_35j section."""
        from reporting.reports import generate_ifrs7_disclosure
        mock_db["query_df"].return_value = pd.DataFrame({
            "product_type": ["mortgage", "consumer"],
            "default_count": [5, 3],
            "gross_writeoff": [100000.0, 50000.0],
            "recovery_amount": [10000.0, 5000.0],
            "net_writeoff": [90000.0, 45000.0],
            "recovery_rate_pct": [10.0, 10.0],
        })
        mock_db["execute"].return_value = None
        with patch("reporting.report_helpers.get_project", return_value={
            "project_id": "proj-001", "reporting_date": "2025-12-31",
        }):
            with patch("reporting.report_helpers.get_attribution", return_value=None):
                with patch("reporting.report_helpers.compute_attribution", return_value={
                    "opening_ecl": {"stage1": 0, "stage2": 0, "stage3": 0, "total": 0},
                }):
                    result = generate_ifrs7_disclosure("proj-001", "analyst")

        sections = result.get("sections", {})
        assert "ifrs7_35j" in sections
        j_section = sections["ifrs7_35j"]
        assert "Write-off" in j_section["title"]

    def test_35j_has_summary_field(self, fastapi_client, mock_db):
        """35J section should include a summary with totals."""
        summary_df = pd.DataFrame({
            "total_defaults": [8],
            "total_gross": [150000.0],
            "total_recovered": [15000.0],
            "total_net_writeoff": [135000.0],
            "contractual_outstanding": [120000.0],
        })
        detail_df = pd.DataFrame({
            "product_type": ["mortgage"],
            "default_count": [5],
            "gross_writeoff": [100000.0],
            "recovery_amount": [10000.0],
            "net_writeoff": [90000.0],
            "recovery_rate_pct": [10.0],
        })
        def mock_query(sql, *args, **kwargs):
            if "GROUP BY product_type" in sql:
                return detail_df
            elif "SUM(gross_carrying_amount_at_default)" in sql and "GROUP BY" not in sql:
                return summary_df
            return pd.DataFrame()

        with patch("reporting.report_helpers.query_df", side_effect=mock_query):
            with patch("reporting.report_helpers.execute"):
                with patch("reporting.report_helpers.get_project", return_value={
                    "project_id": "proj-002", "reporting_date": "2025-12-31",
                }):
                    with patch("reporting.report_helpers.get_attribution", return_value=None):
                        with patch("reporting.report_helpers.compute_attribution", return_value={
                            "opening_ecl": {"stage1": 0, "stage2": 0, "stage3": 0, "total": 0},
                        }):
                            from reporting.reports import generate_ifrs7_disclosure
                            result = generate_ifrs7_disclosure("proj-002", "analyst")

        j_section = result.get("sections", {}).get("ifrs7_35j", {})
        assert "ifrs7_35j" in result.get("sections", {})
        assert "summary" in j_section


# ── IFRS 7.35H Prior-Period Comparatives Tests ─────────────────────────────

class TestIFRS735HPriorPeriod:
    """Tests for prior-period comparatives in 35H section."""

    def test_35h_includes_prior_period_fields(self, fastapi_client, mock_db):
        """35H data rows should include prior_ecl_amount and ecl_movement fields."""
        from reporting.reports import generate_ifrs7_disclosure
        current_df = pd.DataFrame({
            "stage": [1, 2, 3],
            "loan_count": [100, 50, 10],
            "gross_carrying_amount": [5000000.0, 2000000.0, 500000.0],
            "ecl_amount": [100000.0, 200000.0, 300000.0],
            "avg_pd": [0.02, 0.10, 0.50],
            "avg_lgd": [0.40, 0.45, 0.55],
            "coverage_ratio": [2.0, 10.0, 60.0],
        })
        with patch("reporting.report_helpers.query_df", return_value=current_df):
            with patch("reporting.report_helpers.execute"):
                with patch("reporting.report_helpers.get_project", return_value={
                    "project_id": "proj-003", "reporting_date": "2025-12-31",
                }):
                    with patch("reporting.ifrs7_disclosure._get_prior_period_35h", return_value=[
                        {"stage": 1, "ecl_amount": 90000, "gross_carrying_amount": 4500000},
                        {"stage": 2, "ecl_amount": 180000, "gross_carrying_amount": 1800000},
                        {"stage": 3, "ecl_amount": 280000, "gross_carrying_amount": 480000},
                    ]):
                        with patch("reporting.report_helpers.get_attribution", return_value=None):
                            with patch("reporting.report_helpers.compute_attribution", return_value={
                                "opening_ecl": {"stage1": 0, "stage2": 0, "stage3": 0, "total": 0},
                            }):
                                result = generate_ifrs7_disclosure("proj-003", "analyst")

        h_section = result.get("sections", {}).get("ifrs7_35h", {})
        data = h_section.get("data", [])
        assert len(data) == 3
        row1 = data[0]
        assert "prior_ecl_amount" in row1
        assert "ecl_movement" in row1
        assert row1["prior_ecl_amount"] == 90000
        assert row1["ecl_movement"] == 10000.0

    def test_35h_no_prior_period_shows_zeros(self, fastapi_client, mock_db):
        """When no prior period exists, prior values should be 0."""
        from reporting.reports import generate_ifrs7_disclosure
        current_df = pd.DataFrame({
            "stage": [1],
            "loan_count": [100],
            "gross_carrying_amount": [5000000.0],
            "ecl_amount": [100000.0],
            "avg_pd": [0.02],
            "avg_lgd": [0.40],
            "coverage_ratio": [2.0],
        })
        with patch("reporting.report_helpers.query_df", return_value=current_df):
            with patch("reporting.report_helpers.execute"):
                with patch("reporting.report_helpers.get_project", return_value={
                    "project_id": "proj-004", "reporting_date": "2025-12-31",
                }):
                    with patch("reporting.ifrs7_disclosure._get_prior_period_35h", return_value=[]):
                        with patch("reporting.report_helpers.get_attribution", return_value=None):
                            with patch("reporting.report_helpers.compute_attribution", return_value={
                                "opening_ecl": {"stage1": 0, "stage2": 0, "stage3": 0, "total": 0},
                            }):
                                result = generate_ifrs7_disclosure("proj-004", "analyst")

        h_section = result.get("sections", {}).get("ifrs7_35h", {})
        assert h_section.get("has_prior_period") == False
        data = h_section.get("data", [])
        if data:
            assert data[0]["prior_ecl_amount"] == 0

    def test_35h_has_prior_period_flag(self, fastapi_client, mock_db):
        from reporting.reports import generate_ifrs7_disclosure
        with patch("reporting.report_helpers.query_df", return_value=pd.DataFrame({
            "stage": [1], "loan_count": [10], "gross_carrying_amount": [1000.0],
            "ecl_amount": [100.0], "avg_pd": [0.01], "avg_lgd": [0.4], "coverage_ratio": [10.0],
        })):
            with patch("reporting.report_helpers.execute"):
                with patch("reporting.report_helpers.get_project", return_value={
                    "project_id": "p", "reporting_date": "2025-12-31",
                }):
                    with patch("reporting.ifrs7_disclosure._get_prior_period_35h", return_value=[
                        {"stage": 1, "ecl_amount": 80},
                    ]):
                        with patch("reporting.report_helpers.get_attribution", return_value=None):
                            with patch("reporting.report_helpers.compute_attribution", return_value={
                                "opening_ecl": {"stage1": 0, "stage2": 0, "stage3": 0, "total": 0},
                            }):
                                result = generate_ifrs7_disclosure("p", "user")

        h_section = result.get("sections", {}).get("ifrs7_35h", {})
        assert h_section.get("has_prior_period") == True


# ── Prior Period Helper Tests ───────────────────────────────────────────────

class TestGetPriorPeriod35H:
    """Tests for _get_prior_period_35h helper function."""

    def test_returns_empty_when_no_prior(self, mock_db):
        from reporting.reports import _get_prior_period_35h
        with patch("reporting.report_helpers.query_df", return_value=pd.DataFrame()):
            result = _get_prior_period_35h("proj-new")
        assert result == []

    def test_returns_prior_data_from_report(self, mock_db):
        from reporting.reports import _get_prior_period_35h
        prior_report = {
            "sections": {
                "ifrs7_35h": {
                    "data": [
                        {"stage": 1, "ecl_amount": 50000},
                        {"stage": 2, "ecl_amount": 30000},
                    ]
                }
            }
        }
        with patch("reporting.report_helpers.query_df", return_value=pd.DataFrame({
            "report_data": [json.dumps(prior_report)],
        })):
            result = _get_prior_period_35h("proj-existing")
        assert len(result) == 2
        assert result[0]["ecl_amount"] == 50000

    def test_handles_exception_gracefully(self, mock_db):
        from reporting.reports import _get_prior_period_35h
        with patch("reporting.report_helpers.query_df", side_effect=Exception("DB error")):
            result = _get_prior_period_35h("proj-error")
        assert result == []
