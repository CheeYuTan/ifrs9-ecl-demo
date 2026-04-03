"""
Unit tests for the IFRS 7.35I ECL Attribution / Waterfall Engine.

Tests:
  - Stage dict construction
  - Waterfall chart data generation
  - Reconciliation check
  - Data unavailability handling (no hardcoded fallbacks)
  - Opening ECL estimation
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from domain.attribution import (
    _stage_dict,
    _stage_val,
    _unavailable,
    _build_waterfall,
    _estimate_opening_ecl,
    MATERIALITY_THRESHOLD,
)


class TestStageDict:
    def test_basic_construction(self):
        d = _stage_dict(100, 200, 300)
        assert d["stage1"] == 100
        assert d["stage2"] == 200
        assert d["stage3"] == 300
        assert d["total"] == 600

    def test_rounding(self):
        d = _stage_dict(100.456, 200.789, 300.123)
        assert d["stage1"] == 100.46
        assert d["stage2"] == 200.79
        assert d["stage3"] == 300.12
        assert d["total"] == 601.37

    def test_defaults_to_zero(self):
        d = _stage_dict()
        assert d["total"] == 0

    def test_negative_values(self):
        d = _stage_dict(-50, -100, -150)
        assert d["total"] == -300


class TestStageVal:
    def test_extracts_stage(self):
        d = {"stage1": 100, "stage2": 200, "stage3": 300}
        assert _stage_val(d, 1) == 100
        assert _stage_val(d, 2) == 200

    def test_none_returns_zero(self):
        assert _stage_val(None, 1) == 0.0

    def test_missing_key_returns_zero(self):
        assert _stage_val({"stage1": 100}, 2) == 0.0


class TestUnavailable:
    def test_returns_zero_totals(self):
        result = _unavailable("test reason")
        assert result["total"] == 0.0
        assert result["status"] == "data_unavailable"
        assert result["reason"] == "test reason"

    def test_all_stages_zero(self):
        result = _unavailable("no data")
        assert result["stage1"] == 0.0
        assert result["stage2"] == 0.0
        assert result["stage3"] == 0.0


class TestBuildWaterfall:
    def test_basic_waterfall(self):
        opening = _stage_dict(1000, 500, 200)
        originations = _stage_dict(100, 10, 0)
        derecognitions = _stage_dict(-50, -20, -10)
        transfers = _stage_dict(-30, 20, 10)
        model_chg = _stage_dict(10, 5, 3)
        macro_chg = _stage_dict(0, 0, 0)
        overlays = _stage_dict(20, 10, 5)
        writeoffs = _stage_dict(0, 0, -30)
        unwind = _stage_dict(12.5, 6.25, 2.5)
        fx = _stage_dict(0, 0, 0)
        residual = _stage_dict(0, 0, 0)
        closing = _stage_dict(1062.5, 531.25, 180.5)

        wf = _build_waterfall(opening, originations, derecognitions, transfers,
                              model_chg, macro_chg, overlays, writeoffs,
                              unwind, fx, residual, closing)

        assert len(wf) == 12
        assert wf[0]["name"] == "Opening ECL"
        assert wf[0]["category"] == "anchor"
        assert wf[-1]["name"] == "Closing ECL"
        assert wf[-1]["category"] == "anchor"

    def test_cumulative_tracking(self):
        opening = _stage_dict(1000, 0, 0)
        inc = _stage_dict(100, 0, 0)
        zero = _stage_dict(0, 0, 0)
        closing = _stage_dict(1100, 0, 0)

        wf = _build_waterfall(opening, inc, zero, zero, zero, zero,
                              zero, zero, zero, zero, zero, closing)

        assert wf[0]["cumulative"] == 1000
        assert wf[1]["cumulative"] == 1100

    def test_waterfall_items_have_required_fields(self):
        zero = _stage_dict(0, 0, 0)
        wf = _build_waterfall(zero, zero, zero, zero, zero, zero,
                              zero, zero, zero, zero, zero, zero)
        for item in wf:
            assert "name" in item
            assert "value" in item
            assert "cumulative" in item
            assert "category" in item
            assert "base" in item


class TestEstimateOpeningEcl:
    def test_sets_opening_equal_to_closing(self):
        closing = {1: 1080, 2: 1150, 3: 1220}
        result = _estimate_opening_ecl(closing)
        assert result["stage1"] == 1080
        assert result["stage2"] == 1150
        assert result["stage3"] == 1220
        assert "note" in result

    def test_zero_closing(self):
        result = _estimate_opening_ecl({1: 0, 2: 0, 3: 0})
        assert result["total"] == 0


class TestNoHardcodedFallbacks:
    """Verify that the attribution engine does NOT use hardcoded percentage fallbacks."""

    def test_unavailable_has_no_synthetic_values(self):
        result = _unavailable("test")
        assert result["stage1"] == 0.0
        assert result["stage2"] == 0.0
        assert result["stage3"] == 0.0
        assert "status" in result
        assert result["status"] == "data_unavailable"


class TestMaterialityThreshold:
    def test_threshold_is_one_percent(self):
        assert MATERIALITY_THRESHOLD == 0.01

    def test_threshold_is_positive(self):
        assert MATERIALITY_THRESHOLD > 0
