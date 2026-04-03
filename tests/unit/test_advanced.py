"""Tests for domain/advanced.py — Cure rates, CCF, and collateral haircuts."""
import json
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch


@pytest.fixture
def portfolio_df():
    return pd.DataFrame({
        "product_type": ["mortgage", "mortgage", "credit_card", "credit_card", "personal_loan", "personal_loan"],
        "assessed_stage": [1, 2, 1, 3, 1, 2],
        "cnt": [5000, 1000, 3000, 500, 4000, 800],
        "gca": [250e6, 50e6, 30e6, 5e6, 80e6, 16e6],
        "dpd_1_30": [200, 400, 150, 50, 180, 350],
        "dpd_31_60": [50, 200, 80, 100, 60, 150],
        "dpd_61_90": [10, 80, 30, 80, 20, 60],
        "dpd_90_plus": [5, 50, 20, 200, 10, 40],
    })


@pytest.fixture
def portfolio_with_gca():
    return pd.DataFrame({
        "product_type": ["mortgage", "credit_card"],
        "assessed_stage": [1, 1],
        "cnt": [5000, 3000],
        "total_gca": [250e6, 30e6],
        "avg_gca": [50000.0, 10000.0],
    })


@pytest.fixture
def _patch_db():
    with patch("domain.advanced.query_df") as mock_q, \
         patch("domain.advanced.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


class TestComputeCureRates:
    def test_returns_expected_structure(self, _patch_db, portfolio_df):
        from domain.advanced import compute_cure_rates
        _patch_db["query_df"].return_value = portfolio_df
        result = compute_cure_rates()
        assert "cure_by_dpd" in result
        assert "cure_by_product" in result
        assert "cure_by_segment" in result
        assert "cure_trend" in result
        assert "time_to_cure" in result
        assert "overall_cure_rate" in result
        assert "analysis_id" in result

    def test_four_dpd_buckets(self, _patch_db, portfolio_df):
        from domain.advanced import compute_cure_rates
        _patch_db["query_df"].return_value = portfolio_df
        result = compute_cure_rates()
        assert len(result["cure_by_dpd"]) == 4
        buckets = {r["dpd_bucket"] for r in result["cure_by_dpd"]}
        assert buckets == {"1-30 DPD", "31-60 DPD", "61-90 DPD", "90+ DPD"}

    def test_three_segments(self, _patch_db, portfolio_df):
        from domain.advanced import compute_cure_rates
        _patch_db["query_df"].return_value = portfolio_df
        result = compute_cure_rates()
        assert len(result["cure_by_segment"]) == 3

    def test_twelve_month_trend(self, _patch_db, portfolio_df):
        from domain.advanced import compute_cure_rates
        _patch_db["query_df"].return_value = portfolio_df
        result = compute_cure_rates()
        assert len(result["cure_trend"]) == 12

    def test_twelve_time_to_cure_entries(self, _patch_db, portfolio_df):
        from domain.advanced import compute_cure_rates
        _patch_db["query_df"].return_value = portfolio_df
        result = compute_cure_rates()
        assert len(result["time_to_cure"]) == 12

    def test_cure_rates_in_range(self, _patch_db, portfolio_df):
        from domain.advanced import compute_cure_rates
        _patch_db["query_df"].return_value = portfolio_df
        result = compute_cure_rates()
        for entry in result["cure_by_dpd"]:
            assert 0 <= entry["cure_rate"] <= 1.0
        for entry in result["cure_by_product"]:
            assert 0 <= entry["cure_rate"] <= 1.0

    def test_with_empty_portfolio(self, _patch_db):
        from domain.advanced import compute_cure_rates
        result = compute_cure_rates()
        assert "cure_by_dpd" in result
        assert len(result["cure_by_dpd"]) == 4

    def test_with_product_filter(self, _patch_db, portfolio_df):
        from domain.advanced import compute_cure_rates
        _patch_db["query_df"].return_value = portfolio_df[portfolio_df["product_type"] == "mortgage"]
        result = compute_cure_rates("mortgage")
        assert result["product_type"] == "mortgage"


class TestComputeCcf:
    def test_returns_expected_structure(self, _patch_db, portfolio_with_gca):
        from domain.advanced import compute_ccf
        _patch_db["query_df"].return_value = portfolio_with_gca
        result = compute_ccf()
        assert "ccf_by_stage" in result
        assert "ccf_by_utilization" in result
        assert "overall_avg_ccf" in result
        assert "analysis_id" in result

    def test_ccf_values_in_range(self, _patch_db, portfolio_with_gca):
        from domain.advanced import compute_ccf
        _patch_db["query_df"].return_value = portfolio_with_gca
        result = compute_ccf()
        for entry in result["ccf_by_stage"]:
            assert 0 < entry["ccf"] <= 1.05

    def test_revolving_lower_ccf(self, _patch_db, portfolio_with_gca):
        from domain.advanced import compute_ccf
        _patch_db["query_df"].return_value = portfolio_with_gca
        result = compute_ccf()
        revolving = [e for e in result["ccf_by_stage"] if e["is_revolving"] and e["stage"] == 1]
        non_revolving = [e for e in result["ccf_by_stage"] if not e["is_revolving"] and e["stage"] == 1]
        if revolving and non_revolving:
            avg_rev = sum(e["ccf"] for e in revolving) / len(revolving)
            avg_non = sum(e["ccf"] for e in non_revolving) / len(non_revolving)
            assert avg_rev < avg_non

    def test_utilization_bands(self, _patch_db, portfolio_with_gca):
        from domain.advanced import compute_ccf
        _patch_db["query_df"].return_value = portfolio_with_gca
        result = compute_ccf()
        assert len(result["ccf_by_utilization"]) == 5


class TestComputeCollateralHaircuts:
    def test_returns_expected_structure(self, _patch_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        assert "haircut_results" in result
        assert "lgd_waterfall" in result
        assert "summary" in result

    def test_seven_collateral_types(self, _patch_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        assert len(result["haircut_results"]) == 7

    def test_haircuts_in_range(self, _patch_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        for entry in result["haircut_results"]:
            assert 0 <= entry["haircut_pct"] <= 1.1
            assert 0 <= entry["recovery_rate"] <= 1.05

    def test_recovery_rates_in_range(self, _patch_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        for entry in result["haircut_results"]:
            assert entry["time_to_recovery_months"] >= 0.5

    def test_lgd_waterfall_steps(self, _patch_db):
        from domain.advanced import compute_collateral_haircuts
        gca_df = pd.DataFrame([{"tgca": 1_000_000_000}])
        _patch_db["query_df"].return_value = gca_df
        result = compute_collateral_haircuts()
        assert len(result["lgd_waterfall"]) == 5
        assert result["lgd_waterfall"][0]["step"] == "Gross Exposure"


class TestGetAndListCureAnalysis:
    def test_get_returns_none_for_missing(self, _patch_db):
        from domain.advanced import get_cure_analysis
        assert get_cure_analysis("nonexistent") is None

    def test_list_returns_empty(self, _patch_db):
        from domain.advanced import list_cure_analyses
        assert list_cure_analyses() == []


class TestGetAndListCcfAnalysis:
    def test_get_returns_none_for_missing(self, _patch_db):
        from domain.advanced import get_ccf_analysis
        assert get_ccf_analysis("nonexistent") is None

    def test_list_returns_empty(self, _patch_db):
        from domain.advanced import list_ccf_analyses
        assert list_ccf_analyses() == []


class TestGetAndListCollateralAnalysis:
    def test_get_returns_none_for_missing(self, _patch_db):
        from domain.advanced import get_collateral_analysis
        assert get_collateral_analysis("nonexistent") is None

    def test_list_returns_empty(self, _patch_db):
        from domain.advanced import list_collateral_analyses
        assert list_collateral_analyses() == []
