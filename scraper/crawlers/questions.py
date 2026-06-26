"""Harvest questions from Google PAA and Reddit."""
import asyncio
import logging
import re
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

log = logging.getLogger(__name__)

_GLOBAL_TOPICS = [
    "cold plunge benefits",
    "cold plunge how long",
    "sauna benefits",
    "infrared sauna vs traditional sauna",
    "contrast therapy benefits",
    "ice bath temperature",
    "cold plunge frequency",
    "sauna before or after workout",
]

_LOCAL_TOPICS = [
    "cold plunge {city}",
    "sauna studio {city}",
    "contrast therapy {city}",
    "best recovery studio {city}",
]

_METRO_CITIES = {
    "denver_co": "Denver CO",
    "dallas_fort_worth_tx": "Dallas TX",
    "philadelphia_pa": "Philadelphia PA",
}

# Reddit communities most relevant to our topics
_SUBREDDITS = [
    "r/coldplunge",
    "r/sauna",
    "r/icebath",
    "r/biohacking",
    "r/fitness",
]

# Expand PAA accordions before extracting
_PAA_JS = """
(async () => {
    const btns = document.querySelectorAll('[jsname="yEVEwb"], .related-question-pair');
    for (const b of Array.from(btns).slice(0, 10)) {
        b.click();
        await new Promise(r => setTimeout(r, 400));
    }
})();
"""

_BROWSER = BrowserConfig(
    headless=True,
    browser_type="chromium",
    extra_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
)


async def harvest_questions() -> list:
    questions = []
    seen: set = set()

    async with AsyncWebCrawler(config=_BROWSER) as crawler:
        # Global topics
        for topic in _GLOBAL_TOPICS:
            paa = await _paa(crawler, topic)
            for q in paa:
                slug = _qslug(q)
                if slug not in seen:
                    seen.add(slug)
                    questions.append({"slug": slug, "question": q, "type": "global", "metro": None})

        # Local topics per metro
        for metro_id, city in _METRO_CITIES.items():
            for tmpl in _LOCAL_TOPICS:
                topic = tmpl.format(city=city)
                paa = await _paa(crawler, topic)
                for q in paa:
                    slug = _qslug(q)
                    if slug not in seen:
                        seen.add(slug)
                        questions.append({"slug": slug, "question": q, "type": "local", "metro": metro_id})

        # Reddit
        reddit_qs = await _reddit(crawler)
        for item in reddit_qs:
            if item["slug"] not in seen:
                seen.add(item["slug"])
                questions.append(item)

    log.info("Harvested %d questions", len(questions))
    return questions


async def _paa(crawler, topic: str) -> list:
    url = "https://www.google.com/search?q=" + topic.replace(" ", "+")
    try:
        res = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                js_code=_PAA_JS,
                delay_before_return_html=3.0,
                cache_mode=CacheMode.BYPASS,
            ),
        )
        if res.success:
            qs = _parse_paa(res.html)
            log.info("PAA '%s' → %d questions", topic, len(qs))
            await asyncio.sleep(2.0)
            return qs
    except Exception as exc:
        log.warning("PAA failed (%s): %s", topic, exc)
    await asyncio.sleep(2.0)
    return []


def _parse_paa(html: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    qs = []
    for sel in ("[jsname='yEVEwb'] span", ".dnXCYb", ".related-question-pair span", "[data-initq]"):
        for el in soup.select(sel):
            text = el.get_text(strip=True)
            if text.endswith("?") and 20 <= len(text) <= 200:
                qs.append(text)
    return list(dict.fromkeys(qs))


async def _reddit(crawler) -> list:
    questions = []
    for sub in _SUBREDDITS:
        url = f"https://old.reddit.com/{sub}/search?q=?&sort=top&t=year&restrict_sr=1"
        try:
            res = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    delay_before_return_html=2.5,
                    cache_mode=CacheMode.BYPASS,
                ),
            )
            if res.success:
                hits = _parse_reddit(res.html)
                questions.extend(hits)
                log.info("Reddit %s → %d questions", sub, len(hits))
        except Exception as exc:
            log.warning("Reddit failed (%s): %s", sub, exc)
        await asyncio.sleep(2.0)
    return questions


def _parse_reddit(html: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.select("a.title"):
        title = a.get_text(strip=True)
        if title.endswith("?") and 25 <= len(title) <= 200:
            slug = _qslug(title)
            out.append({"slug": slug, "question": title, "type": "global", "metro": None})
    return out


def _qslug(question: str) -> str:
    s = re.sub(r"[^\w\s-]", "", question.lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")[:80]
