"""In-memory rate limiter middleware with per-endpoint tiers for API endpoints."""

import os
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

ENDPOINT_LIMITS: dict[str, tuple[int, int]] = {
    "/api/simulate": (5, 60),
    "/api/simulate-stream": (5, 60),
    "/api/simulate-job": (5, 60),
    "/api/reports/generate": (10, 60),
    "/api/pipeline/start": (10, 60),
    "/api/backtest/run": (10, 60),
    "/api/hazard/estimate": (10, 60),
    "/api/markov/estimate": (10, 60),
}


def _match_endpoint_limit(path: str) -> tuple[int, int] | None:
    for prefix, limits in ENDPOINT_LIMITS.items():
        if path == prefix or path.startswith(prefix + "/"):
            return limits
    return None


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter scoped to API paths.

    Applies per-IP throttling only to /api/* endpoints.
    Heavy endpoints (simulation, report generation) have stricter limits.
    Static assets and documentation paths are exempt.
    Set RATE_LIMIT_DISABLED=1 to bypass (e.g. in tests).
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._disabled = os.environ.get("RATE_LIMIT_DISABLED", "").strip() in ("1", "true")

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, key: str, max_req: int, window: int) -> bool:
        now = time.monotonic()
        bucket = self._buckets[key]
        cutoff = now - window
        self._buckets[key] = [t for t in bucket if t > cutoff]
        if len(self._buckets[key]) >= max_req:
            return True
        self._buckets[key].append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        if self._disabled:
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        if path in ("/api/health", "/api/health/detailed"):
            return await call_next(request)

        client = self._client_key(request)

        endpoint_limit = _match_endpoint_limit(path)
        if endpoint_limit and request.method == "POST":
            ep_max, ep_window = endpoint_limit
            ep_key = f"{client}:{path}"
            if self._is_rate_limited(ep_key, ep_max, ep_window):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded for this endpoint. Please try again later."},
                    headers={"Retry-After": str(ep_window)},
                )

        global_key = f"{client}:global"
        if self._is_rate_limited(global_key, self.max_requests, self.window_seconds):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(self.window_seconds)},
            )
        return await call_next(request)
