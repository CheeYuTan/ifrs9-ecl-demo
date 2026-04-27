"""Response-time tracking middleware.

Records p50/p95/p99 latencies per endpoint using a fixed-size ring buffer
(no external dependencies). Stats exposed via /api/admin/perf/stats.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_BUFFER_SIZE = 200


class _RingBuffer:
    __slots__ = ("_buf", "_idx", "_full", "_lock")

    def __init__(self, size: int = _BUFFER_SIZE) -> None:
        self._buf: list[float] = [0.0] * size
        self._idx = 0
        self._full = False
        self._lock = threading.Lock()

    def push(self, value: float) -> None:
        with self._lock:
            self._buf[self._idx] = value
            self._idx = (self._idx + 1) % len(self._buf)
            if self._idx == 0:
                self._full = True

    def percentiles(self) -> dict[str, float]:
        with self._lock:
            n = len(self._buf) if self._full else self._idx
            if n == 0:
                return {"p50": 0, "p95": 0, "p99": 0, "count": 0, "avg": 0}
            vals = sorted(self._buf[:n])
            return {
                "p50": vals[int(n * 0.50)],
                "p95": vals[min(int(n * 0.95), n - 1)],
                "p99": vals[min(int(n * 0.99), n - 1)],
                "count": n,
                "avg": round(sum(vals) / n, 3),
            }


_endpoint_buffers: dict[str, _RingBuffer] = defaultdict(lambda: _RingBuffer())


def get_perf_stats() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path, buf in sorted(_endpoint_buffers.items()):
        stats = buf.percentiles()
        if stats["count"] > 0:
            result[path] = stats
    return result


class PerfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        start = time.monotonic()
        response: Response = await call_next(request)
        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        key = f"{request.method} {request.url.path}"
        _endpoint_buffers[key].push(elapsed_ms)
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        return response
