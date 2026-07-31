#!/usr/bin/env python3
"""
Validate the static site in site/ before it is deployed.

Runs identically in CI and locally:
    python3 scripts/validate_site.py

Exits non-zero on any failure so a broken page cannot reach production.
"""

from __future__ import annotations

import html.parser
import json
import pathlib
import re
import sys
import xml.dom.minidom

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}

REQUIRED = ["index.html", "404.html", "robots.txt", "sitemap.xml", "_headers"]

# Meta that must be present on every indexable page.
REQUIRED_META = [
    ('lang="en"', "lang attribute"),
    ("<title>", "title"),
    ('name="viewport"', "viewport"),
    ("prefers-color-scheme: dark", "dark theme"),
    ('data-theme="dark"', "theme override"),
]

# Landing page carries the SEO surface that the 404 deliberately does not.
INDEX_ONLY_META = [
    ('rel="canonical"', "canonical"),
    ('name="description"', "meta description"),
    ('property="og:title"', "og:title"),
    ("application/ld+json", "structured data"),
]

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


class TagBalance(html.parser.HTMLParser):
    """Catches unclosed and mismatched tags — the failure mode that renders
    fine locally and collapses in another browser."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}>")
        elif self.stack[-1] != tag:
            self.errors.append(f"</{tag}> closes <{self.stack[-1]}>")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def check_required_files() -> None:
    for name in REQUIRED:
        if (SITE / name).is_file():
            ok(f"present: {name}")
        else:
            fail(f"missing required file: site/{name}")


def check_html() -> None:
    pages = sorted(SITE.glob("*.html"))
    if not pages:
        fail("no HTML pages found in site/")
        return
    for page in pages:
        src = page.read_text(encoding="utf-8")
        parser = TagBalance()
        parser.feed(src)
        parser.close()
        problems = parser.errors + ([f"unclosed: {parser.stack}"] if parser.stack else [])
        if problems:
            for p in problems:
                fail(f"{page.name}: {p}")
        else:
            ok(f"{page.name}: tags balanced ({len(src):,} bytes)")

        for needle, label in REQUIRED_META:
            if needle in src:
                ok(f"{page.name}: {label}")
            else:
                fail(f"{page.name}: missing {label}")


def check_index_meta() -> None:
    src = (SITE / "index.html").read_text(encoding="utf-8")
    for needle, label in INDEX_ONLY_META:
        if needle in src:
            ok(f"index.html: {label}")
        else:
            fail(f"index.html: missing {label}")

    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try:
            json.loads(block)
            ok("index.html: JSON-LD parses")
        except json.JSONDecodeError as exc:
            fail(f"index.html: JSON-LD invalid — {exc}")


def check_sitemap() -> None:
    path = SITE / "sitemap.xml"
    try:
        xml.dom.minidom.parseString(path.read_text(encoding="utf-8"))
        ok("sitemap.xml: valid XML")
    except Exception as exc:
        fail(f"sitemap.xml: invalid — {exc}")
        return
    if "https://bountycharts.com/" in path.read_text(encoding="utf-8"):
        ok("sitemap.xml: canonical host")
    else:
        fail("sitemap.xml: does not reference the canonical host")


# <link> rel values that cause an actual fetch. Everything else (canonical,
# alternate, author...) is metadata and is never subject to CSP.
FETCHING_REL = {"stylesheet", "preload", "prefetch", "icon", "shortcut icon",
                "apple-touch-icon", "manifest", "modulepreload"}


def check_no_external_refs() -> None:
    """The CSP is default-src 'self'. A genuine external subresource would be
    blocked at runtime, so catch it here instead of in production.

    Only real fetches count. Anchor hrefs are navigation and <link rel=canonical>
    is metadata — neither is governed by CSP, and flagging them would train the
    reader to ignore this check."""
    for page in sorted(SITE.glob("*.html")):
        src = page.read_text(encoding="utf-8")
        bad: list[str] = []

        # src= always denotes a fetched subresource (script, img, iframe, ...).
        bad += re.findall(r'\bsrc="(https?://[^"]+)"', src)

        # href= only fetches on <link> tags carrying a fetching rel.
        for tag in re.findall(r"<link\b[^>]*>", src, re.I):
            href = re.search(r'href="(https?://[^"]+)"', tag)
            if not href:
                continue
            rel = re.search(r'rel="([^"]*)"', tag, re.I)
            rel_val = rel.group(1).strip().lower() if rel else ""
            if rel_val in FETCHING_REL:
                bad.append(href.group(1))

        if bad:
            fail(f"{page.name}: external subresource would be blocked by CSP — {bad}")
        else:
            ok(f"{page.name}: no external subresources")


def main() -> int:
    if not SITE.is_dir():
        print("FAIL  site/ directory not found")
        return 1

    print(f"Validating {SITE}\n")
    check_required_files()
    check_html()
    check_index_meta()
    check_sitemap()
    check_no_external_refs()

    print()
    if failures:
        print(f"{len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
