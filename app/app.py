"""
IFRS 9 ECL — FastAPI Backend serving React frontend + embedded documentation.
Powered by Databricks Lakebase.
"""
import os, logging, json
from contextlib import asynccontextmanager
from decimal import Decimal
from datetime import datetime, date
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import backend

# Structured logging with consistent format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
)
log = logging.getLogger(__name__)


class _SafeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)

DecimalEncoder = _SafeEncoder


def _sanitize(obj):
    """Recursively replace NaN/Inf floats with None for JSON safety."""
    import math
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def df_to_records(df):
    records = _sanitize(df.to_dict("records"))
    return json.loads(json.dumps(records, cls=_SafeEncoder))


@asynccontextmanager
async def lifespan(app):
    log.info("Initializing Lakebase pool...")
    backend.init_pool()
    log.info("Lakebase ready.")
    yield


app = FastAPI(
    title="IFRS 9 ECL API",
    lifespan=lifespan,
    docs_url="/api/swagger",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Production middleware — order matters: outermost first
from middleware.request_id import RequestIDMiddleware
from middleware.analytics import AnalyticsMiddleware
from middleware.error_handler import ErrorHandlerMiddleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(AnalyticsMiddleware)
app.add_middleware(RequestIDMiddleware)


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    try:
        df = backend.query_df("SELECT 1 as ok")
        return {"status": "healthy", "lakebase": "connected", "rows": len(df)}
    except Exception as e:
        return {"status": "degraded", "lakebase": "error", "error": str(e)}


@app.get("/api/health/detailed")
def health_check_detailed():
    """Detailed health check — verifies Lakebase, tables, config, scipy."""
    from domain.health import run_health_check
    return run_health_check()


# ── Register route modules ───────────────────────────────────────────────────

from routes.projects import router as projects_router
from routes.data import router as data_router
from routes.models import router as models_router
from routes.satellite import router as satellite_router
from routes.attribution import router as attribution_router
from routes.gl_journals import router as gl_journals_router
from routes.jobs import router as jobs_router
from routes.simulation import router as simulation_router
from routes.markov import router as markov_router
from routes.backtesting import router as backtesting_router
from routes.hazard import router as hazard_router
from routes.setup import router as setup_router
from routes.admin import router as admin_router
from routes.rbac import router as rbac_router
from routes.reports import router as reports_router
from routes.advanced import router as advanced_router
from routes.audit import router as audit_router
from routes.data_mapping import router as data_mapping_router
from routes.period_close import router as period_close_router
from routes.analytics import router as analytics_router
from routes.project_members import router as project_members_router

app.include_router(projects_router)
app.include_router(data_router)
app.include_router(models_router)
app.include_router(satellite_router)
app.include_router(attribution_router)
app.include_router(gl_journals_router)
app.include_router(jobs_router)
app.include_router(simulation_router)
app.include_router(markov_router)
app.include_router(backtesting_router)
app.include_router(hazard_router)
app.include_router(setup_router)
app.include_router(admin_router)
app.include_router(rbac_router)
app.include_router(reports_router)
app.include_router(advanced_router)
app.include_router(audit_router)
app.include_router(data_mapping_router)
app.include_router(period_close_router)
app.include_router(analytics_router)
app.include_router(project_members_router)


# ── Serve embedded documentation at /docs ─────────────────────────────────────

# Docusaurus build output — check app/docs_site/ first (deployed with app),
# then docs/build/ (local dev), then legacy docs/ fallback
_app_dir = os.path.dirname(__file__)
_project_root = os.path.dirname(_app_dir)
_embedded_docs = os.path.join(_app_dir, "docs_site")
_docusaurus_build = os.path.join(_project_root, "docs", "build")
docs_dir = (
    _embedded_docs if os.path.isdir(_embedded_docs)
    else _docusaurus_build if os.path.isdir(_docusaurus_build)
    else os.path.join(_project_root, "docs")
)
screenshots_dir = os.path.join(_project_root, "screenshots")
eval_screenshots_dir = os.path.join(_project_root, "eval-screenshots")

if os.path.isdir(docs_dir):
    if os.path.isdir(screenshots_dir):
        app.mount("/docs/screenshots", StaticFiles(directory=screenshots_dir), name="doc-screenshots")
    if os.path.isdir(eval_screenshots_dir):
        app.mount("/docs/eval-screenshots", StaticFiles(directory=eval_screenshots_dir), name="doc-eval-screenshots")
    # Mount Docusaurus static assets (JS, CSS, images)
    _assets_dir = os.path.join(docs_dir, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/docs/assets", StaticFiles(directory=_assets_dir), name="doc-assets")
    _img_dir = os.path.join(docs_dir, "img")
    if os.path.isdir(_img_dir):
        app.mount("/docs/img", StaticFiles(directory=_img_dir), name="doc-img")

    @app.get("/docs")
    def docs_landing():
        return FileResponse(os.path.join(docs_dir, "index.html"))

    @app.get("/docs/{full_path:path}")
    def serve_docs(full_path: str):
        file_path = os.path.join(docs_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(docs_dir, "index.html"))


# ── Serve React build ────────────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # Never intercept /api/* or /docs/* routes
        if full_path.startswith("api/") or full_path.startswith("docs/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("DATABRICKS_APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
