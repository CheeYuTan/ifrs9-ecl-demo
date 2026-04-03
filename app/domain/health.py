"""Health check module — verifies dependent services and infrastructure.

Returns structured JSON with per-service status for IT admin monitoring.
"""
import logging
from db.pool import query_df, SCHEMA, _t

log = logging.getLogger(__name__)

REQUIRED_TABLES = [
    "ecl_workflow",
    "model_ready_loans",
    "loan_level_ecl",
    "loan_ecl_weighted",
    "app_config",
]


def check_lakebase_connection() -> dict:
    """Verify Lakebase connectivity."""
    try:
        df = query_df("SELECT 1 as ok")
        return {"status": "connected", "healthy": True}
    except Exception as e:
        return {"status": "error", "healthy": False, "error": str(e)}


def check_required_tables() -> dict:
    """Verify required tables exist."""
    results = {}
    missing = []
    for table in REQUIRED_TABLES:
        try:
            full_name = _t(table)
            df = query_df(f"SELECT COUNT(*) as cnt FROM {full_name}")
            cnt = int(df.iloc[0]["cnt"]) if not df.empty else 0
            results[table] = {"exists": True, "row_count": cnt}
        except Exception:
            results[table] = {"exists": False, "row_count": 0}
            missing.append(table)
    return {
        "tables": results,
        "all_present": len(missing) == 0,
        "missing": missing,
    }


def check_config_loaded() -> dict:
    """Verify admin config is loaded."""
    try:
        import admin_config
        cfg = admin_config.get_config()
        sections = list(cfg.keys())
        return {
            "loaded": True,
            "sections": sections,
            "section_count": len(sections),
        }
    except Exception as e:
        return {"loaded": False, "error": str(e)}


def check_scipy_available() -> dict:
    """Verify scipy is importable (required for backtesting)."""
    try:
        import scipy
        return {"available": True, "version": scipy.__version__}
    except ImportError as e:
        return {"available": False, "error": str(e)}


def run_health_check() -> dict:
    """Run full health check across all services."""
    lakebase = check_lakebase_connection()
    tables = check_required_tables()
    config = check_config_loaded()
    scipy_status = check_scipy_available()

    all_healthy = (
        lakebase["healthy"]
        and tables["all_present"]
        and config["loaded"]
        and scipy_status["available"]
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": {
            "lakebase": lakebase,
            "tables": tables,
            "config": config,
            "scipy": scipy_status,
        },
    }
