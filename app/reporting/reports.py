"""Regulatory reporting module -- backward-compatible facade.

All logic now lives in focused sub-modules under reporting/.
This module re-exports every public name so that existing callers
(e.g. ``from reporting.reports import generate_ifrs7_disclosure``)
continue to work without changes.

It also re-exports low-level dependencies (query_df, execute, get_project,
get_attribution, compute_attribution, _t, _json, _dt, _tz, log) so that
test patches against ``reporting.reports.<name>`` keep working.

Sub-modules:
  report_helpers          -- shared constants and utilities
  _ifrs7_sections_a/b     -- IFRS 7 section builders (35F-36)
  ifrs7_disclosure        -- generate_ifrs7_disclosure, _get_prior_period_35h
  ecl_movement            -- generate_ecl_movement_report
  stage_migration         -- generate_stage_migration_report
  sensitivity_report      -- generate_sensitivity_report
  concentration_report    -- generate_concentration_report
  report_crud             -- list_reports, get_report, finalize_report, export_report_csv
"""

# ── Low-level deps re-exported for backward-compatible test patching ──────
import json as _json  # noqa: F401
import logging  # noqa: F401
from datetime import datetime as _dt, timezone as _tz  # noqa: F401

from db.pool import query_df, execute, _t, SCHEMA  # noqa: F401
from domain.workflow import get_project  # noqa: F401
from domain.attribution import get_attribution, compute_attribution  # noqa: F401

log = logging.getLogger(__name__)  # noqa: F811

# ── Shared helpers & constants ────────────────────────────────────────────
from reporting.report_helpers import (  # noqa: F401
    REPORT_TABLE,
    ensure_report_tables,
    _report_id,
)

# ── IFRS 7 Disclosure ────────────────────────────────────────────────────
from reporting.ifrs7_disclosure import (  # noqa: F401
    generate_ifrs7_disclosure,
    _get_prior_period_35h,
)

# ── ECL Movement ─────────────────────────────────────────────────────────
from reporting.ecl_movement import (  # noqa: F401
    generate_ecl_movement_report,
)

# ── Stage Migration ──────────────────────────────────────────────────────
from reporting.stage_migration import (  # noqa: F401
    generate_stage_migration_report,
)

# ── Sensitivity Analysis ─────────────────────────────────────────────────
from reporting.sensitivity_report import (  # noqa: F401
    generate_sensitivity_report,
)

# ── Concentration Risk ───────────────────────────────────────────────────
from reporting.concentration_report import (  # noqa: F401
    generate_concentration_report,
)

# ── Report CRUD ──────────────────────────────────────────────────────────
from reporting.report_crud import (  # noqa: F401
    list_reports,
    get_report,
    finalize_report,
    export_report_csv,
)
