"""Search for magazine listicles and extract studio mentions."""
import asyncio
import logging
import re
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawlers.google_maps import _slug

log = logging.getLogger(__name__)

_SEARCH_TEMPLATES = [
    "best cold plunge {city}",
    "best sauna studio {city}",
    "contrast therapy {city}",
    "best recovery studio {city}",
]

# Domains likely to publish pre-verified studio lists
_TRUSTED = {
    "timeout.com", "eater.com", "yelp.com",
    "5280.com", "303magazine.com", "denverpost.com",
    "dallasobserver.com", "dmagazine.com",
    "phillymag.com", "phillyvoice.com",
}

_MODALITY_HINTS = {
    "cold plunge", "sauna", "contrast", "cryotherapy",
    "ice bath", "infrared", "recovery studio",
}

_BROWSER = BrowserConfig(
    headless=True,
    browser_type="chromium",
    extra_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
)


async def scrape_listicles(metro: dict) -> list:
    results = []
    primary_city = metro.get("cities", [metro["name"].split("–")[0]])[0]

    async with AsyncWebCrawler(config=_BROWSER) as crawler:
        for tmpl in _SEARCH_TEMPLATES:
            query = tmpl.format(city=primary_city)
            search_url = "https://www.google.com/search?q=" + query.replace(" ", "+")
            log.info("Listicle search: %s", query)

            try:
                sr = await crawler.arun(
                    url=search_url,
                    config=CrawlerRunConfig(
                        delay_before_return_html=2.5,
                        cache_mode=CacheMode.BYPASS,
                    ),
                )
                if not sr.success:
                    continue

                urls = _extract_result_urls(sr.html)
                log.info("  → %d candidate URLs", len(urls))

                for url in urls[:5]:
                    try:
                        page = await crawler.arun(
                            url=url,
                            config=CrawlerRunConfig(
                                delay_before_return_html=2.0,
                                cache_mode=CacheMode.BYPASS,
                                word_count_threshold=100,
                            ),
                        )
                        if page.success:
                            studios = _parse_listicle(page.markdown or "", metro, url)
                            results.extend(studios)
                            log.info("  → %d studios from %s", len(studios), url)
                    except Exception as exc:
                        log.warning("Listicle fetch failed (%s): %s", url, exc)
                    await asyncio.sleep(1.5)

            except Exception as exc:
                log.warning("Listicle search failed (%s): %s", query, exc)
            await asyncio.sleep(2.0)

    return results


def _extract_result_urls(html: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        m = re.search(r"/url\?q=([^&]+)", href)
        url = m.group(1) if m else href
        if not url.startswith("http"):
            continue
        is_trusted = any(d in url for d in _TRUSTED)
        is_listicle = (
            ("best" in url.lower() or "top" in url.lower())
            and any(h in url.lower() for h in ("sauna", "plunge", "contrast", "recovery"))
        )
        if is_trusted or is_listicle:
            urls.append(url)
    return list(dict.fromkeys(urls))


def _parse_listicle(markdown: str, metro: dict, source_url: str) -> list:
    studios = []
    lines = markdown.split("\n")
    cities = [c.lower() for c in metro.get("cities", [])]

    for i, line in enumerate(lines):
        line_low = line.lower()
        is_numbered = bool(re.match(r"^#+\s+\d+[\.\)]\s+", line) or re.match(r"^\d+[\.\)]\s+\*\*", line))
        is_header_mention = bool(re.match(r"^#{1,3}\s+", line))
        has_hint = any(h in line_low for h in _MODALITY_HINTS)

        if not ((is_numbered or is_header_mention) and has_hint):
            continue

        name_m = re.search(r"\*\*([^*]+)\*\*", line) or re.search(r"^#+\s+(?:\d+[\.\)]\s+)?(.+)", line)
        if not name_m:
            continue

        name = name_m.group(1).strip().rstrip("*").strip()
        if len(name) < 4 or len(name) > 80:
            continue

        block = "\n".join(lines[i: i + 6])
        context = block.lower()
        city_hit = next((c.title() for c in cities if c in context), None)
        city = city_hit or metro["name"].split("–")[0]

        # Capture the studio's OWN website link (markdown) so the detail crawler
        # can fetch its address. Skip the listicle host, aggregators and socials.
        src_host = re.sub(r"^https?://(www\.)?", "", source_url).split("/")[0]
        website = None
        for lm in re.finditer(r"\]\((https?://[^)\s]+)\)", block):
            u = lm.group(1).split("?")[0].rstrip("/")
            low = u.lower()
            if src_host in low or any(d in low for d in (
                "google.", "facebook.", "instagram.", "yelp.", "twitter.", "x.com",
                "tripadvisor.", "youtube.", "tiktok.", "maps.", "wikipedia.",
            )):
                continue
            website = u
            break

        studios.append({
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
            "address": None,
            "website": website,
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
            "google_place_id": None,
            "google_rating": None,
            "google_reviews_count": None,
            "source_urls": [source_url],
            "last_verified": None,
            "_source": "listicle",
        })

    return studios
