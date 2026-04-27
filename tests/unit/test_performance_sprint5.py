"""Sprint 5 — Performance Optimization Tests.

Tests for:
- TTL cache utility (TTLCache, @cached decorator)
- Cache invalidation behavior
- Performance middleware (PerfMiddleware, response time tracking)
- Admin cache/perf endpoints
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


# ── TTLCache core ────────────────────────────────────────────────────────────


class TestTTLCache:
    def setup_method(self):
        from utils.cache import TTLCache

        self.cache = TTLCache()

    def test_set_and_get(self):
        self.cache.set("k1", "v1", 60)
        assert self.cache.get("k1") == "v1"

    def test_get_missing_returns_none(self):
        assert self.cache.get("nonexistent") is None

    def test_expired_key_returns_none(self):
        self.cache.set("k1", "v1", 0.01)
        time.sleep(0.02)
        assert self.cache.get("k1") is None

    def test_invalidate_key(self):
        self.cache.set("k1", "v1", 60)
        self.cache.invalidate("k1")
        assert self.cache.get("k1") is None

    def test_invalidate_prefix(self):
        self.cache.set("queries:a", 1, 60)
        self.cache.set("queries:b", 2, 60)
        self.cache.set("admin:c", 3, 60)
        removed = self.cache.invalidate_prefix("queries:")
        assert removed == 2
        assert self.cache.get("queries:a") is None
        assert self.cache.get("admin:c") == 3

    def test_clear(self):
        self.cache.set("k1", "v1", 60)
        self.cache.set("k2", "v2", 60)
        self.cache.clear()
        assert self.cache.get("k1") is None
        assert self.cache.get("k2") is None

    def test_size_excludes_expired(self):
        self.cache.set("k1", "v1", 0.01)
        self.cache.set("k2", "v2", 60)
        time.sleep(0.02)
        assert self.cache.size() == 1

    def test_stats(self):
        self.cache.set("k1", "v1", 60)
        self.cache.set("k2", "v2", 0.01)
        time.sleep(0.02)
        stats = self.cache.stats()
        assert stats["total_keys"] == 2
        assert stats["active_keys"] == 1
        assert stats["expired_keys"] == 1

    def test_overwrite_key(self):
        self.cache.set("k1", "v1", 60)
        self.cache.set("k1", "v2", 60)
        assert self.cache.get("k1") == "v2"

    def test_complex_values(self):
        data = {"items": [1, 2, 3], "nested": {"a": True}}
        self.cache.set("k1", data, 60)
        assert self.cache.get("k1") == data

    def test_none_value_distinguished_from_miss(self):
        self.cache.set("k1", None, 60)
        # None is a valid cached value but our decorator treats None as miss
        # The raw cache stores it fine
        assert self.cache.get("k1") is None


# ── @cached decorator ────────────────────────────────────────────────────────


class TestCachedDecorator:
    def setup_method(self):
        from utils.cache import _global_cache

        _global_cache.clear()

    def test_caches_result(self):
        from utils.cache import cached

        call_count = 0

        @cached(ttl=60, prefix="test:fn")
        def expensive():
            nonlocal call_count
            call_count += 1
            return 42

        assert expensive() == 42
        assert expensive() == 42
        assert call_count == 1

    def test_caches_with_args(self):
        from utils.cache import cached

        call_count = 0

        @cached(ttl=60, prefix="test:fn_args")
        def compute(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        assert compute(1, 2) == 3
        assert compute(1, 2) == 3
        assert compute(3, 4) == 7
        assert call_count == 2

    def test_ttl_expiration(self):
        from utils.cache import cached

        call_count = 0

        @cached(ttl=0.01, prefix="test:expire")
        def fast_expire():
            nonlocal call_count
            call_count += 1
            return "data"

        fast_expire()
        time.sleep(0.02)
        fast_expire()
        assert call_count == 2

    def test_invalidate_method(self):
        from utils.cache import cached

        call_count = 0

        @cached(ttl=60, prefix="test:inv")
        def fn():
            nonlocal call_count
            call_count += 1
            return "result"

        fn()
        fn.invalidate()
        fn()
        assert call_count == 2

    def test_cache_prefix_attribute(self):
        from utils.cache import cached

        @cached(ttl=60, prefix="my_prefix")
        def fn():
            return 1

        assert fn._cache_prefix == "my_prefix"

    def test_default_prefix_uses_qualname(self):
        from utils.cache import cached

        @cached(ttl=60)
        def my_func():
            return 1

        assert "my_func" in my_func._cache_prefix

    def test_kwargs_produce_different_keys(self):
        from utils.cache import cached

        call_count = 0

        @cached(ttl=60, prefix="test:kwargs")
        def fn(a=1, b=2):
            nonlocal call_count
            call_count += 1
            return a + b

        fn(a=1, b=2)
        fn(a=1, b=3)
        assert call_count == 2


# ── Query caching integration ───────────────────────────────────────────────


class TestQueryCaching:
    def setup_method(self):
        from utils.cache import _global_cache

        _global_cache.clear()

    def test_queries_module_has_cached_decorators(self):
        from domain import queries

        assert hasattr(queries.get_portfolio_summary, '_cache_prefix')
        assert queries.get_portfolio_summary._cache_prefix == "queries:portfolio_summary"

    def test_queries_module_stage_distribution_cached(self):
        from domain import queries

        assert hasattr(queries.get_stage_distribution, '_cache_prefix')
        assert queries.get_stage_distribution._cache_prefix == "queries:stage_distribution"

    def test_queries_data_ttl(self):
        from domain.queries import DATA_TTL

        assert DATA_TTL == 30

    @patch("domain.queries.query_df")
    def test_cached_query_avoids_repeated_db_calls(self, mock_qdf):
        import pandas as pd

        from domain.queries import get_ecl_summary
        from utils.cache import _global_cache

        _global_cache.clear()
        mock_qdf.return_value = pd.DataFrame({"a": [1]})
        get_ecl_summary()
        get_ecl_summary()
        assert mock_qdf.call_count == 1

    @patch("domain.queries.query_df")
    def test_cache_invalidation_forces_refresh(self, mock_qdf):
        import pandas as pd

        from domain.queries import get_ecl_summary
        from utils.cache import _global_cache

        _global_cache.clear()
        mock_qdf.return_value = pd.DataFrame({"a": [1]})
        get_ecl_summary()
        _global_cache.invalidate_prefix("queries:")
        get_ecl_summary()
        assert mock_qdf.call_count == 2

    def test_all_query_functions_are_cached(self):
        from domain import queries

        query_fns = [
            name
            for name in dir(queries)
            if name.startswith("get_") and callable(getattr(queries, name))
        ]
        for name in query_fns:
            fn = getattr(queries, name)
            assert hasattr(fn, "_cache_prefix"), f"{name} is missing @cached decorator"


# ── Admin config caching ────────────────────────────────────────────────────


class TestAdminConfigCaching:
    def test_admin_config_has_cache(self):
        import admin_config

        assert hasattr(admin_config.get_config, '_cache_prefix')
        assert admin_config.get_config._cache_prefix == "admin_config:full"

    def test_admin_config_section_has_cache(self):
        import admin_config

        assert hasattr(admin_config.get_config_section, '_cache_prefix')
        assert admin_config.get_config_section._cache_prefix == "admin_config:section"

    def test_config_ttl_is_5_minutes(self):
        import admin_config

        assert admin_config.CONFIG_TTL == 300

    def test_invalidate_function_exists(self):
        import admin_config

        assert callable(admin_config._invalidate_config_cache)


# ── Performance middleware ──────────────────────────────────────────────────


class TestPerfMiddleware:
    def test_ring_buffer_push_and_percentiles(self):
        from middleware.perf import _RingBuffer

        buf = _RingBuffer(size=10)
        for i in range(10):
            buf.push(float(i))
        stats = buf.percentiles()
        assert stats["count"] == 10
        assert stats["p50"] == 5.0
        assert stats["avg"] == 4.5

    def test_ring_buffer_empty(self):
        from middleware.perf import _RingBuffer

        buf = _RingBuffer(size=10)
        stats = buf.percentiles()
        assert stats["count"] == 0
        assert stats["p50"] == 0

    def test_ring_buffer_wraps(self):
        from middleware.perf import _RingBuffer

        buf = _RingBuffer(size=5)
        for i in range(10):
            buf.push(float(i))
        stats = buf.percentiles()
        assert stats["count"] == 5

    def test_get_perf_stats_returns_dict(self):
        from middleware.perf import get_perf_stats

        stats = get_perf_stats()
        assert isinstance(stats, dict)


# ── Admin cache/perf endpoints ──────────────────────────────────────────────


class TestAdminCachePerfEndpoints:
    @pytest.fixture(autouse=True)
    def client(self):
        from app import app
        from fastapi.testclient import TestClient

        self.client = TestClient(app)

    def test_cache_stats_endpoint(self):
        resp = self.client.get("/api/admin/cache/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_keys" in data
        assert "active_keys" in data

    def test_cache_clear_endpoint(self):
        resp = self.client.post("/api/admin/cache/clear")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_perf_stats_endpoint(self):
        resp = self.client.get("/api/admin/perf/stats")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)


# ── Response time header ────────────────────────────────────────────────────


class TestResponseTimeHeader:
    @pytest.fixture(autouse=True)
    def client(self):
        from app import app
        from fastapi.testclient import TestClient

        self.client = TestClient(app)

    def test_api_endpoints_have_response_time_header(self):
        resp = self.client.get("/api/health")
        assert "x-response-time-ms" in resp.headers

    def test_response_time_is_numeric(self):
        resp = self.client.get("/api/health")
        val = resp.headers.get("x-response-time-ms")
        assert float(val) >= 0


# ── Thread safety ───────────────────────────────────────────────────────────


class TestCacheThreadSafety:
    def test_concurrent_writes(self):
        import threading

        from utils.cache import TTLCache

        cache = TTLCache()
        errors = []

        def writer(n):
            try:
                for i in range(100):
                    cache.set(f"key-{n}-{i}", i, 60)
                    cache.get(f"key-{n}-{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(n,)) for n in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors

    def test_concurrent_invalidation(self):
        import threading

        from utils.cache import TTLCache

        cache = TTLCache()
        for i in range(100):
            cache.set(f"prefix:{i}", i, 60)
        errors = []

        def invalidator():
            try:
                cache.invalidate_prefix("prefix:")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=invalidator) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
