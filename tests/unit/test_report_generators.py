"""Tests for reporting generators: concentration, ecl_movement, stage_migration, sensitivity."""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


_H = "reporting.report_helpers"


def _project(reporting_date="2025-03-31"):
    return {"project_id": "p1", "reporting_date": reporting_date, "scenario_weights": {"base": 0.5, "adverse": 0.5}}


# ── Concentration Report ───────────────────────────────────────

class TestConcentrationReport:
    @patch(f"{_H}.save_report")
    @patch(f"{_H}.query_df")
    @patch(f"{_H}.get_project", return_value=_project())
    def test_generates_report(self, mock_proj, mock_qdf, mock_save):
        mock_qdf.side_effect = [
            pd.DataFrame([
                {"product_type": "mortgage", "loan_count": 100, "total_gca": 5000000.0,
                 "total_ecl": 50000.0, "avg_pd": 0.02, "avg_lgd": 0.3},
                {"product_type": "credit_card", "loan_count": 200, "total_gca": 1000000.0,
                 "total_ecl": 30000.0, "avg_pd": 0.05, "avg_lgd": 0.6},
            ]),
            pd.DataFrame([
                {"segment": "retail", "loan_count": 300, "total_gca": 6000000.0,
                 "total_ecl": 80000.0, "avg_pd": 0.03},
            ]),
            pd.DataFrame([
                {"loan_id": "L1", "product_type": "mortgage", "borrower_segment": "retail",
                 "gross_carrying_amount": 1000000, "assessed_stage": 1, "pd_lifetime": 0.01,
                 "ecl": 5000, "days_past_due": 0},
            ]),
        ]
        from reporting.concentration_report import generate_concentration_report
        result = generate_concentration_report("p1")

        assert result["report_type"] == "concentration_risk"
        assert result["report_date"] == "2025-03-31"
        sections = result["sections"]
        assert "by_product" in sections
        assert len(sections["by_product"]["data"]) == 2
        assert sections["by_product"]["data"][0]["concentration_pct"] > 0
        mock_save.assert_called_once()

    @patch(f"{_H}.get_project", return_value=None)
    def test_project_not_found(self, mock_proj):
        from reporting.concentration_report import generate_concentration_report
        with pytest.raises(ValueError, match="not found"):
            generate_concentration_report("nope")

    @patch(f"{_H}.save_report")
    @patch(f"{_H}.query_df", side_effect=Exception("DB down"))
    @patch(f"{_H}.get_project", return_value=_project())
    def test_handles_db_error_gracefully(self, mock_proj, mock_qdf, mock_save):
        from reporting.concentration_report import generate_concentration_report
        result = generate_concentration_report("p1")
        assert result["sections"]["by_product"]["data"] == []
        assert result["sections"]["by_segment"]["data"] == []
        assert result["sections"]["top_exposures"]["data"] == []


# ── ECL Movement Report ───────────────────────────────────────

class TestEclMovementReport:
    @patch(f"{_H}.save_report")
    @patch(f"{_H}.compute_attribution", return_value={
        "opening_ecl": {"total": 100000, "stage1": 50000, "stage2": 30000, "stage3": 20000},
        "closing_ecl": {"total": 110000, "stage1": 55000, "stage2": 35000, "stage3": 20000},
    })
    @patch(f"{_H}.get_attribution", return_value=None)
    @patch(f"{_H}.query_df")
    @patch(f"{_H}.get_project", return_value=_project())
    def test_generates_with_waterfall(self, mock_proj, mock_qdf, mock_attr, mock_compute, mock_save):
        mock_qdf.return_value = pd.DataFrame([
            {"product_type": "mortgage", "stage": 1, "gca": 5000000, "ecl": 50000,
             "loan_count": 100, "avg_pd": 0.02, "avg_lgd": 0.3},
        ])
        from reporting.ecl_movement import generate_ecl_movement_report
        result = generate_ecl_movement_report("p1")
        assert result["report_type"] == "ecl_movement"
        waterfall = result["sections"]["waterfall"]["data"]
        assert len(waterfall) > 0
        assert waterfall[0]["component"] == "Opening Ecl"

    @patch(f"{_H}.get_project", return_value=None)
    def test_project_not_found(self, mock_proj):
        from reporting.ecl_movement import generate_ecl_movement_report
        with pytest.raises(ValueError, match="not found"):
            generate_ecl_movement_report("nope")


# ── Stage Migration Report ─────────────────────────────────────

class TestStageMigrationReport:
    @patch(f"{_H}.save_report")
    @patch(f"{_H}.query_df")
    @patch(f"{_H}.get_project", return_value=_project())
    def test_generates_with_transition_rates(self, mock_proj, mock_qdf, mock_save):
        mock_qdf.side_effect = [
            pd.DataFrame([
                {"original_stage": 1, "assessed_stage": 1, "loan_count": 900, "total_gca": 4500000, "total_ecl": 45000},
                {"original_stage": 1, "assessed_stage": 2, "loan_count": 100, "total_gca": 500000, "total_ecl": 20000},
            ]),
            pd.DataFrame([
                {"original_stage": 1, "total_from_stage": 1000, "to_stage1": 900, "to_stage2": 100, "to_stage3": 0},
            ]),
        ]
        from reporting.stage_migration import generate_stage_migration_report
        result = generate_stage_migration_report("p1")
        assert result["report_type"] == "stage_migration"
        rates = result["sections"]["transition_rates"]["data"]
        assert len(rates) == 1
        assert rates[0]["to_stage1_pct"] == 90.0
        assert rates[0]["to_stage2_pct"] == 10.0

    @patch(f"{_H}.save_report")
    @patch(f"{_H}.query_df", side_effect=Exception("table not found"))
    @patch(f"{_H}.get_project", return_value=_project())
    def test_handles_missing_table(self, mock_proj, mock_qdf, mock_save):
        from reporting.stage_migration import generate_stage_migration_report
        result = generate_stage_migration_report("p1")
        assert result["sections"]["migration_matrix"]["data"] == []
        assert result["sections"]["transition_rates"]["data"] == []


# ── Sensitivity Report ─────────────────────────────────────────

class TestSensitivityReport:
    @patch(f"{_H}.save_report")
    @patch(f"{_H}.query_df")
    @patch(f"{_H}.get_project", return_value=_project())
    def test_generates_sensitivity_grid(self, mock_proj, mock_qdf, mock_save):
        mock_qdf.side_effect = [
            pd.DataFrame([
                {"stage": 1, "ecl": 50000.0},
                {"stage": 2, "ecl": 30000.0},
                {"stage": 3, "ecl": 20000.0},
            ]),
            pd.DataFrame([
                {"scenario": "base", "total_ecl": 100000.0, "weight": 0.5, "weighted_contribution": 50000.0},
                {"scenario": "adverse", "total_ecl": 150000.0, "weight": 0.5, "weighted_contribution": 75000.0},
            ]),
            pd.DataFrame([{"total_gca": 10000000.0, "loan_count": 500}]),
        ]
        from reporting.sensitivity_report import generate_sensitivity_report
        result = generate_sensitivity_report("p1")
        assert result["report_type"] == "sensitivity_analysis"
        grid = result["sections"]["sensitivity_grid"]["data"]
        assert len(grid) == 25  # 5 PD shifts x 5 LGD shifts
        base_entry = [g for g in grid if g["pd_shift_pct"] == 0 and g["lgd_shift_pct"] == 0][0]
        assert base_entry["ecl"] == 100000.0
        assert base_entry["change_from_base"] == 0.0

    @patch(f"{_H}.save_report")
    @patch(f"{_H}.query_df", side_effect=Exception("DB error"))
    @patch(f"{_H}.get_project", return_value=_project())
    def test_zero_base_ecl_no_division_error(self, mock_proj, mock_qdf, mock_save):
        from reporting.sensitivity_report import generate_sensitivity_report
        result = generate_sensitivity_report("p1")
        grid = result["sections"]["sensitivity_grid"]["data"]
        for entry in grid:
            assert entry["change_pct"] == 0
