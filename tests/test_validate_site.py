#!/usr/bin/env python3
"""Behavioural tests for the deploy gate (scripts/validate_site.py).

The gate is the only thing standing between a broken page and production, and
until now nothing tested the gate itself. These tests run it as a subprocess
against a mutated copy of site/, so they exercise the real script end to end
without importing it.

Run:
    python3 -m unittest discover -s tests -v

Standard library only, matching the rest of the repo.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "validate_site.py"
SITE = ROOT / "site"


def run_gate(mutate=None):
    """Copy site/ + the gate into a temp dir, optionally mutate, run the gate.

    Returns (exit_code, combined_output).
    """
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        shutil.copytree(SITE, work / "site")
        (work / "scripts").mkdir()
        shutil.copy(GATE, work / "scripts" / "validate_site.py")
        if mutate:
            mutate(work / "site")
        proc = subprocess.run(
            [sys.executable, "scripts/validate_site.py"],
            cwd=work, capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout + proc.stderr


def read(site: pathlib.Path, name: str) -> str:
    return (site / name).read_text(encoding="utf-8")


def write(site: pathlib.Path, name: str, text: str) -> None:
    (site / name).write_text(text, encoding="utf-8")


class GateAcceptsTheRealSite(unittest.TestCase):
    """Regression guard: the gate must stay green on the shipped site."""

    def test_unmodified_site_passes(self):
        code, out = run_gate()
        self.assertEqual(code, 0, f"gate must accept the real site:\n{out}")
        self.assertIn("All checks passed", out)


class GateCatchesMissingBoilerplate(unittest.TestCase):
    """Existing behaviour worth pinning down so a refactor cannot lose it."""

    def test_new_page_without_lang_and_viewport_is_rejected(self):
        def mutate(site):
            write(site, "pricing.html",
                  "<!doctype html><html><head><title>Pricing</title></head>"
                  "<body><h1>Pricing</h1></body></html>")
        code, out = run_gate(mutate)
        self.assertEqual(code, 1)
        self.assertIn("pricing.html: missing lang attribute", out)
        self.assertIn("pricing.html: missing viewport", out)

    def test_unbalanced_tags_are_rejected(self):
        # Dropping </footer> makes the next </div> close the wrong element; the
        # gate reports the mismatch rather than an "unclosed" stack.
        def mutate(site):
            write(site, "index.html", read(site, "index.html").replace("</footer>", ""))
        code, out = run_gate(mutate)
        self.assertEqual(code, 1)
        self.assertIn("closes <footer>", out)

    def test_truly_unclosed_tag_is_rejected(self):
        def mutate(site):
            write(site, "index.html", read(site, "index.html").replace("</body>\n</html>", ""))
        code, out = run_gate(mutate)
        self.assertEqual(code, 1)
        self.assertIn("unclosed", out)

    def test_broken_json_ld_is_rejected(self):
        def mutate(site):
            src = read(site, "index.html").replace('"@type": "WebSite",', '"@type": "WebSite",,')
            write(site, "index.html", src)
        code, out = run_gate(mutate)
        self.assertEqual(code, 1)
        self.assertIn("JSON-LD invalid", out)


class GateDetectsDarkThemeRemoval(unittest.TestCase):
    """The hole this suite exists to close.

    The gate's 'dark theme' assertion used to be a substring search over the
    whole document. index.html carries <meta name="theme-color" media="(prefers-
    color-scheme: dark)">, which satisfies that substring on its own -- so the
    entire dark-theme stylesheet could be deleted and the gate still printed
    "All checks passed", reporting success for exactly the regression it exists
    to prevent. The assertion now reads the page's CSS instead.
    """

    @staticmethod
    def _strip_dark_css(site):
        src = read(site, "index.html")
        block = re.search(r"  @media \(prefers-color-scheme: dark\) \{.*?\n  \}\n", src, re.S)
        assert block, "dark-theme CSS block not found -- test needs updating"
        write(site, "index.html", src.replace(block.group(0), ""))

    def test_deleting_the_dark_theme_css_is_rejected(self):
        code, out = run_gate(self._strip_dark_css)
        self.assertEqual(
            code, 1,
            "gate passed a site with its dark-theme CSS deleted:\n" + out)

    def test_theme_color_meta_alone_does_not_satisfy_the_dark_theme_check(self):
        """The meta tag is browser chrome colour, not a stylesheet."""
        def mutate(site):
            GateDetectsDarkThemeRemoval._strip_dark_css(site)
            # The theme-color meta tag survives and still contains the substring.
            self_src = read(site, "index.html")
            assert 'media="(prefers-color-scheme: dark)"' in self_src
        code, out = run_gate(mutate)
        self.assertEqual(code, 1)
        self.assertIn("dark theme", out)

    def test_extracting_css_to_a_stylesheet_is_allowed(self):
        """The likeliest first move of any redesign. The theming rules still
        exist -- they just live in a file now -- so the gate must not report
        them as deleted."""
        def mutate(site):
            for name in ("index.html", "404.html"):
                src = read(site, name)
                block = re.search(r"<style>(.*?)</style>", src, re.S)
                (site / "styles.css").write_text(block.group(1), encoding="utf-8")
                write(site, name,
                      src.replace(block.group(0), '<link rel="stylesheet" href="/styles.css">'))
        code, out = run_gate(mutate)
        self.assertEqual(
            code, 0,
            "moving CSS into a stylesheet must not read as deleted dark mode:\n" + out)


class GateCatchesCspBlockedSubresources(unittest.TestCase):
    """The CSP is default-src 'self'. Anything the gate misses here ships and
    is then blocked at runtime in production, where it is far more expensive
    to notice."""

    def _inject(self, snippet):
        def mutate(site):
            write(site, "index.html",
                  read(site, "index.html").replace("</head>", snippet + "</head>"))
        return mutate

    def test_double_quoted_external_script_is_caught(self):
        # Control: this one already works.
        code, out = run_gate(self._inject('<script src="https://cdn.example.com/a.js"></script>'))
        self.assertEqual(code, 1)
        self.assertIn("external subresource", out)

    def test_single_quoted_external_script_is_caught(self):
        code, out = run_gate(self._inject("<script src='https://cdn.example.com/a.js'></script>"))
        self.assertEqual(code, 1, "single-quoted src slipped past the gate:\n" + out)

    def test_protocol_relative_external_script_is_caught(self):
        code, out = run_gate(self._inject('<script src="//cdn.example.com/a.js"></script>'))
        self.assertEqual(code, 1, "protocol-relative src slipped past the gate:\n" + out)

    def test_multi_value_rel_stylesheet_is_caught(self):
        code, out = run_gate(
            self._inject('<link rel="stylesheet preload" href="https://cdn.example.com/a.css">'))
        self.assertEqual(code, 1, "multi-value rel slipped past the gate:\n" + out)

    def test_css_import_of_external_stylesheet_is_caught(self):
        def mutate(site):
            write(site, "index.html",
                  read(site, "index.html").replace(
                      "<style>", '<style>@import url("https://fonts.example.com/f.css");', 1))
        code, out = run_gate(mutate)
        self.assertEqual(code, 1, "@import slipped past the gate:\n" + out)

    def test_relative_subresource_is_not_flagged(self):
        """Same-origin assets are exactly what the CSP allows -- flagging them
        would train the reader to ignore this check."""
        def mutate(site):
            (site / "app.js").write_text("// local\n", encoding="utf-8")
            write(site, "index.html",
                  read(site, "index.html").replace("</head>", '<script src="/app.js"></script></head>'))
        code, out = run_gate(mutate)
        self.assertEqual(code, 0, "a same-origin subresource must not be flagged:\n" + out)


class SitemapIsDated(unittest.TestCase):
    """changefreq without lastmod tells a crawler how often to come back but
    never whether anything actually changed."""

    def test_sitemap_declares_lastmod(self):
        src = (SITE / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("<lastmod>", src)

    def test_lastmod_is_a_valid_iso_date(self):
        src = (SITE / "sitemap.xml").read_text(encoding="utf-8")
        found = re.findall(r"<lastmod>([^<]+)</lastmod>", src)
        self.assertTrue(found, "no <lastmod> element found")
        for value in found:
            self.assertRegex(value.strip(), r"^\d{4}-\d{2}-\d{2}$")

    def test_every_url_entry_has_a_lastmod(self):
        src = (SITE / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(
            len(re.findall(r"<url>", src)),
            len(re.findall(r"<lastmod>", src)),
            "every <url> entry needs its own <lastmod>")


class RepoDoesNotTrackBuildArtifacts(unittest.TestCase):
    """Compiled bytecode encodes the interpreter version and the source mtime,
    so it goes stale silently and differs per contributor."""

    def test_no_compiled_bytecode_is_tracked(self):
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
        offenders = [f for f in tracked if f.endswith((".pyc", ".pyo")) or "__pycache__" in f]
        self.assertEqual(offenders, [], f"build artifacts are tracked: {offenders}")


class CspDoesNotAllowInlineScript(unittest.TestCase):
    """The page ships zero executable JavaScript. The deployment doc deferred
    removing 'unsafe-inline' on the belief that some browsers evaluate JSON-LD
    against script-src; serving the real page under script-src 'none' in
    Chromium produced zero violations and left the JSON-LD parseable, so the
    allowance bought nothing."""

    @staticmethod
    def _csp():
        headers = (ROOT / "site" / "_headers").read_text(encoding="utf-8")
        match = re.search(r"Content-Security-Policy:\s*(.+)", headers)
        assert match, "no Content-Security-Policy in site/_headers"
        return match.group(1).strip()

    @staticmethod
    def _directive(csp, name):
        for part in csp.split(";"):
            tokens = part.strip().split()
            if tokens and tokens[0] == name:
                return tokens[1:]
        return []

    def test_script_src_does_not_allow_unsafe_inline(self):
        self.assertNotIn("'unsafe-inline'", self._directive(self._csp(), "script-src"))

    def test_style_src_still_allows_inline(self):
        """The page really does use inline <style>; removing this would break it."""
        self.assertIn("'unsafe-inline'", self._directive(self._csp(), "style-src"))

    def test_no_executable_script_is_served(self):
        """Guards the assumption the tightened policy rests on."""
        for page in sorted(SITE.glob("*.html")):
            with self.subTest(page=page.name):
                src = page.read_text(encoding="utf-8")
                for tag in re.findall(r"<script\b[^>]*>", src, re.I):
                    self.assertIn(
                        "application/ld+json", tag.lower(),
                        f"{page.name} serves an executable script: {tag}")


class PrintStylesheetExists(unittest.TestCase):
    """prefers-color-scheme still applies when printing, so a reader whose OS
    is in dark mode printed the dark palette as a near-black page fill."""

    def test_index_has_a_print_block_that_restores_a_light_background(self):
        css = (SITE / "index.html").read_text(encoding="utf-8")
        match = re.search(r"@media print \{(.*?)\n  \}\n", css, re.S)
        self.assertIsNotNone(match, "no @media print block")
        self.assertIn("--bg: #FFFFFF", match.group(1))

    def test_print_block_reveals_link_urls(self):
        css = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertRegex(css, r'a\[href\^="http"\]::after')
        self.assertIn("attr(href)", css)


class LandmarksArePresent(unittest.TestCase):
    """A page whose content sits in no landmark gives a screen-reader user no
    way to skip to it. 404.html already got this right; index.html did not."""

    def test_every_page_has_a_main_landmark(self):
        for page in sorted(SITE.glob("*.html")):
            with self.subTest(page=page.name):
                src = page.read_text(encoding="utf-8")
                self.assertRegex(
                    src, r"<main[\s>]",
                    f"{page.name} has no <main> landmark")


if __name__ == "__main__":
    unittest.main(verbosity=2)
