"""Tests for reporting/stage_migration.py — stage transition analysis."""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from reporting.stage_migration import generate_stage_migration_report


class TestGenerateStageMigrationReport:
    def test_project_not_found(self):
        with patch("reporting.stage_migration._h") as mock_h:
            mock_h.get_project.return_value = None
            with pytest.raises(ValueError, match="not found"):
                generate_stage_migration_report("nonexistent")

    def test_generates_migration_matrix(self):
        matrix_df = pd.DataFrame({
            "original_stage": [1, 1, 2, 2, 3],
            "assessed_stage": [1, 2, 1, 2, 3],
            "loan_count": [800, 100, 50, 300, 150],
            "total_gca": [8_000_000.0, 1_000_000.0, 500_000.0, 3_000_000.0, 1_500_000.0],
            "total_ecl": [40_000.0, 10_000.0, 5_000.0, 30_000.0, 60_000.0],
        })
        rates_df = pd.DataFrame({
            "original_stage": [1, 2, 3],
            "total_from_stage": [900, 350, 150],
            "to_stage1": [800, 50, 0],
            "to_stage2": [100, 300, 0],
            "to_stage3": [0, 0, 150],
        })
        call_count = [0]

        def mock_query(sql, *args):
            call_count[0] += 1
            if call_count[0] == 1:
                return matrix_df
            else:
                return rates_df

        with patch("reporting.stage_migration._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.side_effect = mock_query
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-STAG-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_stage_migration_report("proj-1")
            assert result["report_type"] == "stage_migration"
            matrix = result["sections"]["migration_matrix"]["data"]
            assert len(matrix) == 5
            rates = result["sections"]["transition_rates"]["data"]
            assert len(rates) == 3
            stage1_rates = next(r for r in rates if r["from_stage"] == 1)
            assert abs(stage1_rates["to_stage1_pct"] + stage1_rates["to_stage2_pct"] + stage1_rates["to_stage3_pct"] - 100.0) < 0.01

    def test_empty_data(self):
        with patch("reporting.stage_migration._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.side_effect = Exception("no data")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-STAG-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_stage_migration_report("proj-1")
            assert result["sections"]["migration_matrix"]["data"] == []
            assert result["sections"]["transition_rates"]["data"] == []

    def test_report_saved(self):
        with patch("reporting.stage_migration._h") as mock_h:
            mock_h.get_project.return_value = {"reporting_date": "2025-12-31"}
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-STAG-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            generate_stage_migration_report("proj-1", user="admin")
            mock_h.save_report.assert_called_once()

    def test_uses_current_date_fallback(self):
        with patch("reporting.stage_migration._h") as mock_h:
            mock_h.get_project.return_value = {"project_id": "proj-1"}
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h._report_id.return_value = "RPT-STAG-p1-20250101"
            mock_h.save_report.return_value = None
            mock_h.log = MagicMock()
            result = generate_stage_migration_report("proj-1")
            assert len(result["report_date"]) == 10
