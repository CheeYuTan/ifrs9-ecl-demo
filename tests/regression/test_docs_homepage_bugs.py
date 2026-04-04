"""Regression tests for docs-site homepage bugs found in Sprint 1 evaluation.

BUG-S1-001: Homepage meta title used stock "Hello from" prefix
BUG-S1-002: Homepage meta description was stock placeholder
BUG-S1-003: Stock Docusaurus feature cards with dinosaur SVGs
BUG-S1-004: onBrokenLinks set to 'warn' instead of 'throw'
"""
import re
from pathlib import Path

DOCS_SITE = Path(__file__).parents[2] / "app" / "docs-site"


class TestBugS1001_HomepageTitleNoHelloFrom:
    """BUG-S1-001: title must not contain 'Hello from' stock template."""

    def test_no_hello_from_in_index_tsx(self):
        content = (DOCS_SITE / "src" / "pages" / "index.tsx").read_text()
        assert "Hello from" not in content, (
            "Homepage title still contains stock 'Hello from' prefix"
        )


class TestBugS1002_HomepageMetaDescription:
    """BUG-S1-002: meta description must not be stock placeholder."""

    def test_no_placeholder_description(self):
        content = (DOCS_SITE / "src" / "pages" / "index.tsx").read_text()
        assert "Description will go into a meta tag" not in content, (
            "Homepage still has stock Docusaurus meta description placeholder"
        )

    def test_description_mentions_ecl_or_ifrs(self):
        content = (DOCS_SITE / "src" / "pages" / "index.tsx").read_text()
        desc_match = re.search(r'description="([^"]+)"', content)
        assert desc_match, "No description prop found in Layout"
        desc = desc_match.group(1).lower()
        assert "ecl" in desc or "ifrs" in desc or "credit loss" in desc, (
            f"Description '{desc_match.group(1)}' doesn't mention ECL/IFRS 9"
        )


class TestBugS1003_NoStockFeatureCards:
    """BUG-S1-003: Homepage must not have stock Docusaurus feature cards."""

    def test_no_stock_feature_titles(self):
        content = (DOCS_SITE / "src" / "components" / "HomepageFeatures" / "index.tsx").read_text()
        for stock_title in ("Easy to Use", "Focus on What Matters", "Powered by React"):
            assert stock_title not in content, (
                f"Stock Docusaurus feature '{stock_title}' still present"
            )

    def test_no_docusaurus_svg_imports(self):
        content = (DOCS_SITE / "src" / "components" / "HomepageFeatures" / "index.tsx").read_text()
        assert "Svg" not in content or "docusaurus" not in content.lower(), (
            "Stock Docusaurus SVG illustrations still referenced"
        )

    def test_features_are_ifrs9_relevant(self):
        content = (DOCS_SITE / "src" / "components" / "HomepageFeatures" / "index.tsx").read_text()
        # At least one IFRS 9 domain term should appear in feature cards
        domain_terms = ("impairment", "ecl", "ifrs", "simulation", "regulatory", "monte carlo")
        content_lower = content.lower()
        matches = [t for t in domain_terms if t in content_lower]
        assert len(matches) >= 2, (
            f"Feature cards should reference IFRS 9 domain terms. Found: {matches}"
        )


class TestBugS1004_OnBrokenLinksThrow:
    """BUG-S1-004: onBrokenLinks must be 'throw' to catch broken links at build time."""

    def test_on_broken_links_is_throw(self):
        content = (DOCS_SITE / "docusaurus.config.ts").read_text()
        assert "onBrokenLinks: 'throw'" in content or 'onBrokenLinks: "throw"' in content, (
            "docusaurus.config.ts must have onBrokenLinks: 'throw'"
        )

    def test_on_broken_links_not_warn(self):
        content = (DOCS_SITE / "docusaurus.config.ts").read_text()
        assert "onBrokenLinks: 'warn'" not in content, (
            "onBrokenLinks should not be 'warn' — use 'throw' to fail build on broken links"
        )
