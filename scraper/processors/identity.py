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

    # ── use ─────────────────────────────────────────────────────────────────

    def resolve(self, studio: dict, proposed_slug: str) -> str:
        """Return the slug this studio owns, claiming `proposed_slug` if new."""
        key = identity_key(studio)
        existing = self._by_key.get(key)
        if existing:
            return existing

        slug = self._first_free(proposed_slug)
        self._by_key[key] = slug
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
