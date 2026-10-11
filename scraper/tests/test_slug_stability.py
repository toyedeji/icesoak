"""Tests for stable studio slugs (processors/identity.py, processors/merger.py).

The bug under test: merger._slug() keys on (name, search-city), and Google Maps
returns name variants between renders. The 2026-07-15 dataset contains BOTH
"West Plano - Sauna /Cold Plunge /Hot Tub" and
"West Plano - Sauna/Cold Plunge/Hot Tub" as separate records. 12 of the 46
studios that "disappeared" between 07-15 and 07-26 in fact reappeared under a
different id: not lost inventory, just broken URLs.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processors.identity import (  # noqa: E402
    SlugRegistry,
    identity_key,
    identity_tier,
)
from processors.merger import merge_sources  # noqa: E402


def raw(name, city="Denver", metro="denver_co", place=None, address=None):
    """A minimal record shaped like crawler output, pre-merge."""
    return {
        "id": None, "name": name, "metro": metro, "city": city,
        "google_place_id": place, "address": address, "status": "active",
        "modalities": [], "amenities": [], "source_urls": [],
    }


class TestSlugSurvivesNameVariant(unittest.TestCase):
    """The headline requirement."""

    def test_slug_survives_name_change_when_place_id_matches(self):
        registry = SlugRegistry()

        week1 = merge_sources(
            [raw("West Plano - Sauna /Cold Plunge /Hot Tub", place="0xabc:0xdef")],
            registry=registry,
        )
        original_slug = week1[0]["id"]
        self.assertTrue(original_slug, "week 1 must produce a slug")

        # Same business, Maps renders the name slightly differently.
        week2 = merge_sources(
            [raw("West Plano - Sauna/Cold Plunge/Hot Tub", place="0xabc:0xdef")],
            registry=registry,
        )

        self.assertEqual(
            week2[0]["id"], original_slug,
            "a Maps name variant must NOT re-slug the studio — that is the "
            "12-of-46 URL churn this registry exists to stop",
        )
        self.assertEqual(len(registry), 1, "no second entry should be created")

    def test_wholly_different_name_still_keeps_slug_on_place_id_match(self):
        registry = SlugRegistry()
        first = merge_sources([raw("Cold Co", place="0x1:0x1")], registry=registry)
        second = merge_sources(
            [raw("Cold Company Recovery Studio", place="0x1:0x1")], registry=registry
        )
        self.assertEqual(second[0]["id"], first[0]["id"])

    def test_registry_survives_a_save_load_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "slug_registry.json"
            reg = SlugRegistry()
            first = merge_sources([raw("Ice Bar", place="0x5:0x5")], registry=reg)
            reg.save(path)

            reloaded = SlugRegistry.load(path)
            second = merge_sources(
                [raw("Ice Bar Recovery", place="0x5:0x5")], registry=reloaded
            )
            self.assertEqual(second[0]["id"], first[0]["id"])

    def test_corrupt_registry_degrades_instead_of_aborting(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "slug_registry.json"
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(len(SlugRegistry.load(path)), 0)
            self.assertEqual(len(SlugRegistry.load(Path(td) / "absent.json")), 0)


class TestIdentityTiers(unittest.TestCase):
    def test_place_id_preferred_over_address_and_name(self):
        self.assertEqual(identity_tier(raw("X", place="0x1:0x1", address="1 A St")), "place")
        self.assertEqual(identity_tier(raw("X", address="1 A St")), "addr")
        self.assertEqual(identity_tier(raw("X")), "name")

    def test_no_place_id_falls_back_to_address_not_name(self):
        """Address is chosen over name because the name is the unstable field."""
        a = raw("Sauna House", address="1234 Larimer St")
        b = raw("Sauna House Denver", address="1234 Larimer St")
        self.assertEqual(identity_key(a), identity_key(b))

    def test_bare_street_and_geocoded_full_address_collapse(self):
        """The geocoder expands "1234 Larimer St" to a full address mid-pipeline."""
        bare = raw("X", address="1234 Larimer St")
        full = raw("X", address="1234 Larimer St, Denver, CO 80202")
        self.assertEqual(identity_key(bare), identity_key(full))

    def test_accents_normalise(self):
        self.assertEqual(
            identity_key(raw("Café Sek", address="1 Café St")),
            identity_key(raw("Cafe Sek", address="1 Cafe St")),
        )

    def test_identity_key_is_always_total(self):
        """No record may fall out of matching, however degenerate."""
        for rec in ({}, {"name": None}, {"metro": "x"}):
            self.assertIsInstance(identity_key(rec), str)
            self.assertTrue(identity_key(rec))


class TestDeterministicCollisionSuffixes(unittest.TestCase):
    """merger.py used to assign -2/-3 in crawler arrival order."""

    def test_suffix_does_not_depend_on_input_order(self):
        # Two DIFFERENT businesses whose names slugify identically.
        a = raw("Plunge Lab", place="0xaaa:0xaaa", address="1 First St")
        b = raw("Plunge Lab", place="0xbbb:0xbbb", address="2 Second St")

        reg1 = SlugRegistry()
        forward = {s["google_place_id"]: s["id"]
                   for s in merge_sources([dict(a), dict(b)], registry=reg1)}

        reg2 = SlugRegistry()
        reverse = {s["google_place_id"]: s["id"]
                   for s in merge_sources([dict(b), dict(a)], registry=reg2)}

        self.assertEqual(
            forward, reverse,
            "slug assignment must not depend on which crawler returned first — "
            "order-dependent suffixes could swap two live URLs' contents",
        )
        self.assertEqual(len(set(forward.values())), 2, "ids must stay unique")

    def test_suffix_is_stable_across_runs(self):
        a = raw("Plunge Lab", place="0xaaa:0xaaa", address="1 First St")
        b = raw("Plunge Lab", place="0xbbb:0xbbb", address="2 Second St")
        reg = SlugRegistry()
        run1 = {s["google_place_id"]: s["id"]
                for s in merge_sources([dict(a), dict(b)], registry=reg)}
        run2 = {s["google_place_id"]: s["id"]
                for s in merge_sources([dict(b), dict(a)], registry=reg)}
        self.assertEqual(run1, run2)

    def test_no_registry_still_produces_unique_ids(self):
        """Backward compatibility: registry is optional."""
        a = raw("Plunge Lab", place="0xaaa:0xaaa", address="1 First St")
        b = raw("Plunge Lab", place="0xbbb:0xbbb", address="2 Second St")
        out = merge_sources([a, b], registry=None)
        self.assertEqual(len({s["id"] for s in out}), 2)


class TestLiveDatasetSeeding(unittest.TestCase):
    """Seeding the real studios.json must not repoint a single live URL."""

    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parent.parent.parent / "studios.json"
        cls.studios = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def test_every_live_slug_is_preserved(self):
        if self.studios is None:
            self.skipTest("studios.json not present")
        reg, collisions = SlugRegistry.from_studios(self.studios)
        self.assertEqual(
            len(reg), len(self.studios),
            "the registry must contain one entry per live record — a collapsed "
            "entry means a live URL silently changed owner",
        )
        live_slugs = {s["id"] for s in self.studios}
        self.assertTrue(
            live_slugs.issubset(set(reg.mapping.values())),
            "every live slug must still be owned by some identity",
        )

    def test_committed_registry_matches_the_live_dataset(self):
        """The checked-in slug_registry.json must not drift from studios.json."""
        if self.studios is None:
            self.skipTest("studios.json not present")
        path = Path(__file__).resolve().parent.parent.parent / "slug_registry.json"
        if not path.exists():
            self.skipTest("slug_registry.json not generated yet")
        committed = SlugRegistry.load(path)
        expected, _ = SlugRegistry.from_studios(self.studios)
        self.assertEqual(
            committed.mapping, expected.mapping,
            "slug_registry.json is out of sync with studios.json — regenerate it",
        )


class TestIdentityTierChange(unittest.TestCase):
    """The 2026-10-10 bug: a studio’s identity tier changes between runs and
    the slug registry fails to find the existing entry — so the fresh record
    gets a “-2” slug and the real one appears to “disappear”. 11 of 15 URLs
    broke on that run exactly this way."""

    def test_addr_tier_upgrade_to_place_tier_preserves_slug(self):
        """Studio was addr-tier last run; Google Maps now gives a place_id."""
        registry = SlugRegistry()

        week1 = merge_sources(
            [raw("NAOSU Sauna", address="3145 Larimer St, Denver, CO 80205")],
            registry=registry,
        )
        original_slug = week1[0]["id"]

        # Same studio, same address, Maps now returns a google_place_id.
        week2 = merge_sources(
            [raw("NAOSU Sauna", address="3145 Larimer St, Denver, CO 80205",
                 place="0x876c791f428ca72f:0x1b5a85b0676536")],
            registry=registry,
        )
        self.assertEqual(
            week2[0]["id"], original_slug,
            "an addr\u2192place upgrade must keep the existing slug, not allocate "
            "<slug>-2 (the 2026-10-10 regression)",
        )

    def test_place_tier_downgrade_to_addr_tier_preserves_slug_via_seeding(self):
        """Studio was place-tier last run; Maps now returns no place_id.

        The scraper seeds fallback-tier aliases from the previous
        studios.json at the start of every run; without that, the registry
        has only the place-tier entry and a downgrade still breaks.
        """
        registry = SlugRegistry()

        week1 = merge_sources(
            [raw("The Cove Sauna and Cold Plunge",
                 address="1361 S Broadway, Denver, CO 80210",
                 place="0x876c7fe47f60749f:0x5a1784de3d69f406")],
            registry=registry,
        )
        original_slug = week1[0]["id"]

        # Simulate the per-run seeding step scrape.py performs: pass the
        # studios list through seed_fallback_tiers so addr and name aliases
        # exist alongside the primary place-tier entry.
        registry.seed_fallback_tiers(week1)

        # Same studio, same address, Maps now returns no place_id.
        week2 = merge_sources(
            [raw("The Cove Sauna and Cold Plunge",
                 address="1361 S Broadway, Denver, CO 80210")],
            registry=registry,
        )
        self.assertEqual(
            week2[0]["id"], original_slug,
            "a place\u2192addr downgrade must keep the existing slug via the "
            "seeded addr-tier alias",
        )

    def test_resolve_auto_upgrades_registry_entry(self):
        """When a weaker-tier alias saves the day, the stronger tiers of the
        fresh record are also recorded, so the next run short-circuits."""
        registry = SlugRegistry()

        week1 = merge_sources(
            [raw("Denver Sports Recovery",
                 address="2242 W 29th Ave, Denver, CO 80211")],
            registry=registry,
        )
        original_slug = week1[0]["id"]
        self.assertNotIn(
            "place:0x876c7894231f0c6b:0x25eae7438d58bfdf", registry.mapping,
            "primary tier was addr; no place entry should exist yet",
        )

        merge_sources(
            [raw("Denver Sports Recovery",
                 address="2242 W 29th Ave, Denver, CO 80211",
                 place="0x876c7894231f0c6b:0x25eae7438d58bfdf")],
            registry=registry,
        )
        self.assertEqual(
            registry.mapping.get("place:0x876c7894231f0c6b:0x25eae7438d58bfdf"),
            original_slug,
            "after an addr\u2192place upgrade, the registry should carry the new "
            "place-tier entry too so the next run finds it directly",
        )

    def test_seed_fallback_tiers_is_first_wins_and_idempotent(self):
        """Two studios colliding on a weaker-tier key must not swap owners,
        and calling twice must not duplicate."""
        registry = SlugRegistry()
        studios = [
            {"id": "first", "name": "First", "metro": "denver_co",
             "address": "100 Main St, Denver, CO",
             "google_place_id": "placeA"},
            {"id": "second", "name": "Second", "metro": "denver_co",
             "address": "100 Main St, Denver, CO",
             "google_place_id": "placeB"},
        ]
        n1 = registry.seed_fallback_tiers(studios)
        snapshot = dict(registry.mapping)
        n2 = registry.seed_fallback_tiers(studios)
        self.assertEqual(n2, 0, "re-seeding must add nothing — idempotent")
        self.assertEqual(snapshot, registry.mapping, "registry must not change")
        self.assertEqual(snapshot["place:placeA"], "first", "first studio keeps its primary")
        self.assertEqual(
            registry.mapping["addr:denver co|100 main st"], "first",
            "the two studios collide on addr-tier; the sorted-id winner takes it",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
