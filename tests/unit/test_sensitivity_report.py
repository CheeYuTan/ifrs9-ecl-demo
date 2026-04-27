"""Tests for reporting/sensitivity_report.py — scenario sensitivity analysis."""

import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from reporting.sensitivity_report import generate_sensitivity_report


class TestGenerateSensitivityReport:
    def test_project_not_found(self):
        with patch("reporting.sensitivity_report._h") as mock_h:
            mock_h.get_project.return_value = None
            with pytest.raises(ValueError, match="not found"):
                generate_sensitivity_report("nonexistent")

    def test_generates_sensitivity_grid(self):
        stage_df = pd.DataFrame({
            "stage": [1, 2, 3],
            "ecl": [50_000.0, 30_000.0, 20_000.0],
        })
        scenario_df = pd.DataFrame({
            "scenario": ["base", "adverse"],
            "total_ecl": [100_000.0, 150_000.0],
            "weight": [0.6, 0.4],
            "weighted_contribution": [60_000.0, 60_000.0],
        })
        gca_df = pd.DataFrame({
            "total_gca": [10_000_000.0],
            "loan_count": [1000],
        })
        call_count = [0]

        def mock_query(sql, *args):
            call_count[0] += 1
            if call_count[0] == 1:
                return stage_df
            elif call_count[0] == 2:
                return scenario_df
            else:
                return gca_df

        with patch("reporting.sensitivity_report._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31", "scenario_weights": {}}
            mock_h.query_df.side_effect = mock_query
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-SENS-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_sensitivity_report("proj-1")
            assert result["report_type"] == "sensitivity_analysis"
            grid = result["sections"]["sensitivity_grid"]["data"]
            assert len(grid) == 25  # 5x5 grid
            center = next(g for g in grid if g["pd_shift_pct"] == 0 and g["lgd_shift_pct"] == 0)
            assert center["change_from_base"] == 0
            assert center["change_pct"] == 0

    def test_sensitivity_grid_symmetry(self):
        stage_df = pd.DataFrame({"stage": [1], "ecl": [100_000.0]})
        with patch("reporting.sensitivity_report._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31", "scenario_weights": {}}
            mock_h.query_df.side_effect = [stage_df, pd.DataFrame(), pd.DataFrame()]
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-SENS-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_sensitivity_report("proj-1")
            grid = result["sections"]["sensitivity_grid"]["data"]
            pd_plus_20 = next(g for g in grid if g["pd_shift_pct"] == 20 and g["lgd_shift_pct"] == 0)
            pd_minus_20 = next(g for g in grid if g["pd_shift_pct"] == -20 and g["lgd_shift_pct"] == 0)
            assert pd_plus_20["change_pct"] == -pd_minus_20["change_pct"]

    def test_zero_base_ecl(self):
        stage_df = pd.DataFrame(columns=["stage", "ecl"])
        with patch("reporting.sensitivity_report._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31", "scenario_weights": {}}
            mock_h.query_df.side_effect = [stage_df, pd.DataFrame(), pd.DataFrame()]
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-SENS-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_sensitivity_report("proj-1")
            grid = result["sections"]["sensitivity_grid"]["data"]
            for entry in grid:
                assert entry["change_pct"] == 0

    def test_scenario_weights_from_string(self):
        stage_df = pd.DataFrame({"stage": [1], "ecl": [100_000.0]})
        with patch("reporting.sensitivity_report._h") as mock_h:
            mock_h.get_project.return_value = {
                "reporting_date": "2025-12-31",
                "scenario_weights": json.dumps({"base": 0.6, "adverse": 0.4}),
            }
            mock_h.query_df.side_effect = [stage_df, pd.DataFrame(), pd.DataFrame()]
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-SENS-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_sensitivity_report("proj-1")
            assert result["report_type"] == "sensitivity_analysis"

    def test_invalid_json_weights(self):
        stage_df = pd.DataFrame({"stage": [1], "ecl": [100_000.0]})
        with patch("reporting.sensitivity_report._h") as mock_h:
            mock_h.get_project.return_value = {
                "reporting_date": "2025-12-31",
                "scenario_weights": "not-valid-json",
            }
            mock_h.query_df.side_effect = [stage_df, pd.DataFrame(), pd.DataFrame()]
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-SENS-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_sensitivity_report("proj-1")
            assert result is not None
