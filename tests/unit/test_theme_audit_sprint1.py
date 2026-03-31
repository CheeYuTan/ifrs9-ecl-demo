"""
Sprint 1 Theme Audit — Regression Tests

Verify that the 19 Sprint 1 .tsx files have no dark-mode-only Tailwind CSS
violations.  Each test reads the file source and checks for patterns that
indicate a missing light-mode pair.

Known exceptions (intentionally always-dark):
  - Toast info variant: bg-slate-800 text-white border-slate-700
  - HelpTooltip bubble: bg-slate-800 (tooltip body)
  - HelpTooltip arrows: border-[dir]-slate-800 (paired with dark: variant)
  - text-white inside hero gradient or brand-colored buttons/badges
  - Classes already paired with a dark: prefix on the same element
"""
import os
import re
import pytest

FRONTEND_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "app", "frontend", "src"
)

# ── Sprint 1 file manifest ──────────────────────────────────────────────

BATCH_1A = ["App.tsx", "components/Sidebar.tsx", "main.tsx"]
BATCH_1B = [
    "components/DataTable.tsx",
    "components/Card.tsx",
    "components/KpiCard.tsx",
    "components/CollapsibleSection.tsx",
    "components/ThreeLevelDrillDown.tsx",
    "components/DrillDownChart.tsx",
    "components/ScenarioProductBarChart.tsx",
    "components/ChartTooltip.tsx",
]
BATCH_1C = [
    "components/Toast.tsx",
    "components/ErrorBoundary.tsx",
    "components/ErrorDisplay.tsx",
    "components/ConfirmDialog.tsx",
    "components/StatusBadge.tsx",
    "components/LockedBanner.tsx",
    "components/HelpTooltip.tsx",
    "components/HelpPanel.tsx",
]

ALL_SPRINT1_FILES = BATCH_1A + BATCH_1B + BATCH_1C

# ── Helpers ──────────────────────────────────────────────────────────────

def _read(relpath: str) -> str:
    fullpath = os.path.join(FRONTEND_SRC, relpath)
    assert os.path.exists(fullpath), f"Missing file: {relpath}"
    with open(fullpath) as f:
        return f.read()


def _lines(relpath: str) -> list[tuple[int, str]]:
    """Return (line_number, line_text) pairs."""
    return list(enumerate(_read(relpath).splitlines(), start=1))


# Known-exception line patterns (substring match):
KNOWN_EXCEPTIONS = [
    # Toast info variant — intentionally always-dark
    "info: 'bg-slate-800 text-white border-slate-700'",
    # HelpTooltip bubble body — intentionally always-dark
    "bg-slate-800 text-white",
]

# Files + patterns for always-dark contexts where text-white/* is correct:
# - App.tsx hero stepper: all text-white/ classes are on dark gradient bg
# - HelpTooltip close button: inside always-dark tooltip bubble
ALWAYS_DARK_TEXT_WHITE_FILES = {
    "App.tsx",            # Hero section and sidebar stepper — always dark gradient
    "components/HelpTooltip.tsx",  # Tooltip bubble — always dark bg
}


def _is_exception(line: str) -> bool:
    for exc in KNOWN_EXCEPTIONS:
        if exc in line:
            return True
    return False


def _has_dark_pair(line: str, pattern: str) -> bool:
    """Check if the line already contains a dark: variant for the pattern.

    Handles compound prefixes like dark:hover:bg-slate-700 — the matched
    'bg-slate-700' is already inside a dark: context.
    """
    prefix = pattern.split("-")[0]  # bg, text, border, etc.
    # Direct dark: prefix (dark:bg-slate-700)
    if f"dark:{prefix}-" in line or f"dark:{pattern}" in line:
        return True
    # Compound dark: prefix (dark:hover:bg-slate-700, dark:focus:bg-slate-700)
    if re.search(rf'dark:\w+:{re.escape(prefix)}-', line):
        return True
    return False


# ── Violation scanners ───────────────────────────────────────────────────

def find_bare_bg_slate_600_plus(relpath: str) -> list[str]:
    """Find bg-slate-[6-9]00 without dark: prefix on same line."""
    violations = []
    pat = re.compile(r'bg-slate-[6-9]00')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            # Check if preceded by 'dark:' (or dark:hover: etc) before this match
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            # Check if there's a dark: variant elsewhere on the line
            if not _has_dark_pair(line, m.group()):
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_bg_white_opacity(relpath: str) -> list[str]:
    """Find bg-white/N without a light pair (bg-black/N) or dark: pair on same line."""
    violations = []
    pat = re.compile(r'(?<!dark:)bg-white/\d+')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            # Has a light pair (bg-black/) or is already marked as dark variant
            if "bg-black/" in line or "dark:bg-white/" in line:
                continue
            # Has a dark:bg- pair on the same className (e.g., bg-white/60 dark:bg-slate-800/60)
            if "dark:bg-" in line:
                continue
            violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_border_white(relpath: str) -> list[str]:
    """Find border-white/N without light pair (border-gray-)."""
    violations = []
    pat = re.compile(r'(?<!dark:)border-white/\d+')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            if "border-gray-" not in line and "dark:border-white/" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_text_white_opacity(relpath: str) -> list[str]:
    """Find text-white/N without light pair (text-gray-).

    Skips files in ALWAYS_DARK_TEXT_WHITE_FILES where text-white/ is
    correct because the container is always dark (hero, tooltip).
    """
    violations = []
    if relpath in ALWAYS_DARK_TEXT_WHITE_FILES:
        return violations
    pat = re.compile(r'(?<!dark:)text-white/\d+')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            if "text-gray-" not in line and "dark:text-white/" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_hover_bg_white(relpath: str) -> list[str]:
    """Find hover:bg-white/N without dark:hover: pair."""
    violations = []
    pat = re.compile(r'(?<!dark:)hover:bg-white/\d+')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            if "dark:hover:bg-white/" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_from_slate(relpath: str) -> list[str]:
    """Find from-slate-[78]00 without dark: prefix."""
    violations = []
    pat = re.compile(r'from-slate-[78]00')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if "dark:from-slate-" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_bg_hex(relpath: str) -> list[str]:
    """Find bg-[#0B0F1A] without dark: prefix."""
    violations = []
    pat = re.compile(r'bg-\[#0B0F1A\]')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


# ── Tests ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_bg_slate_dark(relpath):
    """No bg-slate-[6-9]00 without dark: prefix (except known exceptions)."""
    violations = find_bare_bg_slate_600_plus(relpath)
    assert violations == [], f"Bare bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_bg_white_opacity(relpath):
    """No bg-white/N without light-mode pair."""
    violations = find_bare_bg_white_opacity(relpath)
    assert violations == [], f"Bare bg-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_border_white(relpath):
    """No border-white/N without light-mode pair."""
    violations = find_bare_border_white(relpath)
    assert violations == [], f"Bare border-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_text_white_opacity(relpath):
    """No text-white/N without light-mode pair."""
    violations = find_bare_text_white_opacity(relpath)
    assert violations == [], f"Bare text-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_hover_bg_white(relpath):
    """No hover:bg-white/N without dark:hover: pair."""
    violations = find_bare_hover_bg_white(relpath)
    assert violations == [], f"Bare hover:bg-white/ violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_from_slate(relpath):
    """No from-slate-[78]00 without dark: prefix."""
    violations = find_bare_from_slate(relpath)
    assert violations == [], f"Bare from-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_bg_hex(relpath):
    """No bg-[#0B0F1A] without dark: prefix."""
    violations = find_bare_bg_hex(relpath)
    assert violations == [], f"Bare bg-hex violations:\n" + "\n".join(violations)


# ── Specific regression tests for iteration 1 fixes ─────────────────────

def test_error_boundary_button_has_light_dark():
    """Regression: ErrorBoundary 'Try Again' button must have light+dark colors."""
    content = _read("components/ErrorBoundary.tsx")
    assert "dark:bg-slate-600" in content, "Missing dark:bg-slate-600"
    assert "bg-slate-200" in content or "bg-gray-200" in content, (
        "Missing light bg for Try Again button"
    )


def test_error_display_tech_details_has_dark_pair():
    """Regression: ErrorDisplay technical details needs dark:bg-red-900/20."""
    content = _read("components/ErrorDisplay.tsx")
    assert "dark:bg-red-900/20" in content, "Missing dark:bg-red-900/20"


def test_help_tooltip_arrows_have_dark_variants():
    """Regression: HelpTooltip arrow borders need dark: variants."""
    content = _read("components/HelpTooltip.tsx")
    assert "dark:border-t-slate-700" in content
    assert "dark:border-b-slate-700" in content
    assert "dark:border-l-slate-700" in content
    assert "dark:border-r-slate-700" in content


# ── File existence test ──────────────────────────────────────────────────

@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_sprint1_file_exists(relpath):
    """All Sprint 1 files must exist."""
    fullpath = os.path.join(FRONTEND_SRC, relpath)
    assert os.path.exists(fullpath), f"Sprint 1 file missing: {relpath}"
