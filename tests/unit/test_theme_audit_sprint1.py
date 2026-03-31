"""
Sprint 1 Theme Audit — Regression Tests (Iteration 4)

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

Scanner inventory (17 total):
  1. bg-slate-[6-9]00 without dark:
  2. bg-white/N without light pair
  3. border-white/N without light pair
  4. text-white/N without light pair
  5. hover:bg-white/N without dark:hover:
  6. hover:bg-slate-[6-9]00 without dark:hover:
  7. from-slate-[78]00 without dark:
  8. bg-[#0B0F1A] without dark:
  9. border-[tblr]-slate-800 without dark:
  10. to-slate-[6-9]00 without dark: (gradient endpoint)
  11. via-slate-[6-9]00 without dark: (gradient midpoint)
  12. focus:bg-slate-[6-9]00 without dark:focus:
  13. hover:bg-slate-50|100/N without dark:hover: (CSS overrides miss opacity)
  14. CSS scrollbar rgba(255,255,255) without .dark scope
  15. hover:bg-slate-100/200 (plain, non-opacity) without dark:hover: or CSS override
  16. hover:text-slate-[6-8]00 without dark:hover: or CSS override
  17. border/bg/ring-slate-50 without dark: pair (near-white, invisible on dark bg)
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


def find_bare_to_slate_dark(relpath: str) -> list[str]:
    """Find to-slate-[6-9]00 (gradient endpoint) without dark: prefix."""
    violations = []
    pat = re.compile(r'to-slate-[6-9]00')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if "dark:to-slate-" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_via_slate_dark(relpath: str) -> list[str]:
    """Find via-slate-[6-9]00 (gradient midpoint) without dark: prefix."""
    violations = []
    pat = re.compile(r'via-slate-[6-9]00')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if "dark:via-slate-" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_focus_bg_slate_dark(relpath: str) -> list[str]:
    """Find focus:bg-slate-[6-9]00 without dark:focus: pair."""
    violations = []
    pat = re.compile(r'focus:bg-slate-[6-9]00')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if "dark:focus:bg-slate-" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_hover_bg_slate_light_opacity(relpath: str) -> list[str]:
    """Find hover:bg-slate-50/N or hover:bg-slate-100/N without dark:hover: pair.

    CSS overrides for .dark .bg-slate-50 do NOT match hover:bg-slate-50/80
    because Tailwind generates a separate class. These light-shade hovers
    would flash bright in dark mode.
    """
    violations = []
    pat = re.compile(r'hover:bg-slate-(?:50|100)/(?:\d+|\[\d*\.?\d+\])')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if "dark:hover:bg-" not in line:
                violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_css_scrollbar_theme_issues() -> list[str]:
    """Find CSS scrollbar styles using rgba(255,255,255) not scoped under .dark.

    Scrollbar thumb/track with white rgba are invisible on light backgrounds.
    They must be scoped under .dark, with a base rule using dark rgba for light mode.
    """
    css = _read_css()
    violations = []
    for lineno, line in enumerate(css.splitlines(), start=1):
        stripped = line.strip()
        if 'scrollbar' not in stripped or 'rgba(255,255,255' not in stripped:
            continue
        # If the line itself contains .dark, it's properly scoped
        if '.dark' in stripped:
            continue
        violations.append(f"index.css:{lineno}: {stripped}")
    return violations


def find_bare_hover_bg_slate_light_plain(relpath: str) -> list[str]:
    """Find hover:bg-slate-100 or hover:bg-slate-200 (plain, no opacity) without
    dark:hover: pair on the same line.

    CSS override .dark .hover\\:bg-slate-100:hover now exists as a safety net,
    but files should still have explicit dark:hover: pairs for clarity.
    This scanner checks for files that rely ONLY on the CSS safety net
    without having an explicit dark:hover: pair — acceptable but flagged.
    """
    violations = []
    pat = re.compile(r'hover:bg-slate-(?:100|200)(?!\/)(?!\d)')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if "dark:hover:bg-" in line:
                continue
            violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_hover_text_slate_dark(relpath: str) -> list[str]:
    """Find hover:text-slate-[6-8]00 without dark:hover: pair on the same line.

    CSS override .dark .hover\\:text-slate-{600,700,800}:hover now exists,
    but explicit dark:hover: pairs are preferred. This scanner flags
    missing explicit pairs in Sprint 1 files.
    """
    violations = []
    pat = re.compile(r'hover:text-slate-[678]00')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if "dark:hover:text-" in line:
                continue
            violations.append(f"{relpath}:{lineno}: {m.group()}")
    return violations


def find_bare_slate_50(relpath: str) -> list[str]:
    """Find border-slate-50 / bg-slate-50 / ring-slate-50 without dark: pair.

    slate-50 (#f8fafc) is near-white — invisible as border/bg on dark backgrounds.
    Matches like `border-slate-50` that lack a `dark:border-` on the same line.
    Excludes:
      - Lines where `dark:` pair already exists (e.g. `border-slate-50 dark:border-slate-700`)
      - Opacity variants like `bg-slate-50/40` used inside `dark:bg-...` context
    """
    violations = []
    pat = re.compile(r'(?:border|bg|ring)-slate-50(?!\d|/)')
    for lineno, line in _lines(relpath):
        if _is_exception(line):
            continue
        for m in pat.finditer(line):
            col = m.start()
            before = line[max(0, col - 20):col]
            if "dark:" in before:
                continue
            if _has_dark_pair(line, m.group()):
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


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_to_slate_dark(relpath):
    """No to-slate-[6-9]00 gradient endpoint without dark: prefix."""
    violations = find_bare_to_slate_dark(relpath)
    assert violations == [], f"Bare to-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_via_slate_dark(relpath):
    """No via-slate-[6-9]00 gradient midpoint without dark: prefix."""
    violations = find_bare_via_slate_dark(relpath)
    assert violations == [], f"Bare via-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_focus_bg_slate_dark(relpath):
    """No focus:bg-slate-[6-9]00 without dark:focus: pair."""
    violations = find_bare_focus_bg_slate_dark(relpath)
    assert violations == [], f"Bare focus:bg-slate violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_hover_bg_slate_light_opacity(relpath):
    """No hover:bg-slate-50/N or hover:bg-slate-100/N without dark:hover: pair."""
    violations = find_bare_hover_bg_slate_light_opacity(relpath)
    assert violations == [], (
        f"Bare hover:bg-slate-light-opacity violations "
        f"(CSS overrides don't catch hover+opacity):\n" + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_hover_bg_slate_light_plain(relpath):
    """No hover:bg-slate-100/200 (plain) without dark:hover: pair or CSS safety net.

    Scanner #15: CSS now provides .dark .hover\\:bg-slate-100:hover override,
    so this is advisory — files relying only on CSS are functionally correct
    but ideally should have explicit pairs.
    """
    violations = find_bare_hover_bg_slate_light_plain(relpath)
    assert violations == [], (
        f"hover:bg-slate-100/200 without explicit dark:hover: pair "
        f"(CSS safety net exists but explicit pair preferred):\n"
        + "\n".join(violations)
    )


@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_no_bare_hover_text_slate_dark(relpath):
    """No hover:text-slate-[6-8]00 without dark:hover: pair or CSS safety net.

    Scanner #16: CSS now provides .dark .hover\\:text-slate-{6,7,8}00:hover,
    so files relying on CSS are functionally correct. This scanner flags
    missing explicit pairs.
    """
    violations = find_bare_hover_text_slate_dark(relpath)
    assert violations == [], (
        f"hover:text-slate-[6-8]00 without explicit dark:hover: pair "
        f"(CSS safety net exists but explicit pair preferred):\n"
        + "\n".join(violations)
    )


def test_no_css_scrollbar_white_without_dark_scope():
    """No scrollbar styles using rgba(255,255,255) outside .dark scope.

    White-rgba scrollbar thumbs are invisible on light backgrounds (white-on-white).
    Base styles should use dark rgba; .dark scope should use white rgba.
    """
    violations = find_css_scrollbar_theme_issues()
    assert violations == [], (
        f"CSS scrollbar styles with white rgba not scoped under .dark:\n"
        + "\n".join(violations)
    )


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


def test_datatable_hover_row_has_dark_pair():
    """Regression: DataTable hover:bg-slate-50/80 must have dark:hover: pair.

    BUG: hover:bg-slate-50/80 was used without dark:hover: pair.
    CSS override .dark .bg-slate-50 does NOT match hover:bg-slate-50/80.
    This caused rows to flash white-ish on hover in dark mode.
    """
    content = _read("components/DataTable.tsx")
    assert "dark:hover:bg-white/[0.04]" in content, (
        "DataTable missing dark:hover:bg-white/[0.04] pair for row hover"
    )


def test_sidebar_scrollbar_has_light_dark_css():
    """Regression: Sidebar scrollbar must have distinct light and dark thumb colors.

    BUG: Sidebar scrollbar-thumb used rgba(255,255,255,0.08) without .dark scope,
    making it invisible on the white sidebar background in light mode.
    Fix: Base uses dark rgba (rgba(0,0,0,0.12)), .dark override uses white rgba.
    """
    css = _read_css()
    # Base (light mode) scrollbar should use dark-colored thumb
    assert "sidebar-scrollbar" in css, "sidebar-scrollbar class missing from CSS"
    assert ".dark .sidebar-scrollbar" in css, (
        "Missing .dark .sidebar-scrollbar override — "
        "scrollbar thumb will be invisible in light mode"
    )


# ── CSS dark override dependency tests ────────────────────────────────────

INDEX_CSS_PATH = os.path.join(FRONTEND_SRC, "index.css")


def _read_css() -> str:
    with open(INDEX_CSS_PATH) as f:
        return f.read()


# Classes used in Sprint 1 files that rely on CSS overrides (no explicit dark: prefix).
# If these CSS overrides are removed, the files will break in dark mode.
CSS_OVERRIDE_DEPENDENCIES = [
    (".dark .bg-white", "bg-white → dark bg override"),
    (".dark .bg-slate-50", "bg-slate-50 → dark bg override"),
    (".dark .bg-slate-100", "bg-slate-100 → dark bg override"),
    (".dark .border-slate-100", "border-slate-100 → dark border override"),
    (".dark .border-slate-200", "border-slate-200 → dark border override"),
    (".dark .text-slate-800", "text-slate-800 → dark text override"),
    (".dark .text-slate-700", "text-slate-700 → dark text override"),
    (".dark .text-slate-600", "text-slate-600 → dark text override"),
    (".dark .text-slate-500", "text-slate-500 → dark text override"),
    (".dark .text-slate-400", "text-slate-400 → dark text override"),
    (".dark .text-slate-300", "text-slate-300 → dark text override"),
    # Hover state CSS safety nets (iteration 4)
    (".dark .hover\\:bg-slate-100:hover", "hover:bg-slate-100 → dark hover bg override"),
    (".dark .hover\\:text-slate-600:hover", "hover:text-slate-600 → dark hover text override"),
    (".dark .hover\\:text-slate-700:hover", "hover:text-slate-700 → dark hover text override"),
    (".dark .hover\\:text-slate-800:hover", "hover:text-slate-800 → dark hover text override"),
]


@pytest.mark.parametrize("css_selector,description", CSS_OVERRIDE_DEPENDENCIES)
def test_css_dark_override_exists(css_selector, description):
    """Verify that CSS dark overrides Sprint 1 files depend on still exist."""
    css = _read_css()
    assert css_selector in css, (
        f"Missing CSS dark override: {css_selector} ({description}). "
        f"Sprint 1 files rely on this for dark mode."
    )


# ── Structural consistency tests ──────────────────────────────────────────

BREADCRUMB_FILES = [
    "components/ThreeLevelDrillDown.tsx",
    "components/DrillDownChart.tsx",
    "components/ScenarioProductBarChart.tsx",
]


def test_breadcrumb_chevrons_consistent_color():
    """All breadcrumb chevron icons should use the same text color class."""
    colors = {}
    pat = re.compile(r'ChevronRight.*?className="([^"]*)"')
    for relpath in BREADCRUMB_FILES:
        content = _read(relpath)
        m = pat.search(content)
        if m:
            colors[relpath] = m.group(1)
    values = list(colors.values())
    if len(values) > 1:
        assert all(v == values[0] for v in values), (
            f"Inconsistent chevron colors across breadcrumb components: {colors}"
        )


CARD_HEADER_FILES = [
    "components/Card.tsx",
    "components/CollapsibleSection.tsx",
    "components/ChartTooltip.tsx",
    "components/ConfirmDialog.tsx",
]


def test_card_headers_use_dark_text_pair():
    """Card/section headers using text-slate-700 must have dark:text-slate-200."""
    for relpath in CARD_HEADER_FILES:
        content = _read(relpath)
        if "text-slate-700" in content:
            assert "dark:text-slate-200" in content, (
                f"{relpath}: uses text-slate-700 but missing dark:text-slate-200 pair"
            )


def test_datatable_gradient_has_light_dark_pair():
    """DataTable header gradient must have both light and dark gradient classes."""
    content = _read("components/DataTable.tsx")
    assert "from-slate-100" in content or "from-gray-100" in content, (
        "DataTable missing light gradient (from-slate-100 or from-gray-100)"
    )
    assert "dark:from-slate-800" in content, "DataTable missing dark:from-slate-800"
    assert "dark:to-slate-700" in content, "DataTable missing dark:to-slate-700"


def test_locked_banner_text_has_dark_pair():
    """LockedBanner heading text must have dark:text-slate-300."""
    content = _read("components/LockedBanner.tsx")
    assert "text-slate-600" in content, "LockedBanner missing text-slate-600"
    assert "dark:text-slate-300" in content, "LockedBanner missing dark:text-slate-300"


# ── File existence test ──────────────────────────────────────────────────

@pytest.mark.parametrize("relpath", ALL_SPRINT1_FILES)
def test_sprint1_file_exists(relpath):
    """All Sprint 1 files must exist."""
    fullpath = os.path.join(FRONTEND_SRC, relpath)
    assert os.path.exists(fullpath), f"Sprint 1 file missing: {relpath}"
