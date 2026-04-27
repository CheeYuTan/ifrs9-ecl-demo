"""Dedicated tests for reporting/pdf_export.py — PDF generation, sanitization, formatting."""
import pytest

from reporting.pdf_export import (
    ECLReportPDF,
    _fmt,
    _is_numeric,
    _sanitize,
    generate_report_pdf,
)


class TestSanitize:
    def test_em_dash(self):
        assert _sanitize("test\u2014value") == "test-value"

    def test_en_dash(self):
        assert _sanitize("2020\u20132025") == "2020-2025"

    def test_smart_quotes(self):
        assert _sanitize("\u201chello\u201d") == '"hello"'

    def test_single_smart_quotes(self):
        assert _sanitize("\u2018it\u2019s\u2019") == "'it's'"

    def test_ellipsis(self):
        assert _sanitize("wait\u2026") == "wait..."

    def test_nbsp(self):
        assert _sanitize("hello\u00a0world") == "hello world"

    def test_bullet(self):
        assert _sanitize("\u2022 item") == "* item"

    def test_non_string(self):
        assert _sanitize(123) == "123"
        assert _sanitize(None) == "None"
        assert _sanitize(True) == "True"

    def test_plain_ascii(self):
        assert _sanitize("hello world") == "hello world"

    def test_empty_string(self):
        assert _sanitize("") == ""

    def test_mixed_unicode(self):
        result = _sanitize("\u201cPrice\u201d \u2014 \u20ac100")
        assert '"Price"' in result
        assert "-" in result

    def test_latin1_fallback(self):
        result = _sanitize("test\u4e16value")
        assert isinstance(result, str)


class TestIsNumeric:
    def test_integer(self):
        assert _is_numeric(42) is True

    def test_float(self):
        assert _is_numeric(3.14) is True

    def test_string_number(self):
        assert _is_numeric("123") is True

    def test_string_float(self):
        assert _is_numeric("1.5") is True

    def test_comma_formatted(self):
        assert _is_numeric("1,234,567") is True

    def test_percentage(self):
        assert _is_numeric("50%") is True

    def test_text(self):
        assert _is_numeric("hello") is False

    def test_empty_string(self):
        assert _is_numeric("") is False

    def test_none(self):
        assert _is_numeric(None) is False

    def test_negative(self):
        assert _is_numeric("-42") is True

    def test_zero(self):
        assert _is_numeric(0) is True


class TestFmt:
    def test_none_value(self):
        assert _fmt(None) == "-"

    def test_large_number(self):
        result = _fmt(1234567.89)
        assert "1,234,567.89" == result

    def test_small_number(self):
        result = _fmt(0.0012)
        assert "0.0012" in result

    def test_zero(self):
        assert _fmt(0) == "0.00"

    def test_negative(self):
        result = _fmt(-1234.5)
        assert "-1,234.50" == result

    def test_string_number(self):
        result = _fmt("42.5")
        assert "42.50" in result

    def test_non_numeric_string(self):
        result = _fmt("hello")
        assert result == "hello"

    def test_custom_decimals(self):
        result = _fmt(1234.5, decimals=0)
        assert "1,234" in result

    def test_very_small_positive(self):
        result = _fmt(0.00001)
        assert "0.0000" in result


class TestECLReportPDF:
    def test_create_instance(self):
        pdf = ECLReportPDF()
        assert pdf.report_title is not None
        assert pdf.org_name is not None

    def test_custom_title(self):
        pdf = ECLReportPDF(report_title="Test Report", org_name="Test Org")
        assert pdf.report_title == "Test Report"
        assert pdf.org_name == "Test Org"

    def test_unicode_title(self):
        pdf = ECLReportPDF(report_title="IFRS 7 \u2014 Disclosure")
        assert "-" in pdf.report_title

    def test_add_page_and_header(self):
        pdf = ECLReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        assert pdf.page_no() == 1

    def test_section_title(self):
        pdf = ECLReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.section_title("Test Section")
        assert pdf.page_no() >= 1

    def test_add_table(self):
        pdf = ECLReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.add_table(["Col A", "Col B"], [["1", "2"], ["3", "4"]])
        assert pdf.page_no() >= 1

    def test_add_table_empty_headers(self):
        pdf = ECLReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.add_table([], [])

    def test_add_table_custom_widths(self):
        pdf = ECLReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.add_table(["A", "B"], [["1", "2"]], col_widths=[100, 90])

    def test_add_key_value(self):
        pdf = ECLReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.add_key_value("Label", "Value")

    def test_add_note(self):
        pdf = ECLReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.add_note("This is a note with \u2014 unicode")


class TestGenerateReportPDF:
    def test_basic_generation(self):
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-001",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {},
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_with_sections(self):
        report = {
            "report_type": "ecl_movement",
            "project_id": "proj-002",
            "report_date": "2025-06-30",
            "generated_at": "2025-06-30T12:00:00Z",
            "status": "final",
            "sections": {
                "movement": {
                    "title": "ECL Movement",
                    "data": [
                        {"stage": "Stage 1", "opening": 100.0, "closing": 110.0},
                        {"stage": "Stage 2", "opening": 50.0, "closing": 55.0},
                    ],
                }
            },
        }
        pdf_bytes = generate_report_pdf(report)
        assert len(pdf_bytes) > 100

    def test_with_error_section(self):
        report = {
            "report_type": "sensitivity_analysis",
            "project_id": "proj-003",
            "report_date": "2025-03-31",
            "generated_at": "2025-03-31T10:00:00Z",
            "status": "draft",
            "sections": {
                "sensitivity": {
                    "title": "Sensitivity Analysis",
                    "data": [],
                    "error": "Insufficient data",
                }
            },
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_with_summary(self):
        report = {
            "report_type": "concentration_risk",
            "project_id": "proj-004",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {
                "concentration": {
                    "title": "Concentration Risk",
                    "data": [{"sector": "Real Estate", "exposure": 5000000}],
                    "summary": {"total_exposure": 10000000, "hhi_index": 0.25},
                }
            },
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_with_note_and_prior_period(self):
        report = {
            "report_type": "stage_migration",
            "project_id": "proj-005",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "final",
            "sections": {
                "migration": {
                    "title": "Stage Migration Matrix",
                    "data": [{"from": "S1", "to": "S2", "count": 50}],
                    "note": "Based on 12-month observation window",
                    "has_prior_period": True,
                }
            },
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_sections_as_json_string(self):
        import json
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-006",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": json.dumps({"test": {"title": "Test", "data": []}}),
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_unknown_report_type(self):
        report = {
            "report_type": "custom_report",
            "project_id": "proj-007",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {},
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_many_rows(self):
        rows = [{"col_a": f"val_{i}", "col_b": i * 1.5} for i in range(150)]
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-008",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {"big_table": {"title": "Large Table", "data": rows}},
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_many_columns(self):
        data = [{f"col_{i}": f"val_{i}" for i in range(15)}]
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-009",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {"wide_table": {"title": "Wide Table", "data": data}},
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_non_dict_section_skipped(self):
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-010",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {"bad_section": "not a dict", "good": {"title": "OK", "data": []}},
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_empty_data_section(self):
        report = {
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-011",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T10:00:00Z",
            "status": "draft",
            "sections": {"empty": {"title": "Empty Section", "data": []}},
        }
        pdf_bytes = generate_report_pdf(report)
        assert isinstance(pdf_bytes, bytes)

    def test_all_five_report_types(self):
        for rt in ("ifrs7_disclosure", "ecl_movement", "stage_migration", "sensitivity_analysis", "concentration_risk"):
            report = {
                "report_type": rt,
                "project_id": "proj-012",
                "report_date": "2025-12-31",
                "generated_at": "2025-12-31T10:00:00Z",
                "status": "draft",
                "sections": {},
            }
            pdf_bytes = generate_report_pdf(report)
            assert isinstance(pdf_bytes, bytes)
            assert pdf_bytes[:4] == b"%PDF"
