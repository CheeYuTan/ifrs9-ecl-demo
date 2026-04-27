"""Dedicated tests for reporting/report_helpers.py — report ID generation."""
import re

import pytest

from reporting.report_helpers import _report_id


class TestReportId:
    def test_starts_with_rpt_prefix(self):
        rid = _report_id("sensitivity", "proj-1")
        assert rid.startswith("RPT-")

    def test_contains_report_type_abbreviated(self):
        rid = _report_id("sensitivity", "proj-1")
        assert "SENS" in rid

    def test_contains_project_id(self):
        rid = _report_id("ifrs7", "my-proj")
        assert "my-proj" in rid

    def test_has_timestamp_suffix(self):
        rid = _report_id("concentration", "proj-1")
        parts = rid.split("-")
        ts_part = parts[-1]
        assert len(ts_part) == 14
        assert ts_part.isdigit()

    def test_ifrs7_type_abbreviation(self):
        rid = _report_id("ifrs7_disclosure", "proj-1")
        assert "IFRS" in rid

    def test_concentration_type_abbreviation(self):
        rid = _report_id("concentration_risk", "proj-1")
        assert "CONC" in rid

    def test_different_projects_give_different_ids(self):
        r1 = _report_id("test", "proj-a")
        r2 = _report_id("test", "proj-b")
        assert r1 != r2

    def test_different_types_give_different_ids(self):
        r1 = _report_id("sensitivity", "proj-1")
        r2 = _report_id("concentration", "proj-1")
        assert r1 != r2

    def test_format_pattern(self):
        rid = _report_id("test", "proj-1")
        assert re.match(r"RPT-[A-Z]{4}-proj-1-\d{14}", rid)

    def test_type_truncated_to_4_chars(self):
        rid = _report_id("verylongreporttype", "proj-1")
        type_part = rid.split("-")[1]
        assert len(type_part) == 4

    def test_short_type(self):
        rid = _report_id("ab", "proj-1")
        assert "AB" in rid

    def test_empty_project_id(self):
        rid = _report_id("test", "")
        assert rid.startswith("RPT-TEST--")
