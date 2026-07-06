"""Scrape franchise location pages for studios in target metros."""
import asyncio
import logging
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawlers.google_maps import _slug

log = logging.getLogger(__name__)

FRANCHISES = [
    {"brand": "SweatHouz", "url": "https://sweathouz.com/locations"},
    {"brand": "Perspire Sauna Studio", "url": "https://www.perspire.com/find-a-studio"},
    {"brand": "Restore Hyper Wellness", "url": "https://www.restorehyperwellness.com/locations"},
    {"brand": "Pause", "url": "https://pause.com/studios"},
    {"brand": "Contrast Studio", "url": "https://contraststudio.com/locations"},
]

# Known modalities by brand
_BRAND_MODALITIES = {
    "sweathouz": ["sauna_infrared", "cold_plunge"],
    "perspire sauna studio": ["sauna_infrared"],
    "restore hyper wellness": ["cryo", "red_light", "compression", "iv"],
    "pause": ["sauna_infrared", "cold_plunge", "contrast"],
    "contrast studio": ["sauna_infrared", "cold_plunge", "contrast"],
}

# Metro → states and city keywords for filtering franchise pages
_METRO_STATES = {
    "denver_co": {"CO"},
    "dallas_fort_worth_tx": {"TX"},
    "philadelphia_pa": {"PA", "NJ"},
    "austin_tx": {"TX"},
    "chicago_il": {"IL"},
    "atlanta_ga": {"GA"},
    "seattle_wa": {"WA"},
    "miami_fl": {"FL"},
    "nashville_tn": {"TN"},
}
_METRO_CITIES = {
    "denver_co": [
        "denver", "aurora", "lakewood", "arvada", "westminster",
        "englewood", "centennial", "littleton", "boulder", "highlands ranch",
    ],
    "dallas_fort_worth_tx": [
        "dallas", "fort worth", "plano", "frisco", "mckinney", "irving",
        "garland", "arlington", "richardson", "southlake", "grapevine",
        "addison", "allen", "flower mound", "lewisville",
    ],
    "philadelphia_pa": [
        "philadelphia", "king of prussia", "cherry hill", "ardmore",
        "conshohocken", "wayne", "horsham", "lansdale", "blue bell",
        "jenkintown", "media",
    ],
    "austin_tx": [
        "austin", "round rock", "cedar park", "pflugerville", "georgetown",
        "lakeway", "bee cave", "kyle", "buda", "manor",
    ],
    "chicago_il": [
        "chicago", "evanston", "oak park", "naperville", "schaumburg",
        "aurora", "joliet", "wicker park", "lincoln park", "river north",
        "bucktown", "lakeview", "south loop",
    ],
    "atlanta_ga": [
        "atlanta", "buckhead", "midtown", "decatur", "sandy springs",
        "marietta", "alpharetta", "roswell", "dunwoody", "brookhaven",
        "smyrna", "vinings", "virginia highland",
    ],
    "seattle_wa": [
        "seattle", "bellevue", "redmond", "kirkland", "bothell",
        "shoreline", "renton", "burien", "capitol hill", "queen anne",
        "fremont", "ballard", "west seattle",
    ],
    "miami_fl": [
        "miami", "miami beach", "coral gables", "brickell", "wynwood",
        "coconut grove", "aventura", "hollywood", "fort lauderdale",
        "doral", "hialeah", "south beach",
    ],
    "nashville_tn": [
        "nashville", "brentwood", "franklin", "murfreesboro", "hendersonville",
        "germantown", "east nashville", "12 south", "gulch", "bellevue",
    ],
}

_BROWSER = BrowserConfig(
    headless=True,
    browser_type="chromium",
    extra_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
)


async def scrape_franchises(metro: dict) -> list:
    results = []
    cities = _METRO_CITIES.get(metro["id"], [])
    states = _METRO_STATES.get(metro["id"], set())

    async with AsyncWebCrawler(config=_BROWSER) as crawler:
        for franchise in FRANCHISES:
            log.info("Franchise: %s → %s", franchise["brand"], metro["id"])
            try:
                res = await crawler.arun(
                    url=franchise["url"],
                    config=CrawlerRunConfig(
                        delay_before_return_html=3.0,
                        cache_mode=CacheMode.BYPASS,
                        word_count_threshold=20,
                    ),
                )
                if res.success:
                    content = res.markdown or res.html or ""
                    hits = _extract_locations(
                        content, franchise, metro, cities, states
                    )
                    results.extend(hits)
                    log.info("  → %d locations", len(hits))
            except Exception as exc:
                log.warning("Franchise scrape failed (%s): %s", franchise["brand"], exc)
            await asyncio.sleep(2.0)

    return results


def _extract_locations(content: str, franchise: dict, metro: dict, cities: list, states: set) -> list:
    brand = franchise["brand"]
    source_url = franchise["url"]
    modalities = _BRAND_MODALITIES.get(brand.lower(), [])
    lines = content.split("\n")
    found = []
    seen_cities: set = set()

    for i, line in enumerate(lines):
        line_low = line.lower()
        matched_city = next((c for c in cities if c in line_low), None)
        matched_state = any(f" {s.lower()}" in line_low or f",{s.lower()}" in line_low for s in states)

        if not (matched_city or matched_state):
            continue

        city_name = matched_city.title() if matched_city else metro["name"].split("–")[0]
        if city_name in seen_cities:
            continue

        # Peek at surrounding lines for an address
        context = "\n".join(lines[max(0, i - 2): i + 6])
        # Prefer a complete "street, City, ST ZIP" match.
        full_m = re.search(
            r"\d+\s+[A-Z][\w .]+?(?:St|Street|Ave|Avenue|Blvd|Dr|Drive|Rd|Road|Way|Ln|Lane"
            r"|Pkwy|Pike|Hwy|Ct|Pl|Ste|Suite|Unit)\b[^\n]*?,\s*[A-Za-z .]+,\s*[A-Z]{2}\s*\d{5}",
            context,
        )
        if full_m:
            address = full_m.group(0).strip()
        else:
            # Fall back to the street line and compose with the matched city +
            # metro state (both known facts, not guesses) so it geocodes.
            street_m = re.search(
                r"\d+\s+[A-Z][\w .]+?(?:St|Street|Ave|Avenue|Blvd|Dr|Drive|Rd|Road|Way|Ln|Lane"
                r"|Pkwy|Pike|Hwy|Ct|Pl|Ste|Suite|Unit)\b[^\n,]*",
                context,
            )
            address = (
                f"{street_m.group(0).strip()}, {city_name}, {metro['state']}"
                if street_m else None
            )

        name = f"{brand} {city_name}"
        seen_cities.add(city_name)
        found.append({
            "id": _slug(name, city_name),
            "name": name,
            "metro": metro["id"],
            "city": city_name,
            "lat": None,
            "lng": None,
            "status": "active",
            "brand": brand,
            "state": metro["state"],
            "neighborhood": None,
            "address": address,
            "website": None,
            "booking_url": None,
            "instagram": None,
            "modalities": list(modalities),
            "plunge_temp_f_min": None,
            "plunge_temp_f_max": None,
            "format": None,
            "session_style": None,
            "access": None,
            "day_pass_price_usd": None,
            "membership_from_usd": None,
            "amenities": [],
            "google_place_id": None,
            "google_rating": None,
            "google_reviews_count": None,
            "source_urls": [source_url],
            "last_verified": None,
            "_source": "franchise",
        })

    return found
