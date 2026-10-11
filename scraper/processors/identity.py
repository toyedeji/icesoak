"""Stable studio identity: identity keys and the persistent slug registry.

Two separate concerns that must not be conflated:

  identity_key(studio)  — "is this the same business as that one?"  Used to
                          match a freshly crawled record against last run's
                          record.  Process-local; never persisted on its own.

  SlugRegistry          — "which URL does this business own?"  Persisted to
                          slug_registry.json at the REPO ROOT so a studio keeps
                          its slug forever, even when Google Maps returns a
                          different spelling of its name next week.

Why the registry exists
-----------------------
merger._slug() keys on (name, search-city).  Maps returns name variants between
renders — the 2026-07-15 dataset contains both
"West Plano - Sauna /Cold Plunge /Hot Tub" and
"West Plano - Sauna/Cold Plunge/Hot Tub" as *separate* records — so the slug,
and therefore the live URL, churns.  12 of the 46 studios that "disappeared"
between 2026-07-15 and 2026-07-26 in fact reappeared under a different id:
not lost inventory, just broken URLs.

Keying the slug on the studio's own city instead of the search city would be
the correct design, but it would rewrite all 232 live URLs in a single commit.
Instead: the first slug a studio is ever assigned is recorded against its
identity key and reused verbatim from then on.  Existing URLs are preserved
exactly; only genuinely new studios get new slugs.

Identity tiers (first match wins)
---------------------------------
  1. place:<google_place_id>   — 174/232 of the live dataset.  Google's own
                                 stable per-place id; survives name changes.
  2. addr:<metro>|<street>     — 53/232.  The first line of the street address,
                                 normalised.  Chosen over the name because a
                                 street address is far more stable than a Maps
                                 display name.
  3. name:<metro>|<name>       — 5/232.  Last resort.  Still drift-prone in
                                 principle, but all five current members
                                 (SweatHouz / Contrast Studio locations) come
                                 from crawlers/franchise.py, which reads brand
                                 locator pages with stable markup — not from
                                 Maps.  See MIGRATION NOTES in the branch
                                 report before relying on this tier.

Multi-tier lookup (added 2026-10-10)
------------------------------------
The 2026-10-10 run dropped 15 studios because their identity *tier* changed
between runs: 10 of them went addr→place (Maps started returning a
google_place_id on this run for a studio that previously had none), 1 went
place→addr (the opposite), and the registry — keyed on primary tier only —
could not find the pre-existing slug and allocated "<slug>-2" instead.

`resolve()` now checks EVERY applicable tier of the fresh record against the
registry, so an upgrade is tolerated.  And `seed_fallback_tiers()`, called once
per run from scrape.py against the current studios.json, backfills the weaker-
tier entries for every known studio, so a downgrade is tolerated too.  The
primary key is still what new entries claim: fallbacks only come into play as
look-up aliases.
"""
import json
import re
import unicodedata
from pathlib import Path
from typing import Optional

# Registry filename, relative to the repo root (the podman volume mount), NOT
# to scraper/.  scraper/.dockerignore excludes studios.json but not data/, so a
# registry under scraper/data/ would be baked into the image and every write
# would be lost when the --rm container exits.
REGISTRY_FILENAME = "slug_registry.json"

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _ascii_fold(text: str) -> str:
    """Strip accents so 'café' and 'cafe' collapse to the same key."""
    return (
        unicodedata.normalize("NFKD", text or "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def _norm(text: Optional[str]) -> str:
    return _NON_ALNUM_RE.sub(" ", _ascii_fold(text or "").lower()).strip()


def _norm_street(address: Optional[str]) -> str:
    """Normalise the first line of a street address.

    Maps sometimes returns a bare street ("1234 Larimer St") and the geocoder
    later expands it to a full "street, city, ST ZIP".  Taking only the segment
    before the first comma keeps both forms on the same key.
    """
    if not address:
        return ""
    return _norm(address.split(",")[0])


def identity_key(studio: dict) -> str:
    """Return a stable cross-run identity for a studio record.

    Deliberately total: always returns a non-empty string, so no record can
    silently fall out of matching.  A record with no metro, address or name
    degrades to "name:|" and collides with other such records — acceptable,
    because merger._clean() already rejects records with no name.
    """
    place_id = (studio.get("google_place_id") or "").strip()
    if place_id:
        return f"place:{place_id}"

    metro = _norm(studio.get("metro"))
    street = _norm_street(studio.get("address"))
    if street:
        return f"addr:{metro}|{street}"

    return f"name:{metro}|{_norm(studio.get('name'))}"


def all_identity_keys(studio: dict) -> list:
    """Return every identity key useful for registry lookup, strongest first.

    `identity_key()` returns the single *primary* key for a studio.  This
    returns every lookup key that key could stand in for — primary plus any
    weaker tier that unambiguously identifies the same business.

    Name tier is DELIBERATELY omitted when a stronger tier applies: two
    different studios inside one metro can share a name (every Perspire Sauna
    Studio is called 'Perspire Sauna Studio'), so a name alias would quietly
    collapse their slugs on the next run.  Name tier is only ever used when
    it IS the primary — i.e. the franchise crawler returned a record with
    neither google_place_id nor address.

    Degenerate case (no metro, no address, no name) collapses to
    "name:|" so the invariant "every record has at least one key" holds.
    """
    keys: list = []
    place_id = (studio.get("google_place_id") or "").strip()
    if place_id:
        keys.append(f"place:{place_id}")

    metro = _norm(studio.get("metro"))
    street = _norm_street(studio.get("address"))
    if street:
        keys.append(f"addr:{metro}|{street}")

    if not keys:
        keys.append(f"name:{metro}|{_norm(studio.get('name'))}")
    return keys


def identity_tier(studio: dict) -> str:
    """Return 'place', 'addr' or 'name' — which tier identified this record.

    Used for reporting only; lets a run surface how much of the dataset is
    resting on the weakest tier.
    """
    return identity_key(studio).split(":", 1)[0]


class SlugRegistry:
    """Persistent identity_key -> slug mapping.

    Once a studio owns a slug it keeps it.  New studios claim their proposed
    slug, or the first free "<slug>-N" variant if another identity already owns
    it.  Claim order is the caller's responsibility — merger.merge_sources
    sorts by identity_key first so that two genuinely new studios colliding on
    the same base slug resolve the same way on every run.
    """

    def __init__(self, mapping: Optional[dict] = None):
        self._by_key: dict = dict(mapping or {})
        self._taken: set = set(self._by_key.values())
        # Proximity-tier index: normalized name -> list of (metro, lat, lng, slug).
        # Populated only by seed_fallback_tiers() against HEAD. The resolver
        # consults it as a last-chance match before allocating a new slug — see
        # resolve() for the when-and-why. Not persisted; rebuilt per run.
        self._by_proximity: dict = {}

    # ── construction ────────────────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path) -> "SlugRegistry":
        """Load from disk.  A missing or corrupt file yields an empty registry
        rather than raising: a lost registry must degrade to current behaviour
        (slugs recomputed from names), never abort the run."""
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        mapping = data.get("slugs") if "slugs" in data else data
        if not isinstance(mapping, dict):
            return cls()
        return cls({str(k): str(v) for k, v in mapping.items()})

    @classmethod
    def from_studios(cls, studios: list) -> tuple["SlugRegistry", list]:
        """Seed a registry from an existing studios.json, PRESERVING every URL.

        Returns (registry, collisions) where each collision is
        {"key", "kept", "shadowed"}.

        The 1:1 guarantee matters. Seeding the live 232-record dataset naively
        collapses 3 pairs of records that share a street address — genuine
        duplicates that deduper.py misses, because it keys on name+address and
        these pairs carry different names for the same address:

            addr:...|6252 camp bowie blvd      sweathouz-camp-bowie-fort-worth
                                               sweathouz-fort-worth-fort-worth
            addr:...|4300 paces ferry rd ...    sweathouz-vinings-vinings
                                               sweathouz-atlanta-atlanta
            addr:...|1035 alpharetta hwy ...    sweathouz-roswell-roswell
                                               sweathouz-alpharetta-alpharetta

        Letting the identity tier pick a winner would silently repoint 3 live
        URLs on the first run — the exact failure this registry exists to
        prevent. So the shadowed record is registered under a synthetic
        "<key>#<slug>" key instead, which identity_key() can never emit at crawl
        time. Both URLs therefore survive seeding unchanged.

        Consequence, deliberately left visible rather than papered over: on the
        next run the fresh crawl record for that address resolves to the KEPT
        slug, so the shadowed record is never re-seen and ages out through the
        normal missed_runs path after `max_missing_runs` runs. That is a genuine
        de-duplication with three weeks of notice — but it will eventually 404
        the shadowed URL, so merge the pair (and add a redirect) before then.
        """
        reg = cls()
        collisions: list = []
        # Sort by id, not identity_key: two records sharing an identity_key must
        # resolve in a stable order, and the id is the tiebreaker that decides
        # which URL is canonical.
        #
        # Only the primary identity_key is registered here.  Fallback-tier
        # aliases that make the registry robust to an identity-tier change
        # (addr <-> place) are added at run time by seed_fallback_tiers()
        # from scrape.py, so that the one-entry-per-studio invariant holds
        # for seeding/migration tools (which call this method directly).
        for studio in sorted(studios, key=lambda s: str(s.get("id") or "")):
            slug = studio.get("id")
            if not slug:
                continue
            key = identity_key(studio)
            if key in reg._by_key:
                shadow_key = f"{key}#{slug}"
                collisions.append({
                    "key": key,
                    "kept": reg._by_key[key],
                    "shadowed": slug,
                })
                reg._by_key[shadow_key] = slug
                reg._taken.add(slug)
                continue
            reg._by_key[key] = slug
            reg._taken.add(slug)
        return reg, collisions

    def seed_fallback_tiers(self, studios: list) -> int:
        """Add weaker-tier aliases for every studio currently in `studios`.

        For each record, register its addr and name tiers (in addition to
        whatever primary tier is already recorded) pointing at the record's
        slug — but ONLY if that key is unambiguous: no other studio in
        `studios` has the same key.  Shadow cases (two different studios
        sharing an addr key, e.g. the three SweatHouz locations at
        6252 Camp Bowie Blvd) are intentionally LEFT UNSEEDED, because
        there is no safe way to tell which HEAD slug a fresh crawl record
        at that addr belongs to; blindly matching the first one swaps live
        URLs' contents on a Google re-index, which is exactly the failure
        class the whole registry exists to prevent.

        First-wins per key is preserved as a safety net: if the registry
        already has an entry, it is not overwritten.  Returns the number of
        alias entries added.  Idempotent — safe to call every run.

        Why: a studio can shift tiers between runs (Google Maps starts or
        stops returning a google_place_id).  Without alias entries the
        registry sees the fresh primary key as new and allocates "<slug>-2".
        The 2026-10-10 run lost 11 URLs to exactly this.
        """
        # First pass: count how many studios claim each potential alias key.
        # A key claimed by two or more studios is a "shadow" and must not be
        # offered as a lookup alias — see docstring.
        key_claimants: dict = {}
        for studio in studios:
            if not studio.get("id"):
                continue
            for k in all_identity_keys(studio):
                key_claimants[k] = key_claimants.get(k, 0) + 1

        # Second pass: seed only unambiguous keys, deterministic by id.
        added = 0
        for studio in sorted(studios, key=lambda s: str(s.get("id") or "")):
            slug = studio.get("id")
            if not slug:
                continue
            for k in all_identity_keys(studio):
                if k in self._by_key:
                    continue
                if key_claimants.get(k, 0) > 1:
                    continue  # shadow — do not alias
                self._by_key[k] = slug
                added += 1
            self._taken.add(slug)

            # Third seeding tier: normalized-name + metro + coordinates. Used
            # by resolve() when primary and addr tiers both miss — the exact
            # case where a studio shifts place_id and address between runs
            # (Perspire chain-page restructure, SweatHouz vendor-page addresses
            # mangled on crawl). Only seeded when the HEAD record has coords;
            # otherwise there is nothing for the proximity check to measure.
            lat = studio.get("lat")
            lng = studio.get("lng")
            if lat is None or lng is None:
                continue
            metro = _norm(studio.get("metro"))
            name_key = _norm(studio.get("name"))
            if not name_key:
                continue
            self._by_proximity.setdefault(name_key, []).append(
                (metro, float(lat), float(lng), slug)
            )
        return added

    @staticmethod
    def _coords_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Approximate great-circle distance in metres.

        Equirectangular projection — accurate to a few metres at <5km and well
        below the 100m threshold we actually compare against. Avoids importing
        math.sin/cos/asin per lookup.
        """
        import math
        lat_mid = math.radians((lat1 + lat2) / 2.0)
        x = math.radians(lng2 - lng1) * math.cos(lat_mid)
        y = math.radians(lat2 - lat1)
        return math.hypot(x, y) * 6371000.0

    def _match_by_proximity(self, studio: dict, threshold_m: float = 100.0) -> Optional[str]:
        """Return an existing slug if a HEAD studio with the same normalized
        name sits within `threshold_m` metres of this record. None otherwise.

        Why: a chain re-crawled on a different date can arrive with a changed
        place_id and a vendor-page address that geocodes elsewhere — same
        business, different identity tiers. If the normalized name and the
        location both match a HEAD record, that is the same business, and the
        existing slug must be preserved rather than allocated "-2".
        """
        lat = studio.get("lat")
        lng = studio.get("lng")
        if lat is None or lng is None:
            return None
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except (TypeError, ValueError):
            return None
        name_key = _norm(studio.get("name"))
        if not name_key:
            return None
        candidates = self._by_proximity.get(name_key, ())
        if not candidates:
            return None
        metro = _norm(studio.get("metro"))
        best_slug: Optional[str] = None
        best_dist: float = threshold_m
        for cand_metro, cand_lat, cand_lng, cand_slug in candidates:
            # Metro must match too — two Perspire Sauna Studios 2 miles apart in
            # the same city are the same chain but different studios, which the
            # proximity check correctly separates. Metro mismatch guards the
            # degenerate case where two different cities happen to share a chain
            # location name.
            if cand_metro and metro and cand_metro != metro:
                continue
            dist = self._coords_distance_m(lat_f, lng_f, cand_lat, cand_lng)
            if dist < best_dist:
                best_dist = dist
                best_slug = cand_slug
        return best_slug

    # ── use ─────────────────────────────────────────────────────────────────

    def resolve(self, studio: dict, proposed_slug: str) -> str:
        """Return the slug this studio owns, claiming `proposed_slug` if new.

        Checks EVERY applicable identity tier of the fresh record, strongest
        first, so a run that upgrades a studio's primary tier (addr → place,
        say, because Google Maps now returns a place_id) still resolves to
        the existing slug via the weaker-tier entry.  When a match is found
        at a weaker tier, the stronger tiers of the fresh record are also
        recorded as aliases so the next run short-circuits on the primary.

        Last-chance fallback — proximity tier: if every explicit identity key
        misses, consult the normalized-name + metro + coords index built by
        seed_fallback_tiers(). A fresh record whose name matches a HEAD
        record's name and whose coordinates sit within 100m of HEAD's is the
        same business even if its place_id and address have drifted. This
        prevents the Perspire / SweatHouz class of regression where a
        re-crawled chain location acquired a different Google Maps place_id
        and ended up at "-2".
        """
        keys = all_identity_keys(studio)

        for k in keys:
            existing = self._by_key.get(k)
            if existing:
                # Auto-upgrade: register any stronger tiers of the fresh
                # record too, so next run finds the primary immediately.
                for alias in keys:
                    if alias not in self._by_key:
                        self._by_key[alias] = existing
                return existing

        # Proximity-tier match — same name, same metro, within 100m.
        existing = self._match_by_proximity(studio)
        if existing:
            for alias in keys:
                if alias not in self._by_key:
                    self._by_key[alias] = existing
            return existing

        # No match at any tier — allocate a fresh slug.
        slug = self._first_free(proposed_slug)
        for k in keys:
            if k not in self._by_key:
                self._by_key[k] = slug
        self._taken.add(slug)
        return slug

    def _first_free(self, base: str) -> str:
        """base, else base-2, base-3, … — the deterministic collision ladder."""
        base = base or "studio"
        if base not in self._taken:
            return base
        n = 2
        while f"{base}-{n}" in self._taken:
            n += 1
        return f"{base}-{n}"

    def get(self, studio: dict) -> Optional[str]:
        return self._by_key.get(identity_key(studio))

    def __len__(self) -> int:
        return len(self._by_key)

    def __contains__(self, key: str) -> bool:
        return key in self._by_key

    @property
    def mapping(self) -> dict:
        return dict(self._by_key)

    # ── persistence ─────────────────────────────────────────────────────────

    def save(self, path: Path) -> None:
        """Write sorted, so the committed diff shows only real changes."""
        payload = {
            "_comment": (
                "identity_key -> slug. Generated by the scraper; do not hand-edit. "
                "An entry here pins a studio's live URL: removing one will cause "
                "that studio to be re-slugged from its current Maps name on the "
                "next run, breaking the existing URL."
            ),
            "slugs": {k: self._by_key[k] for k in sorted(self._by_key)},
        }
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
