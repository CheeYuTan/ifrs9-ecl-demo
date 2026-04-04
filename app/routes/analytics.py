"""Analytics routes — /api/admin/analytics/*"""
import logging
from fastapi import APIRouter, HTTPException

from domain.usage_analytics import get_usage_stats, get_recent_requests
from db.pool import query_df, SCHEMA

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/analytics", tags=["analytics"])


def _get_project_counts() -> dict:
    """Return total and active project counts."""
    try:
        df = query_df(f"""
            SELECT
                COUNT(*)::INT AS total,
                COUNT(*) FILTER (WHERE signed_off_by IS NULL)::INT AS active
            FROM {SCHEMA}.ecl_workflow
        """)
        if df.empty:
            return {"total_projects": 0, "active_projects": 0}
        row = df.iloc[0]
        return {
            "total_projects": int(row.get("total", 0)),
            "active_projects": int(row.get("active", 0)),
        }
    except Exception:
        log.debug("ecl_workflow table may not exist yet", exc_info=True)
        return {"total_projects": 0, "active_projects": 0}


def _get_model_count() -> int:
    """Return number of active models in the registry."""
    try:
        df = query_df(f"""
            SELECT COUNT(*)::INT AS cnt
            FROM {SCHEMA}.model_registry
            WHERE status = 'active'
        """)
        return int(df.iloc[0]["cnt"]) if not df.empty else 0
    except Exception:
        return 0


@router.get("/summary")
def analytics_summary():
    """Return key platform metrics for the Admin Analytics tab."""
    try:
        usage = get_usage_stats(days=7)
        projects = _get_project_counts()
        active_models = _get_model_count()
        return {
            "total_requests_7d": usage.get("total_requests", 0),
            "unique_users_7d": usage.get("unique_users", 0),
            "avg_latency_ms": usage.get("avg_duration_ms", 0),
            "error_count_7d": usage.get("error_count", 0),
            "requests_today": usage.get("requests_today", 0),
            "total_projects": projects["total_projects"],
            "active_projects": projects["active_projects"],
            "active_models": active_models,
        }
    except Exception as e:
        log.exception("Failed to get analytics summary")
        raise HTTPException(500, f"Failed to get analytics summary: {e}")


@router.get("/recent-requests")
def analytics_recent_requests(limit: int = 50):
    """Return recent API request records."""
    try:
        return get_recent_requests(min(limit, 200))
    except Exception as e:
        raise HTTPException(500, f"Failed to get recent requests: {e}")
