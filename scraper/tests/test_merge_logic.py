"""Tests for the studios.json write path in scrape.py.

WHAT CHANGED IN THIS FILE, AND WHY IT MATTERS
---------------------------------------------
The previous version of this file reimplemented scrape.py's write logic inline as
a local `_write_studios()` helper and asserted against that copy. Its fourth
scenario was:

    def test_full_run_overwrites(self):
        ...
        self.assertEqual(merged, fresh)
        self.assertEqual(len(merged), 1)
        print("PASS: full run overwrites completely (old=5 records -> new=1 record)")

That test passed, permanently and cheerfully, while describing the exact defect
that dropped 45 of 239 studios on 2026-07-19 and 23 of 229 on 2026-07-26. It
codified "the scheduled run throws away everything it did not just see" as
intended behaviour, and because it tested a COPY of the logic it could never have
noticed a divergence between the copy and the shipped code either.

Two lessons applied here:
  1. The assertion is inverted: a full run must now RETAIN.
  2. The tests call the real functions — scrape.partition_previous and
     retention.merge_with_previous — not a local re-implementation. A test that
     mirrors the source cannot detect the source drifting away from it.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processors.retention import merge_with_previous  # noqa: E402
from scrape import partition_previous  # noqa: E402

EXISTING = [
    {"id": "d1", "metro": "denver_co",       "name": "Denver Studio 1", "address": "1 D St"},
    {"id": "d2", "metro": "denver_co",       "name": "Denver Studio 2", "address": "2 D St"},
    {"id": "p1", "metro": "philadelphia_pa", "name": "Philly Studio 1", "address": "1 P St"},
    {"id": "p2", "metro": "philadelphia_pa", "name": "Philly Studio 2", "address": "2 P St"},
    {"id": "a1", "metro": "austin_tx",       "name": "Austin Studio 1", "address": "1 A St"},
]

NEW_AUSTIN = [
    {"id": "a2", "metro": "austin_tx", "name": "Austin Studio 2", "address": "2 A St"},
    {"id": "a3", "metro": "austin_tx", "name": "Austin Studio 3", "address": "3 A St"},
]


def write(fresh, metro_filter, previous, **kw):
    """Exercise the real production path: partition, then merge."""
    scoped, untouched = partition_previous(previous, metro_filter)
    merged_scope, stats = merge_with_previous(
        fresh=fresh, previous=scoped,
        run_date=kw.pop("run_date", "2026-08-02"),
        previous_run_date=kw.pop("previous_run_date", "2026-07-26"),
        **kw,
    )
    return untouched + merged_scope, stats


class TestFullRun(unittest.TestCase):
    """The inverted assertion. This is the regression that matters."""

    def test_full_run_RETAINS_studios_absent_from_the_crawl(self):
        # A crawl that only saw Denver — Philadelphia and Austin went dark.
        fresh = [dict(s) for s in EXISTING if s["metro"] == "denver_co"]

        merged, stats = write(fresh, metro_filter=None, previous=EXISTING)

        ids = {s["id"] for s in merged}
        self.assertEqual(
            ids, {"d1", "d2", "p1", "p2", "a1"},
            "a full run must NOT discard studios this crawl did not return — "
            "this is the 2026-07-19 / 07-26 data loss",
        )
        self.assertEqual(len(merged), 5)
        self.assertEqual(stats["reseen"], 2)
        self.assertEqual(stats["retained"], 3)
        self.assertEqual(stats["dropped"], 0)

        for sid in ("p1", "p2", "a1"):
            rec = next(s for s in merged if s["id"] == sid)
            self.assertEqual(rec["missed_runs"], 1)
            self.assertEqual(rec["last_seen_at"], "2026-07-26")

    def test_full_run_still_adds_new_studios(self):
        fresh = [dict(s) for s in EXISTING] + NEW_AUSTIN
        merged, stats = write(fresh, metro_filter=None, previous=EXISTING)
        self.assertEqual(len(merged), 7)
        self.assertEqual(stats["new"], 2)
        self.assertEqual(stats["retained"], 0)

    def test_full_run_on_a_first_run_writes_fresh(self):
        merged, stats = write(NEW_AUSTIN, metro_filter=None, previous=[])
        self.assertEqual({s["id"] for s in merged}, {"a2", "a3"})
        self.assertEqual(stats["new"], 2)


class TestPartialRun(unittest.TestCase):
    """The --metros branch keeps its original guarantees, plus retention."""

    def test_non_targeted_metros_pass_through_untouched(self):
        merged, stats = write(NEW_AUSTIN, metro_filter=["austin"], previous=EXISTING)
        ids = {s["id"] for s in merged}
        for sid in ("d1", "d2", "p1", "p2"):
            self.assertIn(sid, ids, f"{sid} is outside the targeted metro")

        # Untouched records must not be marked as missed — they were not crawled.
        for sid in ("d1", "d2", "p1", "p2"):
            rec = next(s for s in merged if s["id"] == sid)
            self.assertNotIn(
                "missed_runs", rec,
                "a metro that was never crawled must not accrue missed_runs",
            )

    def test_targeted_metro_gains_new_records(self):
        merged, _ = write(NEW_AUSTIN, metro_filter=["austin"], previous=EXISTING)
        austin = {s["id"] for s in merged if s["metro"] == "austin_tx"}
        self.assertIn("a2", austin)
        self.assertIn("a3", austin)

    def test_targeted_metro_RETAINS_its_old_records_too(self):
        """Changed behaviour: the old code rebuilt the metro from scratch.

        Previously a1 was dropped outright because the targeted metro was
        replaced wholesale. It is now retained with missed_runs=1, on the same
        reasoning as the full run: one crawl missing a studio is not evidence the
        studio closed.
        """
        merged, stats = write(NEW_AUSTIN, metro_filter=["austin"], previous=EXISTING)
        ids = {s["id"] for s in merged}
        self.assertIn("a1", ids)
        a1 = next(s for s in merged if s["id"] == "a1")
        self.assertEqual(a1["missed_runs"], 1)
        self.assertEqual(stats["retained"], 1)

    def test_zero_result_for_the_targeted_metro_aborts(self):
        """Old behaviour warned and rewrote the file; aborting is stronger.

        Nothing is lost either way — but not writing means no spurious commit,
        no Netlify deploy, and a non-zero exit the cron log will show.
        """
        from processors.retention import RetentionAbort
        with self.assertRaises(RetentionAbort):
            write([], metro_filter=["austin"], previous=EXISTING)

    def test_partial_run_with_no_existing_file_writes_fresh(self):
        merged, stats = write(NEW_AUSTIN, metro_filter=["austin"], previous=[])
        self.assertEqual({s["id"] for s in merged}, {"a2", "a3"})


class TestPartitioning(unittest.TestCase):
    def test_full_run_puts_everything_in_scope(self):
        scoped, untouched = partition_previous(EXISTING, None)
        self.assertEqual(len(scoped), 5)
        self.assertEqual(untouched, [])

    def test_metro_aliases_resolve(self):
        for alias in ("philly", "philadelphia", "philadelphia_pa"):
            scoped, _ = partition_previous(EXISTING, [alias])
            self.assertEqual({s["id"] for s in scoped}, {"p1", "p2"}, f"alias {alias}")

    def test_multiple_metros(self):
        scoped, untouched = partition_previous(EXISTING, ["austin", "denver"])
        self.assertEqual({s["id"] for s in scoped}, {"a1", "d1", "d2"})
        self.assertEqual({s["id"] for s in untouched}, {"p1", "p2"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
