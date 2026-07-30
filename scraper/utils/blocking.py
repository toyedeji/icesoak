"""Detect Google anti-bot responses: consent walls, CAPTCHAs, rate limits.

Why this exists
---------------
crawlers/google_maps.py used to treat every non-result identically: a bare
`if res.success:` with no else, wrapped in `except Exception: log.warning(...)`.
A consent interstitial, a "/sorry/" CAPTCHA page or an HTTP 429 all produced
zero records, one warning line nobody reads, and a run that carried on to write
a partial dataset as if it were complete.

One full run issues 5 queries x 3 cities x 12 metros = 180 Maps searches at
2.5s spacing from a single IP, plus crawlers/listicles.py hitting
google.com/search on top.  Throttling is expected, not exceptional.

The 2026-07-19 losses clustered by metro — DFW 7, Philadelphia 7,
Los Angeles 6, Chicago 5, Denver 5 — which is the signature of contiguous
blocks of the query loop being served anti-bot pages rather than of ~40
businesses closing in the same week.

This module is deliberately free of crawl4ai imports so it can be unit-tested
in an environment without a browser stack.
"""
import logging
import os
import re

log = logging.getLogger(__name__)

# Abort the run if more than this fraction of Maps searches fail. A run that lost
# a quarter of its searches has not observed the directory and must not be
# allowed to write a dataset that looks complete.
DEFAULT_MAX_SEARCH_FAILURE_RATE = 0.25


def max_search_failure_rate_from_env(
    default: float = DEFAULT_MAX_SEARCH_FAILURE_RATE,
) -> float:
    """Read ICESOAK_MAX_SEARCH_FAILURE_RATE, falling back to the default.

    Lives here rather than in crawlers/google_maps.py so scrape.py can read it
    without importing that module — google_maps pulls in crawl4ai, which drags a
    whole browser stack into any process that touches it (and is absent in the
    test environment).
    """
    raw = os.environ.get("ICESOAK_MAX_SEARCH_FAILURE_RATE")
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        log.warning(
            "ICESOAK_MAX_SEARCH_FAILURE_RATE=%r is not a number — using %.2f",
            raw, default,
        )
        return default
    if not 0.0 < value <= 1.0:
        log.warning(
            "ICESOAK_MAX_SEARCH_FAILURE_RATE=%.2f out of range (0,1] — using %.2f",
            value, default,
        )
        return default
    return value


# Consent interstitial ("Before you continue to Google", cookie choices).
_CONSENT_RE = re.compile(
    r"(?i)consent\.google\.|/consent\?|before\s+you\s+continue"
    r"|choose\s+your\s+(?:cookie|search)\s+settings"
    r"|accept\s+all\s*(?:</|\|)|id=\"?consent"
)

# Interstitial CAPTCHA / "unusual traffic" block page.
_CAPTCHA_RE = re.compile(
    r"(?i)/sorry/index|/sorry/image|unusual\s+traffic"
    r"|our\s+systems\s+have\s+detected"
    r"|recaptcha|g-recaptcha|captcha-form"
    r"|automated\s+queries|not\s+a\s+robot"
)

# Explicit rate-limit signalling in body text (the status code is checked
# separately by the caller, which has the response object).
_RATELIMIT_RE = re.compile(
    r"(?i)\btoo\s+many\s+requests\b|\brate[\s-]?limit"
    r"|\berror\s*429\b|\bquota\s+exceeded\b"
)

# Statuses that mean "we were refused", not "there is nothing here".
BLOCKING_STATUS_CODES = frozenset({403, 429, 503})

# A rendered results page always contains the feed container.  Its absence,
# combined with a substantial body, means we were served *something else*.
_FEED_RE = re.compile(r"(?i)role=[\"']?feed")

# Below this length the response is a stub/error, not a rendered page.
_MIN_PLAUSIBLE_HTML = 2_000


def classify_response(html: str | None, status_code: int | None = None) -> str | None:
    """Return a block reason, or None if the response looks legitimate.

    Reasons: 'captcha', 'consent', 'rate_limit', 'http_<code>', 'empty',
    'no_feed'.  Ordered most-specific first so the log names the real cause.
    """
    if status_code is not None and status_code in BLOCKING_STATUS_CODES:
        return "rate_limit" if status_code == 429 else f"http_{status_code}"

    if not html or len(html) < _MIN_PLAUSIBLE_HTML:
        return "empty"

    # CAPTCHA before consent: a /sorry/ page can also carry consent markup, and
    # the CAPTCHA is the more actionable diagnosis (back off vs. send a cookie).
    if _CAPTCHA_RE.search(html):
        return "captcha"
    if _CONSENT_RE.search(html):
        return "consent"
    if _RATELIMIT_RE.search(html):
        return "rate_limit"
    if not _FEED_RE.search(html):
        return "no_feed"
    return None


def is_blocked(html: str | None, status_code: int | None = None) -> bool:
    return classify_response(html, status_code) is not None


class SearchStats:
    """Per-run tally of search outcomes, and the abort decision.

    A run that quietly loses a third of its searches must not be allowed to
    write a dataset that looks complete.  Retention (processors/retention.py)
    already prevents the *loss*, but a heavily blocked run should not be
    trusted to add or refresh anything either — so we abort before the write
    rather than commit a half-observed dataset.
    """

    def __init__(self, max_failure_rate: float = 0.25, min_attempts: int = 8):
        self.max_failure_rate = max_failure_rate
        # Below this many attempts the rate is too noisy to act on (a targeted
        # --metros run may legitimately issue only a handful of searches).
        self.min_attempts = min_attempts
        self.attempted = 0
        self.succeeded = 0
        self.failed = 0
        self.reasons: dict = {}
        self.by_metro: dict = {}

    def record_success(self, metro: str, cards: int) -> None:
        self.attempted += 1
        self.succeeded += 1
        bucket = self.by_metro.setdefault(metro, {"ok": 0, "fail": 0, "cards": 0})
        bucket["ok"] += 1
        bucket["cards"] += cards

    def record_failure(self, metro: str, reason: str) -> None:
        self.attempted += 1
        self.failed += 1
        self.reasons[reason] = self.reasons.get(reason, 0) + 1
        bucket = self.by_metro.setdefault(metro, {"ok": 0, "fail": 0, "cards": 0})
        bucket["fail"] += 1

    @property
    def failure_rate(self) -> float:
        return (self.failed / self.attempted) if self.attempted else 0.0

    @property
    def blocked_count(self) -> int:
        """Failures attributable to anti-bot measures specifically."""
        return sum(
            count for reason, count in self.reasons.items()
            if reason in ("captcha", "consent", "rate_limit")
            or reason.startswith("http_")
        )

    def should_abort(self) -> bool:
        if self.attempted < self.min_attempts:
            return False
        return self.failure_rate > self.max_failure_rate

    def fully_failed_metros(self) -> list:
        """Metros where every single search failed — the clustered signature."""
        return sorted(
            metro for metro, b in self.by_metro.items()
            if b["fail"] > 0 and b["ok"] == 0
        )

    def summary(self) -> str:
        reasons = ", ".join(
            f"{r}={n}" for r, n in sorted(self.reasons.items(), key=lambda kv: -kv[1])
        ) or "none"
        return (
            f"searches={self.attempted} ok={self.succeeded} failed={self.failed} "
            f"({self.failure_rate:.0%}) blocked={self.blocked_count} reasons: {reasons}"
        )
