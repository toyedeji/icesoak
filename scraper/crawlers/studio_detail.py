"""Visit studio websites to enrich records with structured attributes."""
import asyncio
import logging
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

log = logging.getLogger(__name__)

_MODALITY_RE = {
    "cold_plunge":      re.compile(r"cold\s*plunge|ice\s*bath|plunge\s*pool|cold\s*immersion", re.I),
    "sauna_traditional": re.compile(r"traditional\s*sauna|finnish\s*sauna|wood.?fired\s*sauna|steam\s*sauna", re.I),
    "sauna_infrared":   re.compile(r"infrared\s*sauna|far.?infrared|ir\s*sauna", re.I),
    "contrast":         re.compile(r"contrast\s*therapy|hot.cold\s*therapy|contrast\s*session", re.I),
    "red_light":        re.compile(r"red\s*light\s*therapy|photobiomodulation|pbm\s*therapy", re.I),
    "compression":      re.compile(r"compression\s*therapy|normatec|pneumatic\s*compression|air\s*compression", re.I),
    "breathwork":       re.compile(r"breathwork|wim\s*hof|pranayama|breathing\s*technique", re.I),
    "float":            re.compile(r"float\s*tank|flotation|sensory\s*deprivation", re.I),
    "cryo":             re.compile(r"cryotherapy|cryo\s*chamber|whole.?body\s*cryo", re.I),
    "iv":               re.compile(r"\biv\s*therapy|\biv\s*drip|intravenous\s*therapy|vitamin\s*drip", re.I),
}
_FORMAT_RE = {
    "both":         re.compile(r"private\s*(?:and|&|or)\s*communal|communal\s*(?:and|&|or)\s*private", re.I),
    "private_suite": re.compile(r"private\s*suite|private\s*room|private\s*session", re.I),
    "communal":     re.compile(r"communal|shared\s*space|open\s*floor\s*plan", re.I),
}
_SESSION_RE = {
    "both":          re.compile(r"guided\s*(?:and|&|or)\s*free|free\s*(?:and|&|or)\s*guided", re.I),
    "guided_social": re.compile(r"guided\s*session|led\s*by|instructor.?led|social\s*session", re.I),
    "free_flow":     re.compile(r"free\s*flow|drop.in|self.?guided|at\s*your\s*own\s*pace", re.I),
}
_ACCESS_RE = {
    "both":            re.compile(r"membership\s*(?:and|&|or)\s*day\s*pass|day\s*pass\s*(?:and|&|or)\s*membership", re.I),
    "membership_only": re.compile(r"members?\s*only|membership\s*only|by\s*membership", re.I),
    "day_pass":        re.compile(r"day\s*pass|drop.in|single\s*visit|walk.?in", re.I),
}
_PRICE_DAY_RE   = re.compile(r"day\s*pass[:\s]*\$\s*([\d]+(?:\.\d{2})?)", re.I)
_PRICE_MEM_RE   = re.compile(r"membership[:\s]*(?:from\s*)?\$\s*([\d]+(?:\.\d{2})?)\s*(?:/mo|per\s*month)?", re.I)
_TEMP_RE        = re.compile(r"(\d{1,3})\s*°?\s*F(?:\s*[-–to]+\s*(\d{1,3})\s*°?\s*F)?", re.I)
_AMENITY_RE = {
    "showers":          re.compile(r"\bshower", re.I),
    "towels_provided":  re.compile(r"towels?\s*(?:provided|included)", re.I),
    "parking":          re.compile(r"parking\s*(?:available|included|free|on.?site)", re.I),
    "lockers":          re.compile(r"\blocker", re.I),
}
# Full US street address on a studio's own site: number + street + ", City, ST ZIP".
# State stays uppercase ([A-Z]{2}) so we never accept a lowercased false match.
_ADDRESS_RE = re.compile(
    r"\d{1,6}\s+[\w .'-]+?\b"
    r"(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Rd|Road|Way|Ln|Lane"
    r"|Pkwy|Parkway|Pike|Hwy|Highway|Ct|Court|Pl|Place|Ter|Terrace|Cir|Circle"
    r"|Ste|Suite|Unit)\b"
    r"[^\n]*?,\s*[A-Za-z .'-]+,\s*[A-Z]{2}\s+\d{5}"
)


def _has_full_address(addr) -> bool:
    return bool(addr and re.search(r"\d.*,.*\b[A-Z]{2}\b\s*\d{5}", addr))


_IG_RE      = re.compile(r"instagram\.com/([a-zA-Z0-9_.]{2,30})", re.I)
_BOOKING_RE = re.compile(
    r"(https?://(?:mindbodysoftware|mindbody|pike13|schedulicity|vagaro|glofox|healcode|book\.)?[^\s\"'>]*(?:book|schedule|reserve)[^\s\"'>]*)",
    re.I,
)

_BROWSER = BrowserConfig(
    headless=True,
    browser_type="chromium",
    extra_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
)


async def enrich_studios(studios: list, today: str) -> list:
    """Visit each studio's website (if known) and fill in attributes."""
    to_enrich = [s for s in studios if s.get("website")]
    log.info("Enriching %d studios from their websites", len(to_enrich))

    async with AsyncWebCrawler(config=_BROWSER) as crawler:
        for studio in to_enrich:
            try:
                res = await crawler.arun(
                    url=studio["website"],
                    config=CrawlerRunConfig(
                        delay_before_return_html=2.5,
                        cache_mode=CacheMode.BYPASS,
                        word_count_threshold=50,
                    ),
                )
                if res.success:
                    _apply(studio, res.markdown or "", studio["website"])
                    studio["last_verified"] = today
                    log.info("Enriched: %s", studio["name"])
            except Exception as exc:
                log.warning("Enrich failed (%s): %s", studio.get("name"), exc)
            await asyncio.sleep(1.0)

    return studios


def _apply(studio: dict, content: str, source_url: str) -> None:
    # Address — pull from the studio's own site when we don't already have a
    # full one (recovers studios that listicles named but never gave an address).
    if not _has_full_address(studio.get("address")):
        m = _ADDRESS_RE.search(content)
        if m:
            studio["address"] = re.sub(r"\s+", " ", m.group(0)).strip()

    # Modalities
    for mod, pat in _MODALITY_RE.items():
        if pat.search(content) and mod not in studio.get("modalities", []):
            studio.setdefault("modalities", []).append(mod)

    # Format (check "both" first to avoid false partial matches)
    if not studio.get("format"):
        for key in ("both", "private_suite", "communal"):
            if _FORMAT_RE[key].search(content):
                studio["format"] = key
                break

    # Session style
    if not studio.get("session_style"):
        for key in ("both", "guided_social", "free_flow"):
            if _SESSION_RE[key].search(content):
                studio["session_style"] = key
                break

    # Access
    if not studio.get("access"):
        for key in ("both", "membership_only", "day_pass"):
            if _ACCESS_RE[key].search(content):
                studio["access"] = key
                break

    # Prices — only from studio's own stated text
    if not studio.get("day_pass_price_usd"):
        m = _PRICE_DAY_RE.search(content)
        if m:
            studio["day_pass_price_usd"] = float(m.group(1))

    if not studio.get("membership_from_usd"):
        m = _PRICE_MEM_RE.search(content)
        if m:
            studio["membership_from_usd"] = float(m.group(1))

    # Plunge temps — only plausible cold-plunge range (28–65 °F)
    if not studio.get("plunge_temp_f_min"):
        cold = [int(t) for pair in _TEMP_RE.findall(content) for t in pair if t and 28 <= int(t) <= 65]
        if cold:
            studio["plunge_temp_f_min"] = min(cold)
            studio["plunge_temp_f_max"] = max(cold) if len(cold) > 1 else None

    # Amenities
    for amenity, pat in _AMENITY_RE.items():
        if pat.search(content) and amenity not in studio.get("amenities", []):
            studio.setdefault("amenities", []).append(amenity)

    # Instagram
    if not studio.get("instagram"):
        m = _IG_RE.search(content)
        if m and m.group(1).lower() not in {"sharer", "share", "p", "explore"}:
            studio["instagram"] = f"@{m.group(1)}"

    # Booking URL
    if not studio.get("booking_url"):
        m = _BOOKING_RE.search(content)
        if m:
            studio["booking_url"] = m.group(1)

    if source_url not in studio.get("source_urls", []):
        studio.setdefault("source_urls", []).append(source_url)
