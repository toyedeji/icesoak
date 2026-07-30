import logging
import re
import unicodedata
from typing import Optional
from utils.schema import (
    VALID_STATUSES, VALID_MODALITIES, VALID_FORMATS,
    VALID_SESSION_STYLES, VALID_ACCESS, VALID_AMENITIES,
)
from utils.franchise_map import modalities_for_name
from processors.identity import identity_key

log = logging.getLogger(__name__)


def merge_sources(studios: list, registry=None) -> list:
    """Validate, clean, assign stable IDs, and return the final record list.

    ID assignment, and why it is ordered
    ------------------------------------
    The previous implementation walked `output` in arrival order and appended
    "-2"/"-3" to whichever colliding record it happened to meet second:

        for studio in output:
            base = studio["id"]
            if base in seen_ids: studio["id"] = f"{base}-{seen_ids[base]}"

    Arrival order is a property of which crawler returned first, so two studios
    colliding on one base slug could swap ids between runs — silently swapping
    two live URLs' contents.

    Now: records are processed in `identity_key` order (stable across runs,
    independent of crawler timing), and a SlugRegistry — if supplied — returns
    the slug this studio already owns, so a Maps name variant can no longer
    re-slug an existing studio.  Collision suffixes come from the registry's
    deterministic ladder.  With no registry the behaviour degrades to the old
    scheme but keeps the deterministic ordering.
    """
    output = []
    for studio in studios:
        cleaned = _clean(studio)
        if cleaned:
            output.append(cleaned)

    # Deterministic, crawler-order-independent claim sequence.
    ordered = sorted(output, key=identity_key)

    if registry is not None:
        for studio in ordered:
            studio["id"] = registry.resolve(studio, studio["id"])
    else:
        seen_ids: dict = {}
        for studio in ordered:
            base = studio["id"]
            if base in seen_ids:
                seen_ids[base] += 1
                studio["id"] = f"{base}-{seen_ids[base]}"
            else:
                seen_ids[base] = 1

    log.info("Final record count: %d", len(output))
    return output


def _clean(studio: dict) -> Optional[dict]:  # noqa: F821
    if not studio.get("name") or not studio.get("metro") or not studio.get("city"):
        return None

    # Reject junk names (article titles, generic modality names, questions)
    from processors.quality_gate import is_valid_studio_name
    if not is_valid_studio_name(studio["name"]):
        log.debug("Rejected junk name: %s", studio["name"])
        return None

    name_lower = studio["name"].lower()
    EXCLUDED = ["nail salon", "hair salon", "barber", "dental", "urgent care", "medical spa"]
    if any(t in name_lower for t in EXCLUDED):
        return None

    if not studio.get("id"):
        studio["id"] = _slug(studio["name"], studio["city"])

    studio["status"] = studio.get("status") if studio.get("status") in VALID_STATUSES else "active"
    studio["modalities"] = [m for m in (studio.get("modalities") or []) if m in VALID_MODALITIES]
    # Backfill from the franchise brand map when the crawl derived nothing, so
    # known chains stay tagged on every run without a manual enrichment pass.
    if not studio["modalities"]:
        studio["modalities"] = modalities_for_name(studio["name"])
    studio["amenities"] = [a for a in (studio.get("amenities") or []) if a in VALID_AMENITIES]
    studio["format"] = studio.get("format") if studio.get("format") in VALID_FORMATS else None
    studio["session_style"] = studio.get("session_style") if studio.get("session_style") in VALID_SESSION_STYLES else None
    studio["access"] = studio.get("access") if studio.get("access") in VALID_ACCESS else None

    for field in ("day_pass_price_usd", "membership_from_usd"):
        val = studio.get(field)
        if val is not None:
            try:
                studio[field] = float(val) if float(val) > 0 else None
            except (ValueError, TypeError):
                studio[field] = None

    for field in ("plunge_temp_f_min", "plunge_temp_f_max"):
        val = studio.get(field)
        if val is not None:
            try:
                v = int(val)
                studio[field] = v if 28 <= v <= 70 else None
            except (ValueError, TypeError):
                studio[field] = None

    for field in ("lat", "lng"):
        val = studio.get(field)
        if val is not None:
            try:
                studio[field] = float(val)
            except (ValueError, TypeError):
                studio[field] = None

    if not isinstance(studio.get("source_urls"), list):
        studio["source_urls"] = []

    studio.pop("_source", None)

    return {
        "id": studio["id"],
        "name": studio["name"],
        "metro": studio["metro"],
        "city": studio["city"],
        "lat": studio.get("lat"),
        "lng": studio.get("lng"),
        "status": studio["status"],
        "brand": studio.get("brand"),
        "state": studio.get("state"),
        "neighborhood": studio.get("neighborhood"),
        "address": studio.get("address"),
        "website": studio.get("website"),
        "booking_url": studio.get("booking_url"),
        "instagram": studio.get("instagram"),
        "modalities": studio["modalities"],
        "plunge_temp_f_min": studio.get("plunge_temp_f_min"),
        "plunge_temp_f_max": studio.get("plunge_temp_f_max"),
        "format": studio.get("format"),
        "session_style": studio.get("session_style"),
        "access": studio.get("access"),
        "day_pass_price_usd": studio.get("day_pass_price_usd"),
        "membership_from_usd": studio.get("membership_from_usd"),
        "amenities": studio["amenities"],
        "google_place_id": studio.get("google_place_id"),
        "google_rating": studio.get("google_rating"),
        "google_reviews_count": studio.get("google_reviews_count"),
        "source_urls": studio["source_urls"],
        "last_verified": studio.get("last_verified"),
        # Retention bookkeeping — authoritatively set by processors/retention.py
        # at write time.  Declared here so every record carries the full schema
        # even on a first run, and so _clean() cannot silently drop them if a
        # future caller passes already-merged records back through.
        "last_seen_at": studio.get("last_seen_at"),
        "missed_runs": studio.get("missed_runs") or 0,
    }



def _slug(name: str, city: str) -> str:
    text = unicodedata.normalize("NFKD", f"{name} {city}").encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:64]
