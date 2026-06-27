"""Nominatim (OpenStreetMap) geocoder for studio addresses.

Usage policy compliance:
  - Maximum 1 request/second (enforced by _INTERVAL).
  - Descriptive User-Agent required by Nominatim policy.
  - Results cached to scraper/data/geocode_cache.json so unchanged addresses
    are never re-queried across runs.
"""
import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "geocode_cache.json"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "IceSoak/1.0 (https://icesoak.com; studio-directory geocoding)"
_INTERVAL = 1.1  # Nominatim allows max 1 req/sec; 1.1s gives a small safety margin

# Bounding boxes [lat_min, lat_max, lng_min, lng_max] per metro id
_METRO_BBOX: dict[str, tuple[float, float, float, float]] = {
    "denver_co":            (38.5,  40.5, -106.0, -104.0),
    "dallas_fort_worth_tx": (32.0,  34.0,  -98.0,  -96.0),
    "philadelphia_pa":      (39.5,  41.0,  -76.5,  -73.5),
}

# Addresses that look like scraper noise rather than real street addresses.
# A real US address must contain at least one digit, a comma, and a US state code.
_ADDRESS_RE = re.compile(
    r"\d"           # at least one digit (street number)
    r".*,"          # a comma somewhere after
    r".*\b[A-Z]{2}\b",  # a two-letter state abbreviation
    re.DOTALL,
)


def _is_real_address(addr: str) -> bool:
    return bool(_ADDRESS_RE.search(addr))


def _load_cache() -> dict:
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def _in_metro_bbox(lat: float, lng: float, metro: str) -> bool:
    bbox = _METRO_BBOX.get(metro)
    if bbox is None:
        return True  # unknown metro — don't reject
    lat_min, lat_max, lng_min, lng_max = bbox
    return lat_min <= lat <= lat_max and lng_min <= lng <= lng_max


# Strip suite/unit tokens from an address before a fallback geocode attempt
_SUITE_RE = re.compile(
    r"\s*(?:Ste|Suite|Unit|Apt|#|Bldg|Fl|Floor)\s*[\w-]+,?",
    re.IGNORECASE,
)


def _strip_suite(address: str) -> str:
    return _SUITE_RE.sub(",", address).replace(",,", ",").strip().strip(",").strip()


def _nominatim_get(query: str) -> Optional[tuple[float, float]]:
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
    })
    url = f"{_NOMINATIM_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        log.warning("Nominatim request failed (%s): %s", type(exc).__name__, exc)
        return None


def _reverse_nominatim(lat: float, lng: float) -> Optional[dict]:
    """Reverse-geocode a point to Nominatim's structured address dict, or None."""
    params = urllib.parse.urlencode({
        "lat": lat, "lon": lng, "format": "json",
        "addressdetails": 1, "zoom": 18,
    })
    url = f"https://nominatim.openstreetmap.org/reverse?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        addr = data.get("address")
        return addr if isinstance(addr, dict) else None
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        log.warning("Nominatim reverse failed (%s): %s", type(exc).__name__, exc)
        return None


# A scraped street is only trusted if it looks like "<number> <street words>"
# and carries no hours/status noise. Otherwise we ignore it and rebuild the
# street from the reverse-geocode result — never label a point with junk text.
_STREET_OK_RE = re.compile(r"^\d{1,6}\s+[A-Za-z0-9].*[A-Za-z]")
_STREET_JUNK_RE = re.compile(
    r"(?i)\bopen\b|\bclos(?:ed|es|ing)\b|\bhours\b|\bam\b|\bpm\b|\bsleeps\b"
    r"|\d{1,2}:\d{2}|\bmin\b|temporarily|permanently|\bsoon\b"
)


def _compose_address(street: Optional[str], rev: dict, state: str) -> Optional[str]:
    """Build 'street, City, ST ZIP' from a scraped street + reverse-geocode result.

    The street (if it is genuinely street-shaped) comes from the scraper; city/
    ZIP come from reverse-geocoding the studio's EXACT coordinates; the state is
    the studio's own field. A junk "street" is discarded and rebuilt from the
    reverse result. Nothing is guessed — this only labels a known point.
    """
    city = (rev.get("city") or rev.get("town") or rev.get("village")
            or rev.get("municipality") or rev.get("suburb") or rev.get("hamlet"))
    postcode = rev.get("postcode")

    street = (street or "").strip()
    if not (_STREET_OK_RE.match(street) and not _STREET_JUNK_RE.search(street)):
        # Untrusted scraped street → rebuild from the reverse-geocode result.
        house, road = rev.get("house_number"), rev.get("road")
        street = f"{house} {road}" if house and road else (road or "")

    if not (street and city and state):
        return None
    tail = f"{city}, {state}" + (f" {postcode}" if postcode else "")
    return f"{street}, {tail}"


def _fetch_nominatim(address: str) -> Optional[tuple[float, float]]:
    """Return (lat, lng) for address or None on failure/no-result.

    Tries the full address first; if that returns nothing, strips suite/unit tokens
    and retries (one extra HTTP request, still within rate-limit spacing).
    """
    result = _nominatim_get(address)
    if result:
        return result
    stripped = _strip_suite(address)
    if stripped and stripped != address:
        time.sleep(_INTERVAL)  # respect rate limit for the retry
        result = _nominatim_get(stripped)
    return result


def geocode_studios(studios: list) -> tuple[list, dict]:
    """Populate lat/lng on studios missing coordinates. Returns (studios, stats).

    Studios that already have both lat and lng are left untouched.
    Studios without a recognisable street address are skipped (lat/lng → null).
    Results outside the studio's metro bounding box are rejected (lat/lng → null).
    Failures leave lat/lng null — no guessing.
    """
    cache = _load_cache()
    stats = {
        "geocoded": 0, "from_cache": 0, "failed": 0,
        "no_address": 0, "junk_address": 0, "bbox_rejected": 0, "already_had": 0,
        "reverse_geocoded": 0,
    }

    # ── Reverse-geocode pass ────────────────────────────────────────────────
    # Studios that already carry EXACT coordinates (e.g. parsed from a Google
    # Maps place link) but whose address is null/junk/street-only: turn the
    # point into an authoritative "street, City, ST ZIP" address.
    rev_targets = [
        s for s in studios
        if s.get("lat") is not None and s.get("lng") is not None
        and not _is_real_address(s.get("address") or "")
    ]
    if rev_targets:
        log.info("Geocoder: reverse-geocoding %d studios with coords but no clean address", len(rev_targets))
        last_request = 0.0
        for s in rev_targets:
            key = f"rev:{s['lat']:.6f},{s['lng']:.6f}"
            rev = cache.get(key)
            if rev is None and key not in cache:
                elapsed = time.monotonic() - last_request
                if elapsed < _INTERVAL:
                    time.sleep(_INTERVAL - elapsed)
                last_request = time.monotonic()
                rev = _reverse_nominatim(s["lat"], s["lng"])
                cache[key] = rev  # cache result (or None) to avoid re-querying
            if rev:
                composed = _compose_address(s.get("address"), rev, s.get("state") or "")
                if composed and _is_real_address(composed):
                    s["address"] = composed
                    stats["reverse_geocoded"] += 1

    needs_geo = []
    for s in studios:
        if s.get("lat") is not None and s.get("lng") is not None:
            stats["already_had"] += 1
        elif not s.get("address"):
            stats["no_address"] += 1
        elif not _is_real_address(s["address"]):
            stats["junk_address"] += 1
            log.debug("Skipping junk address: %s | %s", s["name"], s["address"])
        else:
            needs_geo.append(s)

    if not needs_geo:
        _save_cache(cache)
        log.info("Geocoder: no forward geocoding needed (%d already had coords, %d reverse-geocoded)",
                 stats["already_had"], stats["reverse_geocoded"])
        return studios, stats

    cache_hits = sum(1 for s in needs_geo if s["address"] in cache)
    log.info(
        "Geocoder: %d studios need coords (%d cached, %d will query Nominatim)",
        len(needs_geo), cache_hits, len(needs_geo) - cache_hits,
    )

    last_request = 0.0
    for s in needs_geo:
        addr = s["address"]
        metro = s.get("metro", "")

        if addr in cache:
            result = cache[addr]
            if result:
                lat, lng = result["lat"], result["lng"]
                if _in_metro_bbox(lat, lng, metro):
                    s["lat"], s["lng"] = lat, lng
                    stats["from_cache"] += 1
                else:
                    stats["bbox_rejected"] += 1
                    log.warning("  Cache bbox-reject: %s → %.4f,%.4f (metro=%s)", s["name"], lat, lng, metro)
            else:
                stats["failed"] += 1
            continue

        # Rate-limit: sleep until 1.1s after the last HTTP request
        elapsed = time.monotonic() - last_request
        if elapsed < _INTERVAL:
            time.sleep(_INTERVAL - elapsed)
        last_request = time.monotonic()

        result = _fetch_nominatim(addr)
        if result:
            lat, lng = result
            if _in_metro_bbox(lat, lng, metro):
                s["lat"], s["lng"] = lat, lng
                cache[addr] = {"lat": lat, "lng": lng}
                stats["geocoded"] += 1
                log.info("  Geocoded %-40s → %.5f, %.5f", s["name"][:40], lat, lng)
            else:
                cache[addr] = None  # cache as bad so we don't retry
                stats["bbox_rejected"] += 1
                log.warning("  bbox-reject: %s → %.4f,%.4f (metro=%s)", s["name"], lat, lng, metro)
        else:
            cache[addr] = None
            stats["failed"] += 1
            log.info("  No result:  %s | %s", s["name"], addr)

    _save_cache(cache)
    log.info(
        "Geocoder done: %d new, %d cached, %d failed, %d bbox-rejected, "
        "%d junk-addr, %d no-addr, %d already-had, %d reverse-geocoded",
        stats["geocoded"], stats["from_cache"], stats["failed"],
        stats["bbox_rejected"], stats["junk_address"],
        stats["no_address"], stats["already_had"], stats["reverse_geocoded"],
    )
    return studios, stats
