"""Request ID middleware — adds a unique request ID to every request for traceability."""
import uuid
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID header to every request/response and log request timing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:12]
        start_time = time.monotonic()

        # Store on request state for access in route handlers
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.monotonic() - start_time) * 1000, 1)
            log.error(
                "request_id=%s method=%s path=%s status=500 duration_ms=%s",
                request_id, request.method, request.url.path, duration_ms,
            )
            raise

        duration_ms = round((time.monotonic() - start_time) * 1000, 1)
        response.headers["X-Request-ID"] = request_id

        # Log all non-static requests
        path = request.url.path
        if not path.startswith("/assets/") and not path.startswith("/docs/"):
            log.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%s",
                request_id, request.method, path, response.status_code, duration_ms,
            )

        return response
