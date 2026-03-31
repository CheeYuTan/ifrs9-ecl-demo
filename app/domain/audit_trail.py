"""
Immutable, hash-chained audit trail for IFRS 9 ECL Platform.

Every audit entry references the previous entry's hash, forming a tamper-evident
chain. Entries are INSERT-only — no UPDATE or DELETE operations are permitted.

Complies with:
  - IAS 8 (changes in accounting estimates must be disclosed)
  - SOX Section 302 (management attestation)
  - BCBS 239 (data governance and traceability)
"""
import hashlib
import json
import logging
from datetime import datetime, timezone

from db.pool import query_df, execute, SCHEMA

log = logging.getLogger(__name__)

AUDIT_TABLE = f"{SCHEMA}.audit_trail"
CONFIG_AUDIT_TABLE = f"{SCHEMA}.config_audit_log"


def ensure_audit_tables():
    execute(f"""
        CREATE TABLE IF NOT EXISTS {AUDIT_TABLE} (
            id              SERIAL PRIMARY KEY,
            project_id      TEXT,
            event_type      TEXT NOT NULL,
            entity_type     TEXT NOT NULL,
            entity_id       TEXT NOT NULL,
            action          TEXT NOT NULL,
            performed_by    TEXT NOT NULL,
            detail          JSONB DEFAULT '{{}}'::jsonb,
            previous_hash   TEXT NOT NULL,
            entry_hash      TEXT NOT NULL,
            created_at      TIMESTAMP DEFAULT NOW()
        )
    """)
    execute(f"""
        CREATE TABLE IF NOT EXISTS {CONFIG_AUDIT_TABLE} (
            id              SERIAL PRIMARY KEY,
            section         TEXT NOT NULL,
            config_key      TEXT,
            old_value       JSONB,
            new_value       JSONB,
            changed_by      TEXT NOT NULL,
            changed_at      TIMESTAMP DEFAULT NOW()
        )
    """)
    log.info("Ensured audit trail tables exist")


def _compute_hash(previous_hash: str, event_type: str, entity_id: str,
                  action: str, detail: dict, created_at: str) -> str:
    payload = json.dumps({
        "previous_hash": previous_hash,
        "event_type": event_type,
        "entity_id": entity_id,
        "action": action,
        "detail": detail,
        "created_at": created_at,
    }, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_last_hash(project_id: str | None) -> str:
    if project_id:
        df = query_df(f"""
            SELECT entry_hash FROM {AUDIT_TABLE}
            WHERE project_id = %s ORDER BY id DESC LIMIT 1
        """, (project_id,))
    else:
        df = query_df(f"""
            SELECT entry_hash FROM {AUDIT_TABLE}
            ORDER BY id DESC LIMIT 1
        """)
    if df.empty:
        return "GENESIS"
    return str(df.iloc[0]["entry_hash"])


def append_audit_entry(
    project_id: str | None,
    event_type: str,
    entity_type: str,
    entity_id: str,
    action: str,
    performed_by: str,
    detail: dict | None = None,
) -> dict:
    detail = detail or {}
    now = datetime.now(timezone.utc).isoformat()
    previous_hash = _get_last_hash(project_id)
    entry_hash = _compute_hash(previous_hash, event_type, entity_id, action, detail, now)

    execute(f"""
        INSERT INTO {AUDIT_TABLE}
            (project_id, event_type, entity_type, entity_id, action, performed_by, detail, previous_hash, entry_hash, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (project_id, event_type, entity_type, entity_id, action, performed_by,
          json.dumps(detail, default=str), previous_hash, entry_hash, now))

    return {
        "project_id": project_id,
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "performed_by": performed_by,
        "detail": detail,
        "previous_hash": previous_hash,
        "entry_hash": entry_hash,
        "created_at": now,
    }


def get_audit_trail(project_id: str) -> list[dict]:
    df = query_df(f"""
        SELECT * FROM {AUDIT_TABLE}
        WHERE project_id = %s ORDER BY id ASC
    """, (project_id,))
    if df.empty:
        return []
    records = []
    for _, row in df.iterrows():
        r = row.to_dict()
        if isinstance(r.get("detail"), str):
            r["detail"] = json.loads(r["detail"])
        records.append(r)
    return records


def verify_audit_chain(project_id: str) -> dict:
    entries = get_audit_trail(project_id)
    if not entries:
        return {"valid": True, "entries": 0, "message": "No audit entries found"}

    broken_at = None
    for i, entry in enumerate(entries):
        expected_prev = "GENESIS" if i == 0 else entries[i - 1]["entry_hash"]
        if str(entry["previous_hash"]) != str(expected_prev):
            broken_at = i
            break
        recomputed = _compute_hash(
            entry["previous_hash"], entry["event_type"],
            entry["entity_id"], entry["action"],
            entry["detail"], entry["created_at"],
        )
        if recomputed != str(entry["entry_hash"]):
            broken_at = i
            break

    if broken_at is not None:
        return {
            "valid": False,
            "entries": len(entries),
            "broken_at_index": broken_at,
            "message": f"Hash chain broken at entry {broken_at}",
        }
    return {"valid": True, "entries": len(entries), "message": "Audit chain is intact"}


def export_audit_package(project_id: str) -> dict:
    from domain.config_audit import get_config_audit_log
    trail = get_audit_trail(project_id)
    chain_status = verify_audit_chain(project_id)
    config_log = get_config_audit_log(limit=500)
    return {
        "project_id": project_id,
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "chain_verification": chain_status,
        "audit_entries": trail,
        "config_changes": config_log,
    }


# Re-export for backward compatibility
from domain.config_audit import log_config_change, get_config_audit_log, get_config_diff  # noqa: E402, F401
