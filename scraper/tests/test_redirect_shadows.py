"""Tests for the redirect-shadow guard (processors/quality_gate.py).

The failure this prevents: a redirect and a live page both claim one URL. When
the redirect is FORCED it wins and the page is unreachable — and because a 301
to a plausible city page is indistinguishable from a deliberate consolidation,
nothing looks wrong. netlify.toml carries 49 /studio/ rules for slugs a healthy
crawl is expected to re-discover, so the collision is scheduled, not theoretical.

Runs on every refresh and blocks. Same reasoning as the churn gate and the
BLKNomad image guard: a check nobody reads is not a check.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processors.quality_gate import (  # noqa: E402
    check_redirect_shadows,
    parse_redirects,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def rule(frm, to, force):
    return (
        f'[[redirects]]\n'
        f'  from = "{frm}"\n'
        f'  to = "{to}"\n'
        f'  status = 301\n'
        f'  force = {"true" if force else "false"}\n\n'
    )


def studio(sid):
    return {"id": sid, "name": sid, "metro": "denver_co", "city": "Denver"}


LIVE = [studio("alpha"), studio("beta"), studio("gamma")]


class TestForcedShadowing(unittest.TestCase):

    def test_forced_redirect_over_a_live_page_ABORTS(self):
        toml = rule("/studio/alpha/", "/cold-plunge/denver/", force=True)
        r = check_redirect_shadows(LIVE, toml)
        self.assertTrue(r["aborts"], "a forced redirect over a live page must abort")
        self.assertIn("unreachable", r["aborts"][0])
        self.assertIn("/studio/alpha/", r["aborts"][0])
        self.assertEqual(r["metrics"]["shadowed"], 1)

    def test_unforced_redirect_over_a_live_page_is_FINE(self):
        """This is the pre-staged de-duplication case — dormant, not broken."""
        toml = rule("/studio/alpha/", "/studio/beta/", force=False)
        r = check_redirect_shadows(LIVE, toml)
        self.assertEqual(r["aborts"], [])
        self.assertEqual(r["metrics"]["dormant"], 1)
        self.assertEqual(r["metrics"]["shadowed"], 0)

    def test_forced_redirect_over_an_ABSENT_page_is_fine(self):
        """The legitimate case the 46 rules were written for."""
        toml = rule("/studio/long-gone/", "/cold-plunge/denver/", force=True)
        r = check_redirect_shadows(LIVE, toml)
        self.assertEqual(r["aborts"], [])
        self.assertEqual(r["metrics"]["shadowed"], 0)

    def test_multiple_shadows_are_all_named(self):
        toml = (rule("/studio/alpha/", "/cold-plunge/denver/", True)
                + rule("/studio/beta/", "/sauna/denver/", True))
        r = check_redirect_shadows(LIVE, toml)
        self.assertEqual(r["metrics"]["shadowed"], 2)
        self.assertIn("alpha", r["aborts"][0])
        self.assertIn("beta", r["aborts"][0])


class TestBrokenTargets(unittest.TestCase):

    def test_redirect_into_a_nonexistent_studio_page_ABORTS(self):
        """A 301 into a 404 launders the failure through a deliberate-looking step."""
        toml = rule("/studio/old-slug/", "/studio/does-not-exist/", force=False)
        r = check_redirect_shadows(LIVE, toml)
        self.assertTrue(r["aborts"])
        self.assertIn("404", r["aborts"][0])
        self.assertEqual(r["metrics"]["broken_targets"], 1)

    def test_redirect_to_a_live_studio_page_is_fine(self):
        toml = rule("/studio/old-slug/", "/studio/gamma/", force=False)
        r = check_redirect_shadows(LIVE, toml)
        self.assertEqual(r["aborts"], [])
        self.assertEqual(r["metrics"]["broken_targets"], 0)

    def test_vertical_landing_page_targets_are_accepted(self):
        toml = "".join(
            rule(f"/studio/gone-{i}/", p + "denver/", False)
            for i, p in enumerate(
                ("/cold-plunge/", "/sauna/", "/infrared-sauna/", "/contrast-therapy/")
            )
        )
        r = check_redirect_shadows(LIVE, toml)
        self.assertEqual(r["aborts"], [])
        self.assertEqual(r["warns"], [])

    def test_unrecognised_target_shape_warns(self):
        toml = rule("/studio/gone/", "/some/other/place/", force=False)
        r = check_redirect_shadows(LIVE, toml)
        self.assertEqual(r["aborts"], [])
        self.assertTrue(any("unrecognised" in w for w in r["warns"]))


class TestParser(unittest.TestCase):

    def test_following_table_does_not_leak_into_a_rule(self):
        """A [[headers]] block after a rule must not supply its keys."""
        toml = (
            rule("/studio/gone/", "/sauna/denver/", False)
            + '[[headers]]\n  for = "/*"\n  [headers.values]\n'
            '    X-Frame-Options = "DENY"\n'
        )
        rules = parse_redirects(toml)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["from"], "/studio/gone/")
        self.assertEqual(rules[0]["to"], "/sauna/denver/")

    def test_missing_force_defaults_to_false(self):
        toml = '[[redirects]]\n  from = "/studio/x/"\n  to = "/sauna/denver/"\n  status = 301\n'
        self.assertFalse(parse_redirects(toml)[0]["force"])

    def test_malformed_block_warns_rather_than_crashes(self):
        toml = '[[redirects]]\n  status = 301\n  force = true\n'
        r = check_redirect_shadows(LIVE, toml)
        self.assertTrue(any("missing from/to" in w for w in r["warns"]))

    def test_trailing_slash_optional(self):
        toml = rule("/studio/alpha", "/cold-plunge/denver/", force=True)
        r = check_redirect_shadows(LIVE, toml)
        self.assertEqual(r["metrics"]["shadowed"], 1, "no trailing slash must still match")


class TestAgainstTheRealFile(unittest.TestCase):
    """The committed netlify.toml must be clean against the committed data."""

    @classmethod
    def setUpClass(cls):
        cls.toml = (REPO_ROOT / "netlify.toml").read_text(encoding="utf-8")
        cls.studios = json.loads(
            (REPO_ROOT / "studios.json").read_text(encoding="utf-8")
        )

    def test_no_shadowing_and_no_broken_targets(self):
        r = check_redirect_shadows(self.studios, self.toml)
        self.assertEqual(r["aborts"], [], "\n".join(r["aborts"]))

    def test_no_studio_rule_is_forced(self):
        """The whole point of the force = false decision — assert it stays true."""
        forced = [
            rl for rl in parse_redirects(self.toml)
            if rl["force"] and rl["from"] and rl["from"].startswith("/studio/")
        ]
        self.assertEqual(
            forced, [],
            "a /studio/ rule was set back to force = true — read the comment "
            "block above the studio section in netlify.toml before changing it",
        )

    def test_the_four_non_studio_rules_are_still_forced(self):
        """Those redirect paths that DO exist and must win. Don't unforce them."""
        forced = {
            rl["from"] for rl in parse_redirects(self.toml) if rl["force"]
        }
        self.assertIn("/sitemap.xml", forced)
        self.assertEqual(len(forced), 4, f"expected exactly 4 forced rules, got {forced}")

    def test_the_three_duplicate_pairs_are_staged_and_dormant(self):
        r = check_redirect_shadows(self.studios, self.toml)
        self.assertEqual(
            r["metrics"]["dormant"], 3,
            "the 3 pre-staged de-duplication rules should sit dormant over live pages",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
