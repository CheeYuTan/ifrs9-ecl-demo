"""TTL cache with automatic expiration and manual invalidation."""

from __future__ import annotations

import threading
import time
from functools import wraps
from typing import Any, Callable


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL expiration."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]
            return len(keys)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        with self._lock:
            now = time.monotonic()
            return sum(1 for _, (__, exp) in self._store.items() if exp > now)

    def stats(self) -> dict[str, int]:
        with self._lock:
            now = time.monotonic()
            total = len(self._store)
            alive = sum(1 for _, (__, exp) in self._store.items() if exp > now)
            return {"total_keys": total, "active_keys": alive, "expired_keys": total - alive}


_global_cache = TTLCache()


def get_cache() -> TTLCache:
    return _global_cache


def cached(ttl: float, prefix: str = "") -> Callable:
    """Decorator that caches function results with a TTL (seconds).

    The cache key is built from the prefix (or function name) and all arguments.
    """

    def decorator(fn: Callable) -> Callable:
        cache_prefix = prefix or fn.__qualname__

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key_parts = [cache_prefix] + [repr(a) for a in args] + [f"{k}={v!r}" for k, v in sorted(kwargs.items())]
            key = ":".join(key_parts)
            result = _global_cache.get(key)
            if result is not None:
                return result
            result = fn(*args, **kwargs)
            _global_cache.set(key, result, ttl)
            return result

        wrapper._cache_prefix = cache_prefix  # type: ignore[attr-defined]
        wrapper._cache = _global_cache  # type: ignore[attr-defined]

        def invalidate() -> int:
            return _global_cache.invalidate_prefix(cache_prefix)

        wrapper.invalidate = invalidate  # type: ignore[attr-defined]
        return wrapper

    return decorator
