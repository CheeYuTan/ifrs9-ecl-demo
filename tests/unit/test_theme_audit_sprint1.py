"""
Sprint 1 Theme Audit — Regression Tests

Verify that the 19 Sprint 1 .tsx files have no dark-mode-only Tailwind CSS
violations.  Each test reads the file source and checks for patterns that
indicate a missing light-mode pair.

Covers both numeric (bg-white/10) and bracket (bg-white/[0.06]) opacity
notations.

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

# Files where bg-white/*, border-white/*, hover:bg-white/* are in always-dark
# contexts (hero gradient, stepper on dark bg) and are NOT violations:
ALWAYS_DARK_WHITE_OPACITY_FILES = {
    "App.tsx",            # Hero stepper, project dropdown — always on dark gradient
    "components/HelpTooltip.tsx",  # Tooltip bubble — always dark bg
}


def _is_exception(line: str) -> bool:
    for exc in KNOWN_EXCEPTIONS:
        if exc in line:
            return True
    return False


def _match_is_in_dark_prefix(line: str, match_start: int) -> bool:
    """Check if match position is inside a dark: compound class (e.g. dark:hover:bg-white/)."""
    # Walk backwards from match to find the start of the class token (after space)
    i = match_start - 1
    while i >= 0 and line[i] not in (' ', '"', "'", '{', '`'):
        i -= 1
    token_start = i + 1
    prefix = line[token_start:match_start]
    return "dark:" in prefix


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
    """Find bg-white/N or bg-white/[0.N] without a light pair or dark: pair."""
    violations = []
    if relpath in ALWAYS_DARK_WHITE_OPACITY_FILES:
        return violations
    pat = re.compile(r'bg-white/(?:\d+|\[\d*\.?\d+\])')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            # Skip if inside a dark: compound prefix (e.g. dark:hover:bg-white/)
            if _match_is_in_dark_prefix(line, m.start()):
                continue
            # Has a light pair (bg-black/) or is already marked as dark variant
            if "bg-black/" in line or "dark:bg-white/" in line:
                continue
            # Has a dark:bg- pair on the same className
            if "dark:bg-" in line:
                continue
            violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_border_white(relpath: str) -> list[str]:
    """Find border-white/N or border-white/[0.N] without light pair."""
    violations = []
    if relpath in ALWAYS_DARK_WHITE_OPACITY_FILES:
        return violations
    pat = re.compile(r'border-white/(?:\d+|\[\d*\.?\d+\])')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            if _match_is_in_dark_prefix(line, m.start()):
                continue
            if "border-gray-" not in line and "dark:border-white/" not in line:
                # Also check for border-slate-200/100 as light pair
                if "border-slate-200" not in line and "border-slate-100" not in line:
                    violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_text_white_opacity(relpath: str) -> list[str]:
    """Find text-white/N or text-white/[0.N] without light pair.

    Skips files in ALWAYS_DARK_TEXT_WHITE_FILES where text-white/ is
    correct because the container is always dark (hero, tooltip).
    """
    violations = []
    if relpath in ALWAYS_DARK_TEXT_WHITE_FILES:
        return violations
    pat = re.compile(r'text-white/(?:\d+|\[\d*\.?\d+\])')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            if _match_is_in_dark_prefix(line, m.start()):
                continue
            if "text-gray-" not in line and "dark:text-white/" not in line:
                # Also check for text-slate-* as light pair
                if "text-slate-" not in line:
                    violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_hover_bg_white(relpath: str) -> list[str]:
    """Find hover:bg-white/N or hover:bg-white/[0.N] without dark:hover: pair."""
    violations = []
    if relpath in ALWAYS_DARK_WHITE_OPACITY_FILES:
        return violations
    pat = re.compile(r'hover:bg-white/(?:\d+|\[\d*\.?\d+\])')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            if _match_is_in_dark_prefix(line, m.start()):
                continue
            if "dark:hover:bg-white/" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_hover_bg_slate_dark(relpath: str) -> list[str]:
    """Find hover:bg-slate-[6-9]00 without dark:hover: pair."""
    violations = []
    pat = re.compile(r'hover:bg-slate-[6-9]00')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if "dark:hover:bg-slate-" not in line:
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


def find_bare_border_dir_slate_dark(relpath: str) -> list[str]:
    """Find border-[t|b|l|r]-slate-800 without dark: pair."""
    violations = []
    pat = re.compile(r'border-[tblr]-slate-800')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if f"dark:{m.group()}" not in line and "dark:border-" not in line:
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
def test_no_bare_hover_bg_slate_dark(relpath):
    """No hover:bg-slate-[6-9]00 without dark:hover: pair."""
    violations = find_bare_hover_bg_slate_dark(relpath)
    assert violations == [], f"Bare hover:bg-slate violations:\n" + "\n".join(violations)


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


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_border_dir_slate(relpath):
    """No border-[t|b|l|r]-slate-800 without dark: pair."""
    violations = find_bare_border_dir_slate_dark(relpath)
    assert violations == [], f"Bare border-dir-slate violations:\n" + "\n".join(violations)


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
