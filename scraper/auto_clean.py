#!/usr/bin/env python3
"""Auto-cleaner — runs after scrape, before quality gate.
Purges junk records and merges duplicates automatically.
Called from run_scrape.sh.
"""
import json
import re
import sys
from pathlib import Path

STUDIOS_PATH = Path("/opt/icesoak/studios.json")
LOG_PATH = Path("/opt/icesoak/scraper/auto_clean.log")

from datetime import datetime, timezone
def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

# ── Junk name patterns ────────────────────────────────────────────────────────
# These catch Reddit post titles, listicle articles, forum questions
_JUNK_PATTERNS = [
    # Question/request posts
    r"^(looking for|so hard to find|anyone know|best place|where (can i|to find)|"
    r"recommendations? for|good (gym|saunas?|spots?)|need (a |some )?recommendations?)",
    # Article/listicle titles
    r"^(the \d+ best|top \d+|\d+ best|best saunas? (in|near|around)|"
    r"best (cold plunge|gyms?|spots?|places?))",
    # Geographic non-starters (asking about other cities/countries)
    r"(belfast|london|regina|goodyear|fresno|belfast|belfast|n down|s down|"
    r"eastern suburbs|coral gables florida)",
    # Forum/reddit style
    r"(recos?$|\?$|looking for a |saunas? in [a-z]+ suburbs|"
    r"map of .+ saunas?|bath house that)",
    # Non-wellness recovery centers
    r"(drug|alcohol|rehab|detox|sobriety|community center|centers of america|"
    r"iv therapy|dynamic recovery)",
    # Generic single words
    r"^(sauna|spa|gym|wellness|recovery|cryo|ice bath)$",
]
_JUNK_RE = re.compile("|".join(_JUNK_PATTERNS), re.IGNORECASE)

# Exact name matches to always delete
_JUNK_EXACT = {
    "sauna", "spa", "gym", "sauna club", "recovery cafe",
    "recovery café sodo", "good saunas",
}

def is_junk(name: str) -> bool:
    if not name or len(name.strip()) < 4:
        return True
    n = name.strip()
    if n.lower() in _JUNK_EXACT:
        return True
    if _JUNK_RE.search(n):
        return True
    # Too many words that suggest a question/post (5+ words with no address-like structure)
    words = n.split()
    if len(words) >= 8 and not any(c.isdigit() for c in n):
        return True
    return False

def main():
    log("=== Auto-clean start ===")

    studios = json.loads(STUDIOS_PATH.read_text(encoding="utf-8"))
    before = len(studios)
    log(f"Input: {before} studios")

    # Step 1 — Purge junk
    cleaned = []
    deleted = 0
    for s in studios:
        name = s.get("name", "")
        if is_junk(name):
            log(f"  JUNK: {name} ({s.get('metro')})")
            deleted += 1
        else:
            cleaned.append(s)
    log(f"Deleted {deleted} junk records")

    # Step 2 — Merge duplicates (keep record with most populated fields)
    def field_count(s):
        fields = ["address", "lat", "lng", "phone", "email",
                  "instagram", "website", "booking_url", "modalities"]
        return sum(1 for f in fields if s.get(f))

    seen = {}
    deduped = []
    merged = 0
    for s in cleaned:
        key = f"{s.get('name','').lower().strip()}::{s.get('metro','')}"
        if key in seen:
            kept = seen[key]
            # Merge missing fields from duplicate into kept
            for field in ["address", "lat", "lng", "phone", "email",
                          "instagram", "website", "booking_url",
                          "crawled_phone", "crawled_email", "modalities"]:
                if s.get(field) and not kept.get(field):
                    kept[field] = s[field]
            merged += 1
        else:
            seen[key] = s
            deduped.append(s)

    log(f"Merged {merged} duplicate records")

    # Step 3 — Write back
    STUDIOS_PATH.write_text(
        json.dumps(deduped, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    after = len(deduped)
    log(f"Output: {after} studios (removed {before - after} total)")
    log("=== Auto-clean complete ===")

    # Exit 0 always — gate will validate the result
    return 0

if __name__ == "__main__":
    sys.exit(main())
