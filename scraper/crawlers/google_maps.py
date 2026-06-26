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

            address = _text(card, [".W4Efsd:nth-child(2)", ".Io6YTe"])

            # Extract place_id from any href on the card
            place_id = None
            for a in card.select("a[href]"):
                m = re.search(r"place_id=([^&]+)", a["href"])
                if m:
                    place_id = m.group(1)
                    break

            out.append({
                "id": _slug(name, city),
                "name": name,
                "metro": metro["id"],
                "city": city,
                "lat": None,
                "lng": None,
                "status": "active",
                "brand": None,
                "state": metro["state"],
                "neighborhood": None,
                "address": address,
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
                "source_urls": [f"https://www.google.com/maps/search/{name.replace(' ', '+')}"],
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
