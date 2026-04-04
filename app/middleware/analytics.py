"""Analytics middleware — records API request metrics to Lakebase for operational dashboards."""
import logging
import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger(__name__)

# Paths to exclude from analytics recording
_EXCLUDED_PREFIXES = ("/assets/", "/docs/")
_EXCLUDED_EXACT = ("/api/health",)


def _should_record(path: str) -> bool:
    """Return True if the request path should be recorded."""
    if path in _EXCLUDED_EXACT:
        return False
    for prefix in _EXCLUDED_PREFIXES:
        if path.startswith(prefix):
            return False
    return True


def _extract_user_id(request: Request) -> str:
    """Extract user identity from proxy headers, falling back to 'anonymous'."""
    return (
        request.headers.get("X-Forwarded-User")
        or request.headers.get("X-User-Id")
        or "anonymous"
    )


def _fire_and_forget_record(
    user_id: str,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    request_id: str | None,
    user_agent: str | None,
) -> None:
    """Record the request in a daemon thread so we never block the response."""
    try:
        from domain.usage_analytics import record_request
        record_request(
            user_id=user_id,
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            request_id=request_id,
            user_agent=user_agent,
        )
    except Exception:
        log.exception("Failed to record analytics for %s %s", method, endpoint)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Capture API request metrics and record them asynchronously to Lakebase."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not _should_record(path):
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        user_id = _extract_user_id(request)
        request_id = getattr(request.state, "request_id", None)
        user_agent = request.headers.get("User-Agent")

        t = threading.Thread(
            target=_fire_and_forget_record,
            args=(
                user_id,
                request.method,
                path,
                response.status_code,
                duration_ms,
                request_id,
                user_agent,
            ),
            daemon=True,
        )
        t.start()

        return response
