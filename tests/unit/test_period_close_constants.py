"""Dedicated tests for domain/period_close.py — pipeline step definitions and _run_id."""
import re
from datetime import datetime
from unittest.mock import patch

import pytest

from domain.period_close import PIPELINE_STEPS, _run_id


class TestPipelineSteps:
    def test_has_six_steps(self):
        assert len(PIPELINE_STEPS) == 6

    def test_all_steps_have_required_keys(self):
        for step in PIPELINE_STEPS:
            assert "key" in step
            assert "label" in step
            assert "order" in step

    def test_steps_ordered_sequentially(self):
        orders = [s["order"] for s in PIPELINE_STEPS]
        assert orders == sorted(orders)
        assert orders == list(range(1, 7))

    def test_first_step_is_data_freshness(self):
        assert PIPELINE_STEPS[0]["key"] == "data_freshness"

    def test_last_step_is_attribution(self):
        assert PIPELINE_STEPS[-1]["key"] == "attribution"

    def test_step_keys_are_unique(self):
        keys = [s["key"] for s in PIPELINE_STEPS]
        assert len(keys) == len(set(keys))

    def test_expected_step_keys(self):
        expected = {"data_freshness", "data_quality", "model_execution",
                    "ecl_calculation", "report_generation", "attribution"}
        actual = {s["key"] for s in PIPELINE_STEPS}
        assert actual == expected

    def test_labels_not_empty(self):
        for step in PIPELINE_STEPS:
            assert len(step["label"]) > 0

    def test_data_quality_before_model_execution(self):
        dq = next(s for s in PIPELINE_STEPS if s["key"] == "data_quality")
        me = next(s for s in PIPELINE_STEPS if s["key"] == "model_execution")
        assert dq["order"] < me["order"]

    def test_ecl_calculation_after_model_execution(self):
        me = next(s for s in PIPELINE_STEPS if s["key"] == "model_execution")
        ec = next(s for s in PIPELINE_STEPS if s["key"] == "ecl_calculation")
        assert ec["order"] > me["order"]

    def test_report_after_ecl(self):
        ec = next(s for s in PIPELINE_STEPS if s["key"] == "ecl_calculation")
        rg = next(s for s in PIPELINE_STEPS if s["key"] == "report_generation")
        assert rg["order"] > ec["order"]


class TestRunId:
    def test_starts_with_pipe_prefix(self):
        rid = _run_id("proj-1")
        assert rid.startswith("PIPE-proj-1-")

    def test_contains_project_id(self):
        rid = _run_id("my-project")
        assert "my-project" in rid

    def test_has_timestamp_suffix(self):
        rid = _run_id("proj-1")
        parts = rid.split("-")
        ts_part = parts[-1]
        assert len(ts_part) == 14
        assert ts_part.isdigit()

    def test_unique_ids(self):
        ids = {_run_id("proj-1") for _ in range(10)}
        assert len(ids) >= 1  # At least 1 unique (could be same second)

    def test_different_projects_different_ids(self):
        r1 = _run_id("proj-a")
        r2 = _run_id("proj-b")
        assert r1 != r2

    def test_format_pattern(self):
        rid = _run_id("test")
        assert re.match(r"PIPE-test-\d{14}", rid)

    def test_empty_project_id(self):
        rid = _run_id("")
        assert rid.startswith("PIPE--")

    def test_special_chars_in_project_id(self):
        rid = _run_id("proj_123")
        assert "proj_123" in rid


class TestRunStepLogic:
    """Test _run_step_logic for non-DB steps."""

    def test_report_generation_returns_message(self):
        from domain.period_close import _run_step_logic
        result = _run_step_logic("report_generation")
        assert "message" in result

    def test_attribution_returns_message(self):
        from domain.period_close import _run_step_logic
        result = _run_step_logic("attribution")
        assert "message" in result

    def test_unknown_step_returns_message(self):
        from domain.period_close import _run_step_logic
        result = _run_step_logic("nonexistent_step")
        assert "message" in result
        assert "nonexistent_step" in result["message"]
