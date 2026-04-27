"""Tests for reporting/concentration_report.py."""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from reporting.concentration_report import generate_concentration_report


class TestGenerateConcentrationReport:
    def test_project_not_found(self):
        with patch("reporting.concentration_report._h") as mock_h:
            mock_h.get_project.return_value = None
            with pytest.raises(ValueError, match="not found"):
                generate_concentration_report("nonexistent")

    def test_generates_all_sections(self):
        product_df = pd.DataFrame({
            "product_type": ["Mortgage", "Auto"],
            "loan_count": [500, 200],
            "total_gca": [5_000_000.0, 1_000_000.0],
            "total_ecl": [25_000.0, 8_000.0],
            "avg_pd": [0.01, 0.03],
            "avg_lgd": [0.35, 0.45],
        })
        segment_df = pd.DataFrame({
            "segment": ["Retail", "Corporate"],
            "loan_count": [400, 300],
            "total_gca": [3_000_000.0, 3_000_000.0],
            "total_ecl": [15_000.0, 18_000.0],
            "avg_pd": [0.02, 0.015],
        })
        top_df = pd.DataFrame({
            "loan_id": ["LN-001"],
            "product_type": ["Mortgage"],
            "borrower_segment": ["Corporate"],
            "gross_carrying_amount": [500_000.0],
            "assessed_stage": [1],
            "pd_lifetime": [0.008],
            "ecl": [2_000.0],
            "days_past_due": [0],
        })
        call_count = [0]

        def mock_query(sql, *args):
            call_count[0] += 1
            if call_count[0] == 1:
                return product_df
            elif call_count[0] == 2:
                return segment_df
            else:
                return top_df

        with patch("reporting.concentration_report._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.side_effect = mock_query
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-CONC-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_concentration_report("proj-1")
            assert result["report_type"] == "concentration_risk"
            assert "by_product" in result["sections"]
            assert "by_segment" in result["sections"]
            assert "top_exposures" in result["sections"]
            by_product = result["sections"]["by_product"]["data"]
            assert len(by_product) == 2
            total_pct = sum(p["concentration_pct"] for p in by_product)
            assert abs(total_pct - 100.0) < 0.01

    def test_empty_data_graceful(self):
        with patch("reporting.concentration_report._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.side_effect = Exception("no data")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-CONC-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_concentration_report("proj-1")
            assert result["sections"]["by_product"]["data"] == []
            assert result["sections"]["by_segment"]["data"] == []
            assert result["sections"]["top_exposures"]["data"] == []

    def test_report_saved(self):
        with patch("reporting.concentration_report._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-CONC-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            generate_concentration_report("proj-1", user="admin")
            mock_h.save_report.assert_called_once()
            args = mock_h.save_report.call_args[0]
            assert args[1] == "proj-1"
            assert args[2] == "concentration_risk"
