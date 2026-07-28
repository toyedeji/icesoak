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
    assert len(with_bodies) >= 32, f"expected >=32 guides with bodies, got {len(with_bodies)}"


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
