#!/usr/bin/env python3
"""IceSoak data quality gate.

Reads a freshly generated studios.json, computes quality metrics, and
enforces thresholds.  Called from run_scrape.sh AFTER scrape + geocode but
BEFORE git add / commit.  The gate never modifies data.

Exit codes:
  0  — PASS or WARN (commit/push may proceed; any warnings are printed)
  2  — ABORT (threshold breached; do NOT commit or push)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── Tunable thresholds ──────────────────────────────────────────────────────

# Abort if the valid-address rate is below this fraction.
ABORT_VALID_ADDR_RATE = 0.60
# Warn (but continue) if the valid-address rate is below this fraction.
WARN_VALID_ADDR_RATE = 0.80
# Warn (but continue) if the geocoded (lat+lng) rate is below this fraction.
WARN_GEO_RATE = 0.50
# Abort if the NET total drops by more than this fraction vs HEAD.
MAX_DROP_FRACTION = 0.40

# Abort if more than this fraction of the PREVIOUS studios are gone, counted
# on disappearances alone and regardless of how many were added.
#
# Why this is separate from MAX_DROP_FRACTION: that check is computed on the net
# total — `drop = (prev_total - total) / prev_total` — so the 2026-07-26 run,
# which removed 23 studios and added 26, evaluated to a *negative* drop and read
# as healthy growth.  46 studios left the dataset across 07-15 → 07-26 (34 with
# no counterpart anywhere) without the gate registering anything.  Net totals
# cannot see substitution; only an id-level set difference can.
#
# With retention in place (processors/retention.py) a studio now needs 3
# consecutive misses to leave, so steady-state churn should sit near zero and 5%
# is a generous ceiling rather than a tight one.  Override with
# ICESOAK_MAX_CHURN_FRACTION for a run whose removals have been reviewed and
# are known to be genuine.
MAX_CHURN_FRACTION = 0.05

# Retention's blind spot: a run where the crawl returns nothing at all now
# yields a file identical to last week's, so both the total and the churn look
# perfect.  The share of records carrying missed_runs > 0 is what exposes that.
WARN_STALE_FRACTION = 0.25
ABORT_STALE_FRACTION = 0.50

# Abort if ANY launch metro has fewer than this many studios.
MIN_STUDIOS_PER_METRO = 3

# The three launch metros that must all meet MIN_STUDIOS_PER_METRO.
LAUNCH_METROS = {
    "denver_co",
    "dallas_fort_worth_tx",
    "philadelphia_pa",
}

# Human-readable metro labels for log output.
_METRO_LABEL = {
    "denver_co":            "Denver",
    "dallas_fort_worth_tx": "DFW",
    "philadelphia_pa":      "Philadelphia",
}

# ── Address classifiers ──────────────────────────────────────────────────────
#
# These are ported verbatim from the inline bash gate that run_scrape.sh used to
# carry (lines 63-98 of the old script), so that consolidating onto this module
# does not change the pass/fail verdict.  Measured against the live 232-record
# studios.json the two implementations agreed on 231 records; the one
# disagreement was "12401 SW 134th Ct", a real street with no comma or state,
# which the bash version accepted and this module's older regex rejected.  The
# bash behaviour is the more correct of the two, so it wins.

_STREET_RE = re.compile(
    r"(?i)\b(?:st|street|ave|avenue|blvd|boulevard|dr|drive|rd|road|way|ln|lane|"
    r"pkwy|parkway|pike|hwy|highway|ct|court|pl|place|ter|terrace|cir|circle|"
    r"ste|suite|unit|trail|trl|loop|sq|square)\b"
)
_HAS_DIGIT_RE = re.compile(r"\d")
_CITY_STATE_RE = re.compile(r",\s*[A-Za-z .]+,\s*[A-Z]{2}\b")

# Business-hours / open-closed noise that the Maps card sometimes yields where
# an address should be.
_STATUS_RE = re.compile(
    r"(?i)\b(?:open|closed|opens|closes|hours|sleeps|temporarily|permanently)\b"
    r"|\b\d{1,2}(?::\d{2})?\s*[ap]m\b"
)


def _is_valid_address(addr: Optional[str]) -> bool:
    if not addr or not addr.strip():
        return False
    s = addr.strip()
    if not _HAS_DIGIT_RE.search(s):
        return False
    # A pure hours/status string. If it also carries a ", City, ST" tail it is a
    # real address that merely mentions one of these words (e.g. "Open Way").
    if _STATUS_RE.search(s) and not _CITY_STATE_RE.search(s):
        return False
    return bool(_STREET_RE.search(s) or _CITY_STATE_RE.search(s))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _metro_label(metro_id: str) -> str:
    return _METRO_LABEL.get(metro_id, metro_id)


def _max_churn_fraction_from_env(
    default: float = MAX_CHURN_FRACTION,
) -> float:
    """Read ICESOAK_MAX_CHURN_FRACTION, falling back to the module default.

    An operator who has reviewed a run's removals and confirmed they are genuine
    closures can raise this for that one run, rather than editing the threshold
    and leaving it raised.
    """
    raw = os.environ.get("ICESOAK_MAX_CHURN_FRACTION")
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        print(
            f"[quality-gate] WARN: ICESOAK_MAX_CHURN_FRACTION={raw!r} is not a "
            f"number — using {default:.0%}"
        )
        return default
    if not 0.0 <= value <= 1.0:
        print(
            f"[quality-gate] WARN: ICESOAK_MAX_CHURN_FRACTION={value} out of "
            f"range [0,1] — using {default:.0%}"
        )
        return default
    return value


def _load_head_studios(repo_root: Path) -> Optional[list]:
    """Return the list of studios from the last commit, or None on failure."""
    try:
        result = subprocess.run(
            ["git", "show", "HEAD:studios.json"],
            capture_output=True, text=True, check=True,
            cwd=str(repo_root),
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
        return None


# ── Redirect-shadow check ────────────────────────────────────────────────────
#
# A redirect and a live page can both claim the same URL. When the redirect is
# forced it wins, and the page becomes permanently unreachable while looking
# entirely intentional — a 301 to a plausible city page is indistinguishable
# from a deliberate consolidation. netlify.toml carries 49 /studio/ rules for
# slugs that a healthy crawl is expected to re-discover (27 of the 33 "genuine
# removals" were Maps-sourced records with no website, the transient-miss
# profile), so this collision is not hypothetical; it is scheduled.
#
# Runs on every refresh and ABORTS, on the same reasoning as the churn gate:
# a check nobody reads is not a check.

_REDIRECT_BLOCK_RE = re.compile(r"\[\[redirects\]\]")
_FROM_RE = re.compile(r'from\s*=\s*"([^"]+)"')
_TO_RE = re.compile(r'to\s*=\s*"([^"]+)"')
_FORCE_RE = re.compile(r"force\s*=\s*(true|false)", re.IGNORECASE)
_STUDIO_PATH_RE = re.compile(r"^/studio/([^/]+)/?$")

# Vertical landing pages a removal redirect may legitimately target.
_VERTICAL_PREFIXES = ("/cold-plunge/", "/sauna/", "/infrared-sauna/", "/contrast-therapy/")


def _studio_slug(path: str) -> Optional[str]:
    m = _STUDIO_PATH_RE.match(path.strip())
    return m.group(1) if m else None


def parse_redirects(toml_text: str) -> list:
    """Extract [[redirects]] rules as {from, to, force}.

    A deliberately small hand parser: netlify.toml is the only input, its shape
    is stable, and adding a TOML dependency to the scraper image to read four
    keys is not worth it. Unparseable blocks are returned with None fields so
    the caller can warn rather than silently skip them.
    """
    rules = []
    for block in _REDIRECT_BLOCK_RE.split(toml_text)[1:]:
        # Stop at the next top-level table so a following [[headers]] block's
        # keys cannot leak into this rule.
        cut = block.find("[[")
        if cut != -1:
            block = block[:cut]
        f = _FROM_RE.search(block)
        t = _TO_RE.search(block)
        fo = _FORCE_RE.search(block)
        rules.append({
            "from": f.group(1) if f else None,
            "to": t.group(1) if t else None,
            "force": (fo.group(1).lower() == "true") if fo else False,
        })
    return rules


def check_redirect_shadows(studios: list, toml_text: str) -> dict:
    """Return {"aborts", "warns", "report", "metrics"} for netlify.toml vs data.

    Two hard invariants:

      1. No FORCED redirect may point away from a live studio record. That page
         exists and would be unreachable.
      2. No /studio/ redirect target may be absent from the data — a 301 into a
         404 is worse than the 404 it was meant to prevent, because it launders
         the failure through a step that looks deliberate.
    """
    aborts: list = []
    warns: list = []
    report: list = []

    live_ids = {s.get("id") for s in studios if s.get("id")}
    rules = parse_redirects(toml_text)

    malformed = [r for r in rules if not r["from"] or not r["to"]]
    studio_rules = [r for r in rules if r["from"] and _studio_slug(r["from"])]

    shadowed: list = []
    dormant: list = []
    for rule in studio_rules:
        slug = _studio_slug(rule["from"])
        if slug not in live_ids:
            continue
        if rule["force"]:
            shadowed.append(rule)
        else:
            # Correct and intended: pre-staged for a record that will age out.
            dormant.append(rule)

    broken_targets = [
        rule for rule in rules
        if rule["to"] and _studio_slug(rule["to"])
        and _studio_slug(rule["to"]) not in live_ids
    ]

    odd_targets = [
        rule for rule in studio_rules
        if rule["to"]
        and not _studio_slug(rule["to"])
        and not rule["to"].startswith(_VERTICAL_PREFIXES)
        and not rule["to"].startswith("http")
    ]

    report.append(
        f"redirects: {len(rules)} rules ({len(studio_rules)} /studio/), "
        f"{len(dormant)} dormant-over-live-page, {len(shadowed)} shadowing, "
        f"{len(broken_targets)} broken target(s)"
    )

    if shadowed:
        detail = "; ".join(f"{r['from']} -> {r['to']}" for r in shadowed[:6])
        aborts.append(
            f"{len(shadowed)} FORCED redirect(s) shadow a live studio page — "
            f"those pages are unreachable: {detail}. Set force = false (the "
            f"page then wins and the rule lies dormant), or delete the rule. "
            f"See the comment block above the studio section in netlify.toml."
        )

    if broken_targets:
        detail = "; ".join(f"{r['from']} -> {r['to']}" for r in broken_targets[:6])
        aborts.append(
            f"{len(broken_targets)} redirect(s) point at a /studio/ page that is "
            f"not in studios.json, so they 301 into a 404: {detail}. Re-point at "
            f"a live record or at the parent city page for its modality."
        )

    if malformed:
        warns.append(
            f"{len(malformed)} [[redirects]] block(s) missing from/to — not checked"
        )
    if odd_targets:
        detail = "; ".join(f"{r['from']} -> {r['to']}" for r in odd_targets[:4])
        warns.append(
            f"{len(odd_targets)} /studio/ redirect(s) target an unrecognised path "
            f"shape (expected a /studio/ page or a vertical landing page): {detail}"
        )
    if dormant:
        report.append(
            f"  {len(dormant)} unforced rule(s) sit over a live page and are "
            f"correctly dormant (pre-staged de-duplication)"
        )

    return {
        "aborts": aborts,
        "warns": warns,
        "report": report,
        "metrics": {
            "rules": len(rules),
            "studio_rules": len(studio_rules),
            "shadowed": len(shadowed),
            "dormant": len(dormant),
            "broken_targets": len(broken_targets),
        },
    }


# ── Evaluation (pure) ────────────────────────────────────────────────────────

def evaluate(
    studios: list,
    prev_studios: Optional[list] = None,
    max_churn_fraction: Optional[float] = None,
) -> dict:
    """Compute metrics and threshold verdicts. No IO, no exit — testable.

    Returns {"aborts": [...], "warns": [...], "metrics": {...}, "report": [...]}.
    `prev_studios` is None when HEAD:studios.json could not be read; the
    regression and churn checks are then skipped (and warned about) rather than
    silently passing.
    """
    if max_churn_fraction is None:
        max_churn_fraction = _max_churn_fraction_from_env()

    aborts: list = []
    warns: list = []
    report: list = []
    total = len(studios)

    if total == 0:
        return {
            "aborts": ["studios.json is empty"],
            "warns": [],
            "metrics": {"total": 0},
            "report": [],
        }

    valid_addr = sum(1 for s in studios if _is_valid_address(s.get("address")))
    geocoded = sum(
        1 for s in studios
        if s.get("lat") is not None and s.get("lng") is not None
    )
    valid_rate = valid_addr / total
    geo_rate = geocoded / total

    metro_counts: dict = {}
    for s in studios:
        m = s.get("metro") or "unknown"
        metro_counts[m] = metro_counts.get(m, 0) + 1

    # Retention bookkeeping (processors/retention.py). Absent on a pre-retention
    # file, in which case every record reads as freshly seen.
    stale = sum(1 for s in studios if (s.get("missed_runs") or 0) > 0)
    stale_rate = stale / total

    metrics = {
        "total": total,
        "valid_addr": valid_addr,
        "valid_rate": valid_rate,
        "geocoded": geocoded,
        "geo_rate": geo_rate,
        "metro_counts": metro_counts,
        "stale": stale,
        "stale_rate": stale_rate,
        "prev_total": None,
        "dropped": None,
        "added": None,
        "churn": None,
        "net_change": None,
    }

    metro_parts = ", ".join(
        f"{_metro_label(m)}={metro_counts.get(m, 0)}" for m in sorted(LAUNCH_METROS)
    )
    report.append(
        f"SUMMARY  total={total}"
        f"  valid-addr={valid_addr}/{total} ({valid_rate:.0%})"
        f"  geocoded={geocoded}/{total} ({geo_rate:.0%})"
        f"  stale={stale}/{total} ({stale_rate:.0%})"
        f"  metros: {metro_parts}"
    )
    for m in sorted(LAUNCH_METROS):
        count = metro_counts.get(m, 0)
        flag = "  ok" if count >= MIN_STUDIOS_PER_METRO else "  *** BELOW FLOOR ***"
        report.append(f"  {_metro_label(m):<15} {count} studios{flag}")

    # ── Hard abort: valid-address rate ──────────────────────────────────────
    if valid_rate < ABORT_VALID_ADDR_RATE:
        aborts.append(
            f"valid-address rate {valid_rate:.1%} < abort threshold "
            f"{ABORT_VALID_ADDR_RATE:.0%}"
        )

    # ── Comparison vs the previous dataset ──────────────────────────────────
    if prev_studios is None:
        warns.append("regression + churn checks skipped (HEAD:studios.json unreadable)")
    else:
        prev_total = len(prev_studios)
        metrics["prev_total"] = prev_total
        if prev_total > 0:
            prev_ids = {s.get("id") for s in prev_studios if s.get("id")}
            new_ids = {s.get("id") for s in studios if s.get("id")}
            disappeared = prev_ids - new_ids
            appeared = new_ids - prev_ids
            churn = len(disappeared) / len(prev_ids) if prev_ids else 0.0
            net_change = total - prev_total

            metrics.update({
                "dropped": len(disappeared),
                "added": len(appeared),
                "churn": churn,
                "net_change": net_change,
            })

            sign = "+" if net_change >= 0 else ""
            report.append(
                f"  vs HEAD: {prev_total} -> {total} ({sign}{net_change})"
                f"  |  dropped={len(disappeared)} added={len(appeared)}"
                f" churn={churn:.1%}"
            )

            # ── CHURN — the check the net-total drop check cannot make ───────
            # Computed on disappearances alone. The 2026-07-26 run removed 23
            # ids and added 26, so the net drop was negative and the old check
            # reported healthy growth while a tenth of the directory silently
            # turned over.
            if churn > max_churn_fraction:
                sample = ", ".join(sorted(disappeared)[:8])
                more = f" (+{len(disappeared) - 8} more)" if len(disappeared) > 8 else ""
                aborts.append(
                    f"{len(disappeared)} of {prev_total} studios disappeared "
                    f"({churn:.1%} churn), exceeds max-churn threshold "
                    f"{max_churn_fraction:.0%} — net change was {sign}{net_change}, "
                    f"which is why the count check alone did not catch this. "
                    f"Dropped ids: {sample}{more}"
                )

            # ── Net-total collapse (retained; catches a different shape) ─────
            drop = (prev_total - total) / prev_total
            if drop > MAX_DROP_FRACTION:
                aborts.append(
                    f"studio count dropped {drop:.0%} ({prev_total} -> {total})"
                    f", exceeds max-drop threshold {MAX_DROP_FRACTION:.0%}"
                )

    # ── Staleness — retention's blind spot ──────────────────────────────────
    # With retention active a completely dead crawl reproduces last week's file
    # exactly: total unchanged, churn zero, every threshold green. The share of
    # records the crawl did NOT re-observe is the only signal that shows it.
    if stale_rate >= ABORT_STALE_FRACTION:
        aborts.append(
            f"{stale}/{total} studios ({stale_rate:.0%}) were not re-observed by "
            f"this crawl, at or above {ABORT_STALE_FRACTION:.0%} — the crawl "
            f"itself is failing, even though the record count looks healthy"
        )
    elif stale_rate >= WARN_STALE_FRACTION:
        warns.append(
            f"{stale}/{total} studios ({stale_rate:.0%}) were not re-observed by "
            f"this crawl (warn threshold {WARN_STALE_FRACTION:.0%})"
        )

    # ── Metro floor ─────────────────────────────────────────────────────────
    # Hard abort ONLY if ALL launch metros collapse below the indexing floor.
    # A single weak metro is a WARN: it makes that one directory noindex and
    # must not block the deploy for the healthy metros.
    failing_metros = [
        m for m in LAUNCH_METROS if metro_counts.get(m, 0) < MIN_STUDIOS_PER_METRO
    ]
    if failing_metros:
        detail = ", ".join(
            f"{_metro_label(m)}={metro_counts.get(m, 0)}"
            for m in sorted(failing_metros)
        )
        if len(failing_metros) == len(LAUNCH_METROS):
            aborts.append(
                f"ALL launch metros below {MIN_STUDIOS_PER_METRO}-studio floor: {detail}"
            )
        else:
            warns.append(
                f"metro(s) below {MIN_STUDIOS_PER_METRO}-studio floor "
                f"(will be noindex): {detail}"
            )

    # ── Soft warns ──────────────────────────────────────────────────────────
    if not aborts and ABORT_VALID_ADDR_RATE <= valid_rate < WARN_VALID_ADDR_RATE:
        warns.append(
            f"valid-address rate {valid_rate:.1%} is between warn "
            f"({WARN_VALID_ADDR_RATE:.0%}) and abort ({ABORT_VALID_ADDR_RATE:.0%})"
        )
    if geo_rate < WARN_GEO_RATE:
        warns.append(f"geocoded rate {geo_rate:.1%} < warn threshold {WARN_GEO_RATE:.0%}")

    return {"aborts": aborts, "warns": warns, "metrics": metrics, "report": report}


# ── Main ─────────────────────────────────────────────────────────────────────

def run(studios_path: Path) -> None:
    try:
        studios = json.loads(studios_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[quality-gate] ABORT: cannot read {studios_path}: {exc}")
        sys.exit(2)

    if not isinstance(studios, list):
        print(f"[quality-gate] ABORT: {studios_path} is not a JSON array")
        sys.exit(2)

    result = evaluate(studios, _load_head_studios(studios_path.parent))

    # ── Redirect shadowing — runs on EVERY refresh, blocks rather than warns ──
    # netlify.toml sits beside studios.json at the repo root.
    toml_path = studios_path.parent / "netlify.toml"
    if toml_path.exists():
        try:
            redirect_result = check_redirect_shadows(
                studios, toml_path.read_text(encoding="utf-8")
            )
        except OSError as exc:
            result["warns"].append(f"could not read {toml_path}: {exc}")
        else:
            result["report"].extend(redirect_result["report"])
            result["warns"].extend(redirect_result["warns"])
            result["aborts"].extend(redirect_result["aborts"])
    else:
        # Not a warn. A missing netlify.toml means the check silently stops
        # running, which is how the original bug survived.
        result["aborts"].append(
            f"netlify.toml not found at {toml_path} — the redirect-shadow check "
            f"cannot run, and an unverified redirect set can make live studio "
            f"pages unreachable. Refusing to pass."
        )

    for line in result["report"]:
        print(f"[quality-gate] {line}")
    for w in result["warns"]:
        print(f"[quality-gate] WARN: {w}")

    if result["aborts"]:
        for reason in result["aborts"]:
            print(f"[quality-gate] ABORT: {reason}")
        print(
            "[quality-gate] Push blocked. Inspect studios.json, fix the scraper, "
            "and re-run. The file is left on disk for diagnosis."
        )
        sys.exit(2)

    if result["warns"]:
        print("[quality-gate] PASS (with warnings) — commit/push will proceed")
    else:
        print("[quality-gate] PASS")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: quality_gate.py <path/to/studios.json>", file=sys.stderr)
        sys.exit(1)
    run(Path(sys.argv[1]))

# ── Studio name validator ─────────────────────────────────────────────────────
# Patterns that indicate a scraper-noise name rather than a real business.
_NAME_JUNK_RE = re.compile(
    r"(?i)"
    r"^(how|what|why|when|where|who|which|the best|best|top \d|tips|key |"
    r"incorporating|a powerful|the science|benefits of|the benefits|"
    r"how often|recovery studio #\d|infrared sauna therapy$|"
    r"contrast therapy$|cryotherapy$|sauna therapy$|"
    r"cold plunge spots$|gym with|massage &|sauna in [a-z]+$|"
    r"location with|sauna recommendation|icepass cold plunge)"
)

# A real business name must have at least 2 words and not be a question/listicle.
_NAME_QUESTION_RE = re.compile(r"\?$")

def is_valid_studio_name(name: str) -> bool:
    """Return True if name looks like a real business, False if it's scraper noise."""
    if not name or not name.strip():
        return False
    name = name.strip()
    # Must have at least 2 characters
    if len(name) < 4:
        return False
    # Reject question titles
    if _NAME_QUESTION_RE.search(name):
        return False
    # Reject known junk patterns
    if _NAME_JUNK_RE.search(name):
        return False
    # Must contain at least one letter
    if not re.search(r'[A-Za-z]', name):
        return False
    return True

def validate_incoming_studios(new_studios: list, existing_studios: list) -> tuple[list, list]:
    """Filter new studios before merging into the main dataset.
    
    Returns (accepted, rejected) lists.
    Rejects:
      - Junk names (article titles, generic modality names)
      - Duplicates of existing studios (same name + metro)
      - Studios missing both city and state
    """
    existing_keys = {
        f"{s.get('name','').lower().strip()}::{s.get('metro','')}"
        for s in existing_studios
    }
    
    accepted = []
    rejected = []
    
    for s in new_studios:
        name = s.get('name', '').strip()
        metro = s.get('metro', '')
        
        # Name validation
        if not is_valid_studio_name(name):
            rejected.append({'studio': s, 'reason': f'junk_name: {name}'})
            continue
        
        # Duplicate check
        key = f"{name.lower()}::{metro}"
        if key in existing_keys:
            rejected.append({'studio': s, 'reason': 'duplicate'})
            continue
        
        # Must have city or address
        if not s.get('city') and not s.get('address'):
            rejected.append({'studio': s, 'reason': 'no_location'})
            continue
        
        existing_keys.add(key)
        accepted.append(s)
    
    return accepted, rejected
