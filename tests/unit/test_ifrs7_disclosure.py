"""Tests for reporting/ifrs7_disclosure.py — orchestrator for IFRS 7 sections."""

import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, call

from reporting.ifrs7_disclosure import (
    _get_prior_period_35h,
    generate_ifrs7_disclosure,
)


class TestGetPriorPeriod35h:
    def test_returns_prior_data(self):
        report_data = {
            "sections": {
                "ifrs7_35h": {
                    "data": [{"stage": 1, "ecl_amount": 5000.0}],
                }
            }
        }
        df = pd.DataFrame({"report_data": [json.dumps(report_data)]})
        with patch("reporting.ifrs7_disclosure._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h.REPORT_TABLE = "schema.regulatory_reports"
            result = _get_prior_period_35h("proj-1")
            assert len(result) == 1
            assert result[0]["stage"] == 1

    def test_returns_prior_data_as_dict(self):
        report_data = {
            "sections": {
                "ifrs7_35h": {
                    "data": [{"stage": 2, "ecl_amount": 8000.0}],
                }
            }
        }
        df = pd.DataFrame({"report_data": [report_data]})
        with patch("reporting.ifrs7_disclosure._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h.REPORT_TABLE = "schema.regulatory_reports"
            result = _get_prior_period_35h("proj-1")
            assert len(result) == 1

    def test_empty_result(self):
        with patch("reporting.ifrs7_disclosure._h") as mock_h:
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h.REPORT_TABLE = "schema.regulatory_reports"
            result = _get_prior_period_35h("proj-1")
            assert result == []

    def test_error_returns_empty(self):
        with patch("reporting.ifrs7_disclosure._h") as mock_h:
            mock_h.query_df.side_effect = Exception("DB error")
            mock_h.REPORT_TABLE = "schema.regulatory_reports"
            result = _get_prior_period_35h("proj-1")
            assert result == []

    def test_missing_sections_key(self):
        report_data = {"other": "data"}
        df = pd.DataFrame({"report_data": [json.dumps(report_data)]})
        with patch("reporting.ifrs7_disclosure._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h.REPORT_TABLE = "schema.regulatory_reports"
            result = _get_prior_period_35h("proj-1")
            assert result == []


class TestGenerateIfrs7Disclosure:
    def test_project_not_found(self):
        with patch("reporting.ifrs7_disclosure._h") as mock_h:
            mock_h.get_project.return_value = None
            with pytest.raises(ValueError, match="not found"):
                generate_ifrs7_disclosure("nonexistent")

    def test_generates_all_sections(self):
        with patch("reporting.ifrs7_disclosure._h") as mock_h, \
             patch("reporting.ifrs7_disclosure._build_35f") as m35f, \
             patch("reporting.ifrs7_disclosure._build_35h") as m35h, \
             patch("reporting.ifrs7_disclosure._build_35i") as m35i, \
             patch("reporting.ifrs7_disclosure._build_35j") as m35j, \
             patch("reporting.ifrs7_disclosure._build_35k") as m35k, \
             patch("reporting.ifrs7_disclosure._build_35l") as m35l, \
             patch("reporting.ifrs7_disclosure._build_35m") as m35m, \
             patch("reporting.ifrs7_disclosure._build_36") as m36, \
             patch("reporting.ifrs7_disclosure._get_prior_period_35h", return_value=[]):
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h._report_id.return_value = "RPT-IFRS-proj1-20250101"
            mock_h.save_report.return_value = None
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h.REPORT_TABLE = "schema.regulatory_reports"
            result = generate_ifrs7_disclosure("proj-1", user="admin")
            assert result["report_type"] == "ifrs7_disclosure"
            assert result["report_date"] == "2025-12-31"
            assert result["generated_by"] == "admin"
            m35f.assert_called_once()
            m35h.assert_called_once()
            m35i.assert_called_once()
            m35j.assert_called_once()
            m35k.assert_called_once()
            m35l.assert_called_once()
            m35m.assert_called_once()
            m36.assert_called_once()

    def test_uses_current_date_when_no_reporting_date(self):
        with patch("reporting.ifrs7_disclosure._h") as mock_h, \
             patch("reporting.ifrs7_disclosure._build_35f"), \
             patch("reporting.ifrs7_disclosure._build_35h"), \
             patch("reporting.ifrs7_disclosure._build_35i"), \
             patch("reporting.ifrs7_disclosure._build_35j"), \
             patch("reporting.ifrs7_disclosure._build_35k"), \
             patch("reporting.ifrs7_disclosure._build_35l"), \
             patch("reporting.ifrs7_disclosure._build_35m"), \
             patch("reporting.ifrs7_disclosure._build_36"), \
             patch("reporting.ifrs7_disclosure._get_prior_period_35h", return_value=[]):
            mock_h.get_project.return_value = {"project_id": "proj-1"}
            mock_h._report_id.return_value = "RPT-IFRS-p-1"
            mock_h.save_report.return_value = None
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h.REPORT_TABLE = "schema.regulatory_reports"
            result = generate_ifrs7_disclosure("proj-1")
            assert result["report_date"] is not None
            assert len(result["report_date"]) == 10
