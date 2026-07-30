"""Tests for the churn and staleness checks (processors/quality_gate.py).

The bug under test: MAX_DROP_FRACTION was computed on the NET total —
`drop = (prev_total - total) / prev_total` — so the 2026-07-26 run, which removed
23 studios and added 26, produced a NEGATIVE drop and read as healthy growth.
46 studios left the dataset across 07-15 -> 07-26 without the gate registering
anything. Net totals cannot see substitution.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processors.quality_gate import (  # noqa: E402
    ABORT_STALE_FRACTION,
    MAX_CHURN_FRACTION,
    MAX_DROP_FRACTION,
    WARN_STALE_FRACTION,
    evaluate,
)


def studio(sid, missed=0):
    """A record that passes every unrelated gate check cleanly."""
    return {
        "id": sid,
        "name": f"Studio {sid}",
        "metro": "denver_co",
        "city": "Denver",
        "address": f"{sid} Larimer St, Denver, CO 80202",
        "lat": 39.75, "lng": -104.99,
        "missed_runs": missed,
        "last_seen_at": "2026-08-02",
    }


def dataset(n, prefix="s", missed=0, start=0):
    return [studio(f"{prefix}{i}", missed=missed) for i in range(start, start + n)]


def metro_healthy(records):
    """Spread records across the 3 launch metros so the floor check passes."""
    metros = ["denver_co", "dallas_fort_worth_tx", "philadelphia_pa"]
    for i, r in enumerate(records):
        r["metro"] = metros[i % 3]
    return records


class TestChurnCheck(unittest.TestCase):

    def test_SIX_PERCENT_CHURN_WITH_NET_POSITIVE_TOTAL_FAILS(self):
        """The exact shape that slipped through: more added than removed."""
        prev = metro_healthy(dataset(100, "keep"))
        # Drop 6 of 100 (6% churn), add 9 -> net +3, a NET GAIN.
        new = metro_healthy(
            [dict(s) for s in prev[6:]] + dataset(9, "new", start=1000)
        )

        result = evaluate(new, prev)

        self.assertEqual(result["metrics"]["dropped"], 6)
        self.assertEqual(result["metrics"]["added"], 9)
        self.assertEqual(result["metrics"]["net_change"], 3)
        self.assertAlmostEqual(result["metrics"]["churn"], 0.06)

        churn_aborts = [a for a in result["aborts"] if "churn" in a]
        self.assertTrue(
            churn_aborts,
            f"6% churn must ABORT even with a net gain. aborts={result['aborts']}",
        )
        self.assertIn("net change was +3", churn_aborts[0])

        # And prove the OLD check would not have caught it.
        old_style_drop = (len(prev) - len(new)) / len(prev)
        self.assertLess(old_style_drop, 0)
        self.assertLess(
            old_style_drop, MAX_DROP_FRACTION,
            "sanity: the net-total check reads this run as growth",
        )

    def test_churn_below_threshold_passes(self):
        prev = metro_healthy(dataset(100, "keep"))
        new = metro_healthy([dict(s) for s in prev[4:]] + dataset(4, "new", start=1000))
        result = evaluate(new, prev)
        self.assertAlmostEqual(result["metrics"]["churn"], 0.04)
        self.assertEqual([a for a in result["aborts"] if "churn" in a], [])

    def test_threshold_is_five_percent(self):
        self.assertAlmostEqual(MAX_CHURN_FRACTION, 0.05)

    def test_churn_is_an_abort_not_a_warn(self):
        prev = metro_healthy(dataset(100, "keep"))
        new = metro_healthy([dict(s) for s in prev[10:]] + dataset(20, "new", start=1000))
        result = evaluate(new, prev)
        self.assertTrue([a for a in result["aborts"] if "churn" in a])
        self.assertEqual([w for w in result["warns"] if "churn" in w], [])

    def test_abort_message_names_the_dropped_ids(self):
        prev = metro_healthy(dataset(100, "keep"))
        new = metro_healthy([dict(s) for s in prev[8:]])
        result = evaluate(new, prev)
        churn_abort = next(a for a in result["aborts"] if "churn" in a)
        self.assertIn("keep0", churn_abort, "operator needs to see what vanished")

    def test_env_override_relaxes_a_reviewed_run(self):
        import os
        prev = metro_healthy(dataset(100, "keep"))
        new = metro_healthy([dict(s) for s in prev[6:]] + dataset(9, "new", start=1000))
        os.environ["ICESOAK_MAX_CHURN_FRACTION"] = "0.10"
        try:
            result = evaluate(new, prev)
            self.assertEqual([a for a in result["aborts"] if "churn" in a], [])
        finally:
            del os.environ["ICESOAK_MAX_CHURN_FRACTION"]

    def test_unreadable_previous_warns_instead_of_silently_passing(self):
        result = evaluate(metro_healthy(dataset(50)), None)
        self.assertTrue(any("churn" in w for w in result["warns"]))
        self.assertIsNone(result["metrics"]["churn"])

    def test_net_collapse_check_is_retained(self):
        """Churn is additional to, not a replacement for, the net-drop check."""
        prev = metro_healthy(dataset(100, "keep"))
        new = metro_healthy([dict(s) for s in prev[:50]])   # 50% gone
        result = evaluate(new, prev)
        self.assertTrue([a for a in result["aborts"] if "max-drop" in a])


class TestStalenessCheck(unittest.TestCase):
    """Retention's blind spot: a dead crawl reproduces last week's file exactly."""

    def test_dead_crawl_is_caught_even_though_total_and_churn_are_perfect(self):
        prev = metro_healthy(dataset(100, "keep"))
        # Every record retained, nothing re-observed: identical ids, identical count.
        new = metro_healthy([dict(s, missed_runs=1) for s in prev])

        result = evaluate(new, prev)

        self.assertEqual(result["metrics"]["churn"], 0.0, "churn is clean")
        self.assertEqual(result["metrics"]["net_change"], 0, "total is unchanged")
        self.assertTrue(
            [a for a in result["aborts"] if "not re-observed" in a],
            "a wholly unobserved dataset must still abort",
        )

    def test_stale_share_between_thresholds_warns(self):
        prev = metro_healthy(dataset(100, "keep"))
        new = metro_healthy(
            [dict(s, missed_runs=1) for s in prev[:30]] + [dict(s) for s in prev[30:]]
        )
        result = evaluate(new, prev)
        self.assertTrue([w for w in result["warns"] if "not re-observed" in w])
        self.assertEqual([a for a in result["aborts"] if "not re-observed" in a], [])

    def test_pre_retention_file_reads_as_fully_fresh(self):
        """A file with no missed_runs field must not trip the staleness gate."""
        records = metro_healthy(dataset(50))
        for r in records:
            del r["missed_runs"]
        result = evaluate(records, None)
        self.assertEqual(result["metrics"]["stale"], 0)
        self.assertEqual([a for a in result["aborts"] if "not re-observed" in a], [])

    def test_thresholds(self):
        self.assertAlmostEqual(WARN_STALE_FRACTION, 0.25)
        self.assertAlmostEqual(ABORT_STALE_FRACTION, 0.50)


class TestGateBasics(unittest.TestCase):
    def test_empty_dataset_aborts(self):
        result = evaluate([], [studio("a")])
        self.assertTrue(result["aborts"])

    def test_clean_run_passes(self):
        prev = metro_healthy(dataset(100, "keep"))
        new = metro_healthy([dict(s) for s in prev] + dataset(3, "new", start=1000))
        result = evaluate(new, prev)
        self.assertEqual(result["aborts"], [], f"unexpected aborts: {result['aborts']}")

    def test_report_lines_include_churn_numbers(self):
        prev = metro_healthy(dataset(100, "keep"))
        new = metro_healthy([dict(s) for s in prev[2:]] + dataset(2, "new", start=1000))
        result = evaluate(new, prev)
        joined = "\n".join(result["report"])
        self.assertIn("dropped=2", joined)
        self.assertIn("churn=", joined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
