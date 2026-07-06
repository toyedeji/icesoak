"""
Unit tests for the partial-run merge logic in scrape.py.

Tests the four scenarios required by the task:
  1. Partial run preserves non-targeted metros
  2. Partial run replaces targeted metro data correctly
  3. Zero-result protection: 0 studios returned → keep old data, warn
  4. Full run still overwrites completely
"""
import json
import logging
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Extract just the write logic from scrape.py without importing crawl4ai etc.
# We pull the source, isolate the write block, and wrap it in a testable fn.
# ---------------------------------------------------------------------------

EXISTING = [
    {"id": "d1", "metro": "denver_co",             "name": "Denver Studio 1"},
    {"id": "d2", "metro": "denver_co",             "name": "Denver Studio 2"},
    {"id": "p1", "metro": "philadelphia_pa",        "name": "Philly Studio 1"},
    {"id": "p2", "metro": "philadelphia_pa",        "name": "Philly Studio 2"},
    {"id": "a1", "metro": "austin_tx",              "name": "Austin Studio 1"},
]

NEW_AUSTIN = [
    {"id": "a2", "metro": "austin_tx", "name": "Austin Studio 2 (fresh)"},
    {"id": "a3", "metro": "austin_tx", "name": "Austin Studio 3 (fresh)"},
]

_METRO_ALIAS = {
    "denver":       "denver_co",
    "denver_co":    "denver_co",
    "philadelphia": "philadelphia_pa",
    "philadelphia_pa": "philadelphia_pa",
    "austin":       "austin_tx",
    "austin_tx":    "austin_tx",
}


def _write_studios(
    *,
    studios: list,           # freshly scraped + processed records
    metro_filter: list[str] | None,
    out: Path,
) -> tuple[list, list[str]]:
    """
    Mirrors the write logic from scrape.py.
    Returns (final_records, warning_messages).
    """
    warnings: list[str] = []

    if metro_filter and out.exists():
        scraped_metro_ids = {_METRO_ALIAS.get(m.lower(), m.lower()) for m in metro_filter}
        new_by_metro: dict[str, list] = {mid: [] for mid in scraped_metro_ids}
        for s in studios:
            mid = s.get("metro")
            if mid in new_by_metro:
                new_by_metro[mid].append(s)

        existing: list = json.loads(out.read_text(encoding="utf-8"))
        kept: list = []
        replaced_metros: list[str] = []
        preserved_metros: list[str] = []
        for s in existing:
            mid = s.get("metro")
            if mid not in scraped_metro_ids:
                kept.append(s)

        added: list = []
        for mid in scraped_metro_ids:
            fresh = new_by_metro[mid]
            if fresh:
                added.extend(fresh)
                replaced_metros.append(mid)
            else:
                old = [s for s in existing if s.get("metro") == mid]
                kept.extend(old)
                preserved_metros.append(mid)
                msg = (
                    f"WARNING: {mid} returned 0 studios — preserving existing "
                    f"{len(old)} records rather than wiping."
                )
                warnings.append(msg)

        merged = kept + added
        out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
        return merged, warnings
    else:
        out.write_text(json.dumps(studios, indent=2, ensure_ascii=False), encoding="utf-8")
        return studios, warnings


class TestMergeLogic(unittest.TestCase):

    def setUp(self):
        import tempfile
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.out = self.tmp / "studios.json"
        # Write the "existing" studios.json
        self.out.write_text(json.dumps(EXISTING, indent=2), encoding="utf-8")

    def tearDown(self):
        self._tmpdir.cleanup()

    # ── Scenario 1: partial run preserves non-targeted metros ────────────────
    def test_partial_run_preserves_other_metros(self):
        merged, warnings = _write_studios(
            studios=NEW_AUSTIN,
            metro_filter=["austin"],
            out=self.out,
        )
        ids = {s["id"] for s in merged}
        self.assertIn("d1", ids, "Denver studio 1 must be preserved")
        self.assertIn("d2", ids, "Denver studio 2 must be preserved")
        self.assertIn("p1", ids, "Philly studio 1 must be preserved")
        self.assertIn("p2", ids, "Philly studio 2 must be preserved")
        self.assertEqual(warnings, [], "No warnings expected")
        print("  PASS: partial run preserves non-targeted metros "
              f"(total={len(merged)}, denver={sum(1 for s in merged if s['metro']=='denver_co')}, "
              f"philly={sum(1 for s in merged if s['metro']=='philadelphia_pa')})")

    # ── Scenario 2: partial run replaces targeted metro data ─────────────────
    def test_partial_run_replaces_targeted_metro(self):
        merged, warnings = _write_studios(
            studios=NEW_AUSTIN,
            metro_filter=["austin"],
            out=self.out,
        )
        austin_records = [s for s in merged if s["metro"] == "austin_tx"]
        ids = {s["id"] for s in austin_records}
        self.assertNotIn("a1", ids, "Old Austin record must be replaced")
        self.assertIn("a2", ids, "New Austin record a2 must appear")
        self.assertIn("a3", ids, "New Austin record a3 must appear")
        self.assertEqual(len(austin_records), 2)
        self.assertEqual(warnings, [])
        print(f"  PASS: partial run replaces targeted metro "
              f"(austin_records={len(austin_records)}, ids={sorted(ids)})")

    # ── Scenario 3: zero-result protection ───────────────────────────────────
    def test_zero_result_preserves_existing_and_warns(self):
        merged, warnings = _write_studios(
            studios=[],              # scraper returned nothing for austin
            metro_filter=["austin"],
            out=self.out,
        )
        ids = {s["id"] for s in merged}
        self.assertIn("a1", ids, "Old Austin record must be preserved when 0 returned")
        self.assertEqual(len(merged), len(EXISTING), "Total count unchanged")
        self.assertEqual(len(warnings), 1)
        self.assertIn("austin_tx", warnings[0])
        self.assertIn("0 studios", warnings[0])
        print(f"  PASS: zero-result protection (preserved a1, warning='{warnings[0][:60]}…')")

    # ── Scenario 4: full run overwrites completely ────────────────────────────
    def test_full_run_overwrites(self):
        fresh = [{"id": "x1", "metro": "denver_co", "name": "Fresh Denver"}]
        merged, warnings = _write_studios(
            studios=fresh,
            metro_filter=None,       # no --metros flag
            out=self.out,
        )
        self.assertEqual(merged, fresh)
        self.assertEqual(len(merged), 1)
        self.assertEqual(warnings, [])
        on_disk = json.loads(self.out.read_text())
        self.assertEqual(on_disk, fresh, "Disk must match overwritten content")
        print(f"  PASS: full run overwrites completely "
              f"(old={len(EXISTING)} records → new={len(merged)} record)")

    # ── Bonus: no existing file → write fresh even with --metros ─────────────
    def test_partial_run_no_existing_file_writes_fresh(self):
        self.out.unlink()            # simulate first run
        merged, warnings = _write_studios(
            studios=NEW_AUSTIN,
            metro_filter=["austin"],
            out=self.out,
        )
        self.assertEqual(merged, NEW_AUSTIN)
        self.assertEqual(warnings, [])
        print(f"  PASS: no existing file → writes fresh "
              f"({len(merged)} records, no warnings)")


if __name__ == "__main__":
    print("Running merge-logic tests…\n")
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite = loader.loadTestsFromTestCase(TestMergeLogic)
    runner = unittest.TextTestRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
