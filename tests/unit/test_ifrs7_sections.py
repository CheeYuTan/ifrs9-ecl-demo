"""Tests for reporting/_ifrs7_sections_a.py and _ifrs7_sections_b.py."""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from reporting._ifrs7_sections_a import _build_35f, _build_35h, _build_35i, _build_35j
from reporting._ifrs7_sections_b import _build_35k, _build_35l, _build_35m, _build_36


def _mock_report_helpers(**overrides):
    """Patch reporting.report_helpers consistently for section builder tests."""
    defaults = {
        "reporting.report_helpers.query_df": pd.DataFrame(),
        "reporting.report_helpers._t": lambda t: f"schema.ecl_{t}",
    }
    defaults.update(overrides)
    return patch.multiple("", **{k: v for k, v in defaults.items()})


class TestBuild35f:
    def test_success_with_data(self):
        df = pd.DataFrame({
            "credit_grade": ["Investment Grade (AAA-BBB)", "Speculative (B)"],
            "assessed_stage": [1, 2],
            "loan_count": [100, 20],
            "gross_carrying_amount": [1_000_000.0, 200_000.0],
            "ecl_amount": [5000.0, 8000.0],
            "avg_pd": [0.005, 0.12],
        })
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35f(sections)
            assert "ifrs7_35f" in sections
            assert len(sections["ifrs7_35f"]["data"]) == 2
            assert "IFRS 7.35F" in sections["ifrs7_35f"]["title"]

    def test_empty_data(self):
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.return_value = pd.DataFrame()
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35f(sections)
            assert sections["ifrs7_35f"]["data"] == []

    def test_query_error(self):
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.side_effect = Exception("DB error")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h.log = MagicMock()
            sections = {}
            _build_35f(sections)
            assert "error" in sections["ifrs7_35f"]
            assert sections["ifrs7_35f"]["data"] == []


class TestBuild35h:
    def test_success_with_prior_data(self):
        df = pd.DataFrame({
            "stage": [1, 2, 3],
            "loan_count": [500, 100, 20],
            "gross_carrying_amount": [5_000_000.0, 1_000_000.0, 200_000.0],
            "ecl_amount": [25_000.0, 50_000.0, 80_000.0],
            "avg_pd": [0.008, 0.05, 0.25],
            "avg_lgd": [0.35, 0.40, 0.55],
            "coverage_ratio": [0.50, 5.0, 40.0],
        })
        prior_data = [
            {"stage": 1, "ecl_amount": 20_000.0, "gross_carrying_amount": 4_500_000.0},
            {"stage": 2, "ecl_amount": 45_000.0, "gross_carrying_amount": 900_000.0},
        ]
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35h(sections, "proj-1", prior_data)
            assert sections["ifrs7_35h"]["has_prior_period"] is True
            data = sections["ifrs7_35h"]["data"]
            stage1 = next(d for d in data if d["stage"] == 1)
            assert stage1["ecl_movement"] == 5000.0
            assert stage1["prior_ecl_amount"] == 20_000.0

    def test_no_prior_data(self):
        df = pd.DataFrame({
            "stage": [1],
            "loan_count": [10],
            "gross_carrying_amount": [100_000.0],
            "ecl_amount": [1000.0],
            "avg_pd": [0.01],
            "avg_lgd": [0.35],
            "coverage_ratio": [1.0],
        })
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35h(sections, "proj-1", [])
            assert sections["ifrs7_35h"]["has_prior_period"] is False
            data = sections["ifrs7_35h"]["data"]
            assert data[0]["ecl_movement_pct"] == 0

    def test_zero_prior_ecl(self):
        df = pd.DataFrame({
            "stage": [1],
            "loan_count": [10],
            "gross_carrying_amount": [100_000.0],
            "ecl_amount": [5000.0],
            "avg_pd": [0.01],
            "avg_lgd": [0.35],
            "coverage_ratio": [5.0],
        })
        prior_data = [{"stage": 1, "ecl_amount": 0, "gross_carrying_amount": 0}]
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35h(sections, "proj-1", prior_data)
            data = sections["ifrs7_35h"]["data"]
            assert data[0]["ecl_movement_pct"] == 0

    def test_query_error(self):
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.side_effect = Exception("DB error")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h.log = MagicMock()
            sections = {}
            _build_35h(sections, "proj-1", [])
            assert "error" in sections["ifrs7_35h"]


class TestBuild35i:
    def test_success_with_attribution(self):
        attr = {
            "opening_ecl": {"stage1": 100, "stage2": 50, "stage3": 20, "total": 170},
            "new_originations": {"stage1": 30, "stage2": 10, "stage3": 5, "total": 45},
            "derecognitions": {"stage1": -20, "stage2": -5, "stage3": -2, "total": -27},
            "stage_transfers": {"stage1": -10, "stage2": 8, "stage3": 2, "total": 0},
            "remeasurement": {"stage1": 5, "stage2": 3, "stage3": 1, "total": 9},
            "management_overlays": {"stage1": 0, "stage2": 0, "stage3": 0, "total": 0},
            "write_offs": {"stage1": 0, "stage2": 0, "stage3": -5, "total": -5},
            "closing_ecl": {"stage1": 105, "stage2": 66, "stage3": 21, "total": 192},
        }
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.get_attribution.return_value = attr
            mock_h.compute_attribution.return_value = attr
            sections = {}
            _build_35i(sections, "proj-1")
            data = sections["ifrs7_35i"]["data"]
            assert len(data) == 8
            assert data[0]["component"] == "Opening Ecl"
            assert data[0]["total"] == 170.0

    def test_no_attribution(self):
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.get_attribution.return_value = None
            mock_h.compute_attribution.return_value = {}
            sections = {}
            _build_35i(sections, "proj-1")
            data = sections["ifrs7_35i"]["data"]
            assert len(data) == 8
            for entry in data:
                assert entry["total"] == 0.0

    def test_error(self):
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.get_attribution.side_effect = Exception("no attr")
            mock_h.log = MagicMock()
            sections = {}
            _build_35i(sections, "proj-1")
            assert "error" in sections["ifrs7_35i"]


class TestBuild35j:
    def test_success_with_data(self):
        count_df = pd.DataFrame({"cnt": [100]})
        wo_df = pd.DataFrame({
            "product_type": ["Mortgage"],
            "default_count": [10],
            "gross_writeoff": [500_000.0],
            "recovery_amount": [200_000.0],
            "net_writeoff": [300_000.0],
            "recovery_rate_pct": [40.0],
        })
        summary_df = pd.DataFrame({
            "total_defaults": [10],
            "total_gross": [500_000.0],
            "total_recovered": [200_000.0],
            "total_net_writeoff": [300_000.0],
            "contractual_outstanding": [100_000.0],
        })
        call_count = [0]

        def mock_query(sql, *args):
            call_count[0] += 1
            if call_count[0] == 1:
                return count_df
            elif call_count[0] == 2:
                return wo_df
            else:
                return summary_df

        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.side_effect = mock_query
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35j(sections)
            assert len(sections["ifrs7_35j"]["data"]) == 1
            assert "summary" in sections["ifrs7_35j"]

    def test_table_not_found(self):
        with patch("reporting._ifrs7_sections_a._h") as mock_h:
            mock_h.query_df.side_effect = Exception("relation schema.historical_defaults does not exist")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h.log = MagicMock()
            sections = {}
            _build_35j(sections)
            assert "error" in sections["ifrs7_35j"]
            assert "Historical defaults table" in sections["ifrs7_35j"]["error"]


class TestBuild35k:
    def test_success(self):
        df = pd.DataFrame({
            "product_type": ["Mortgage", "Auto"],
            "stage": [1, 2],
            "loan_count": [100, 50],
            "gross_carrying_amount": [1_000_000.0, 500_000.0],
            "avg_exposure": [10_000.0, 10_000.0],
            "min_exposure": [1_000.0, 2_000.0],
            "max_exposure": [50_000.0, 30_000.0],
        })
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35k(sections)
            assert len(sections["ifrs7_35k"]["data"]) == 2

    def test_error(self):
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.side_effect = Exception("err")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h.log = MagicMock()
            sections = {}
            _build_35k(sections)
            assert "error" in sections["ifrs7_35k"]


class TestBuild35l:
    def test_success(self):
        df = pd.DataFrame({
            "product_type": ["Mortgage"],
            "total_loans": [200],
            "modified_performing": [15],
            "cured_to_stage1": [5],
            "modified_gca": [150_000.0],
        })
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35l(sections)
            assert len(sections["ifrs7_35l"]["data"]) == 1

    def test_error(self):
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.side_effect = Exception("err")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h.log = MagicMock()
            sections = {}
            _build_35l(sections)
            assert "error" in sections["ifrs7_35l"]


class TestBuild35m:
    def test_success(self):
        df = pd.DataFrame({
            "product_type": ["Mortgage"],
            "stage": [1],
            "loan_count": [500],
            "total_exposure": [5_000_000.0],
            "estimated_collateral": [3_500_000.0],
            "avg_recovery_rate": [0.65],
            "avg_lgd": [0.35],
        })
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_35m(sections)
            assert len(sections["ifrs7_35m"]["data"]) == 1

    def test_error(self):
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.side_effect = Exception("err")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h.log = MagicMock()
            sections = {}
            _build_35m(sections)
            assert "error" in sections["ifrs7_35m"]


class TestBuild36:
    def test_success_with_nonzero_base(self):
        df = pd.DataFrame({"base_ecl": [1_000_000.0]})
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_36(sections)
            data = sections["ifrs7_36"]["data"]
            assert len(data) == 8
            pd_plus_10 = next(d for d in data if d["scenario"] == "PD +10%")
            assert pd_plus_10["stressed_ecl"] == 1_100_000.0
            assert pd_plus_10["change_pct"] == 10.0

    def test_zero_base_ecl(self):
        df = pd.DataFrame({"base_ecl": [0.0]})
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_36(sections)
            data = sections["ifrs7_36"]["data"]
            for entry in data:
                assert entry["change_pct"] == 0

    def test_combined_stress(self):
        df = pd.DataFrame({"base_ecl": [100_000.0]})
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.return_value = df
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            sections = {}
            _build_36(sections)
            data = sections["ifrs7_36"]["data"]
            combined = next(d for d in data if d["scenario"] == "PD+10% & LGD+10%")
            expected = round(100_000.0 * 1.1 * 1.1, 2)
            assert combined["stressed_ecl"] == expected

    def test_error(self):
        with patch("reporting._ifrs7_sections_b._h") as mock_h:
            mock_h.query_df.side_effect = Exception("err")
            mock_h._t.side_effect = lambda t: f"schema.{t}"
            mock_h.log = MagicMock()
            sections = {}
            _build_36(sections)
            assert "error" in sections["ifrs7_36"]
