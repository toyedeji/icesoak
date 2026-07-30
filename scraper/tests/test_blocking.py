"""Tests for anti-bot detection and search accounting (utils/blocking.py).

The bug under test: crawlers/google_maps.py had `if res.success:` with no else,
inside `except Exception: log.warning(...)`. A consent wall, a /sorry/ CAPTCHA
and an HTTP 429 all produced zero records, one unread warning line, and a run
that carried on to write a partial dataset as if it were complete.

The 2026-07-19 losses clustered by metro — DFW 7, Philadelphia 7,
Los Angeles 6, Chicago 5, Denver 5 — the signature of contiguous blocks of the
180-search query loop being served anti-bot pages, not of ~40 businesses closing
in one week.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.blocking import (  # noqa: E402
    DEFAULT_MAX_SEARCH_FAILURE_RATE,
    SearchStats,
    classify_response,
    is_blocked,
    max_search_failure_rate_from_env,
)

FEED = '<div role="feed">' + ("<div>studio</div>" * 400) + "</div>"


def page(body: str) -> str:
    """Pad to clear the minimum-plausible-length check."""
    return body + ("<!-- pad -->" * 400)


class TestClassifyResponse(unittest.TestCase):

    def test_a_real_results_page_is_not_blocked(self):
        self.assertIsNone(classify_response(page(FEED), 200))
        self.assertFalse(is_blocked(page(FEED), 200))

    def test_429_is_rate_limit(self):
        self.assertEqual(classify_response(page(FEED), 429), "rate_limit")

    def test_403_and_503_are_blocks(self):
        self.assertEqual(classify_response(page(FEED), 403), "http_403")
        self.assertEqual(classify_response(page(FEED), 503), "http_503")

    def test_captcha_page(self):
        for body in (
            '<form id="captcha-form">',
            "Our systems have detected unusual traffic from your computer network",
            '<div class="g-recaptcha">',
            '<img src="/sorry/image?id=123">',
            "automated queries",
        ):
            self.assertEqual(
                classify_response(page(body), 200), "captcha",
                f"should classify as captcha: {body!r}",
            )

    def test_consent_wall(self):
        for body in (
            "<title>Before you continue to Google</title>",
            '<script src="https://consent.google.com/x">',
            "Choose your cookie settings",
        ):
            self.assertEqual(
                classify_response(page(body), 200), "consent",
                f"should classify as consent: {body!r}",
            )

    def test_captcha_wins_over_consent(self):
        """A /sorry/ page can carry consent markup; the CAPTCHA is the real cause."""
        body = page('<div class="g-recaptcha"> Before you continue to Google ')
        self.assertEqual(classify_response(body, 200), "captcha")

    def test_a_200_with_no_feed_is_flagged(self):
        """Silent-failure mode: HTTP 200, plausible length, but not a results page."""
        self.assertEqual(classify_response(page("<div>something else</div>"), 200), "no_feed")

    def test_empty_or_stub_response(self):
        self.assertEqual(classify_response("", 200), "empty")
        self.assertEqual(classify_response(None, 200), "empty")
        self.assertEqual(classify_response("<html></html>", 200), "empty")

    def test_status_code_beats_body(self):
        """A 429 that still renders a feed is a block, not a success."""
        self.assertEqual(classify_response(page(FEED), 429), "rate_limit")


class TestSearchStats(unittest.TestCase):

    def test_clean_run_does_not_abort(self):
        s = SearchStats(max_failure_rate=0.25)
        for _ in range(20):
            s.record_success("denver_co", cards=12)
        self.assertEqual(s.failure_rate, 0.0)
        self.assertFalse(s.should_abort())

    def test_run_over_the_failure_threshold_aborts(self):
        s = SearchStats(max_failure_rate=0.25)
        for _ in range(14):
            s.record_success("denver_co", cards=10)
        for _ in range(6):
            s.record_failure("philadelphia_pa", "captcha")
        self.assertAlmostEqual(s.failure_rate, 0.30)
        self.assertTrue(s.should_abort())

    def test_exactly_at_threshold_does_not_abort(self):
        s = SearchStats(max_failure_rate=0.25)
        for _ in range(15):
            s.record_success("denver_co", cards=10)
        for _ in range(5):
            s.record_failure("denver_co", "consent")
        self.assertAlmostEqual(s.failure_rate, 0.25)
        self.assertFalse(s.should_abort(), "strictly greater-than, not >=")

    def test_small_sample_does_not_abort(self):
        """A targeted --metros run may issue only a handful of searches."""
        s = SearchStats(max_failure_rate=0.25, min_attempts=8)
        s.record_failure("denver_co", "captcha")
        s.record_success("denver_co", cards=3)
        self.assertGreater(s.failure_rate, 0.25)
        self.assertFalse(s.should_abort(), "too few attempts to judge")

    def test_clustered_metro_failure_is_surfaced(self):
        """The 2026-07-19 signature: whole metros dark while others are fine."""
        s = SearchStats()
        for _ in range(15):
            s.record_success("denver_co", cards=10)
        for _ in range(15):
            s.record_failure("philadelphia_pa", "rate_limit")
        s.record_success("austin_tx", cards=5)
        s.record_failure("austin_tx", "consent")

        self.assertEqual(s.fully_failed_metros(), ["philadelphia_pa"],
                         "a partially-failing metro is not 'dark'")

    def test_blocked_count_separates_anti_bot_from_ordinary_errors(self):
        s = SearchStats()
        s.record_failure("m", "captcha")
        s.record_failure("m", "rate_limit")
        s.record_failure("m", "http_403")
        s.record_failure("m", "exception")     # a timeout, not anti-bot
        s.record_failure("m", "no_feed")       # ambiguous
        self.assertEqual(s.blocked_count, 3)
        self.assertEqual(s.failed, 5)

    def test_summary_is_human_readable(self):
        s = SearchStats()
        s.record_success("denver_co", cards=9)
        s.record_failure("denver_co", "captcha")
        text = s.summary()
        for token in ("searches=2", "ok=1", "failed=1", "captcha=1"):
            self.assertIn(token, text)


class TestFailureRateEnv(unittest.TestCase):
    def test_default(self):
        self.assertAlmostEqual(DEFAULT_MAX_SEARCH_FAILURE_RATE, 0.25)
        self.assertAlmostEqual(max_search_failure_rate_from_env(), 0.25)

    def test_override_and_rejection(self):
        import os
        os.environ["ICESOAK_MAX_SEARCH_FAILURE_RATE"] = "0.5"
        self.assertAlmostEqual(max_search_failure_rate_from_env(), 0.5)
        for bad in ("abc", "0", "-1", "1.5"):
            os.environ["ICESOAK_MAX_SEARCH_FAILURE_RATE"] = bad
            self.assertAlmostEqual(
                max_search_failure_rate_from_env(), 0.25,
                f"{bad!r} must fall back to the default",
            )
        del os.environ["ICESOAK_MAX_SEARCH_FAILURE_RATE"]


if __name__ == "__main__":
    unittest.main(verbosity=2)
