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


async def run(metro_filter: list[str] | None = None) -> None:
    today = date.today().isoformat()
    all_records: list = []

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

    for metro in metros:
        log.info("━━ Metro: %s ━━", metro["name"])

        gm = await scrape_google_maps(metro)
        log.info("Google Maps → %d records", len(gm))
        all_records.extend(gm)

        fr = await scrape_franchises(metro)
        log.info("Franchises  → %d records", len(fr))
        all_records.extend(fr)

        li = await scrape_listicles(metro)
        log.info("Listicles   → %d records", len(li))
        all_records.extend(li)

    # ── Dedup ───────────────────────────────────────────────────────────────
    deduped = deduplicate(all_records)

    # ── Enrich from studio websites ──────────────────────────────────────────
    enriched = await enrich_studios(deduped, today)

    # ── Final merge + validation ─────────────────────────────────────────────
    studios = merge_sources(enriched)

    # ── Geocode addresses → lat/lng (cached; 1 req/sec Nominatim policy) ─────
    from processors.geocoder import geocode_studios
    studios, geo_stats = geocode_studios(studios)
    log.info(
        "Geocoding: %d new, %d cached, %d failed, %d no-address",
        geo_stats["geocoded"], geo_stats["from_cache"],
        geo_stats["failed"], geo_stats["no_address"],
    )

    # ── Write studios.json ───────────────────────────────────────────────────
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out = WORK_DIR / "studios.json"

    if metro_filter and out.exists():
        # Partial run: merge new records into existing studios.json instead of
        # overwriting it.  For each targeted metro, replace existing records
        # only when the scrape actually returned data; if a metro came back
        # empty (blocked / no results) keep the old records and warn.
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
                kept.append(s)  # not targeted — always keep
            # targeted metros are rebuilt below; don't carry old records forward

        added: list = []
        for mid in scraped_metro_ids:
            fresh = new_by_metro[mid]
            if fresh:
                added.extend(fresh)
                replaced_metros.append(mid)
            else:
                # Zero-result protection: scraper was blocked — keep old data
                old = [s for s in existing if s.get("metro") == mid]
                kept.extend(old)
                preserved_metros.append(mid)
                log.warning(
                    "WARNING: %s returned 0 studios — preserving existing %d records "
                    "rather than wiping.",
                    mid, len(old),
                )

        merged = kept + added
        out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
        other_metros = sorted({s.get("metro") for s in kept})
        log.info(
            "Merged %d new records for metros %s. "
            "Preserved %d records from %s. Total: %d studios → %s",
            len(added), replaced_metros,
            len(kept), other_metros,
            len(merged), out,
        )
    else:
        # Full run (or first run with no existing file): write fresh.
        out.write_text(json.dumps(studios, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("Wrote %d studios → %s", len(studios), out)

    # ── Questions ────────────────────────────────────────────────────────────
    from crawlers.questions import harvest_questions
    questions = await harvest_questions()
    q_out = WORK_DIR / "questions.json"
    q_out.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Wrote %d questions → %s", len(questions), q_out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IceSoak studio scraper")
    parser.add_argument(
        "--metros", nargs="+", metavar="METRO",
        help="Limit scrape to specific metros (e.g. austin chicago). "
             f"Available: {', '.join(_METRO_ALIAS.keys())}",
    )
    args = parser.parse_args()
    asyncio.run(run(metro_filter=args.metros))
