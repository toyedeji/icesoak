"""Scrape Google Maps search results for studios in each metro."""
import asyncio
import logging
import re
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

log = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "cold plunge",
    "contrast therapy",
    "sauna studio",
    "recovery studio",
    "ice bath therapy",
]

# Terms that disqualify a result
_EXCLUDE = {"nail", "hair salon", "barber", "dental", "urgent care", "med spa"}
# At least one must match for inclusion
_REQUIRE = {"cold", "plunge", "sauna", "contrast", "recovery", "cryo", "ice", "thermal", "sweat"}

_BROWSER = BrowserConfig(
    headless=True,
    browser_type="chromium",
    extra_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
)

# Maps result cards render a "Category · Street" line and a separate
# "Open/Closed · Closes 9 PM" status line — both inside .W4Efsd. We must take
# the street and reject the status. These patterns separate the two.
_STATUS_RE = re.compile(
    r"(?i)\bopen\b|\bclos(?:ed|es|ing)\b|\bopens\b|\bhours\b|\bam\b|\bpm\b"
    r"|\d{1,2}:\d{2}|\bmon\b|\btue\b|\bwed\b|\bthu\b|\bfri\b|\bsat\b|\bsun\b"
    r"|monday|tuesday|wednesday|thursday|friday|saturday|sunday"
    r"|\bsoon\b|temporarily|permanently|\bmin\b"
)
# A street fragment: starts with a house number then a street word.
_STREET_RE = re.compile(r"^\d{1,6}\s+[A-Za-z0-9].*[A-Za-z]")
# Exact coordinates embedded in a Maps place href: ...!3d{lat}!4d{lng}...
_COORD_RE = re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)")
# Google place CID, e.g. !1s0x...:0x...  — a stable per-place identifier.
_CID_RE = re.compile(r"!1s(0x[0-9a-f]+:0x[0-9a-f]+)")


def _card_street(card) -> str:
    """Return the street fragment from a Maps card, never the hours/status line."""
    for w in card.select(".W4Efsd"):
        txt = w.get_text(" ", strip=True)
        if "·" not in txt:
            continue
        # The address line is "Category · Street". Take the segment after the
        # last middot, then reject anything that smells like hours/status.
        seg = txt.split("·")[-1].strip()
        if not seg or _STATUS_RE.search(seg):
            continue
        if _STREET_RE.match(seg):
            return seg
    return ""


def _card_place(card) -> tuple:
    """Return (place_href, lat, lng, cid) parsed from the card's place link."""
    for a in card.select("a[href]"):
        href = a.get("href", "")
        if "/maps/place/" not in href:
            continue
        cm = _COORD_RE.search(href)
        lat, lng = (float(cm.group(1)), float(cm.group(2))) if cm else (None, None)
        idm = _CID_RE.search(href)
        return href, lat, lng, (idm.group(1) if idm else None)
    return None, None, None, None

# JS to scroll the results feed so Maps lazy-loads more cards
_SCROLL_JS = """
(async () => {
    const feed = document.querySelector('[role="feed"]');
    if (!feed) return;
    for (let i = 0; i < 6; i++) {
        feed.scrollTop += 600;
        await new Promise(r => setTimeout(r, 700));
    }
})();
"""


async def scrape_google_maps(metro: dict) -> list:
    results = []
    cities = metro.get("cities", [metro["name"].split("–")[0]])[:3]

    async with AsyncWebCrawler(config=_BROWSER) as crawler:
        for query in SEARCH_QUERIES:
            for city in cities:
                url = (
                    "https://www.google.com/maps/search/"
                    + f"{query.replace(' ', '+')}+{city.replace(' ', '+')}+{metro['state']}"
                )
                log.info("Maps search: %s / %s", query, city)
                try:
                    res = await crawler.arun(
                        url=url,
                        config=CrawlerRunConfig(
                            wait_for="css:[role='feed']",
                            delay_before_return_html=3.5,
                            js_code=_SCROLL_JS,
                            cache_mode=CacheMode.BYPASS,
                        ),
                    )
                    if res.success:
                        cards = _parse(res.html, metro, city)
                        results.extend(cards)
                        log.info("  → %d cards", len(cards))
                except Exception as exc:
                    log.warning("Maps scrape failed (%s/%s): %s", query, city, exc)
                await asyncio.sleep(2.5)

    return _filter(results)


def _parse(html: str, metro: dict, city: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    out = []

    # Google Maps uses several class names; try each
    cards = (
        soup.select('[role="article"]')
        or soup.select(".Nv2PK")
        or soup.select(".bfdHYd")
    )

    for card in cards:
        try:
            name = _text(card, [".qBF1Pd", ".fontHeadlineSmall", "[aria-label]"])
            if not name:
                continue

            rating_str = _text(card, [".MW4etd"])
            rating = float(rating_str) if rating_str else None

            reviews_str = _text(card, [".UY7F9"])
            reviews = int(re.sub(r"\D", "", reviews_str)) if reviews_str else None

            # Street fragment (never the hours/status line) + exact coords from
            # the place href. The geocoder reverse-geocodes these coords into a
            # full "street, city, ST ZIP" address — so we store the street here.
            street = _card_street(card)
            place_href, lat, lng, place_id = _card_place(card)
            source_url = place_href or f"https://www.google.com/maps/search/{name.replace(' ', '+')}"

            out.append({
                "id": _slug(name, city),
                "name": name,
                "metro": metro["id"],
                "city": city,
                "lat": lat,
                "lng": lng,
                "status": "active",
                "brand": None,
                "state": metro["state"],
                "neighborhood": None,
                "address": street or None,
                "website": None,
                "booking_url": None,
                "instagram": None,
                "modalities": [],
                "plunge_temp_f_min": None,
                "plunge_temp_f_max": None,
                "format": None,
                "session_style": None,
                "access": None,
                "day_pass_price_usd": None,
                "membership_from_usd": None,
                "amenities": [],
                "google_place_id": place_id,
                "google_rating": rating,
                "google_reviews_count": reviews,
                "source_urls": [source_url],
                "last_verified": None,
                "_source": "google_maps",
            })
        except Exception:
            continue
    return out


def _text(tag, selectors: list) -> str:
    for sel in selectors:
        el = tag.select_one(sel)
        if el:
            t = el.get_text(strip=True)
            if t:
                return t
    return ""


def _filter(studios: list) -> list:
    out = []
    for s in studios:
        nl = s["name"].lower()
        if any(ex in nl for ex in _EXCLUDE):
            continue
        if any(req in nl for req in _REQUIRE):
            out.append(s)
    return out


def _slug(name: str, city: str) -> str:
    s = re.sub(r"[^\w\s-]", "", f"{name} {city}".lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")[:64]
