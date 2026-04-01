"""
Sprint 8 Theme Audit — Final Regression Tests (Dynamic Sprint C)

Verify that ALL files fixed in Sprint 8 (text-slate-600/700/800 dark pair sweep
+ iteration 2: bg-slate-100, hover:bg-slate-50, border-slate-100/200 dark pairs)
have no remaining dark-mode-only Tailwind CSS violations.

Covers files across the entire codebase that had bare text-slate-600,
text-slate-700, text-slate-800, bg-slate-100, hover:bg-slate-50,
and border-slate-100/200 without dark pairs.
"""
import pytest

from tests.unit.test_theme_audit_sprint1 import (
    find_bare_bg_slate_600_plus,
    find_bare_bg_white_opacity,
    find_bare_border_white,
    find_bare_text_white_opacity,
    find_bare_hover_bg_white,
    find_bare_hover_bg_slate_dark,
    find_bare_from_slate,
    find_bare_bg_hex,
    find_bare_hover_bg_slate_light_plain,
    find_bare_hover_text_slate_dark,
    find_bare_text_slate_600,
    find_bare_text_slate_700,
    find_bare_bg_slate_100,
    find_bare_hover_bg_slate_50,
    find_bare_border_slate_100,
    find_bare_border_slate_200,
)

# All files fixed in Sprint 8 (iteration 1 + iteration 2)
ALL_SPRINT8_FILES = [
    # Components with text-slate-600 fixes
    "components/ConfirmDialog.tsx",
    "components/StepDescription.tsx",
    "components/SimulationPanel.tsx",
    "components/KpiCard.tsx",
    "components/SimulationResults.tsx",
    "components/DrillDownChart.tsx",
    "components/DataTable.tsx",
    "components/ThreeLevelDrillDown.tsx",
    "components/JobRunLink.tsx",
    "components/ScenarioProductBarChart.tsx",
    "components/ScenarioChecklist.tsx",
    "components/ApprovalForm.tsx",
    "components/EmptyState.tsx",
    "components/HelpPanel.tsx",
    "components/PageHeader.tsx",
    "components/SetupWizard.tsx",
    # Pages with text-slate-600/700/800 fixes
    "pages/SatelliteModel.tsx",
    "pages/SignOff.tsx",
    "pages/ModelExecution.tsx",
    "pages/Overlays.tsx",
    "pages/DataControl.tsx",
    "pages/DataProcessing.tsx",
    "pages/CreateProject.tsx",
    # App shell
    "App.tsx",
]

# Files specifically fixed in iteration 2 (bg-slate-100, hover:bg-slate-50,
# border-slate-100/200 dark pair sweep)
ITER2_FILES = [
    "App.tsx",
    "components/SimulationResults.tsx",
    "components/DrillDownChart.tsx",
    "components/SimulationProgress.tsx",
    "components/ThreeLevelDrillDown.tsx",
    "components/Stepper.tsx",
    "components/EmptyState.tsx",
    "components/DataTable.tsx",
    "components/ScenarioChecklist.tsx",
    "components/StatusBadge.tsx",
    "components/JobRunLink.tsx",
    "components/SimulationPanel.tsx",
    "pages/SatelliteModel.tsx",
    "pages/SignOff.tsx",
    "pages/MarkovChains.tsx",
    "pages/ApprovalWorkflow.tsx",
    "pages/CreateProject.tsx",
    "pages/DataProcessing.tsx",
    "pages/DataControl.tsx",
]


# ── Iteration 1 tests (text-slate-600/700/800) ─────────────────────────


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_text_slate_600(relpath):
    """No bare text-slate-600 without dark:text-slate- pair."""
    violations = find_bare_text_slate_600(relpath)
    assert violations == [], f"text-slate-600 without dark pair:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_text_slate_700(relpath):
    """No bare text-slate-700 without dark:text-slate- pair."""
    violations = find_bare_text_slate_700(relpath)
    assert violations == [], f"text-slate-700 without dark pair:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_bg_slate_dark(relpath):
    """No bare bg-slate-800/900 without dark: prefix."""
    violations = find_bare_bg_slate_600_plus(relpath)
    assert violations == [], f"Bare bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_bg_white_opacity(relpath):
    violations = find_bare_bg_white_opacity(relpath)
    assert violations == [], f"Bare bg-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_border_white(relpath):
    violations = find_bare_border_white(relpath)
    assert violations == [], f"Bare border-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_text_white_opacity(relpath):
    violations = find_bare_text_white_opacity(relpath)
    assert violations == [], f"Bare text-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_hover_bg_white(relpath):
    violations = find_bare_hover_bg_white(relpath)
    assert violations == [], f"Bare hover:bg-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_hover_bg_slate_dark(relpath):
    violations = find_bare_hover_bg_slate_dark(relpath)
    assert violations == [], f"Bare hover:bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_from_slate(relpath):
    violations = find_bare_from_slate(relpath)
    assert violations == [], f"Bare from-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_bg_hex(relpath):
    violations = find_bare_bg_hex(relpath)
    assert violations == [], f"Bare bg-hex violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_hover_bg_slate_light_plain(relpath):
    violations = find_bare_hover_bg_slate_light_plain(relpath)
    assert violations == [], (
        f"hover:bg-slate-100/200 without dark:hover: pair:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT8_FILES)
def test_no_bare_hover_text_slate_dark(relpath):
    violations = find_bare_hover_text_slate_dark(relpath)
    assert violations == [], (
        f"hover:text-slate-[6-8]00 without dark:hover: pair:\n" + "\n".join(violations)
    )


# ── Iteration 2 tests (bg-slate-100, hover:bg-slate-50, borders) ───────


@pytest.mark.parametrize("relpath", ITER2_FILES)
def test_iter2_no_bare_bg_slate_100(relpath):
    """No bare bg-slate-100 without dark:bg-slate- pair."""
    violations = find_bare_bg_slate_100(relpath)
    assert violations == [], f"bg-slate-100 without dark pair:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ITER2_FILES)
def test_iter2_no_bare_hover_bg_slate_50(relpath):
    """No bare hover:bg-slate-50 without dark:hover:bg- pair."""
    violations = find_bare_hover_bg_slate_50(relpath)
    assert violations == [], f"hover:bg-slate-50 without dark pair:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ITER2_FILES)
def test_iter2_no_bare_border_slate_100(relpath):
    """No bare border-slate-100 without dark:border- pair."""
    violations = find_bare_border_slate_100(relpath)
    assert violations == [], f"border-slate-100 without dark pair:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ITER2_FILES)
def test_iter2_no_bare_border_slate_200(relpath):
    """No bare border-slate-200 without dark:border- pair."""
    violations = find_bare_border_slate_200(relpath)
    assert violations == [], f"border-slate-200 without dark pair:\n" + "\n".join(violations)
