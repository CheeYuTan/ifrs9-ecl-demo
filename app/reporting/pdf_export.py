"""PDF export for IFRS 9 ECL regulatory reports.

Uses fpdf2 to generate formatted PDF documents with tables, headers,
page numbers, and organization branding. Supports all 5 report types.
"""

import io
import json
import logging
from datetime import UTC
from datetime import datetime as _dt

from fpdf import FPDF

log = logging.getLogger(__name__)


def _sanitize(text):
    """Replace Unicode chars not supported by Helvetica with ASCII equivalents."""
    if not isinstance(text, str):
        return str(text)
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
        "\u2022": "*",
        "\u2003": " ",
        "\u2002": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _is_numeric(val):
    try:
        float(str(val).replace(",", "").replace("%", ""))
        return True
    except (ValueError, TypeError):
        return False


def _fmt(val, decimals=2):
    """Format a numeric value for display."""
    if val is None:
        return "-"
    try:
        num = float(val)
        if abs(num) >= 1:
            return f"{num:,.{decimals}f}"
        elif abs(num) > 0:
            return f"{num:.{max(decimals, 4)}f}"
        return "0.00"
    except (ValueError, TypeError):
        return _sanitize(str(val))


class ECLReportPDF(FPDF):
    """Custom PDF class with header/footer for ECL regulatory reports."""

    def __init__(self, report_title="ECL Report", org_name="IFRS 9 ECL Platform"):
        super().__init__()
        self.report_title = _sanitize(report_title)
        self.org_name = _sanitize(org_name)
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, self.org_name, new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, self.report_title, new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_draw_color(100, 100, 100)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="C", new_x="LMARGIN", new_y="NEXT")
        ts = _dt.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        self.cell(0, 5, f"Generated: {ts} | Confidential", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(240, 240, 245)
        self.cell(0, 8, _sanitize(f"  {title}"), fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def add_table(self, headers, rows, col_widths=None):
        if not headers:
            return
        available = 190
        if col_widths is None:
            col_widths = [available / len(headers)] * len(headers)
        elif sum(col_widths) != available:
            scale = available / sum(col_widths)
            col_widths = [w * scale for w in col_widths]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(50, 60, 80)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, _sanitize(str(h)), border=1, fill=True, align="C")
        self.ln()

        self.set_font("Helvetica", "", 7)
        self.set_text_color(0, 0, 0)
        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                self.set_fill_color(248, 248, 252)
            else:
                self.set_fill_color(255, 255, 255)
            for i, val in enumerate(row):
                align = "R" if _is_numeric(val) else "L"
                self.cell(col_widths[i], 6, _sanitize(str(val)[:40]), border=1, fill=True, align=align)
            self.ln()
        self.ln(3)

    def add_key_value(self, label, value):
        self.set_font("Helvetica", "B", 8)
        self.cell(50, 6, _sanitize(label + ":"))
        self.set_font("Helvetica", "", 8)
        self.cell(0, 6, _sanitize(str(value)), new_x="LMARGIN", new_y="NEXT")

    def add_note(self, text):
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 5, _sanitize(text))
        self.set_text_color(0, 0, 0)
        self.ln(2)


def generate_report_pdf(report):
    """Generate a PDF for any report type. Returns PDF bytes."""
    report_type = report.get("report_type", "unknown")
    project_id = report.get("project_id", "")
    report_date = report.get("report_date", "")
    sections = report.get("sections", {})
    if isinstance(sections, str):
        sections = json.loads(sections)

    title_map = {
        "ifrs7_disclosure": "IFRS 7 Disclosure Report",
        "ecl_movement": "ECL Movement Report",
        "stage_migration": "Stage Migration Report",
        "sensitivity_analysis": "Sensitivity Analysis Report",
        "concentration_risk": "Concentration Risk Report",
    }
    title = title_map.get(report_type, f"Report: {report_type}")

    pdf = ECLReportPDF(
        report_title=f"{title} - {report_date}",
        org_name="IFRS 9 ECL Platform",
    )
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, _sanitize(title), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    pdf.add_key_value("Project ID", project_id)
    pdf.add_key_value("Reporting Date", report_date)
    pdf.add_key_value("Report Type", report_type)
    pdf.add_key_value("Generated", report.get("generated_at", "")[:19])
    pdf.add_key_value("Status", report.get("status", "draft"))
    pdf.ln(5)

    for key, section in sections.items():
        if not isinstance(section, dict):
            continue
        _render_section(pdf, key, section)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def _render_section(pdf, key, section):
    """Render a single report section."""
    title = section.get("title", key)
    data = section.get("data", [])
    error = section.get("error")

    pdf.section_title(title)

    if error:
        pdf.add_note(f"Error: {error}")
        return

    if not data:
        pdf.add_note("No data available for this section.")
        return

    summary = section.get("summary")
    if summary and isinstance(summary, dict):
        for sk, sv in summary.items():
            pdf.add_key_value(sk.replace("_", " ").title(), _fmt(sv))
        pdf.ln(2)

    note = section.get("note")
    if note:
        pdf.add_note(note)

    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        headers = list(data[0].keys())
        if len(headers) > 10:
            headers = headers[:10]
        rows = []
        for row in data[:100]:
            rows.append([_fmt(row.get(h)) for h in headers])
        display_headers = [h.replace("_", " ").title() for h in headers]
        pdf.add_table(display_headers, rows)

    if section.get("has_prior_period"):
        pdf.add_note("Prior-period comparative data included in this section.")
