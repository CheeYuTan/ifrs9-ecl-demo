"""Tests for reporting/report_crud.py — list, get, finalize, export."""
import json
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


_MODULE = "reporting.report_helpers"


def _empty_df():
    return pd.DataFrame()


def _reports_df():
    return pd.DataFrame([
        {"report_id": "RPT-1", "project_id": "p1", "report_type": "ecl_movement",
         "report_date": "2025-01-01", "status": "draft", "generated_by": "system", "created_at": "2025-01-01T00:00:00"},
        {"report_id": "RPT-2", "project_id": "p1", "report_type": "concentration_risk",
         "report_date": "2025-01-01", "status": "final", "generated_by": "admin", "created_at": "2025-01-02T00:00:00"},
    ])


def _single_report_df(report_data=None):
    rd = report_data or {"sections": {"s1": {"title": "Sec", "data": [{"a": 1}]}}}
    return pd.DataFrame([{
        "report_id": "RPT-1", "project_id": "p1", "report_type": "ecl_movement",
        "report_date": "2025-01-01", "status": "draft", "generated_by": "system",
        "report_data": rd, "created_at": "2025-01-01T00:00:00",
    }])


class TestListReports:
    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.query_df", return_value=_reports_df())
    def test_list_all(self, mock_qdf, mock_ensure):
        from reporting.report_crud import list_reports
        result = list_reports()
        assert len(result) == 2
        assert result[0]["report_id"] == "RPT-1"

    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.query_df", return_value=_reports_df().iloc[:1])
    def test_filter_by_project(self, mock_qdf, mock_ensure):
        from reporting.report_crud import list_reports
        result = list_reports(project_id="p1")
        assert len(result) == 1
        mock_qdf.assert_called_once()
        call_sql = mock_qdf.call_args[0][0]
        assert "project_id = %s" in call_sql

    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.query_df", return_value=_empty_df())
    def test_empty_result(self, mock_qdf, mock_ensure):
        from reporting.report_crud import list_reports
        assert list_reports() == []


class TestGetReport:
    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.query_df", return_value=_single_report_df())
    def test_found(self, mock_qdf, mock_ensure):
        from reporting.report_crud import get_report
        result = get_report("RPT-1")
        assert result is not None
        assert result["report_id"] == "RPT-1"

    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.query_df", return_value=_empty_df())
    def test_not_found(self, mock_qdf, mock_ensure):
        from reporting.report_crud import get_report
        assert get_report("RPT-999") is None

    @patch(f"{_MODULE}.ensure_report_tables")
    def test_json_string_parsed(self, mock_ensure):
        rd_str = json.dumps({"sections": {"x": {"title": "X", "data": []}}})
        df = pd.DataFrame([{
            "report_id": "RPT-1", "project_id": "p1", "report_type": "test",
            "report_date": "2025-01-01", "status": "draft", "generated_by": "system",
            "report_data": rd_str, "created_at": "2025-01-01T00:00:00",
        }])
        with patch(f"{_MODULE}.query_df", return_value=df):
            from reporting.report_crud import get_report
            result = get_report("RPT-1")
            assert isinstance(result["report_data"], dict)
            assert "sections" in result["report_data"]

    @patch(f"{_MODULE}.ensure_report_tables")
    def test_invalid_json_string_passthrough(self, mock_ensure):
        df = pd.DataFrame([{
            "report_id": "RPT-1", "project_id": "p1", "report_type": "test",
            "report_date": "2025-01-01", "status": "draft", "generated_by": "system",
            "report_data": "{broken-json", "created_at": "2025-01-01T00:00:00",
        }])
        with patch(f"{_MODULE}.query_df", return_value=df):
            from reporting.report_crud import get_report
            result = get_report("RPT-1")
            assert result["report_data"] == "{broken-json"


class TestFinalizeReport:
    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.execute")
    @patch(f"{_MODULE}.query_df", return_value=_single_report_df())
    def test_finalize(self, mock_qdf, mock_exec, mock_ensure):
        from reporting.report_crud import finalize_report
        result = finalize_report("RPT-1")
        assert result is not None
        mock_exec.assert_called_once()
        call_sql = mock_exec.call_args[0][0]
        assert "status = 'final'" in call_sql


class TestExportReportCsv:
    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.query_df")
    def test_export_with_sections(self, mock_qdf, mock_ensure):
        rd = {"sections": {
            "s1": {"title": "Section 1", "data": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]},
            "s2": {"title": "Section 2", "data": [{"a": 10}]},
        }}
        mock_qdf.return_value = _single_report_df(report_data=rd)
        from reporting.report_crud import export_report_csv
        rows = export_report_csv("RPT-1")
        assert len(rows) == 3
        assert rows[0]["section"] == "Section 1"
        assert rows[0]["x"] == 1
        assert rows[2]["section"] == "Section 2"

    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.query_df", return_value=_empty_df())
    def test_export_not_found(self, mock_qdf, mock_ensure):
        from reporting.report_crud import export_report_csv
        assert export_report_csv("RPT-999") == []

    @patch(f"{_MODULE}.ensure_report_tables")
    @patch(f"{_MODULE}.query_df")
    def test_export_no_sections(self, mock_qdf, mock_ensure):
        rd = {"some_other_key": "value"}
        mock_qdf.return_value = _single_report_df(report_data=rd)
        from reporting.report_crud import export_report_csv
        assert export_report_csv("RPT-1") == []
