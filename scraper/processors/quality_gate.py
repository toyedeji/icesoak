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
# Abort if total studio count drops by more than this fraction vs HEAD.
MAX_DROP_FRACTION = 0.40
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

# Patterns that indicate a scraper-noise "address" (business hours, occupancy
# info, status text) rather than a real street address.
_JUNK_RE = re.compile(
    r"(?i)"
    r"\bopen\b|\bclosed?\b|\bhours\b|\bsleeps\b"
    r"|\bam\b|\bpm\b"
    r"|\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b"
    r"|\bfriday\b|\bsaturday\b|\bsunday\b"
    r"|\d{1,2}:\d{2}"           # time like "9:00" or "10:30"
    r"|\bpermanently\b|\btemporarily\b"
    r"|\bcloses\s+soon\b"
)

# A real US street address must have: a digit, then eventually a comma,
# then eventually a two-letter state abbreviation.
_VALID_RE = re.compile(r"\d.*,.*\b[A-Z]{2}\b", re.DOTALL)


def _is_valid_address(addr: Optional[str]) -> bool:
    if not addr:
        return False
    if _JUNK_RE.search(addr):
        return False
    return bool(_VALID_RE.search(addr))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _metro_label(metro_id: str) -> str:
    return _METRO_LABEL.get(metro_id, metro_id)


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


# ── Main ─────────────────────────────────────────────────────────────────────

def run(studios_path: Path) -> None:
    studios = json.loads(studios_path.read_text(encoding="utf-8"))
    total = len(studios)

    if total == 0:
        print("[quality-gate] ABORT: studios.json is empty")
        sys.exit(2)

    # Core metrics
    valid_addr = sum(1 for s in studios if _is_valid_address(s.get("address")))
    geocoded   = sum(1 for s in studios if s.get("lat") is not None and s.get("lng") is not None)
    valid_rate = valid_addr / total
    geo_rate   = geocoded / total

    metro_counts: dict = {}
    for s in studios:
        m = s.get("metro") or "unknown"
        metro_counts[m] = metro_counts.get(m, 0) + 1

    # One-line summary — always printed so every weekly run is auditable
    metro_parts = ", ".join(
        f"{_metro_label(m)}={metro_counts.get(m, 0)}"
        for m in sorted(LAUNCH_METROS)
    )
    print(
        f"[quality-gate] SUMMARY  total={total}"
        f"  valid-addr={valid_addr}/{total} ({valid_rate:.0%})"
        f"  geocoded={geocoded}/{total} ({geo_rate:.0%})"
        f"  metros: {metro_parts}"
    )

    # Per-metro detail for the three launch metros
    for m in sorted(LAUNCH_METROS):
        count = metro_counts.get(m, 0)
        flag = "  ✓" if count >= MIN_STUDIOS_PER_METRO else "  ✗ BELOW FLOOR"
        print(f"[quality-gate]   {_metro_label(m):<15} {count} studios{flag}")

    aborts: list = []
    warns:  list = []

    # ── Hard abort: valid-address rate ──────────────────────────────────────
    if valid_rate < ABORT_VALID_ADDR_RATE:
        aborts.append(
            f"valid-address rate {valid_rate:.1%} < abort threshold {ABORT_VALID_ADDR_RATE:.0%}"
        )

    # ── Hard abort: catastrophic regression vs HEAD ──────────────────────────
    prev_studios = _load_head_studios(studios_path.parent)
    if prev_studios is None:
        print("[quality-gate] WARN: cannot read HEAD:studios.json — regression check skipped")
        warns.append("regression check skipped (HEAD:studios.json unreadable)")
    else:
        prev_total = len(prev_studios)
        if prev_total > 0:
            drop = (prev_total - total) / prev_total
            if drop > MAX_DROP_FRACTION:
                aborts.append(
                    f"studio count dropped {drop:.0%} ({prev_total} → {total})"
                    f", exceeds max-drop threshold {MAX_DROP_FRACTION:.0%}"
                )
            else:
                change = total - prev_total
                sign = "+" if change >= 0 else ""
                print(f"[quality-gate]   vs HEAD: {prev_total} → {total} ({sign}{change})")

    # ── Metro floor ──────────────────────────────────────────────────────────
    # Hard abort ONLY if ALL launch metros collapse below the indexing floor
    # (a total wipeout — the site would have no indexable directory pages).
    # A single weak metro is a WARN: it just makes that one directory noindex,
    # and must not block the deploy for the healthy metros.
    failing_metros = [m for m in LAUNCH_METROS if metro_counts.get(m, 0) < MIN_STUDIOS_PER_METRO]
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
                f"metro(s) below {MIN_STUDIOS_PER_METRO}-studio floor (will be noindex): {detail}"
            )

    # ── Soft warn: address rate in the grey zone ─────────────────────────────
    if not aborts and ABORT_VALID_ADDR_RATE <= valid_rate < WARN_VALID_ADDR_RATE:
        warns.append(
            f"valid-address rate {valid_rate:.1%} is between warn ({WARN_VALID_ADDR_RATE:.0%})"
            f" and abort ({ABORT_VALID_ADDR_RATE:.0%}) thresholds"
        )

    # ── Soft warn: geocoded rate ─────────────────────────────────────────────
    if geo_rate < WARN_GEO_RATE:
        warns.append(
            f"geocoded rate {geo_rate:.1%} < warn threshold {WARN_GEO_RATE:.0%}"
        )

    # ── Emit warns ───────────────────────────────────────────────────────────
    for w in warns:
        print(f"[quality-gate] WARN: {w}")

    # ── Emit aborts and exit ─────────────────────────────────────────────────
    if aborts:
        for reason in aborts:
            print(f"[quality-gate] ABORT: {reason}")
        print(
            "[quality-gate] Push blocked. Inspect studios.json, fix the scraper, "
            "and re-run. The file is left on disk for diagnosis."
        )
        sys.exit(2)

    if warns:
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
    r"contrast therapy$|cryotherapy$|sauna therapy$)"
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
