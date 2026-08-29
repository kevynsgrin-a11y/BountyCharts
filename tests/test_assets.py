#!/usr/bin/env python3
"""Tests for asset fingerprinting.

site/_headers caches /assets/* for a year with `immutable`. With no build step,
the filename is the only cache-buster, so an unfingerprinted or stale-hashed
asset is frozen wrong for twelve months. These tests exercise the real gate as
a subprocess against mutated copies of site/.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "validate_site.py"
PRODUCER = ROOT / "scripts" / "fingerprint_assets.py"
SITE = ROOT / "site"

PNG = b"\x89PNG\r\n\x1a\n" + b"fake image bytes for testing"


def run_gate(mutate=None):
    """Copy site/ + scripts/ + docs/ into a temp dir, mutate, run the gate.

    docs/ is copied because the sibling suite's ledger test reads it via ROOT.
    """
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        shutil.copytree(SITE, work / "site")
        (work / "scripts").mkdir()
        shutil.copy(GATE, work / "scripts" / "validate_site.py")
        if mutate:
            mutate(work / "site")
        proc = subprocess.run([sys.executable, "scripts/validate_site.py"],
                              cwd=work, capture_output=True, text=True)
        return proc.returncode, proc.stdout + proc.stderr


def fingerprinted(name: str, data: bytes) -> str:
    stem, _, ext = name.rpartition(".")
    return f"{stem}.{hashlib.sha256(data).hexdigest()[:8]}.{ext}"


class AssetFingerprints(unittest.TestCase):

    def test_gate_passes_with_no_assets_directory(self):
        """Today's state must remain landable."""
        code, out = run_gate()
        self.assertEqual(code, 0, out)

    def test_correctly_fingerprinted_asset_is_accepted(self):
        def mutate(site):
            (site / "assets").mkdir()
            (site / "assets" / fingerprinted("og-card.png", PNG)).write_bytes(PNG)
        code, out = run_gate(mutate)
        self.assertEqual(code, 0, "a correctly fingerprinted asset was rejected:\n" + out)

    def test_unfingerprinted_asset_is_rejected(self):
        def mutate(site):
            (site / "assets").mkdir()
            (site / "assets" / "og-card.png").write_bytes(PNG)
        code, out = run_gate(mutate)
        self.assertEqual(code, 1)
        self.assertIn("not fingerprinted", out)

    def test_asset_edited_in_place_is_rejected(self):
        """The real bug: same filename, different bytes. A name-pattern check
        alone cannot see this, and the result is served stale for a year."""
        def mutate(site):
            (site / "assets").mkdir()
            name = fingerprinted("og-card.png", PNG)
            (site / "assets" / name).write_bytes(PNG + b" EDITED")
        code, out = run_gate(mutate)
        self.assertEqual(code, 1, "an asset edited in place was accepted:\n" + out)
        self.assertIn("does not match its content", out)

    def test_dangling_asset_reference_is_rejected(self):
        def mutate(site):
            src = (site / "index.html").read_text(encoding="utf-8")
            (site / "index.html").write_text(
                src.replace("</head>",
                            '<meta property="og:image" '
                            'content="https://bountycharts.com/assets/gone.deadbeef.png">'
                            "</head>"),
                encoding="utf-8")
        code, out = run_gate(mutate)
        self.assertEqual(code, 1, "a dangling asset reference was accepted:\n" + out)
        self.assertIn("dangling asset reference", out)

    def test_producer_and_verifier_regexes_agree(self):
        """The pattern is deliberately duplicated so the gate stays
        dependency-free. This is the guard against the two drifting."""
        spec = importlib.util.spec_from_file_location("fp", PRODUCER)
        fp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fp)
        gate_spec = importlib.util.spec_from_file_location("vs", GATE)
        vs = importlib.util.module_from_spec(gate_spec)
        gate_spec.loader.exec_module(vs)
        self.assertEqual(fp.FINGERPRINTED.pattern, vs.ASSET_FINGERPRINT.pattern,
                         "producer and verifier fingerprint patterns have drifted")


class ProducerRenamesAndRewrites(unittest.TestCase):
    """The producer must rename the file AND update every reference, or it
    trades a cache bug for a 404."""

    def test_producer_renames_and_updates_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = pathlib.Path(tmp)
            shutil.copytree(SITE, work / "site")
            (work / "scripts").mkdir()
            shutil.copy(PRODUCER, work / "scripts" / "fingerprint_assets.py")
            (work / "site" / "assets").mkdir()
            (work / "site" / "assets" / "og-card.png").write_bytes(PNG)
            src = (work / "site" / "index.html").read_text(encoding="utf-8")
            (work / "site" / "index.html").write_text(
                src.replace("</head>",
                            '<meta property="og:image" '
                            'content="https://bountycharts.com/assets/og-card.png"></head>'),
                encoding="utf-8")

            proc = subprocess.run([sys.executable, "scripts/fingerprint_assets.py"],
                                  cwd=work, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            want = fingerprinted("og-card.png", PNG)
            self.assertTrue((work / "site" / "assets" / want).is_file(),
                            f"expected {want} to exist")
            page = (work / "site" / "index.html").read_text(encoding="utf-8")
            self.assertIn(want, page, "reference was not rewritten")
            self.assertNotIn("/assets/og-card.png", page, "stale reference left behind")


if __name__ == "__main__":
    unittest.main(verbosity=2)
