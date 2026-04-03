"""Tests for domain/model_runs.py — Model run history and satellite model queries."""
import json
import pytest
import pandas as pd
from unittest.mock import patch


@pytest.fixture
def _patch_db():
    with patch("domain.model_runs.query_df") as mock_q, \
         patch("domain.model_runs.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


class TestSaveModelRun:
    def test_stores_and_returns(self, _patch_db):
        from domain.model_runs import save_model_run
        result_row = pd.DataFrame([{
            "run_id": "run-001",
            "run_type": "satellite_model",
            "models_used": json.dumps(["linear", "logistic"]),
            "products": json.dumps(["mortgage", "credit_card"]),
            "total_cohorts": 10,
            "best_model_summary": json.dumps({"best": "logistic"}),
            "notes": "test run",
            "run_timestamp": "2025-12-31",
            "status": "completed",
            "created_by": "system",
        }])
        _patch_db["query_df"].return_value = result_row
        result = save_model_run(
            "run-001", "satellite_model",
            ["linear", "logistic"], ["mortgage", "credit_card"],
            10, {"best": "logistic"}, "test run",
        )
        assert result["run_id"] == "run-001"
        assert _patch_db["execute"].called


class TestGetModelRun:
    def test_returns_none_for_missing(self, _patch_db):
        from domain.model_runs import get_model_run
        assert get_model_run("nonexistent") is None

    def test_parses_json_fields(self, _patch_db):
        from domain.model_runs import get_model_run
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "run_id": "run-001",
            "run_type": "satellite_model",
            "models_used": json.dumps(["linear", "logistic"]),
            "products": json.dumps(["mortgage"]),
            "best_model_summary": json.dumps({"best": "logistic"}),
            "total_cohorts": 5,
            "run_timestamp": "2025-12-31",
            "status": "completed",
            "notes": "",
            "created_by": "system",
        }])
        result = get_model_run("run-001")
        assert isinstance(result["models_used"], list)
        assert isinstance(result["products"], list)
        assert isinstance(result["best_model_summary"], dict)


class TestListModelRuns:
    def test_returns_dataframe(self, _patch_db):
        from domain.model_runs import list_model_runs
        result = list_model_runs()
        assert isinstance(result, pd.DataFrame)

    def test_with_run_type_filter(self, _patch_db):
        from domain.model_runs import list_model_runs
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "run_id": "r1", "run_type": "satellite_model",
        }])
        result = list_model_runs("satellite_model")
        assert len(result) == 1


class TestGetActiveRunId:
    def test_returns_none_when_no_data(self, _patch_db):
        from domain.model_runs import get_active_run_id
        assert get_active_run_id() is None

    def test_returns_latest_timestamp(self, _patch_db):
        from domain.model_runs import get_active_run_id
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "run_timestamp": "2025-12-31 10:00:00",
        }])
        result = get_active_run_id()
        assert result == "2025-12-31 10:00:00"

    def test_handles_exception(self, _patch_db):
        from domain.model_runs import get_active_run_id
        _patch_db["query_df"].side_effect = Exception("DB error")
        assert get_active_run_id() is None


class TestGetSatelliteModelComparison:
    def test_returns_dataframe(self, _patch_db):
        from domain.model_runs import get_satellite_model_comparison
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "product_type": "mortgage", "cohort_id": "2024",
            "model_type": "logistic", "r_squared": 0.85,
        }])
        result = get_satellite_model_comparison()
        assert len(result) == 1

    def test_with_run_id_filter(self, _patch_db):
        from domain.model_runs import get_satellite_model_comparison
        result = get_satellite_model_comparison("2025-12-31")
        assert isinstance(result, pd.DataFrame)


class TestGetSatelliteModelSelected:
    def test_returns_dataframe(self, _patch_db):
        from domain.model_runs import get_satellite_model_selected
        result = get_satellite_model_selected()
        assert isinstance(result, pd.DataFrame)


class TestDetectAvailableDimensions:
    def test_returns_ordered_list(self, _patch_db):
        from domain.model_runs import _detect_available_dimensions
        _patch_db["query_df"].return_value = pd.DataFrame({
            "column_name": ["credit_grade", "assessed_stage", "vintage_year", "region"],
        })
        result = _detect_available_dimensions("test_table")
        assert result[0] == "credit_grade"
        assert "assessed_stage" in result
        assert "vintage_year" in result

    def test_handles_empty_columns(self, _patch_db):
        from domain.model_runs import _detect_available_dimensions
        result = _detect_available_dimensions("test_table")
        assert result == []

    def test_handles_exception(self, _patch_db):
        from domain.model_runs import _detect_available_dimensions
        _patch_db["query_df"].side_effect = Exception("DB error")
        result = _detect_available_dimensions("test_table")
        assert result == []


class TestGetDrillDownDimensions:
    def test_returns_labeled_dimensions(self, _patch_db):
        from domain.model_runs import get_drill_down_dimensions
        _patch_db["query_df"].return_value = pd.DataFrame({
            "column_name": ["credit_grade", "assessed_stage"],
        })
        result = get_drill_down_dimensions("mortgage")
        assert len(result) == 2
        assert result[0]["key"] == "credit_grade"
        assert result[0]["label"] == "Credit Grade"


class TestGetEclByProductDrilldown:
    def test_returns_dataframe(self, _patch_db):
        from domain.model_runs import get_ecl_by_product_drilldown
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "product_type": "mortgage", "loan_count": 5000,
            "total_gca": 250e6, "total_ecl": 5e6, "coverage_ratio": 2.0,
        }])
        result = get_ecl_by_product_drilldown()
        assert len(result) == 1


class TestGetPortfolioByDimension:
    def test_auto_dimension(self, _patch_db):
        from domain.model_runs import get_portfolio_by_dimension
        cols_df = pd.DataFrame({"column_name": ["credit_grade", "assessed_stage"]})
        data_df = pd.DataFrame([{
            "cohort_id": "AAA", "loan_count": 100, "total_gca": 1e6,
            "avg_pd_pct": 1.5, "avg_dpd": 5.0,
        }])
        _patch_db["query_df"].side_effect = [cols_df, data_df]
        result = get_portfolio_by_dimension("mortgage", "auto")
        assert isinstance(result, pd.DataFrame)
