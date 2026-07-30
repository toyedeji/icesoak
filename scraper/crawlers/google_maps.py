"""Scrape Google Maps search results for studios in each metro."""
import asyncio
import logging
import re
import unicodedata
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from utils.blocking import SearchStats, classify_response

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

# JS to scroll the results feed so Maps lazy-loads more cards.
#
# The previous version did six fixed 600px steps with a 700ms wait each: a
# 4.2s time budget with no completion check, so how many cards had been
# hydrated when it expired was a function of that morning's render latency.
# That is the single largest contributor to week-over-week inventory churn.
#
# This version scrolls to the bottom of the feed and keeps going until the card
# count stops growing (STABLE_ROUNDS consecutive no-growth polls), Maps prints
# its end-of-list marker, or a hard ceiling is reached.  Completion is now a
# property of the DOM, not of the clock.
#
# Worst-case wall clock is MAX_ROUNDS * STEP_MS = 12.5s per search; typical
# convergence is 5-9 rounds. At 180 searches per full run that is ~30-45 min of
# scrolling, which is within budget for a weekly 03:00 UTC job.
_SCROLL_JS = """
(async () => {
    const feed = document.querySelector('[role="feed"]');
    if (!feed) return;

    const CARD_SEL      = '[role="article"], .Nv2PK, .bfdHYd';
    const MAX_ROUNDS    = 25;   // hard ceiling on wall-clock per search
    const STABLE_ROUNDS = 3;    // consecutive no-growth polls == fully loaded
    const MAX_CARDS     = 140;  // Maps caps a single search near ~120 results
    const STEP_MS       = 500;
    const END_RE        = /you.{0,3}ve reached the end of the list/i;

    let last = -1, stable = 0;

    for (let round = 0; round < MAX_ROUNDS; round++) {
        const count = feed.querySelectorAll(CARD_SEL).length;

        if (count >= MAX_CARDS) break;
        if (END_RE.test(feed.innerText || '')) break;

        if (count === last) {
            if (++stable >= STABLE_ROUNDS) break;
        } else {
            stable = 0;
            last = count;
        }

        feed.scrollTo({ top: feed.scrollHeight });
        await new Promise(r => setTimeout(r, STEP_MS));
    }
})();
"""


async def scrape_google_maps(metro: dict, stats: SearchStats | None = None) -> list:
    """Scrape one metro.  Records every search outcome into `stats`.

    NOTE: cities[:3] deliberately left in place for now — see MIGRATION NOTES.
    Each metro defines 10-18 cities and only the first three are ever queried,
    which caps discovery well below the configured footprint.  That is a
    coverage bug, not a churn bug (it is deterministic), and expanding it in the
    same change as the retention rework would confound the two.
    """
    results = []
    cities = metro.get("cities", [metro["name"].split("–")[0]])[:3]
    metro_id = metro["id"]

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
                except Exception as exc:
                    # Timeout waiting for [role=feed] lands here, and a consent
                    # wall or CAPTCHA is the most likely reason the feed never
                    # appeared — so this is a *failure*, not a quiet zero.
                    log.warning(
                        "Maps search ERRORED (%s / %s / %s): %s",
                        metro_id, query, city, exc,
                    )
                    if stats:
                        stats.record_failure(metro_id, "exception")
                    await asyncio.sleep(2.5)
                    continue

                status = getattr(res, "status_code", None)
                html = getattr(res, "html", None)

                if not res.success:
                    reason = classify_response(html, status) or "request_failed"
                    log.warning(
                        "Maps search FAILED (%s / %s / %s): reason=%s status=%s %s",
                        metro_id, query, city, reason, status,
                        getattr(res, "error_message", "") or "",
                    )
                    if stats:
                        stats.record_failure(metro_id, reason)
                    await asyncio.sleep(2.5)
                    continue

                # A 200 that is really a consent wall / CAPTCHA / throttle page.
                reason = classify_response(html, status)
                if reason:
                    log.warning(
                        "Maps search BLOCKED (%s / %s / %s): reason=%s status=%s",
                        metro_id, query, city, reason, status,
                    )
                    if stats:
                        stats.record_failure(metro_id, reason)
                    # Back off harder on an anti-bot response than on a plain
                    # miss: hammering a throttle is what produced the clustered
                    # metro-shaped losses on 2026-07-19.
                    await asyncio.sleep(15.0 if reason in ("captcha", "rate_limit") else 5.0)
                    continue

                cards = _parse(html, metro, city)
                results.extend(cards)
                log.info("  → %d cards", len(cards))
                if stats:
                    stats.record_success(metro_id, len(cards))
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
    text = unicodedata.normalize("NFKD", f"{name} {city}").encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")[:64]
