"""Dedicated tests for domain/audit_trail.py — hash computation and chain verification logic."""
import hashlib
import json

import pytest

from domain.audit_trail import _compute_hash


class TestComputeHash:
    def test_returns_string(self):
        result = _compute_hash("GENESIS", "config_change", "cfg-1", "update", {}, "2025-01-01T00:00:00")
        assert isinstance(result, str)

    def test_returns_sha256_hex(self):
        result = _compute_hash("GENESIS", "config_change", "cfg-1", "update", {}, "2025-01-01T00:00:00")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        args = ("GENESIS", "config_change", "cfg-1", "update", {"key": "val"}, "2025-01-01T00:00:00")
        h1 = _compute_hash(*args)
        h2 = _compute_hash(*args)
        assert h1 == h2

    def test_different_previous_hash_gives_different_result(self):
        h1 = _compute_hash("GENESIS", "event", "e1", "create", {}, "2025-01-01")
        h2 = _compute_hash("abc123", "event", "e1", "create", {}, "2025-01-01")
        assert h1 != h2

    def test_different_event_type_gives_different_result(self):
        h1 = _compute_hash("GENESIS", "config_change", "e1", "create", {}, "2025-01-01")
        h2 = _compute_hash("GENESIS", "simulation_run", "e1", "create", {}, "2025-01-01")
        assert h1 != h2

    def test_different_entity_id_gives_different_result(self):
        h1 = _compute_hash("GENESIS", "event", "e1", "create", {}, "2025-01-01")
        h2 = _compute_hash("GENESIS", "event", "e2", "create", {}, "2025-01-01")
        assert h1 != h2

    def test_different_action_gives_different_result(self):
        h1 = _compute_hash("GENESIS", "event", "e1", "create", {}, "2025-01-01")
        h2 = _compute_hash("GENESIS", "event", "e1", "delete", {}, "2025-01-01")
        assert h1 != h2

    def test_different_detail_gives_different_result(self):
        h1 = _compute_hash("GENESIS", "event", "e1", "create", {"a": 1}, "2025-01-01")
        h2 = _compute_hash("GENESIS", "event", "e1", "create", {"a": 2}, "2025-01-01")
        assert h1 != h2

    def test_different_timestamp_gives_different_result(self):
        h1 = _compute_hash("GENESIS", "event", "e1", "create", {}, "2025-01-01")
        h2 = _compute_hash("GENESIS", "event", "e1", "create", {}, "2025-06-15")
        assert h1 != h2

    def test_empty_detail(self):
        result = _compute_hash("GENESIS", "event", "e1", "create", {}, "2025-01-01")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_complex_detail(self):
        detail = {
            "old_value": {"lgd": 0.45, "product": "mortgage"},
            "new_value": {"lgd": 0.50, "product": "mortgage"},
            "changed_by": "admin",
            "fields_changed": ["lgd"],
        }
        result = _compute_hash("prev_hash", "config_change", "cfg-1", "update", detail, "2025-01-01T12:00:00")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_matches_manual_sha256(self):
        prev_hash = "GENESIS"
        event_type = "test"
        entity_id = "e1"
        action = "create"
        detail = {}
        created_at = "2025-01-01"
        payload = json.dumps(
            {
                "previous_hash": prev_hash,
                "event_type": event_type,
                "entity_id": entity_id,
                "action": action,
                "detail": detail,
                "created_at": created_at,
            },
            sort_keys=True,
            default=str,
        )
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        result = _compute_hash(prev_hash, event_type, entity_id, action, detail, created_at)
        assert result == expected

    def test_chain_linkage(self):
        h1 = _compute_hash("GENESIS", "event", "e1", "create", {}, "2025-01-01")
        h2 = _compute_hash(h1, "event", "e2", "create", {}, "2025-01-02")
        h3 = _compute_hash(h2, "event", "e3", "create", {}, "2025-01-03")
        assert h1 != h2 != h3
        assert len(h1) == len(h2) == len(h3) == 64

    def test_genesis_previous_hash(self):
        result = _compute_hash("GENESIS", "event", "e1", "create", {}, "2025-01-01")
        assert result is not None

    def test_unicode_in_detail(self):
        detail = {"note": "LGD updated for résumé portfolio — €50M exposure"}
        result = _compute_hash("GENESIS", "event", "e1", "update", detail, "2025-01-01")
        assert isinstance(result, str) and len(result) == 64

    def test_numeric_values_in_detail(self):
        detail = {"old_lgd": 0.45, "new_lgd": 0.50, "loan_count": 1000}
        result = _compute_hash("GENESIS", "config_change", "lgd", "update", detail, "2025-06-15")
        assert isinstance(result, str) and len(result) == 64

    def test_nested_detail(self):
        detail = {"scenarios": {"base": {"pd_mult": 1.0}, "adverse": {"pd_mult": 2.0}}}
        result = _compute_hash("GENESIS", "sim_run", "sim-1", "execute", detail, "2025-03-01")
        assert isinstance(result, str) and len(result) == 64

    def test_detail_key_order_independent(self):
        d1 = {"a": 1, "b": 2, "c": 3}
        d2 = {"c": 3, "a": 1, "b": 2}
        h1 = _compute_hash("GENESIS", "event", "e1", "create", d1, "2025-01-01")
        h2 = _compute_hash("GENESIS", "event", "e1", "create", d2, "2025-01-01")
        assert h1 == h2

    def test_long_chain(self):
        prev = "GENESIS"
        for i in range(20):
            prev = _compute_hash(prev, "event", f"e{i}", "create", {"step": i}, f"2025-01-{i+1:02d}")
        assert isinstance(prev, str) and len(prev) == 64
