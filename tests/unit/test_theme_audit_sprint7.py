"""
Sprint 7 (Dynamic Sprint A) Theme Audit — Regression Tests

Verify that SetupWizard.tsx has no dark-mode-only Tailwind CSS violations.
Reuses the 20 scanner functions from Sprint 1.

Sprint 7 Files:
  - components/SetupWizard.tsx
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
    find_bare_border_dir_slate_dark,
    find_bare_to_slate_dark,
    find_bare_via_slate_dark,
    find_bare_focus_bg_slate_dark,
    find_bare_hover_bg_slate_light_opacity,
    find_bare_hover_bg_slate_light_plain,
    find_bare_hover_text_slate_dark,
    find_bare_slate_50,
    find_bare_text_slate_600,
    find_bare_text_slate_700,
    find_bare_text_slate_500,
    find_bare_border_slate_100,
)

ALL_SPRINT7_FILES = [
    "components/SetupWizard.tsx",
]


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_bg_slate_dark(relpath):
    violations = find_bare_bg_slate_600_plus(relpath)
    assert violations == [], f"Bare bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_bg_white_opacity(relpath):
    violations = find_bare_bg_white_opacity(relpath)
    assert violations == [], f"Bare bg-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_border_white(relpath):
    violations = find_bare_border_white(relpath)
    assert violations == [], f"Bare border-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_text_white_opacity(relpath):
    violations = find_bare_text_white_opacity(relpath)
    assert violations == [], f"Bare text-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_hover_bg_white(relpath):
    violations = find_bare_hover_bg_white(relpath)
    assert violations == [], f"Bare hover:bg-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_hover_bg_slate_dark(relpath):
    violations = find_bare_hover_bg_slate_dark(relpath)
    assert violations == [], f"Bare hover:bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_from_slate(relpath):
    violations = find_bare_from_slate(relpath)
    assert violations == [], f"Bare from-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_bg_hex(relpath):
    violations = find_bare_bg_hex(relpath)
    assert violations == [], f"Bare bg-hex violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_border_dir_slate(relpath):
    violations = find_bare_border_dir_slate_dark(relpath)
    assert violations == [], f"Bare border-dir-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_to_slate_dark(relpath):
    violations = find_bare_to_slate_dark(relpath)
    assert violations == [], f"Bare to-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_via_slate_dark(relpath):
    violations = find_bare_via_slate_dark(relpath)
    assert violations == [], f"Bare via-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_focus_bg_slate_dark(relpath):
    violations = find_bare_focus_bg_slate_dark(relpath)
    assert violations == [], f"Bare focus:bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_hover_bg_slate_light_opacity(relpath):
    violations = find_bare_hover_bg_slate_light_opacity(relpath)
    assert violations == [], (
        f"Bare hover:bg-slate-light-opacity violations:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_hover_bg_slate_light_plain(relpath):
    violations = find_bare_hover_bg_slate_light_plain(relpath)
    assert violations == [], (
        f"hover:bg-slate-100/200 without dark:hover: pair:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_hover_text_slate_dark(relpath):
    violations = find_bare_hover_text_slate_dark(relpath)
    assert violations == [], (
        f"hover:text-slate-[6-8]00 without dark:hover: pair:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_slate_50(relpath):
    violations = find_bare_slate_50(relpath)
    assert violations == [], (
        f"*-slate-50 without dark: pair:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_text_slate_600(relpath):
    """No text-slate-600 without dark:text-slate- pair."""
    violations = find_bare_text_slate_600(relpath)
    assert violations == [], (
        f"text-slate-600 without dark pair:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_text_slate_700(relpath):
    """No text-slate-700 without dark:text-slate- pair."""
    violations = find_bare_text_slate_700(relpath)
    assert violations == [], (
        f"text-slate-700 without dark pair:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_text_slate_500(relpath):
    """No text-slate-500 without dark:text-slate- pair."""
    violations = find_bare_text_slate_500(relpath)
    assert violations == [], (
        f"text-slate-500 without dark pair:\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT7_FILES)
def test_no_bare_border_slate_100(relpath):
    """No border-slate-100 without dark:border-slate- pair."""
    violations = find_bare_border_slate_100(relpath)
    assert violations == [], (
        f"border-slate-100 without dark pair:\n" + "\n".join(violations)
    )
