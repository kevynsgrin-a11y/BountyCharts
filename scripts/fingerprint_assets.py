#!/usr/bin/env python3
"""Content-hash every file in site/assets/ and update the references to it.

site/_headers caches /assets/* for 31536000s with `immutable`, which tells the
browser never to revalidate — not even on a hard reload. There is no build step
to emit hashed filenames, so the filename is the ONLY cache-buster that exists.
An asset shipped as `og-card.png` and later edited in place is frozen, wrong,
for a year.

This script is the producer; `check_assets()` in validate_site.py is the
verifier, and tests/test_assets.py asserts the two agree.

    python3 scripts/fingerprint_assets.py            # rename + rewrite refs
    python3 scripts/fingerprint_assets.py --check    # report only, exit 1 if stale

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ASSETS = SITE / "assets"
HASH_LEN = 8

# Shared with validate_site.check_assets(). tests/test_assets.py asserts the
# two definitions have not drifted apart.
FINGERPRINTED = re.compile(r"^(?P<stem>.+)\.(?P<hash>[0-9a-f]{8})\.(?P<ext>[A-Za-z0-9]+)$")

# Files whose text may reference an asset path.
REFERRERS = ("*.html", "_headers", "sitemap.xml", "robots.txt")


def content_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:HASH_LEN]


def target_name(path: pathlib.Path) -> str:
    """The name this file should have, given its bytes."""
    m = FINGERPRINTED.match(path.name)
    stem = m.group("stem") if m else path.stem
    ext = m.group("ext") if m else path.suffix.lstrip(".")
    return f"{stem}.{content_hash(path)}.{ext}"


def referrer_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for pattern in REFERRERS:
        out.extend(sorted(SITE.rglob(pattern)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="report what would change; exit 1 if anything is stale")
    args = ap.parse_args()

    if not ASSETS.is_dir():
        print("no site/assets/ directory — nothing to fingerprint")
        return 0

    renames: list[tuple[str, str]] = []
    for f in sorted(ASSETS.rglob("*")):
        if not f.is_file():
            continue
        want = target_name(f)
        if f.name != want:
            renames.append((f.name, want))

    if not renames:
        print(f"all {sum(1 for f in ASSETS.rglob('*') if f.is_file())} asset(s) correctly fingerprinted")
        return 0

    for old, new in renames:
        print(f"{'would rename' if args.check else 'rename'}  {old}  ->  {new}")
    if args.check:
        print(f"\n{len(renames)} asset(s) stale. Run without --check to fix.")
        return 1

    for old, new in renames:
        (ASSETS / old).rename(ASSETS / new)

    # Rewrite every reference. Match the old name wherever it appears so a
    # reference in _headers or a sitemap is updated too, not just in HTML.
    for ref in referrer_files():
        text = ref.read_text(encoding="utf-8")
        updated = text
        for old, new in renames:
            updated = updated.replace(old, new)
        if updated != text:
            ref.write_text(updated, encoding="utf-8")
            print(f"updated references in {ref.relative_to(SITE)}")

    print(f"\n{len(renames)} asset(s) fingerprinted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
