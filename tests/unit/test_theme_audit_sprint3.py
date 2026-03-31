"""
Sprint 3 Theme Audit — Regression Tests

Verify that the 10 Sprint 3 workflow-page-part-2 + admin .tsx files have no
dark-mode-only Tailwind CSS violations. Reuses the 15 scanner functions from
Sprint 1.

Sprint 3 Files:
  - pages/ModelRegistry.tsx
  - pages/Backtesting.tsx
  - pages/MarkovChains.tsx
  - pages/HazardModels.tsx
  - pages/AdvancedFeatures.tsx
  - pages/Attribution.tsx
  - pages/Admin.tsx
  - pages/GLJournals.tsx
  - pages/RegulatoryReports.tsx
  - pages/ApprovalWorkflow.tsx
"""
import pytest

# Reuse all scanner functions from Sprint 1
from tests.unit.test_theme_audit_sprint1 import (
    find_bare_bg_slate_600_plus,
    find_bare_bg_white_opacity,
    find_bare_border_white,
    find_bare_text_white_opacity,
    find_bare_hover_bg_white,
    find_bare_hover_bg_slate_dark,
    find_bare_from_slate,
    find_bare_bg_hex,
    find_bare_border_dir_slate_dark,
    find_bare_to_slate_dark,
    find_bare_via_slate_dark,
    find_bare_focus_bg_slate_dark,
    find_bare_hover_bg_slate_light_opacity,
    find_bare_hover_bg_slate_light_plain,
    find_bare_hover_text_slate_dark,
    find_bare_slate_50,
)

# ── Sprint 3 file manifest ──────────────────────────────────────────────

ALL_SPRINT3_FILES = [
    "pages/ModelRegistry.tsx",
    "pages/Backtesting.tsx",
    "pages/MarkovChains.tsx",
    "pages/HazardModels.tsx",
    "pages/AdvancedFeatures.tsx",
    "pages/Attribution.tsx",
    "pages/Admin.tsx",
    "pages/GLJournals.tsx",
    "pages/RegulatoryReports.tsx",
    "pages/ApprovalWorkflow.tsx",
]

# ── Tests (16 scanners × 10 files) ──────────────────────────────────────


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_bg_slate_dark(relpath):
    """No bg-slate-[6-9]00 without dark: prefix."""
    violations = find_bare_bg_slate_600_plus(relpath)
    assert violations == [], f"Bare bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_bg_white_opacity(relpath):
    """No bg-white/N without light-mode pair."""
    violations = find_bare_bg_white_opacity(relpath)
    assert violations == [], f"Bare bg-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_border_white(relpath):
    """No border-white/N without light-mode pair."""
    violations = find_bare_border_white(relpath)
    assert violations == [], f"Bare border-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_text_white_opacity(relpath):
    """No text-white/N without light-mode pair."""
    violations = find_bare_text_white_opacity(relpath)
    assert violations == [], f"Bare text-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_hover_bg_white(relpath):
    """No hover:bg-white/N without dark:hover: pair."""
    violations = find_bare_hover_bg_white(relpath)
    assert violations == [], f"Bare hover:bg-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_hover_bg_slate_dark(relpath):
    """No hover:bg-slate-[6-9]00 without dark:hover: pair."""
    violations = find_bare_hover_bg_slate_dark(relpath)
    assert violations == [], f"Bare hover:bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_from_slate(relpath):
    """No from-slate-[78]00 without dark: prefix."""
    violations = find_bare_from_slate(relpath)
    assert violations == [], f"Bare from-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_bg_hex(relpath):
    """No bg-[#0B0F1A] without dark: prefix."""
    violations = find_bare_bg_hex(relpath)
    assert violations == [], f"Bare bg-hex violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_border_dir_slate(relpath):
    """No border-[t|b|l|r]-slate-800 without dark: pair."""
    violations = find_bare_border_dir_slate_dark(relpath)
    assert violations == [], f"Bare border-dir-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_to_slate_dark(relpath):
    """No to-slate-[6-9]00 gradient endpoint without dark: prefix."""
    violations = find_bare_to_slate_dark(relpath)
    assert violations == [], f"Bare to-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_via_slate_dark(relpath):
    """No via-slate-[6-9]00 gradient midpoint without dark: prefix."""
    violations = find_bare_via_slate_dark(relpath)
    assert violations == [], f"Bare via-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_focus_bg_slate_dark(relpath):
    """No focus:bg-slate-[6-9]00 without dark:focus: pair."""
    violations = find_bare_focus_bg_slate_dark(relpath)
    assert violations == [], f"Bare focus:bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_hover_bg_slate_light_opacity(relpath):
    """No hover:bg-slate-50/N or hover:bg-slate-100/N without dark:hover: pair."""
    violations = find_bare_hover_bg_slate_light_opacity(relpath)
    assert violations == [], (
        f"Bare hover:bg-slate-light-opacity violations:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_hover_bg_slate_light_plain(relpath):
    """No hover:bg-slate-100/200 (plain) without dark:hover: pair or CSS safety net."""
    violations = find_bare_hover_bg_slate_light_plain(relpath)
    assert violations == [], (
        f"hover:bg-slate-100/200 without explicit dark:hover: pair:\n"
        + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_hover_text_slate_dark(relpath):
    """No hover:text-slate-[6-8]00 without dark:hover: pair or CSS safety net."""
    violations = find_bare_hover_text_slate_dark(relpath)
    assert violations == [], (
        f"hover:text-slate-[6-8]00 without explicit dark:hover: pair:\n"
        + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT3_FILES)
def test_no_bare_slate_50(relpath):
    """No border/bg/ring-slate-50 without dark: pair (near-white, invisible on dark bg)."""
    violations = find_bare_slate_50(relpath)
    assert violations == [], (
        f"*-slate-50 without dark: pair (BUG-S3-001 regression guard):\n"
        + "\n".join(violations)
    )
