"""Regulatory report routes — /api/reports/*"""
import json, logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import backend
from routes._utils import DecimalEncoder

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


class GenerateReportRequest(BaseModel):
    report_type: str
    user: str = "system"

class FinalizeReportRequest(BaseModel):
    pass


@router.post("/generate/{project_id}")
def generate_report(project_id: str, body: GenerateReportRequest):
    try:
        generators = {
            "ifrs7_disclosure": backend.generate_ifrs7_disclosure,
            "ecl_movement": backend.generate_ecl_movement_report,
            "stage_migration": backend.generate_stage_migration_report,
            "sensitivity_analysis": backend.generate_sensitivity_report,
            "concentration_risk": backend.generate_concentration_report,
        }
        gen = generators.get(body.report_type)
        if not gen:
            raise HTTPException(400, f"Unknown report type: {body.report_type}")
        result = gen(project_id, body.user)
        return json.loads(json.dumps(result, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to generate report")
        raise HTTPException(500, f"Failed to generate report: {e}")

@router.get("")
def list_reports(project_id: Optional[str] = None, report_type: Optional[str] = None):
    try:
        reports = backend.list_reports(project_id, report_type)
        return json.loads(json.dumps(reports, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list reports: {e}")

@router.get("/{report_id}")
def get_report(report_id: str):
    try:
        report = backend.get_report(report_id)
        if not report:
            raise HTTPException(404, "Report not found")
        return json.loads(json.dumps(report, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get report: {e}")

@router.get("/{report_id}/export")
def export_report(report_id: str):
    try:
        rows = backend.export_report_csv(report_id)
        if not rows:
            raise HTTPException(404, "Report not found or empty")
        import io, csv
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        csv_content = output.getvalue()
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={report_id}.csv"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to export report: {e}")

@router.post("/{report_id}/finalize")
def finalize_report(report_id: str):
    try:
        report = backend.finalize_report(report_id)
        if not report:
            raise HTTPException(404, "Report not found")
        return json.loads(json.dumps(report, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to finalize report: {e}")

@router.get('/{report_id}/export/pdf')
def export_report_pdf(report_id: str):
    try:
        report = backend.get_report(report_id)
        if not report:
            raise HTTPException(404, 'Report not found')
        from reporting.pdf_export import generate_report_pdf
        # Build report dict with sections from report_data
        report_data = report.get('report_data', {})
        if isinstance(report_data, str):
            report_data = json.loads(report_data)
        pdf_input = {
            'report_type': report.get('report_type', report_data.get('report_type', '')),
            'project_id': report.get('project_id', report_data.get('project_id', '')),
            'report_date': report.get('report_date', report_data.get('report_date', '')),
            'sections': report_data.get('sections', {}),
            'generated_at': report_data.get('generated_at', ''),
            'status': report.get('status', 'draft'),
        }
        pdf_bytes = generate_report_pdf(pdf_input)
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename={report_id}.pdf'},
        )
    except HTTPException:
        raise
    except Exception as e:
        log.exception('Failed to export PDF')
        raise HTTPException(500, f'Failed to export PDF: {e}')

