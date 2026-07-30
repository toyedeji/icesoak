"""Retention and staleness tracking for studios.json.

Why this module exists
----------------------
Until this change the scheduled full run (run_scrape.sh, no --metros) took the
`else` branch in scrape.py and wrote studios.json wholesale:

    out.write_text(json.dumps(studios, indent=2, ensure_ascii=False))

Inventory each week was therefore exactly — and only — what that single crawl
happened to see.  The merge-and-preserve logic, including the explicit
"scraper was blocked — keep old data" guard, existed *only* on the --metros
partial branch, which the scheduled run never takes.  The two guards added
after the 2026-07-19 incident (empty-harvest refusal, 80% shrink floor) were
likewise attached only to the questions.json write.

Measured cost of the gap:

    2026-07-15 → 07-19 run:  239 → 229,  45 dropped (18.8%), 35 added
    2026-07-19 → 07-26 run:  229 → 232,  23 dropped (10.0%), 26 added

Of the 34 studios that vanished with no counterpart anywhere across that span,
27 carried a google_place_id and only 3 had a website — i.e. Maps-sourced
records that exist in the output only if that morning's Maps render happened
to include them.

The fix
-------
Absence from ONE crawl is a missed observation, not a closure.  A studio absent
from the current crawl is retained, its `missed_runs` counter incremented, and
it is dropped only after `max_missing_runs` CONSECUTIVE misses (default 3 —
about three weeks at the current Sunday cadence).

Two bookkeeping fields are added to each record:

    last_seen_at  ISO date (YYYY-MM-DD) of the most recent run whose crawl
                  actually returned this studio.  None only when the record
                  predates this change and the previous run date could not be
                  determined from git.
    missed_runs   Consecutive runs since then.  0 whenever the crawl returned
                  the studio.

A NOTE ON THE NEW FAILURE MODE
------------------------------
Retention makes data loss impossible but makes a dead scraper *invisible*: a
run where Maps returns nothing now produces a file identical to last week's
and the quality gate sees a healthy, unchanged total.  `fresh_ratio` in the
returned stats exists for exactly this — scrape.py logs it loudly and
quality_gate.py fails on a stale-record share above its threshold.
"""
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from processors.identity import identity_key, identity_tier

log = logging.getLogger(__name__)

# Consecutive misses before a studio is removed.  Override with
# ICESOAK_MAX_MISSING_RUNS.  3 ≈ three weeks at the Sunday 03:00 UTC cadence.
DEFAULT_MAX_MISSING_RUNS = 3

# Bookkeeping fields owned by this module.  Never filled forward as data.
_BOOKKEEPING = ("last_seen_at", "missed_runs")


class RetentionAbort(RuntimeError):
    """Raised when the merge refuses to write. Never write a partial result."""


def max_missing_runs_from_env(default: int = DEFAULT_MAX_MISSING_RUNS) -> int:
    raw = os.environ.get("ICESOAK_MAX_MISSING_RUNS")
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        log.warning(
            "ICESOAK_MAX_MISSING_RUNS=%r is not an integer — using default %d",
            raw, default,
        )
        return default
    if value < 1:
        log.warning(
            "ICESOAK_MAX_MISSING_RUNS=%d is < 1, which would drop studios on "
            "their first miss — using default %d", value, default,
        )
        return default
    return value


def previous_run_date_from_git(repo_root: Path) -> Optional[str]:
    """Committer date (YYYY-MM-DD) of the last commit touching studios.json.

    Used to seed `last_seen_at` on records that predate this change.  Every
    record in the current file was, by construction of the old overwrite path,
    returned by the crawl that produced that commit — so the commit date is a
    factual "last seen", not a guess.  Returns None if git is unavailable
    (e.g. inside the scraper container without the .git directory).
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", "studios.json"],
            capture_output=True, text=True, check=True, cwd=str(repo_root),
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    stamp = result.stdout.strip()
    return stamp or None


def _is_empty(value) -> bool:
    """True for None / "" / [] / {} but NOT for 0 or False.

    Generic falsiness would treat a legitimate `0` price or `False` flag as
    missing and overwrite it from the previous record.
    """
    return value is None or value == "" or value == [] or value == {}


def _fill_forward(fresh: dict, previous: dict) -> int:
    """Fill fields that are empty in `fresh` from `previous`.  Fresh wins.

    Same "prefer the non-null value" semantics deduper._merge_into already
    uses.  Without this, a re-seen studio whose Maps card came back thinner
    than last week's would silently lose its website, phone, Instagram and
    booking URL — the fields enrich_contacts.py spends a whole pass building.
    """
    filled = 0
    for key, value in previous.items():
        if key in _BOOKKEEPING:
            continue
        if key in fresh and not _is_empty(fresh[key]):
            continue
        if _is_empty(value):
            continue
        fresh[key] = value
        filled += 1
    return filled


def merge_with_previous(
    fresh: list,
    previous: list,
    run_date: str,
    previous_run_date: Optional[str] = None,
    max_missing_runs: int = DEFAULT_MAX_MISSING_RUNS,
) -> tuple[list, dict]:
    """Merge a fresh crawl into the previous dataset, retaining absentees.

    Returns (merged, stats).  Raises RetentionAbort if the crawl returned
    nothing at all while a previous dataset exists — the empty-harvest guard
    questions.json has had since 2026-07-28, now on this path too.

    `fresh` records win on every field they actually populate; `previous`
    supplies anything they left empty.  Records only in `previous` are retained
    with an incremented `missed_runs` until the threshold is reached.
    """
    if not fresh and previous:
        raise RetentionAbort(
            f"crawl returned 0 studios while {len(previous)} exist on disk — "
            f"refusing to overwrite. This is a scraper failure, not an empty "
            f"directory. Investigate the crawl log before re-running."
        )

    # Two previous records can share an identity key — the live dataset has 3
    # such pairs, SweatHouz locations recorded twice under different city labels
    # for one street address (see SlugRegistry.from_studios). A plain
    # dict/setdefault would silently discard the second record here, so it would
    # vanish from `merged` on the very next run with no missed_runs grace and no
    # churn signal. Extras are therefore split out and sent through the absentee
    # path, where they age out over `max_missing_runs` runs like anything else.
    #
    # WHICH of the two becomes canonical is not arbitrary. The slug registry
    # resolves a fresh crawl record for that address to exactly one slug, so the
    # prior carrying THAT id must be the one the fresh record matches. Picking
    # the other (e.g. by file order) makes the re-seen record inherit the fresh
    # record's canonical id while the canonical prior is separately retained
    # under the same id — two records, one id, one of them a duplicate URL.
    # Preferring a prior whose id the crawl actually returned avoids that
    # without retention needing to know about the registry at all.
    fresh_ids = {s.get("id") for s in fresh if s.get("id")}
    prev_by_key: dict = {}
    prev_duplicates: list = []
    for record in previous:
        key = identity_key(record)
        incumbent = prev_by_key.get(key)
        if incumbent is None:
            prev_by_key[key] = record
            continue
        # Both are candidates; the one the crawl returned wins.
        if record.get("id") in fresh_ids and incumbent.get("id") not in fresh_ids:
            prev_by_key[key] = record
            prev_duplicates.append(incumbent)
        else:
            prev_duplicates.append(record)

    merged: list = []
    seen_keys: set = set()
    reseen = new = filled_fields = 0

    # Deterministic order so the output diff is driven by data, not by the
    # order the crawlers happened to return records in.
    for record in sorted(fresh, key=identity_key):
        key = identity_key(record)
        if key in seen_keys:
            # Two fresh records with the same identity: deduper should have
            # collapsed these, but never emit a duplicate id from here.
            log.warning("Duplicate identity in fresh crawl, dropping: %s", key)
            continue
        seen_keys.add(key)

        prior = prev_by_key.get(key)
        if prior is not None:
            filled_fields += _fill_forward(record, prior)
            reseen += 1
        else:
            new += 1

        record["last_seen_at"] = run_date
        record["missed_runs"] = 0
        merged.append(record)

    # ── Absentees ───────────────────────────────────────────────────────────
    # Previous records the crawl did not return: those whose identity was not
    # seen, plus the duplicate-identity extras (which can never be "seen",
    # because the fresh record for that identity matched the canonical record).
    absentees: list = [
        prev_by_key[key] for key in sorted(prev_by_key) if key not in seen_keys
    ]
    absentees.extend(
        sorted(prev_duplicates, key=lambda s: str(s.get("id") or ""))
    )

    retained: list = []
    dropped: list = []
    for original in absentees:
        record = dict(original)

        if _is_empty(record.get("last_seen_at")):
            # Predates this change: it was returned by the crawl behind the
            # previous commit, so that commit's date is its true last sighting.
            record["last_seen_at"] = previous_run_date

        misses = record.get("missed_runs")
        misses = (misses if isinstance(misses, int) and misses >= 0 else 0) + 1
        record["missed_runs"] = misses

        if misses >= max_missing_runs:
            dropped.append(record)
        else:
            retained.append(record)
            merged.append(record)

    # ── Invariant: ids must be unique ───────────────────────────────────────
    # Two records sharing an id means two directory pages competing for one URL,
    # and whichever the Next.js build happens to emit last wins. This is checked
    # rather than assumed because the duplicate-identity handling above is the
    # exact place it can go wrong, and a silently duplicated id is precisely the
    # class of defect this whole change exists to stop shipping.
    id_counts: dict = {}
    for record in merged:
        rid = record.get("id")
        id_counts[rid] = id_counts.get(rid, 0) + 1
    collisions = {rid: n for rid, n in id_counts.items() if n > 1}
    if collisions:
        raise RetentionAbort(
            f"merge produced {len(collisions)} duplicated studio id(s): "
            f"{sorted(collisions)[:5]} — refusing to write. Two records sharing "
            f"an id means two pages competing for one URL. This usually means "
            f"slug_registry.json is out of sync with studios.json; regenerate it."
        )

    # Count every previous RECORD, not every distinct identity, so the numbers
    # reconcile against the file on disk.
    prev_total = len(previous)
    # fresh_ratio is measured against distinct identities, because a duplicate
    # extra can never be re-observed and would otherwise permanently depress the
    # ratio and trip the staleness gate.
    prev_identities = len(prev_by_key)
    stats = {
        "fresh": len(fresh),
        "previous": prev_total,
        "previous_identities": prev_identities,
        "duplicate_identities": len(prev_duplicates),
        "reseen": reseen,
        "new": new,
        "retained": len(retained),
        "dropped": len(dropped),
        "filled_fields": filled_fields,
        "total": len(merged),
        # Share of the previous dataset this crawl actually re-observed. The
        # single best signal that the crawl itself is healthy.
        "fresh_ratio": (reseen / prev_identities) if prev_identities else 1.0,
        "stale": sum(1 for s in merged if (s.get("missed_runs") or 0) > 0),
        "dropped_ids": [s.get("id") for s in dropped],
        "retained_ids": [s.get("id") for s in retained],
        "identity_tiers": _tier_counts(merged),
    }
    return merged, stats


def _tier_counts(studios: list) -> dict:
    counts: dict = {}
    for studio in studios:
        tier = identity_tier(studio)
        counts[tier] = counts.get(tier, 0) + 1
    return counts


def metros_with_no_fresh_records(fresh: list, previous: list) -> list:
    """Metros that had records before and returned none this run.

    The full-run equivalent of the per-metro zero-result warning the --metros
    branch has always emitted.  Retention already protects these records; this
    exists so the run *says* which metros went dark, because a metro-shaped
    hole is the signature of partial rate limiting (the 2026-07-19 losses
    clustered: DFW 7, Philadelphia 7, Los Angeles 6, Chicago 5, Denver 5).
    """
    fresh_metros = {s.get("metro") for s in fresh if s.get("metro")}
    prev_metros = {s.get("metro") for s in previous if s.get("metro")}
    return sorted(prev_metros - fresh_metros)


def read_previous(path: Path) -> list:
    """Read the existing studios.json.  Never raises.

    A corrupt previous file must not abort the run — but it must not silently
    look like "no previous data" either, because that would re-enable the
    wholesale overwrite this module exists to prevent.  Callers get [] and the
    RetentionAbort empty-crawl guard no longer applies, so the caller checks
    `existed` separately.
    """
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.error(
            "Could not parse existing %s (%s). Treating as empty — the "
            "retention guard cannot protect records it cannot read.", path, exc,
        )
        return []
    return data if isinstance(data, list) else []
