"""Regression tests for the questions.json merge.

The bug these exist to prevent: scrape.py used to overwrite questions.json with
harvest_questions() output, which emits only slug/question/type/metro. Every run
therefore deleted the prose written by the separate content pass. Git history
shows it happening three times (2026-06-28, 2026-07-12, and 2026-07-19, the last
of which wrote a literal []).

Run: python3 -m pytest scraper/test_merge_questions.py   (or: python3 scraper/test_merge_questions.py)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scrape import _merge_questions, _read_existing_questions  # noqa: E402
from crawlers.relevance import is_on_topic, filter_on_topic  # noqa: E402


# A fixture shaped exactly like a post-content-pass record.
EXISTING = [
    {
        "slug": "how-long-do-you-sit-in-an-ice-bath",
        "question": "How long do you sit in an ice bath?",
        "type": "global",
        "metro": None,
        "category": "ice-bath",
        "capsule": "Most people sit in an ice bath for 2 to 5 minutes.",
        "author": "The IceSoak Team",
        "risk_tier": "B",
        "updated": "2026-07-06",
        "sections": [{"h2": "How long is enough", "body": "Two to five minutes is plenty."}],
    },
    {
        "slug": "orphan-stub-no-content",
        "question": "Orphan stub with no content?",
        "type": "global",
        "metro": None,
    },
]

# What a later harvest returns: same slugs, stub fields only, one reworded.
HARVESTED = [
    {
        "slug": "how-long-do-you-sit-in-an-ice-bath",
        "question": "How long should you sit in an ice bath?",  # reworded upstream
        "type": "global",
        "metro": "denver_co",                                    # newly localised
    },
    {"slug": "brand-new-question", "question": "Brand new question?", "type": "global", "metro": None},
]


def test_bodies_survive_a_harvest():
    merged, _ = _merge_questions(HARVESTED, EXISTING)
    rec = next(q for q in merged if q["slug"] == "how-long-do-you-sit-in-an-ice-bath")

    assert rec["sections"], "sections must survive the merge"
    assert rec["sections"][0]["body"] == "Two to five minutes is plenty."
    assert rec["capsule"].startswith("Most people sit")
    assert rec["author"] == "The IceSoak Team"
    assert rec["category"] == "ice-bath"
    assert rec["updated"] == "2026-07-06"


def test_risk_tier_survives_a_harvest():
    """risk_tier drives affiliate suppression and the medical disclaimer.

    If a harvest strips it, a Tier A page about autoimmune thyroid disease
    silently starts selling a $4,990 cold plunge tub again. Nothing else in the
    build would catch that, because a missing field is not a broken field —
    the page renders fine, it just renders the wrong thing.
    """
    merged, _ = _merge_questions(HARVESTED, EXISTING)
    rec = next(q for q in merged if q["slug"] == "how-long-do-you-sit-in-an-ice-bath")

    assert rec.get("risk_tier") == "B", "risk_tier must survive the merge"


def test_risk_tier_is_not_invented_for_new_slugs():
    """A freshly harvested stub has no tier, so it must not claim one.

    Untiered guides are bodyless stubs served noindex. They must never inherit
    a tier by accident — an unearned "D" would render the affiliate block.
    """
    merged, _ = _merge_questions(HARVESTED, EXISTING)
    rec = next(q for q in merged if q["slug"] == "brand-new-question")

    assert "risk_tier" not in rec


def test_every_published_guide_in_the_repo_carries_a_tier():
    """The real file, not a fixture. An untiered published guide is a hole."""
    repo_file = Path(__file__).resolve().parent.parent / "questions.json"
    data = json.loads(repo_file.read_text(encoding="utf-8"))

    published = [
        q for q in data
        if any((s or {}).get("body", "").strip() for s in (q.get("sections") or []))
    ]
    untiered = [q["slug"] for q in published if not q.get("risk_tier")]
    assert not untiered, f"published guides with no risk_tier: {untiered}"

    bad = [
        (q["slug"], q["risk_tier"]) for q in published
        if q["risk_tier"] not in {"A", "B", "C", "D", "E"}
    ]
    assert not bad, f"risk_tier outside A-E: {bad}"


def test_harvest_fields_win():
    """The scraper owns slug/question/type/metro and refreshes them."""
    merged, _ = _merge_questions(HARVESTED, EXISTING)
    rec = next(q for q in merged if q["slug"] == "how-long-do-you-sit-in-an-ice-bath")

    assert rec["question"] == "How long should you sit in an ice bath?"
    assert rec["metro"] == "denver_co"


def test_new_slugs_are_added_without_content_fields():
    merged, _ = _merge_questions(HARVESTED, EXISTING)
    rec = next(q for q in merged if q["slug"] == "brand-new-question")

    assert "sections" not in rec
    assert "author" not in rec


def test_dropped_slug_with_prose_is_retained():
    """A slug the harvest stops returning keeps its URL if it has content."""
    harvested = [h for h in HARVESTED if h["slug"] == "brand-new-question"]
    merged, retained = _merge_questions(harvested, EXISTING)
    slugs = {q["slug"] for q in merged}

    assert "how-long-do-you-sit-in-an-ice-bath" in slugs, "content must not be deleted"
    assert len(retained) == 1


def test_dropped_empty_stub_is_discarded():
    """A slug with no content and no harvest entry is not worth keeping."""
    harvested = [h for h in HARVESTED if h["slug"] == "brand-new-question"]
    merged, _ = _merge_questions(harvested, EXISTING)

    assert "orphan-stub-no-content" not in {q["slug"] for q in merged}


def test_empty_harvest_preserves_everything():
    """Merging nothing must not empty the file — the 2026-07-19 failure."""
    merged, retained = _merge_questions([], EXISTING)

    assert len(merged) == 1
    assert merged[0]["slug"] == "how-long-do-you-sit-in-an-ice-bath"
    assert merged[0]["sections"]
    assert len(retained) == 1


def test_read_existing_handles_missing_and_corrupt(tmp_path=None):
    base = Path(tmp_path) if tmp_path else Path("/tmp")
    missing = base / "definitely-not-here.json"
    assert _read_existing_questions(missing) == []

    corrupt = base / "corrupt-questions.json"
    corrupt.write_text("{not json", encoding="utf-8")
    assert _read_existing_questions(corrupt) == []
    corrupt.unlink()

    notalist = base / "notalist-questions.json"
    notalist.write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert _read_existing_questions(notalist) == []
    notalist.unlink()


def test_real_repo_file_has_bodies():
    """Guards the restored questions.json itself, not just the merge logic."""
    repo_file = Path(__file__).resolve().parent.parent / "questions.json"
    data = json.loads(repo_file.read_text(encoding="utf-8"))

    assert len(data) > 0, "questions.json must never be empty — that 404s every guide"
    with_bodies = [q for q in data if q.get("sections")]
    # 32 recovered on 2026-07-28, minus the 7 dropped on 2026-08-01.
    assert len(with_bodies) >= 25, f"expected >=25 guides with bodies, got {len(with_bodies)}"


def test_denylisted_slugs_are_absent_and_have_redirect_targets():
    """The denylist is only half a deletion — the other half is the 301."""
    root = Path(__file__).resolve().parent.parent
    deny = json.loads((root / "guide_denylist.json").read_text(encoding="utf-8"))
    data = json.loads((root / "questions.json").read_text(encoding="utf-8"))

    slugs = deny["slugs"]
    assert len(slugs) == 7, f"expected 7 denylisted slugs, got {len(slugs)}"

    live = {q["slug"] for q in data}
    resurrected = sorted(live & set(slugs))
    assert not resurrected, f"denylisted slugs are back in questions.json: {resurrected}"

    for slug, meta in slugs.items():
        target = meta.get("redirect_to", "")
        assert target.startswith("/"), f"{slug} has no redirect target"
        assert target.endswith("/"), f"{slug} target must have a trailing slash: {target}"
        assert target != f"/guides/{slug}/", f"{slug} redirects to itself"
        # Single hop: no target may itself be denylisted.
        assert target.removeprefix("/guides/").rstrip("/") not in slugs, (
            f"{slug} -> {target} is a redirect chain"
        )


def test_off_topic_questions_are_rejected_for_every_metro():
    """The two Dallas travel guides were a symptom; the filter is the fix.

    Every metro seeds the same local PAA queries, so a Dallas-shaped fix would
    just move the problem to whichever metro drifted next. These assertions run
    the known-bad phrasing against several metros precisely so the filter cannot
    quietly become a Dallas special case.
    """
    metros = ["Dallas", "Denver", "Philadelphia", "Miami", "Nashville"]

    for metro in metros:
        for template in (
            "What are some hidden free gems in {}?",
            "Where to walk indoors in {}?",
            "What is there to do in {} on a rainy day?",
            "Is {} a good place to live?",
        ):
            q = template.format(metro)
            assert not is_on_topic(q), f"off-topic question accepted: {q}"


def test_on_topic_local_questions_still_pass_for_every_metro():
    """The filter must not cost legitimate local harvesting.

    This is the half that would fail if someone 'fixed' the filter by dropping
    metro seeds instead of filtering on subject.
    """
    for metro in ["Dallas", "Denver", "Philadelphia", "Miami", "Nashville"]:
        for template in (
            "Where can I cold plunge in {}?",
            "What is the best sauna studio in {}?",
            "How much does contrast therapy cost in {}?",
            "Is there an ice bath near me in {}?",
            "Best recovery studio in {}?",
        ):
            q = template.format(metro)
            assert is_on_topic(q), f"on-topic question rejected: {q}"


def test_relevance_filter_handles_the_awkward_inputs():
    assert not is_on_topic("")
    assert not is_on_topic("   ")
    assert not is_on_topic(None)
    # Punctuation, casing and hyphenation must not decide the outcome.
    assert is_on_topic("COLD-PLUNGE benefits?")
    assert is_on_topic("How long in the sauna??")
    assert is_on_topic("Cold plunge — how cold?")


def test_filter_on_topic_partitions_records():
    records = [
        {"slug": "a", "question": "How cold should an ice bath be?"},
        {"slug": "b", "question": "What are some hidden free gems in Dallas?"},
        {"slug": "c", "question": "Does sauna help recovery?"},
    ]
    kept, rejected = filter_on_topic(records)

    assert [r["slug"] for r in kept] == ["a", "c"]
    assert [r["slug"] for r in rejected] == ["b"]


def test_the_two_removed_guides_would_be_rejected_today():
    """Closes the loop: the exact titles that shipped must not survive now."""
    assert not is_on_topic("What are some hidden free gems in Dallas?")
    assert not is_on_topic("Where to walk indoors in Dallas?")


def test_dallas_is_still_harvested():
    """The seed was restored — the filter is the fix, not the metro list."""
    src = (
        Path(__file__).resolve().parent / "crawlers" / "questions.py"
    ).read_text(encoding="utf-8")
    assert "Dallas TX" in src, "Dallas seed was removed instead of filtering on subject"


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL  {name}: {e}")
    print(f"\n{'FAILED' if failed else 'All scraper merge tests passed'} ({failed} failing)")
    sys.exit(1 if failed else 0)
