"""One-time backfill: crawl studio websites for email/phone/instagram/booking_url.

Resumable — progress is checkpointed to enrichment_progress.json and studios.json
after every BATCH_SIZE studios, so a crash/restart skips already-processed studios.
"""
import asyncio
import json
import logging
import re
import sys
import time
import urllib.robotparser
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

ROOT = Path(__file__).resolve().parent.parent
STUDIOS_PATH = ROOT / "studios.json"
PROGRESS_PATH = Path(__file__).resolve().parent / "enrichment_progress.json"

USER_AGENT = "IceSoak-Directory-Bot/1.0 (+https://icesoak.com/about)"
BATCH_SIZE = 25
SAME_DOMAIN_DELAY = 2.0
CROSS_DOMAIN_DELAY = 1.0
MAX_RETRIES = 3
SUBPAGES = ["/contact", "/about", "/contact-us"]

# "website" values that are actually media/social-intent links picked up by
# upstream listicle scraping, not real studio homepages — skip rather than crawl.
_NON_WEBSITE_HOSTS = {
    "threads.net", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "beehiiv.com", "media.beehiiv.com", "medium.com", "substack.com",
    "tiktok.com", "youtube.com", "openstreetmap.org", "tile.openstreetmap.org",
    "linkedin.com", "maps.google.com",
}
_NON_WEBSITE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".pdf", ".mp4")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
log = logging.getLogger("enrich_contacts")

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_MAILTO_RE = re.compile(r'mailto:([^"\'?\s>]+)', re.I)
_TEL_RE = re.compile(r'tel:([+\d()\-.\s]{7,20})', re.I)
_PHONE_RE = re.compile(r'(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}')
_IG_HREF_RE = re.compile(r'href=["\']([^"\']*instagram\.com/[^"\']+)["\']', re.I)
_BOOKING_HREF_RE = re.compile(
    r'href=["\']([^"\']*(?:book|reserve|schedule|mindbody|vagaro|glofox|acuity|pike13)[^"\']*)["\']',
    re.I,
)
_EXCLUDED_EMAIL_PREFIXES = ("noreply@", "no-reply@", "privacy@", "legal@")
_GENERIC_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com"}
_IG_EXCLUDED_SEGMENTS = {"p", "explore", "accounts", "tv", "reel", "reels", "stories", "share", "sharer"}

_BROWSER = BrowserConfig(
    headless=True,
    browser_type="chromium",
    extra_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
)

_robots_cache = {}


def _looks_like_real_website(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host in _NON_WEBSITE_HOSTS or any(host.endswith("." + h) for h in _NON_WEBSITE_HOSTS):
        return False
    if parsed.path.lower().endswith(_NON_WEBSITE_EXT):
        return False
    return True


def _registrable_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


class RateLimiter:
    def __init__(self):
        self._last_time = None
        self._last_domain = None

    async def wait(self, domain: str):
        now = time.monotonic()
        if self._last_time is not None:
            required = SAME_DOMAIN_DELAY if domain == self._last_domain else CROSS_DOMAIN_DELAY
            elapsed = now - self._last_time
            if elapsed < required:
                await asyncio.sleep(required - elapsed)
        self._last_time = time.monotonic()
        self._last_domain = domain


async def _robots_allowed(client: httpx.AsyncClient, url: str) -> bool:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            resp = await client.get(f"{origin}/robots.txt", timeout=10, headers={"User-Agent": USER_AGENT})
            rp.parse(resp.text.splitlines() if resp.status_code == 200 else [])
        except Exception:
            rp.parse([])  # unreachable robots.txt => treat as allowed
        _robots_cache[origin] = rp
    return _robots_cache[origin].can_fetch(USER_AGENT, url)


async def _fetch(crawler: AsyncWebCrawler, limiter: RateLimiter, url: str) -> str | None:
    domain = urlparse(url).netloc
    for attempt in range(1, MAX_RETRIES + 1):
        await limiter.wait(domain)
        try:
            res = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    delay_before_return_html=1.5,
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=20000,
                ),
            )
        except Exception as exc:
            log.warning("Fetch error %s (attempt %d/%d): %s", url, attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2 ** (attempt - 1))
                continue
            return None

        status = getattr(res, "status_code", None)
        if status is not None and 400 <= status < 500:
            return None  # deterministic client-side rejection (404, 403 anti-bot, ...) — retry won't help
        if res.success and res.html:
            return res.html
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** (attempt - 1))
    return None


def _extract_email(html: str, studio_domain: str) -> str | None:
    candidates = []
    for m in _MAILTO_RE.finditer(html):
        candidates.append(m.group(1).split("?")[0].strip())
    for m in _EMAIL_RE.finditer(html):
        candidates.append(m.group(0))

    seen, ordered = set(), []
    for addr in candidates:
        addr = addr.lower().rstrip(".,;")
        if addr in seen or "@" not in addr:
            continue
        seen.add(addr)
        ordered.append(addr)

    filtered = [a for a in ordered if not any(a.startswith(p) for p in _EXCLUDED_EMAIL_PREFIXES)]
    if not filtered:
        return None

    domain_matches = [a for a in filtered if studio_domain and a.split("@")[-1].endswith(studio_domain)]
    if domain_matches:
        return domain_matches[0]

    non_generic = [a for a in filtered if a.split("@")[-1] not in _GENERIC_EMAIL_DOMAINS]
    if non_generic:
        return non_generic[0]

    return filtered[0]


def _normalize_phone(digits: str) -> str | None:
    digits = re.sub(r"\D", "", digits)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    return None


def _extract_phone(html: str) -> str | None:
    # Prefer the human-visible page text over tel: href values — some sites'
    # href and displayed number disagree (typo'd href, or a call-tracking
    # script rewriting the href only), and the visible number is what a
    # human (and a studio's real customers) would actually trust and dial.
    visible_text = BeautifulSoup(html, "lxml").get_text(separator=" ")
    m = _PHONE_RE.search(visible_text)
    if m:
        phone = _normalize_phone(m.group(0))
        if phone:
            return phone

    m = _TEL_RE.search(html)
    if m:
        return _normalize_phone(m.group(1))
    return None


def _extract_instagram(html: str) -> str | None:
    for m in _IG_HREF_RE.finditer(html):
        handle = m.group(1).split("instagram.com/", 1)[-1]
        handle = handle.split("?")[0].split("#")[0].strip("/")
        if not handle:
            continue
        first_seg = handle.split("/")[0].lower()
        if first_seg in _IG_EXCLUDED_SEGMENTS:
            continue
        return f"@{first_seg}"
    return None


def _extract_booking(html: str, base_url: str) -> str | None:
    m = _BOOKING_HREF_RE.search(html)
    if m:
        return urljoin(base_url, m.group(1))
    return None


async def _process_studio(crawler, http_client, limiter, studio: dict) -> tuple[str, dict]:
    website = studio.get("website")
    if not website:
        return "no_website", {}

    if not _looks_like_real_website(website):
        log.info("Skipping non-website URL for %s: %s", studio.get("name"), website)
        return "fetch_failed", {}

    if not await _robots_allowed(http_client, website):
        log.info("Robots blocked: %s (%s)", studio["name"], website)
        return "robots_blocked", {}

    studio_domain = _registrable_domain(website)
    pages = []

    home_html = await _fetch(crawler, limiter, website)
    if home_html:
        pages.append(home_html)

    for path in SUBPAGES:
        sub_url = urljoin(website, path)
        if not await _robots_allowed(http_client, sub_url):
            continue
        sub_html = await _fetch(crawler, limiter, sub_url)
        if sub_html:
            pages.append(sub_html)

    if not pages:
        return "fetch_failed", {}

    combined = "\n".join(pages)
    found = {
        "email": _extract_email(combined, studio_domain),
        "phone": _extract_phone(combined),
        "instagram": _extract_instagram(combined),
        "booking_url": _extract_booking(combined, website),
    }

    if not any(found.values()):
        return "no_data_found", {}

    return "success", found


def _load_progress() -> dict:
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text())
    return {"processed_ids": [], "totals": {}}


def _save_progress(progress: dict) -> None:
    PROGRESS_PATH.write_text(json.dumps(progress, indent=2, ensure_ascii=False))


def _save_studios(studios: list) -> None:
    STUDIOS_PATH.write_text(json.dumps(studios, indent=2, ensure_ascii=False) + "\n")


async def main():
    today = date.today().isoformat()

    studios = json.loads(STUDIOS_PATH.read_text())
    progress = _load_progress()
    processed_ids = set(progress["processed_ids"])
    totals = progress.get("totals", {})

    remaining = [s for s in studios if s["id"] not in processed_ids]
    log.info("Loaded %d studios (%d already processed, %d remaining)", len(studios), len(processed_ids), len(remaining))

    limiter = RateLimiter()
    batch_count = 0

    async with httpx.AsyncClient(follow_redirects=True) as http_client, \
            AsyncWebCrawler(config=_BROWSER) as crawler:
        for studio in remaining:
            try:
                status, found = await _process_studio(crawler, http_client, limiter, studio)
            except Exception as exc:
                log.error("Unhandled error for %s: %s", studio.get("name"), exc)
                status, found = "fetch_failed", {}

            filled = []
            for field in ("email", "phone", "instagram", "booking_url"):
                value = found.get(field)
                if value and not studio.get(field):
                    studio[field] = value
                    filled.append(f"{field}={value}")

            studio["enriched_at"] = today
            studio["enrichment_status"] = status

            totals[status] = totals.get(status, 0) + 1
            processed_ids.add(studio["id"])

            log.info(
                "[%d/%d] %s -> %s (%s)",
                len(processed_ids), len(studios), studio["name"], status,
                ", ".join(filled) if filled else "nothing new",
            )

            batch_count += 1
            if batch_count >= BATCH_SIZE:
                _save_studios(studios)
                progress["processed_ids"] = list(processed_ids)
                progress["totals"] = totals
                _save_progress(progress)
                log.info("=== Batch checkpoint: %d/%d processed. Running totals: %s ===",
                          len(processed_ids), len(studios), totals)
                batch_count = 0

        _save_studios(studios)
        progress["processed_ids"] = list(processed_ids)
        progress["totals"] = totals
        _save_progress(progress)

    total = len(studios)
    log.info("=== ENRICHMENT COMPLETE ===")
    log.info("Total studios processed: %d", total)
    for status, count in sorted(totals.items()):
        log.info("  %s: %d (%.1f%%)", status, count, 100 * count / total)

    email_n = sum(1 for s in studios if s.get("email"))
    phone_n = sum(1 for s in studios if s.get("phone"))
    ig_n = sum(1 for s in studios if s.get("instagram"))
    booking_n = sum(1 for s in studios if s.get("booking_url"))
    log.info("Email found: %d (%.1f%%)", email_n, 100 * email_n / total)
    log.info("Phone found: %d (%.1f%%)", phone_n, 100 * phone_n / total)
    log.info("Instagram found: %d (%.1f%%)", ig_n, 100 * ig_n / total)
    log.info("Booking URL found: %d (%.1f%%)", booking_n, 100 * booking_n / total)


if __name__ == "__main__":
    asyncio.run(main())
