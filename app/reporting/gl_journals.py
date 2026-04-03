import json as _json
import uuid
import logging
import pandas as pd
from datetime import datetime as _dt, timezone as _tz

from db.pool import query_df, execute, _t, SCHEMA
from domain.workflow import get_project

log = logging.getLogger(__name__)


def _migrate_gl_tables():
    """Drop old GL tables if they have the legacy schema (Sprint 1/2 stubs)."""
    try:
        cols_df = query_df(
            "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = 'gl_journal_entries'",
            (SCHEMA,),
        )
        existing = set(cols_df["column_name"].tolist()) if not cols_df.empty else set()
        if existing and "journal_id" not in existing:
            log.info("GL tables have legacy schema — dropping and recreating")
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.gl_journal_entries CASCADE")
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.gl_account_map CASCADE")
    except Exception:
        log.debug("GL migration check skipped")


def ensure_gl_tables():
    _migrate_gl_tables()
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.gl_chart_of_accounts (
            account_code TEXT PRIMARY KEY,
            account_name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            parent_account TEXT,
            is_ecl_related BOOLEAN DEFAULT TRUE
        )
    """)
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.gl_journal_entries (
            journal_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            journal_date DATE NOT NULL DEFAULT CURRENT_DATE,
            journal_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_by TEXT DEFAULT 'system',
            posted_by TEXT,
            posted_at TIMESTAMP,
            description TEXT,
            reference TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.gl_journal_lines (
            line_id TEXT PRIMARY KEY,
            journal_id TEXT NOT NULL,
            account_code TEXT NOT NULL,
            debit NUMERIC(18,2) NOT NULL DEFAULT 0,
            credit NUMERIC(18,2) NOT NULL DEFAULT 0,
            product_type TEXT,
            stage TEXT,
            description TEXT
        )
    """)
    _seed_gl_chart()
    log.info("Ensured GL tables exist")


GL_CHART_TABLE = f"{SCHEMA}.gl_chart_of_accounts"
GL_JOURNAL_TABLE = f"{SCHEMA}.gl_journal_entries"
GL_LINE_TABLE = f"{SCHEMA}.gl_journal_lines"

_GL_SEED_ACCOUNTS = [
    ("1200", "Loans and Advances", "asset", None),
    ("1210", "Stage 1 ECL Provision", "contra-asset", "1200"),
    ("1220", "Stage 2 ECL Provision", "contra-asset", "1200"),
    ("1230", "Stage 3 ECL Provision", "contra-asset", "1200"),
    ("1240", "Management Overlay Provision", "contra-asset", "1200"),
    ("4100", "ECL Impairment Charge", "expense", None),
    ("4110", "ECL Recovery Income", "income", None),
    ("4120", "Write-off Expense", "expense", None),
    ("4130", "Overlay Adjustment Expense", "expense", None),
]

_STAGE_PROVISION_ACCOUNT = {1: "1210", 2: "1220", 3: "1230"}
_ECL_EXPENSE_ACCOUNT = "4100"
_OVERLAY_PROVISION_ACCOUNT = "1240"
_OVERLAY_EXPENSE_ACCOUNT = "4130"
_WRITEOFF_EXPENSE_ACCOUNT = "4120"


def _seed_gl_chart():
    """Insert standard IFRS 9 ECL GL accounts if chart is empty."""
    df = query_df(f"SELECT COUNT(*) as cnt FROM {GL_CHART_TABLE}")
    if not df.empty and int(df.iloc[0]["cnt"]) > 0:
        return
    for code, name, atype, parent in _GL_SEED_ACCOUNTS:
        execute(f"""
            INSERT INTO {GL_CHART_TABLE} (account_code, account_name, account_type, parent_account, is_ecl_related)
            VALUES (%s, %s, %s, %s, TRUE)
            ON CONFLICT (account_code) DO NOTHING
        """, (code, name, atype, parent))
    log.info("Seeded GL chart of accounts with %d IFRS 9 accounts", len(_GL_SEED_ACCOUNTS))


def get_gl_chart() -> list[dict]:
    df = query_df(f"SELECT * FROM {GL_CHART_TABLE} ORDER BY account_code")
    return df.to_dict("records") if not df.empty else []


def generate_ecl_journals(project_id: str, user: str = "system") -> dict:
    """Auto-generate balanced journal entries from ECL data for a project."""
    proj = get_project(project_id)
    if not proj:
        raise ValueError(f"Project {project_id} not found")

    journal_id = f"JE-{project_id}-{_dt.now(_tz.utc).strftime('%Y%m%d%H%M%S')}"
    journal_date = proj.get("reporting_date") or _dt.now(_tz.utc).strftime("%Y-%m-%d")

    execute(f"""
        INSERT INTO {GL_JOURNAL_TABLE}
            (journal_id, project_id, journal_date, journal_type, status, created_by, description, reference)
        VALUES (%s, %s, %s, 'ecl_provision', 'draft', %s, %s, %s)
    """, (journal_id, project_id, journal_date, user,
          f"ECL provision journals for project {project_id}",
          f"AUTO-{project_id}"))

    lines = []
    total_debit = 0.0
    total_credit = 0.0

    # 1. ECL provision by product/stage
    try:
        ecl_df = query_df(f"""
            SELECT product_type, assessed_stage,
                   ROUND(SUM(total_ecl)::numeric, 2) as total_ecl
            FROM {_t('portfolio_ecl_summary')}
            GROUP BY product_type, assessed_stage
            ORDER BY product_type, assessed_stage
        """)
        for _, row in ecl_df.iterrows():
            ecl_amt = float(row["total_ecl"] or 0)
            if ecl_amt <= 0:
                continue
            stage = int(row["assessed_stage"])
            product = str(row["product_type"])
            provision_acct = _STAGE_PROVISION_ACCOUNT.get(stage, "1230")

            line_id_dr = str(uuid.uuid4())
            line_id_cr = str(uuid.uuid4())
            lines.append((line_id_dr, journal_id, _ECL_EXPENSE_ACCOUNT, ecl_amt, 0,
                          product, str(stage), f"ECL charge - {product} Stage {stage}"))
            lines.append((line_id_cr, journal_id, provision_acct, 0, ecl_amt,
                          product, str(stage), f"ECL provision - {product} Stage {stage}"))
            total_debit += ecl_amt
            total_credit += ecl_amt
    except Exception as e:
        log.warning("Could not generate ECL provision lines: %s", e)

    # 2. Management overlays
    overlays_list = proj.get("overlays") or []
    if isinstance(overlays_list, str):
        try:
            overlays_list = _json.loads(overlays_list)
        except Exception:
            overlays_list = []

    for o in overlays_list:
        amt = abs(float(o.get("amount", 0) or 0))
        if amt <= 0:
            continue
        product = o.get("product", "All")
        line_id_dr = str(uuid.uuid4())
        line_id_cr = str(uuid.uuid4())
        lines.append((line_id_dr, journal_id, _OVERLAY_EXPENSE_ACCOUNT, amt, 0,
                      product, "", f"Overlay: {o.get('reason', 'Management overlay')}"))
        lines.append((line_id_cr, journal_id, _OVERLAY_PROVISION_ACCOUNT, 0, amt,
                      product, "", f"Overlay provision: {o.get('reason', 'Management overlay')}"))
        total_debit += amt
        total_credit += amt

    # 3. Write-offs (Stage 3 loans with 180+ DPD)
    try:
        wo_df = query_df(f"""
            SELECT l.product_type,
                   ROUND(SUM(e.weighted_ecl)::numeric, 2) as wo_ecl
            FROM {_t('model_ready_loans')} l
            JOIN {_t('loan_ecl_weighted')} e ON l.loan_id = e.loan_id
            WHERE l.days_past_due >= 180 AND l.assessed_stage = 3
            GROUP BY l.product_type
        """)
        for _, row in wo_df.iterrows():
            wo_amt = abs(float(row["wo_ecl"] or 0)) * 0.15
            if wo_amt <= 0:
                continue
            product = str(row["product_type"])
            wo_journal_id = f"JE-WO-{project_id}-{_dt.now(_tz.utc).strftime('%Y%m%d%H%M%S')}"

            execute(f"""
                INSERT INTO {GL_JOURNAL_TABLE}
                    (journal_id, project_id, journal_date, journal_type, status, created_by, description, reference)
                VALUES (%s, %s, %s, 'write_off', 'draft', %s, %s, %s)
                ON CONFLICT (journal_id) DO NOTHING
            """, (wo_journal_id, project_id, journal_date, user,
                  f"Write-off entries for {product}", f"WO-{project_id}"))

            line_id_dr = str(uuid.uuid4())
            line_id_cr = str(uuid.uuid4())
            execute(f"""
                INSERT INTO {GL_LINE_TABLE} (line_id, journal_id, account_code, debit, credit, product_type, stage, description)
                VALUES (%s, %s, %s, %s, 0, %s, '3', %s)
            """, (line_id_dr, wo_journal_id, _WRITEOFF_EXPENSE_ACCOUNT, wo_amt, product, f"Write-off - {product}"))
            execute(f"""
                INSERT INTO {GL_LINE_TABLE} (line_id, journal_id, account_code, debit, credit, product_type, stage, description)
                VALUES (%s, %s, %s, 0, %s, %s, '3', %s)
            """, (line_id_cr, wo_journal_id, _STAGE_PROVISION_ACCOUNT[3], wo_amt, product, f"Write-off release - {product}"))
    except Exception as e:
        log.warning("Could not generate write-off lines: %s", e)

    # Insert all main journal lines
    for line in lines:
        execute(f"""
            INSERT INTO {GL_LINE_TABLE}
                (line_id, journal_id, account_code, debit, credit, product_type, stage, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, line)

    return get_journal(journal_id)


def list_journals(project_id: str) -> list[dict]:
    df = query_df(f"""
        SELECT j.journal_id, j.project_id, j.journal_date, j.journal_type,
               j.status, j.created_by, j.posted_by, j.posted_at,
               j.description, j.reference, j.created_at,
               COALESCE(SUM(l.debit), 0) as total_debit,
               COALESCE(SUM(l.credit), 0) as total_credit,
               COUNT(l.line_id) as line_count
        FROM {GL_JOURNAL_TABLE} j
        LEFT JOIN {GL_LINE_TABLE} l ON j.journal_id = l.journal_id
        WHERE j.project_id = %s
        GROUP BY j.journal_id, j.project_id, j.journal_date, j.journal_type,
                 j.status, j.created_by, j.posted_by, j.posted_at,
                 j.description, j.reference, j.created_at
        ORDER BY j.created_at DESC
    """, (project_id,))
    if df.empty:
        return []
    records = df.to_dict("records")
    for r in records:
        r["balanced"] = abs(float(r.get("total_debit", 0)) - float(r.get("total_credit", 0))) < 0.01
    return records


def get_journal(journal_id: str) -> dict | None:
    df = query_df(f"SELECT * FROM {GL_JOURNAL_TABLE} WHERE journal_id = %s", (journal_id,))
    if df.empty:
        return None
    journal = df.iloc[0].to_dict()

    lines_df = query_df(f"""
        SELECT l.*, c.account_name, c.account_type
        FROM {GL_LINE_TABLE} l
        LEFT JOIN {GL_CHART_TABLE} c ON l.account_code = c.account_code
        WHERE l.journal_id = %s
        ORDER BY l.debit DESC, l.account_code
    """, (journal_id,))
    journal["lines"] = lines_df.to_dict("records") if not lines_df.empty else []

    total_dr = sum(float(l.get("debit", 0)) for l in journal["lines"])
    total_cr = sum(float(l.get("credit", 0)) for l in journal["lines"])
    journal["total_debit"] = round(total_dr, 2)
    journal["total_credit"] = round(total_cr, 2)
    journal["balanced"] = abs(total_dr - total_cr) < 0.01
    return journal


def post_journal(journal_id: str, user: str) -> dict:
    journal = get_journal(journal_id)
    if not journal:
        raise ValueError(f"Journal {journal_id} not found")
    if journal["status"] != "draft":
        raise ValueError(f"Only draft journals can be posted (current: {journal['status']})")
    if not journal["balanced"]:
        raise ValueError("Journal does not balance — cannot post")

    execute(f"""
        UPDATE {GL_JOURNAL_TABLE}
        SET status = 'posted', posted_by = %s, posted_at = NOW()
        WHERE journal_id = %s
    """, (user, journal_id))
    return get_journal(journal_id)


def reverse_journal(journal_id: str, user: str, reason: str = "") -> dict:
    journal = get_journal(journal_id)
    if not journal:
        raise ValueError(f"Journal {journal_id} not found")
    if journal["status"] != "posted":
        raise ValueError(f"Only posted journals can be reversed (current: {journal['status']})")

    execute(f"""
        UPDATE {GL_JOURNAL_TABLE} SET status = 'reversed' WHERE journal_id = %s
    """, (journal_id,))

    rev_id = f"REV-{journal_id}"
    execute(f"""
        INSERT INTO {GL_JOURNAL_TABLE}
            (journal_id, project_id, journal_date, journal_type, status, created_by, description, reference)
        VALUES (%s, %s, CURRENT_DATE, %s, 'posted', %s, %s, %s)
    """, (rev_id, journal["project_id"], journal["journal_type"], user,
          f"Reversal of {journal_id}: {reason}", f"REV-{journal_id}"))

    for line in journal.get("lines", []):
        execute(f"""
            INSERT INTO {GL_LINE_TABLE}
                (line_id, journal_id, account_code, debit, credit, product_type, stage, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()), rev_id, line["account_code"],
              float(line.get("credit", 0)), float(line.get("debit", 0)),
              line.get("product_type"), line.get("stage"),
              f"Reversal: {line.get('description', '')}"))

    return get_journal(rev_id)


def get_gl_trial_balance(project_id: str) -> list[dict]:
    df = query_df(f"""
        SELECT l.account_code, c.account_name, c.account_type,
               ROUND(SUM(l.debit)::numeric, 2) as total_debit,
               ROUND(SUM(l.credit)::numeric, 2) as total_credit,
               ROUND((SUM(l.debit) - SUM(l.credit))::numeric, 2) as balance
        FROM {GL_LINE_TABLE} l
        JOIN {GL_JOURNAL_TABLE} j ON l.journal_id = j.journal_id
        LEFT JOIN {GL_CHART_TABLE} c ON l.account_code = c.account_code
        WHERE j.project_id = %s AND j.status = 'posted'
        GROUP BY l.account_code, c.account_name, c.account_type
        HAVING SUM(l.debit) != 0 OR SUM(l.credit) != 0
        ORDER BY l.account_code
    """, (project_id,))
    return df.to_dict("records") if not df.empty else []
