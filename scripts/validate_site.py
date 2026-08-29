#!/usr/bin/env python3
"""
Validate the static site in site/ before it is deployed.

Runs identically in CI and locally:
    python3 scripts/validate_site.py

Exits non-zero on any failure so a broken page cannot reach production.
"""

from __future__ import annotations

import hashlib
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

# Markup that must be present on every indexable page. These are genuinely
# document-level facts, so a substring search over the HTML is the right test.
REQUIRED_META = [
    ('lang="en"', "lang attribute"),
    ("<title>", "title"),
    ('name="viewport"', "viewport"),
]

# Theming rules that must exist in the page's CSS. These are deliberately NOT
# checked against the raw HTML: <meta name="theme-color" media="(prefers-color-
# scheme: dark)"> contains the string "prefers-color-scheme: dark" while being
# browser-chrome colour rather than a stylesheet, so a whole-document substring
# search passes even when every dark-theme rule has been deleted. Checking the
# CSS instead closes that hole, and simultaneously lets a contributor move the
# CSS into a stylesheet without the gate reporting it as deleted dark mode.
REQUIRED_CSS = [
    ("prefers-color-scheme: dark", "dark theme"),
    ('[data-theme="dark"]', "theme override"),
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


def css_for(src: str) -> str:
    """Every rule that styles a page: inline <style> blocks plus any local
    stylesheet it links. Returns the concatenated CSS text.

    Collecting linked stylesheets is what lets the theming checks survive the
    single most likely first step of a redesign -- moving the CSS out of the
    document and into a file.
    """
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", src, re.S | re.I))
    for tag in re.findall(r"<link\b[^>]*>", src, re.I):
        rel = re.search(r'rel\s*=\s*["\']([^"\']*)["\']', tag, re.I)
        if not rel or "stylesheet" not in rel.group(1).lower().split():
            continue
        href = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if not href or is_external(href.group(1)):
            continue
        local = SITE / href.group(1).lstrip("/")
        if local.is_file():
            css += "\n" + local.read_text(encoding="utf-8")
    return css


def check_html() -> None:
    pages = sorted(SITE.rglob("*.html"))
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

        css = css_for(src)
        for needle, label in REQUIRED_CSS:
            if needle in css:
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
                "apple-touch-icon", "mask-icon", "manifest", "modulepreload"}


def is_external(url: str) -> bool:
    """True for anything that leaves this origin. Protocol-relative URLs count:
    //cdn.example.com resolves to https://cdn.example.com in production and is
    blocked by default-src 'self' exactly like an absolute one."""
    u = url.strip()
    return u.startswith(("http://", "https://", "//"))


def check_no_external_refs() -> None:
    """The CSP is default-src 'self'. A genuine external subresource would be
    blocked at runtime, so catch it here instead of in production.

    Only real fetches count. Anchor hrefs are navigation and <link rel=canonical>
    is metadata — neither is governed by CSP, and flagging them would train the
    reader to ignore this check.

    Attribute quoting, URL scheme and rel spelling are all things a contributor
    varies without thinking about it, so match on all the forms a browser
    honours rather than the one this site happens to use today."""
    for page in sorted(SITE.rglob("*.html")):
        src = page.read_text(encoding="utf-8")
        bad: list[str] = []

        # src= always denotes a fetched subresource (script, img, iframe, ...).
        # Either quote style, and srcset carries a comma-separated candidate list.
        for attr in ("src", "srcset"):
            for value in re.findall(rf'\b{attr}\s*=\s*["\']([^"\']+)["\']', src, re.I):
                for candidate in value.split(","):
                    url = candidate.strip().split()[0] if candidate.strip() else ""
                    if url and is_external(url):
                        bad.append(url)

        # href= only fetches on <link> tags carrying a fetching rel. rel accepts
        # a space-separated token list, so compare tokens rather than the whole
        # attribute value.
        for tag in re.findall(r"<link\b[^>]*>", src, re.I):
            href = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
            if not href or not is_external(href.group(1)):
                continue
            rel = re.search(r'rel\s*=\s*["\']([^"\']*)["\']', tag, re.I)
            tokens = set(rel.group(1).lower().split()) if rel else set()
            if tokens & FETCHING_REL:
                bad.append(href.group(1))

        # CSS fetches that never appear as a src= or a <link>, so none of the
        # checks above can see them:
        #   @import   pulls a stylesheet (style-src)
        #   url(...)  pulls background-image, @font-face src, mask, cursor...
        # The url() case is the likeliest way a contributor ships a Google Font
        # and only finds out in production.
        css = css_for(src)
        for value in re.findall(r"@import\s+(?:url\()?\s*['\"]?([^'\")\s;]+)", css, re.I):
            if is_external(value):
                bad.append(value)
        for value in re.findall(r"url\(\s*['\"]?([^'\")\s]+)", css, re.I):
            if is_external(value):
                bad.append(value)

        # <use href> and <image href> pull an external SVG sprite. The CSP
        # refuses it at runtime, so without this it ships broken rather than
        # failing the check.
        for tag in re.findall(r"<(?:use|image)\b[^>]*>", src, re.I):
            href = re.search(r'\b(?:xlink:)?href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
            if href and is_external(href.group(1)):
                bad.append(href.group(1))

        if bad:
            fail(f"{page.name}: external subresource would be blocked by CSP — {bad}")
        else:
            ok(f"{page.name}: no external subresources")


# Mirrors scripts/fingerprint_assets.py::FINGERPRINTED. tests/test_assets.py
# asserts the two have not drifted apart -- the duplication is deliberate so the
# gate stays dependency-free, but it needs a guard.
ASSET_FINGERPRINT = re.compile(r"^(?P<stem>.+)\.(?P<hash>[0-9a-f]{8})\.(?P<ext>[A-Za-z0-9]+)$")


def check_assets() -> None:
    """_headers caches /assets/* for a year with `immutable`, so the browser
    never revalidates -- not even on a hard reload. With no build step, the
    filename is the only cache-buster there is.

    Two failure modes, and the second is the one a name-pattern check alone
    would miss: a correctly-named asset edited in place keeps its old hash and
    is then served stale, from cache, for twelve months.
    """
    assets = SITE / "assets"
    if not assets.is_dir():
        ok("no site/assets/ directory (nothing to fingerprint)")
    else:
        for f in sorted(assets.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(SITE)
            m = ASSET_FINGERPRINT.match(f.name)
            if not m:
                fail(f"{rel}: not fingerprinted — /assets/* is immutable for a "
                     f"year, so the name must be <stem>.<hash8>.<ext>")
                continue
            actual = hashlib.sha256(f.read_bytes()).hexdigest()[:len(m.group("hash"))]
            if actual != m.group("hash"):
                fail(f"{rel}: filename hash {m.group('hash')} does not match its "
                     f"content ({actual}) — edited in place, will serve stale for a year")
            else:
                ok(f"{rel}: fingerprinted ({f.stat().st_size:,} B)")

    # A rename that missed a reference produces a 404 on a cached path.
    referenced: set[str] = set()
    for page in sorted(SITE.rglob("*.html")):
        src = page.read_text(encoding="utf-8")
        referenced.update(re.findall(r"/assets/([^\"'\s)>]+)", src))
    for name in sorted(referenced):
        if (SITE / "assets" / name).is_file():
            ok(f"asset reference resolves: /assets/{name}")
        else:
            fail(f"dangling asset reference: /assets/{name} does not exist")


def main() -> int:
    if not SITE.is_dir():
        print("FAIL  site/ directory not found")
        return 1

    print(f"Validating {SITE}\n")
    check_required_files()
    check_html()
    check_index_meta()
    check_sitemap()
    check_assets()
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
