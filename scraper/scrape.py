#!/usr/bin/env python3
"""IceSoak studio directory scraper.

Entrypoint for nightly container runs:
    podman run --rm --shm-size=1g -v /opt/icesoak:/work -w /work <image> \
        python scraper/scrape.py

Outputs are written to the REPO ROOT (the parent of this scraper/ folder), so the
Next.js build reads a single source-of-truth file:
    <repo root>/studios.json   – deduplicated, schema-validated studio records
    <repo root>/questions.json – harvested PAA / Reddit questions
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("icesoak")

# Repo root = the parent of this scraper/ directory. Outputs are written here so
# the Next.js app reads ONE studios.json / questions.json at the repo root.
# WORK_DIR env var still overrides (e.g. if a volume is mounted elsewhere).
REPO_ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = Path(os.environ["WORK_DIR"]) if os.environ.get("WORK_DIR") else REPO_ROOT
SEED_FILE = Path(__file__).resolve().parent / "data" / "seed_studios.json"

# The slug registry lives at the REPO ROOT (the podman volume mount), next to
# studios.json — NOT under scraper/data/. scraper/.dockerignore does not exclude
# data/, so a registry there would be baked into the image and every write would
# vanish when the --rm container exits, silently re-enabling slug churn.
from processors.identity import REGISTRY_FILENAME, SlugRegistry  # noqa: E402
from processors.retention import (  # noqa: E402
    RetentionAbort,
    max_missing_runs_from_env,
    merge_with_previous,
    metros_with_no_fresh_records,
    previous_run_date_from_git,
    read_previous,
)
from utils.blocking import (  # noqa: E402
    SearchStats,
    max_search_failure_rate_from_env,
)

ALL_METROS = [
    {
        "id": "denver_co",
        "name": "Denver",
        "state": "CO",
        "cities": [
            "Denver", "Aurora", "Lakewood", "Arvada", "Westminster",
            "Englewood", "Centennial", "Littleton", "Boulder", "Highlands Ranch",
        ],
    },
    {
        "id": "dallas_fort_worth_tx",
        "name": "Dallas–Fort Worth",
        "state": "TX",
        "cities": [
            "Dallas", "Fort Worth", "Plano", "Frisco", "McKinney",
            "Irving", "Garland", "Arlington", "Richardson", "Southlake",
            "Grapevine", "Addison", "Allen", "Flower Mound", "Lewisville",
        ],
    },
    {
        "id": "philadelphia_pa",
        "name": "Philadelphia",
        "state": "PA",
        "cities": [
            "Philadelphia", "King of Prussia", "Cherry Hill", "Ardmore",
            "Conshohocken", "Wayne", "Horsham", "Lansdale", "Blue Bell",
            "Jenkintown", "Media",
        ],
    },
    {
        "id": "austin_tx",
        "name": "Austin",
        "state": "TX",
        "cities": [
            "Austin", "Round Rock", "Cedar Park", "Pflugerville", "Georgetown",
            "Lakeway", "Bee Cave", "Kyle", "Buda", "Manor",
        ],
    },
    {
        "id": "chicago_il",
        "name": "Chicago",
        "state": "IL",
        "cities": [
            "Chicago", "Evanston", "Oak Park", "Naperville", "Schaumburg",
            "Aurora", "Joliet", "Wicker Park", "Lincoln Park", "River North",
            "Bucktown", "Lakeview", "South Loop",
        ],
    },
    {
        "id": "atlanta_ga",
        "name": "Atlanta",
        "state": "GA",
        "cities": [
            "Atlanta", "Buckhead", "Midtown", "Decatur", "Sandy Springs",
            "Marietta", "Alpharetta", "Roswell", "Dunwoody", "Brookhaven",
            "Smyrna", "Vinings", "Virginia Highland",
        ],
    },
    {
        "id": "seattle_wa",
        "name": "Seattle",
        "state": "WA",
        "cities": [
            "Seattle", "Bellevue", "Redmond", "Kirkland", "Bothell",
            "Shoreline", "Renton", "Burien", "Capitol Hill", "Queen Anne",
            "Fremont", "Ballard", "West Seattle",
        ],
    },
    {
        "id": "miami_fl",
        "name": "Miami",
        "state": "FL",
        "cities": [
            "Miami", "Miami Beach", "Coral Gables", "Brickell", "Wynwood",
            "Coconut Grove", "Aventura", "Hollywood", "Fort Lauderdale",
            "Doral", "Hialeah", "South Beach",
        ],
    },
    {
        "id": "nashville_tn",
        "name": "Nashville",
        "state": "TN",
        "cities": [
            "Nashville", "Brentwood", "Franklin", "Murfreesboro", "Hendersonville",
            "Germantown", "East Nashville", "12 South", "Gulch", "Bellevue",
        ],
    },
    {
        "id": "los_angeles_ca",
        "name": "Los Angeles",
        "state": "CA",
        "cities": [
            "Los Angeles", "West Hollywood", "Beverly Hills", "Santa Monica",
            "Culver City", "Brentwood", "West LA", "Silver Lake", "Los Feliz",
            "Echo Park", "Venice", "Marina del Rey", "Playa Vista",
            "Pasadena", "Burbank", "Glendale", "Studio City", "Sherman Oaks",
        ],
    },
    {
        "id": "phoenix_az",
        "name": "Phoenix",
        "state": "AZ",
        "cities": [
            "Phoenix", "Scottsdale", "Tempe", "Mesa", "Chandler",
            "Gilbert", "Peoria", "Glendale", "Surprise", "Goodyear",
            "Paradise Valley", "Fountain Hills", "Cave Creek",
        ],
    },
]

# Short alias map: scrape.py --metros austin chicago → resolves to full metro IDs
_METRO_ALIAS = {m["id"]: m["id"] for m in ALL_METROS}
_METRO_ALIAS.update({
    "denver": "denver_co",
    "dallas": "dallas_fort_worth_tx", "dfw": "dallas_fort_worth_tx",
    "philadelphia": "philadelphia_pa", "philly": "philadelphia_pa",
    "austin": "austin_tx",
    "chicago": "chicago_il",
    "atlanta": "atlanta_ga",
    "seattle": "seattle_wa",
    "miami": "miami_fl",
    "nashville": "nashville_tn",
    "los_angeles": "los_angeles_ca", "la": "los_angeles_ca", "los angeles": "los_angeles_ca",
    "phoenix": "phoenix_az", "phx": "phoenix_az",
})


def _apply_sticky_modalities(records: list, prev_path: Path) -> int:
    """Carry previously-known modalities onto records that re-scraped with an
    empty modalities list, keyed by the stable studio id (_slug of name+city).

    The crawl only derives modalities for known franchises and for studios whose
    website text matches a modality pattern; every other record comes back with
    an empty list. Without this, hand-curated / backfilled modality tags would be
    wiped on every weekly run. Fresh, non-empty modalities always win — this only
    fills gaps, so a studio that genuinely changes its services still updates.
    Returns the number of records patched.
    """
    if not prev_path.exists():
        return 0
    try:
        previous = json.loads(prev_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0
    prev_mods = {
        s.get("id"): s["modalities"]
        for s in previous
        if s.get("id") and s.get("modalities")
    }
    patched = 0
    for s in records:
        if not s.get("modalities"):
            inherited = prev_mods.get(s.get("id"))
            if inherited:
                s["modalities"] = list(inherited)
                patched += 1
    return patched


# ── Question merge ───────────────────────────────────────────────────────────
# questions.json is written by TWO pipelines: harvest_questions() below supplies
# the stub fields, and a separate content pass fills in the prose. Until
# 2026-07-28 this file was overwritten wholesale on every scrape, so each run
# silently destroyed the content pass's work — see the sawtooth in git history
# (267 KB on 2026-07-06, 8 KB on 2026-07-12, and a literal [] on 2026-07-19).
# studios.json already merges and preserves sticky fields; questions.json never
# did. It does now.

# Owned by the content pass. The scraper must never author or clear these.
#
# risk_tier is on this list for a specific reason: the site suppresses the
# affiliate block and renders a medical disclaimer based on it (see
# app/guides/[slug]/page.tsx). A harvest that dropped the field would silently
# put a cold-plunge tub back at the bottom of a page about autoimmune thyroid
# disease, with no build error and nothing in the diff to notice. This list is a
# whitelist, so a new content-owned field is invisible to the merge until it is
# added here.
CONTENT_FIELDS = (
    "capsule", "sections", "faqs", "author", "category", "updated", "risk_tier",
)

# Owned by the scraper. Refreshed from every harvest.
HARVEST_FIELDS = ("slug", "question", "type", "metro")


def _merge_questions(harvested: list, existing: list) -> tuple[list, list]:
    """Merge harvested stubs into existing records, preserving content fields.

    Returns (merged, retained_dropped) where retained_dropped are records the
    harvest no longer returns but which still carry prose.

    Removed slugs: a slug vanishing from a harvest usually means PAA/Reddit
    stopped surfacing that phrasing, not that the guide is worthless. So a
    dropped slug that HAS prose is retained (it is a live, linked, possibly
    ranking URL — deleting it would 404 real content), while a dropped slug
    that is still an empty stub is discarded, since nothing is lost.
    """
    by_slug = {
        q.get("slug"): q
        for q in existing
        if isinstance(q, dict) and isinstance(q.get("slug"), str)
    }

    merged = []
    for h in harvested:
        slug = h.get("slug")
        rec = dict(h)                      # harvest fields win
        prev = by_slug.pop(slug, None)
        if prev:
            for f in CONTENT_FIELDS:       # content fields survive
                if prev.get(f):
                    rec[f] = prev[f]
        merged.append(rec)

    retained = [
        q for q in by_slug.values() if any(q.get(f) for f in CONTENT_FIELDS)
    ]
    return merged + retained, retained


def partition_previous(previous: list, metro_filter: list[str] | None) -> tuple[list, list]:
    """Split the previous dataset into (in_scope, untouched) for this run.

    The ONLY difference between a full run and a --metros run. Records outside
    the targeted metros were never crawled, so they must not be judged as
    "missed" by retention — they pass through untouched. On a full run every
    record is in scope and nothing passes through.

    Extracted so tests can exercise the real partitioning rather than a copy of
    it. The previous version of scraper/tests/test_merge_logic.py reimplemented
    the write logic inline and asserted against its own copy, which is why it
    still passed while the production path it was supposed to describe was
    wholesale-overwriting studios.json every week.
    """
    if not metro_filter:
        return list(previous), []

    scraped_metro_ids = {
        _METRO_ALIAS.get(m.lower(), m.lower()) for m in metro_filter
    }
    in_scope = [s for s in previous if s.get("metro") in scraped_metro_ids]
    untouched = [s for s in previous if s.get("metro") not in scraped_metro_ids]
    return in_scope, untouched


def _read_existing_questions(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Could not read existing %s (%s) — treating as empty.", path, exc)
        return []
    return data if isinstance(data, list) else []


async def run(
    metro_filter: list[str] | None = None,
    force: bool = False,
    max_missing_runs: int | None = None,
    max_search_failure_rate: float | None = None,
) -> None:
    today = date.today().isoformat()
    all_records: list = []

    if max_missing_runs is None:
        max_missing_runs = max_missing_runs_from_env()
    if max_search_failure_rate is None:
        max_search_failure_rate = max_search_failure_rate_from_env()
    log.info(
        "Retention: a studio is dropped after %d consecutive runs without being "
        "seen. Abort if > %.0f%% of Maps searches fail.",
        max_missing_runs, max_search_failure_rate * 100,
    )

    metros = ALL_METROS
    if metro_filter:
        resolved = {_METRO_ALIAS.get(m.lower(), m.lower()) for m in metro_filter}
        metros = [m for m in ALL_METROS if m["id"] in resolved]
        if not metros:
            log.error("No known metros matched: %s", metro_filter)
            sys.exit(1)
        log.info("Filtering to metros: %s", [m["id"] for m in metros])


    # ── Seed baseline (provisional; crawler output overwrites) ──────────────
    if SEED_FILE.exists():
        seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
        log.info("Loaded %d seed records (source=seed, last_verified=null)", len(seed))
        all_records.extend(seed)
    else:
        log.warning("No seed file at %s; starting from scratch", SEED_FILE)

    # ── Live crawl per metro ─────────────────────────────────────────────────
    from crawlers.google_maps import scrape_google_maps
    from crawlers.franchise import scrape_franchises
    from crawlers.listicles import scrape_listicles
    from crawlers.studio_detail import enrich_studios
    from processors.deduper import deduplicate
    from processors.merger import merge_sources

    # Per-run tally of Maps search outcomes. Before this existed a consent wall,
    # CAPTCHA or 429 produced zero records, one warning line, and a run that
    # carried on to write a partial dataset as though it were complete.
    search_stats = SearchStats(max_failure_rate=max_search_failure_rate)

    for metro in metros:
        log.info("━━ Metro: %s ━━", metro["name"])

        gm = await scrape_google_maps(metro, stats=search_stats)
        log.info("Google Maps → %d records", len(gm))
        all_records.extend(gm)

        fr = await scrape_franchises(metro)
        log.info("Franchises  → %d records", len(fr))
        all_records.extend(fr)

        li = await scrape_listicles(metro)
        log.info("Listicles   → %d records", len(li))
        all_records.extend(li)

    # ── Crawl health gate ───────────────────────────────────────────────────
    log.info("Maps search outcomes: %s", search_stats.summary())
    dark_metros = search_stats.fully_failed_metros()
    if dark_metros:
        log.warning(
            "Metros where EVERY Maps search failed: %s — this is the clustered "
            "signature of partial rate limiting, not of businesses closing.",
            ", ".join(dark_metros),
        )
    if search_stats.should_abort():
        log.error(
            "ABORT: %.0f%% of Maps searches failed (threshold %.0f%%). %s. "
            "Refusing to write studios.json from a partially-observed crawl. "
            "Back off, then re-run; override with "
            "ICESOAK_MAX_SEARCH_FAILURE_RATE if this is expected.",
            search_stats.failure_rate * 100,
            search_stats.max_failure_rate * 100,
            search_stats.summary(),
        )
        sys.exit(1)

    # ── Dedup ───────────────────────────────────────────────────────────────
    deduped = deduplicate(all_records)

    # ── Enrich from studio websites ──────────────────────────────────────────
    enriched = await enrich_studios(deduped, today)

    # ── Final merge + validation ─────────────────────────────────────────────
    # The registry pins each studio's slug to its identity, so a Maps name
    # variant can no longer re-slug an existing studio and break its live URL.
    registry_path = WORK_DIR / REGISTRY_FILENAME
    registry = SlugRegistry.load(registry_path)
    registry_size_before = len(registry)
    studios = merge_sources(enriched, registry=registry)

    # ── Geocode addresses → lat/lng (cached; 1 req/sec Nominatim policy) ─────
    from processors.geocoder import geocode_studios
    studios, geo_stats = geocode_studios(studios)
    log.info(
        "Geocoding: %d new, %d cached, %d failed, %d no-address",
        geo_stats["geocoded"], geo_stats["from_cache"],
        geo_stats["failed"], geo_stats["no_address"],
    )

    # ── Write studios.json ───────────────────────────────────────────────────
    #
    # ONE path for both full and partial runs. The bug this replaces was
    # structural, not arithmetical: the merge-and-preserve logic (including the
    # explicit "scraper was blocked - keep old data" guard) lived only on the
    # `if metro_filter and out.exists():` branch, and the scheduled weekly run
    # never takes that branch. It fell through to a bare
    # `out.write_text(json.dumps(studios))` and inventory became whatever that
    # single crawl happened to see.
    #
    # The difference between the two run kinds is now only WHICH records are in
    # scope for comparison, not whether retention applies at all.
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out = WORK_DIR / "studios.json"

    previous = read_previous(out)

    scoped_previous, untouched = partition_previous(previous, metro_filter)
    if metro_filter:
        log.info(
            "Partial run: %d records in scope, %d passed through untouched",
            len(scoped_previous), len(untouched),
        )

    # Metros that had records before and returned nothing now. Retention already
    # protects them; this says so out loud, because a metro-shaped hole is the
    # signature of partial rate limiting.
    for metro_id in metros_with_no_fresh_records(studios, scoped_previous):
        log.warning(
            "Metro %s returned 0 studios this run — its records are retained "
            "(missed_runs incremented), not wiped.", metro_id,
        )

    try:
        merged_scope, retention_stats = merge_with_previous(
            fresh=studios,
            previous=scoped_previous,
            run_date=today,
            previous_run_date=previous_run_date_from_git(WORK_DIR),
            max_missing_runs=max_missing_runs,
        )
    except RetentionAbort as exc:
        log.error("ABORT: %s", exc)
        sys.exit(1)

    merged_studios = untouched + merged_scope

    # Kept alongside retention's field-level fill-forward as a second, id-keyed
    # safety net for hand-curated modality tags. Only fills empties, so it can
    # never contradict a fresh non-empty crawl result.
    sticky = _apply_sticky_modalities(merged_studios, out)
    if sticky:
        log.info("Preserved modalities on %d studios that re-scraped empty.", sticky)

    out.write_text(
        json.dumps(merged_studios, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    log.info(
        "Wrote %d studios → %s  (crawl returned %d: %d re-seen, %d new; "
        "%d retained unseen, %d dropped after %d consecutive misses; "
        "%d empty fields filled from previous)",
        len(merged_studios), out, retention_stats["fresh"], retention_stats["reseen"],
        retention_stats["new"], retention_stats["retained"],
        retention_stats["dropped"], max_missing_runs,
        retention_stats["filled_fields"],
    )
    log.info(
        "Crawl re-observed %.0f%% of the previous dataset; %d records now carry "
        "missed_runs > 0. Identity tiers: %s",
        retention_stats["fresh_ratio"] * 100, retention_stats["stale"],
        retention_stats["identity_tiers"],
    )
    if retention_stats["dropped"]:
        log.warning(
            "Dropped %d studios that were missing from %d consecutive runs: %s",
            retention_stats["dropped"], max_missing_runs,
            ", ".join(str(i) for i in retention_stats["dropped_ids"]),
        )

    # Persist the slug registry so today's assignments hold next week.
    registry.save(registry_path)
    log.info(
        "Slug registry: %d entries (%+d this run) → %s",
        len(registry), len(registry) - registry_size_before, registry_path,
    )

    # ── Questions ────────────────────────────────────────────────────────────
    from crawlers.questions import harvest_questions
    harvested = await harvest_questions()
    q_out = WORK_DIR / "questions.json"
    existing = _read_existing_questions(q_out)

    # Guard 1: never let an empty harvest truncate the file. Commit f5880df
    # (2026-07-19) wrote a literal [] this way, which would have 404'd all 52
    # guide URLs on the next deploy.
    if not harvested and not force:
        log.error(
            "Harvest returned 0 questions — refusing to overwrite %s (%d existing). "
            "Re-run with --force to override.",
            q_out, len(existing),
        )
        return

    merged, retained = _merge_questions(harvested, existing)

    # Guard 2: refuse a materially smaller file. A harvest that collapses is a
    # scrape failure, not an editorial decision.
    THRESHOLD = 0.8
    if existing and len(merged) < len(existing) * THRESHOLD and not force:
        log.error(
            "Refusing to shrink %s from %d to %d entries (below %.0f%% of existing). "
            "This usually means the harvest partially failed. Re-run with --force "
            "if the reduction is intended.",
            q_out, len(existing), len(merged), THRESHOLD * 100,
        )
        return

    preserved = sum(1 for q in merged if any(q.get(f) for f in CONTENT_FIELDS))
    q_out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(
        "Wrote %d questions → %s (%d harvested, %d with content preserved, "
        "%d retained despite dropping out of the harvest)",
        len(merged), q_out, len(harvested), preserved, len(retained),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IceSoak studio scraper")
    parser.add_argument(
        "--metros", nargs="+", metavar="METRO",
        help="Limit scrape to specific metros (e.g. austin chicago). "
             f"Available: {', '.join(_METRO_ALIAS.keys())}",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Override the questions.json safety guards (empty harvest, or a "
             "materially smaller file). Use only when the reduction is intended.",
    )
    parser.add_argument(
        "--max-missing-runs", type=int, default=None, metavar="N",
        help="Consecutive runs a studio may be missing before it is removed "
             "(default 3, or ICESOAK_MAX_MISSING_RUNS). Absence from one crawl "
             "is far more often a Maps render miss than a closure.",
    )
    parser.add_argument(
        "--max-search-failure-rate", type=float, default=None, metavar="F",
        help="Abort the run if more than this fraction of Maps searches fail "
             "(default 0.25, or ICESOAK_MAX_SEARCH_FAILURE_RATE).",
    )
    args = parser.parse_args()
    asyncio.run(run(
        metro_filter=args.metros,
        force=args.force,
        max_missing_runs=args.max_missing_runs,
        max_search_failure_rate=args.max_search_failure_rate,
    ))
