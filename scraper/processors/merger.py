import logging
import re
import unicodedata
from typing import Optional
from utils.schema import (
    VALID_STATUSES, VALID_MODALITIES, VALID_FORMATS,
    VALID_SESSION_STYLES, VALID_ACCESS, VALID_AMENITIES,
)

log = logging.getLogger(__name__)


def merge_sources(studios: list) -> list:
    """Validate, clean, assign unique IDs, and return final record list."""
    output = []
    for studio in studios:
        cleaned = _clean(studio)
        if cleaned:
            output.append(cleaned)

    seen_ids: dict = {}
    for studio in output:
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

    name_lower = studio["name"].lower()
    EXCLUDED = ["nail salon", "hair salon", "barber", "dental", "urgent care", "medical spa"]
    if any(t in name_lower for t in EXCLUDED):
        return None

    if not studio.get("id"):
        studio["id"] = _slug(studio["name"], studio["city"])

    studio["status"] = studio.get("status") if studio.get("status") in VALID_STATUSES else "active"
    studio["modalities"] = [m for m in (studio.get("modalities") or []) if m in VALID_MODALITIES]
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
    }



def _slug(name: str, city: str) -> str:
    text = unicodedata.normalize("NFKD", f"{name} {city}").encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:64]
