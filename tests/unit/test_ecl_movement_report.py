"""Tests for reporting/ecl_movement.py — period-over-period ECL movement report."""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from reporting.ecl_movement import generate_ecl_movement_report


class TestGenerateEclMovementReport:
    def test_project_not_found(self):
        with patch("reporting.ecl_movement._h") as mock_h:
            mock_h.get_project.return_value = None
            with pytest.raises(ValueError, match="not found"):
                generate_ecl_movement_report("nonexistent")

    def test_generates_movement_data(self):
        movement_df = pd.DataFrame({
            "product_type": ["Mortgage", "Auto"],
            "stage": [1, 2],
            "gca": [5_000_000.0, 500_000.0],
            "ecl": [25_000.0, 15_000.0],
            "loan_count": [500, 100],
            "avg_pd": [0.01, 0.05],
            "avg_lgd": [0.35, 0.45],
        })
        attr = {
            "opening_ecl": {"stage1": 100, "stage2": 50, "stage3": 20, "total": 170},
            "closing_ecl": {"stage1": 110, "stage2": 55, "stage3": 18, "total": 183},
            "new_originations": {"total": 30, "stage1": 20, "stage2": 8, "stage3": 2},
            "derecognitions": {"total": -15, "stage1": -10, "stage2": -3, "stage3": -2},
            "stage_transfers": {"total": 0, "stage1": -5, "stage2": 3, "stage3": 2},
            "remeasurement": {"total": 5, "stage1": 3, "stage2": 1, "stage3": 1},
            "management_overlays": {"total": 0, "stage1": 0, "stage2": 0, "stage3": 0},
            "write_offs": {"total": -7, "stage1": 0, "stage2": -2, "stage3": -5},
        }
        with patch("reporting.ecl_movement._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.return_value = movement_df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-ECL-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.get_attribution.return_value = attr
            mock_h.compute_attribution.return_value = attr
            mock_h.log = MagicMock()
            result = generate_ecl_movement_report("proj-1")
            assert result["report_type"] == "ecl_movement"
            assert len(result["sections"]["ecl_by_product_stage"]["data"]) == 2
            waterfall = result["sections"]["waterfall"]["data"]
            assert len(waterfall) == 8
            assert waterfall[0]["component"] == "Opening Ecl"

    def test_no_attribution(self):
        with patch("reporting.ecl_movement._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-ECL-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.get_attribution.return_value = None
            mock_h.compute_attribution.return_value = None
            mock_h.log = MagicMock()
            result = generate_ecl_movement_report("proj-1")
            assert result["sections"]["waterfall"]["data"] == []

    def test_attribution_error(self):
        with patch("reporting.ecl_movement._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-ECL-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.get_attribution.side_effect = Exception("attr error")
            mock_h.log = MagicMock()
            result = generate_ecl_movement_report("proj-1")
            assert result["sections"]["waterfall"]["data"] == []

    def test_report_saved(self):
        with patch("reporting.ecl_movement._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-ECL-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.get_attribution.return_value = None
            mock_h.compute_attribution.return_value = None
            mock_h.log = MagicMock()
            generate_ecl_movement_report("proj-1", user="admin")
            mock_h.save_report.assert_called_once()
