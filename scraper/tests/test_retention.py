"""Tests for the full-run retention path (processors/retention.py).

The bug under test: the scheduled weekly run (run_scrape.sh, no --metros) used to
fall through to a bare `out.write_text(json.dumps(studios))`, so inventory each
week was exactly what that one crawl saw. Measured cost: 45 of 239 studios
dropped on 2026-07-19, 23 of 229 on 2026-07-26.

Run:  python3 -m pytest scraper/tests/test_retention.py
  or: python3 scraper/tests/test_retention.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processors.retention import (  # noqa: E402
    DEFAULT_MAX_MISSING_RUNS,
    RetentionAbort,
    max_missing_runs_from_env,
    merge_with_previous,
    metros_with_no_fresh_records,
)


def studio(sid, metro="denver_co", place=None, **kw):
    rec = {
        "id": sid,
        "name": kw.pop("name", sid.replace("-", " ").title()),
        "metro": metro,
        "city": kw.pop("city", "Denver"),
        "address": kw.pop("address", f"{abs(hash(sid)) % 9000 + 100} Main St"),
        "google_place_id": place,
    }
    rec.update(kw)
    return rec


class TestFullRunRetention(unittest.TestCase):
    """The headline requirement: absence from one crawl must not drop a studio."""

    def test_studio_absent_from_crawl_is_RETAINED(self):
        previous = [studio("alpha", place="0x1:0x1"), studio("beta", place="0x2:0x2")]
        fresh = [studio("alpha", place="0x1:0x1")]  # beta not returned this run

        merged, stats = merge_with_previous(
            fresh=fresh, previous=previous,
            run_date="2026-08-02", previous_run_date="2026-07-26",
        )

        ids = {s["id"] for s in merged}
        self.assertIn("beta", ids, "absent studio must be RETAINED, not dropped")
        self.assertEqual(len(merged), 2)
        self.assertEqual(stats["retained"], 1)
        self.assertEqual(stats["dropped"], 0)

        beta = next(s for s in merged if s["id"] == "beta")
        self.assertEqual(beta["missed_runs"], 1)
        self.assertEqual(beta["last_seen_at"], "2026-07-26",
                         "last_seen_at must be seeded from the previous run date")

        alpha = next(s for s in merged if s["id"] == "alpha")
        self.assertEqual(alpha["missed_runs"], 0)
        self.assertEqual(alpha["last_seen_at"], "2026-08-02")

    def test_dropped_only_after_N_consecutive_misses(self):
        """Default N=3: retained on misses 1 and 2, dropped on 3."""
        previous = [studio("ghost", place="0x9:0x9")]
        seen_counts = []

        for run in range(1, 5):
            # merge_with_previous refuses a wholly empty crawl outright, so drive
            # the absentee path with a fresh record of a DIFFERENT identity.
            merged, stats = merge_with_previous(
                fresh=[studio("decoy", place="0xd:0xd")],
                previous=previous,
                run_date=f"2026-08-{run:02d}", previous_run_date="2026-07-26",
                max_missing_runs=3,
            )
            still_there = any(s["id"] == "ghost" for s in merged)
            misses = next((s["missed_runs"] for s in merged if s["id"] == "ghost"), None)
            seen_counts.append((run, still_there, misses))
            previous = merged

        self.assertEqual(
            seen_counts,
            [(1, True, 1), (2, True, 2), (3, False, None), (4, False, None)],
            f"expected retain/retain/drop, got {seen_counts}",
        )

    def test_N_is_configurable(self):
        previous = [studio("ghost", place="0x9:0x9")]
        merged, stats = merge_with_previous(
            fresh=[studio("decoy", place="0xd:0xd")], previous=previous,
            run_date="2026-08-02", previous_run_date="2026-07-26",
            max_missing_runs=1,
        )
        self.assertEqual(stats["dropped"], 1, "N=1 drops on the first miss")
        self.assertNotIn("ghost", {s["id"] for s in merged})
        self.assertEqual(DEFAULT_MAX_MISSING_RUNS, 3)

    def test_env_override_rejects_nonsense(self):
        import os
        for bad in ("abc", "0", "-2"):
            os.environ["ICESOAK_MAX_MISSING_RUNS"] = bad
            self.assertEqual(max_missing_runs_from_env(), 3,
                             f"{bad!r} must fall back to the safe default")
        os.environ["ICESOAK_MAX_MISSING_RUNS"] = "5"
        self.assertEqual(max_missing_runs_from_env(), 5)
        del os.environ["ICESOAK_MAX_MISSING_RUNS"]


class TestEmptyCrawlGuard(unittest.TestCase):
    """The empty-harvest refusal questions.json has had since 2026-07-28."""

    def test_totally_empty_crawl_raises_rather_than_wiping(self):
        previous = [studio("alpha"), studio("beta")]
        with self.assertRaises(RetentionAbort) as ctx:
            merge_with_previous(fresh=[], previous=previous, run_date="2026-08-02")
        self.assertIn("0 studios", str(ctx.exception))

    def test_empty_crawl_with_no_previous_is_fine(self):
        merged, stats = merge_with_previous(fresh=[], previous=[], run_date="2026-08-02")
        self.assertEqual(merged, [])


class TestFieldFillForward(unittest.TestCase):
    """A thinner re-scrape must not erase enrich_contacts.py's work."""

    def test_empty_fresh_fields_are_filled_from_previous(self):
        previous = [studio(
            "alpha", place="0x1:0x1",
            website="https://alpha.com", instagram="@alpha",
            modalities=["cold_plunge"], day_pass_price_usd=45.0,
        )]
        fresh = [studio(
            "alpha", place="0x1:0x1",
            website=None, instagram="", modalities=[], day_pass_price_usd=None,
        )]
        merged, stats = merge_with_previous(
            fresh=fresh, previous=previous, run_date="2026-08-02",
        )
        a = merged[0]
        self.assertEqual(a["website"], "https://alpha.com")
        self.assertEqual(a["instagram"], "@alpha")
        self.assertEqual(a["modalities"], ["cold_plunge"])
        self.assertEqual(a["day_pass_price_usd"], 45.0)
        self.assertGreater(stats["filled_fields"], 0)

    def test_fresh_non_empty_values_always_win(self):
        previous = [studio("alpha", place="0x1:0x1", website="https://old.com")]
        fresh = [studio("alpha", place="0x1:0x1", website="https://new.com")]
        merged, _ = merge_with_previous(
            fresh=fresh, previous=previous, run_date="2026-08-02",
        )
        self.assertEqual(merged[0]["website"], "https://new.com")

    def test_zero_and_false_are_not_treated_as_missing(self):
        """Generic falsiness would overwrite a real 0 price or False flag."""
        previous = [studio("alpha", place="0x1:0x1", day_pass_price_usd=99.0,
                           sms_ok=True)]
        fresh = [studio("alpha", place="0x1:0x1", day_pass_price_usd=0,
                        sms_ok=False)]
        merged, _ = merge_with_previous(
            fresh=fresh, previous=previous, run_date="2026-08-02",
        )
        self.assertEqual(merged[0]["day_pass_price_usd"], 0)
        self.assertIs(merged[0]["sms_ok"], False)


class TestDuplicateIdentities(unittest.TestCase):
    """The live dataset has 3 pairs of records sharing one street address.

    A dict/setdefault build of the previous index silently discards the second
    record, which would delete it on the next run with no missed_runs grace and
    no churn signal.
    """

    def test_duplicate_identity_extra_ages_out_instead_of_vanishing(self):
        dup_a = studio("sweathouz-camp-bowie", metro="dfw",
                       address="6252 Camp Bowie Blvd", name="SweatHouz Camp Bowie")
        dup_b = studio("sweathouz-fort-worth", metro="dfw",
                       address="6252 Camp Bowie Blvd", name="SweatHouz Fort Worth")
        previous = [dup_a, dup_b]

        fresh = [studio("sweathouz-camp-bowie", metro="dfw",
                        address="6252 Camp Bowie Blvd", name="SweatHouz Camp Bowie")]

        merged, stats = merge_with_previous(
            fresh=fresh, previous=previous,
            run_date="2026-08-02", previous_run_date="2026-07-26",
        )

        ids = {s["id"] for s in merged}
        self.assertIn("sweathouz-fort-worth", ids,
                      "the duplicate extra must be retained, not silently dropped")
        self.assertEqual(stats["duplicate_identities"], 1)
        self.assertEqual(stats["previous"], 2, "prev_total counts records, not identities")
        extra = next(s for s in merged if s["id"] == "sweathouz-fort-worth")
        self.assertEqual(extra["missed_runs"], 1)

    def test_canonical_prior_is_the_one_the_crawl_returned(self):
        """Regression: prior selection used to be file order, producing a dup id.

        The registry resolves a fresh record for a shared address to exactly ONE
        slug. If the prior matched against it is the OTHER record of the pair,
        the re-seen record inherits the canonical id while the canonical prior is
        separately retained under that same id — two records, one URL.

        Ordering here puts the SHADOWED record first, which is what used to
        trigger the collision.
        """
        shadowed = studio("sweathouz-roswell", metro="atlanta_ga",
                          address="1035 Alpharetta Hwy Suite 1400")
        canonical = studio("sweathouz-alpharetta", metro="atlanta_ga",
                           address="1035 Alpharetta Hwy Suite 1400")
        previous = [shadowed, canonical]          # shadowed FIRST, deliberately

        # The registry resolved the crawl's record to the canonical slug.
        fresh = [studio("sweathouz-alpharetta", metro="atlanta_ga",
                        address="1035 Alpharetta Hwy Suite 1400")]

        merged, stats = merge_with_previous(
            fresh=fresh, previous=previous,
            run_date="2026-08-02", previous_run_date="2026-07-26",
        )

        ids = [s["id"] for s in merged]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate ids produced: {ids}")
        self.assertIn("sweathouz-alpharetta", ids)
        self.assertIn("sweathouz-roswell", ids,
                      "the shadowed record keeps its OWN id while it ages out")

        roswell = next(s for s in merged if s["id"] == "sweathouz-roswell")
        self.assertEqual(roswell["missed_runs"], 1)
        alpharetta = next(s for s in merged if s["id"] == "sweathouz-alpharetta")
        self.assertEqual(alpharetta["missed_runs"], 0, "this one WAS re-observed")

    def test_duplicate_ids_are_refused_outright(self):
        """The invariant, independent of how it might be violated."""
        previous = [
            studio("clash", place="0x1:0x1"),
            studio("other", place="0x2:0x2"),
        ]
        # A fresh record that collides on id with a record that will be retained.
        fresh = [studio("other", place="0x3:0x3", address="9 Elsewhere Ave")]
        # 'other' (0x2) is not re-seen -> retained with id 'other';
        # the fresh 0x3 record also carries id 'other'. That must abort.
        with self.assertRaises(RetentionAbort) as ctx:
            merge_with_previous(
                fresh=fresh, previous=previous,
                run_date="2026-08-02", previous_run_date="2026-07-26",
            )
        self.assertIn("duplicated studio id", str(ctx.exception))

    def test_fresh_ratio_ignores_unreachable_duplicates(self):
        """Otherwise 3 permanent duplicates would depress the ratio forever."""
        dup_a = studio("a", address="1 Same St")
        dup_b = studio("b", address="1 Same St")
        fresh = [studio("a", address="1 Same St")]
        _, stats = merge_with_previous(
            fresh=fresh, previous=[dup_a, dup_b], run_date="2026-08-02",
        )
        self.assertEqual(stats["fresh_ratio"], 1.0)


class TestMetroReporting(unittest.TestCase):
    def test_metro_that_returned_nothing_is_named(self):
        previous = [studio("a", metro="denver_co"), studio("b", metro="austin_tx")]
        fresh = [studio("a", metro="denver_co")]
        self.assertEqual(metros_with_no_fresh_records(fresh, previous), ["austin_tx"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
