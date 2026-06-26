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

METROS = [
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
]


async def run() -> None:
    today = date.today().isoformat()
    all_records: list = []

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

    for metro in METROS:
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
    out.write_text(json.dumps(studios, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Wrote %d studios → %s", len(studios), out)

    # ── Questions ────────────────────────────────────────────────────────────
    from crawlers.questions import harvest_questions
    questions = await harvest_questions()
    q_out = WORK_DIR / "questions.json"
    q_out.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Wrote %d questions → %s", len(questions), q_out)


if __name__ == "__main__":
    asyncio.run(run())
