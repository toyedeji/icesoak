#!/usr/bin/env bash
# Weekly IceSoak scrape — invoked by n8n (CT 170).
# Builds the image locally, scrapes studios, commits + pushes only if data changed.
set -euo pipefail

IMAGE="localhost/icesoak-scraper:latest"
WORK_DIR="${ICESOAK_WORK_DIR:-/opt/icesoak}"
SCRAPER_DIR="${WORK_DIR}/scraper"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

log "=== IceSoak weekly scrape start ==="

# 1. Pull latest repo state
log "Pulling latest repo..."
cd "${WORK_DIR}"
git pull

# 2. Build image from local Dockerfile (avoids short-name registry resolution)
log "Building scraper image: ${IMAGE}"
podman build --network=host -t "${IMAGE}" "${SCRAPER_DIR}"

# 3. Run scraper — mounts repo root at /work; scrape.py writes studios.json + questions.json there
log "Running scraper..."
podman run --rm \
    --shm-size=1g \
    -v "${WORK_DIR}:/work" \
    -w /work \
    "${IMAGE}" \
    python scraper/scrape.py

log "Scrape complete."

# 4. Quality gate — validate the freshly generated studios.json BEFORE any git
#    commit/push (and therefore before the Netlify deploy). Two checks:
#      CHECK 1: valid-address rate must be >= 60%
#      CHECK 2: studio count must not drop > 40% vs the last successful run
#    On failure: append to quality_gate.log, leave studios.json untouched, exit 1.
STUDIOS_JSON="${WORK_DIR}/studios.json"
COUNT_FILE="${SCRAPER_DIR}/.last_studio_count"
GATE_LOG="${SCRAPER_DIR}/quality_gate.log"
MIN_ADDRESS_RATE=60   # percent — abort below this valid-address rate
MAX_DROP_PCT=40       # percent — abort if count drops more than this vs last run

log "Running quality gate..."

# Extract "TOTAL VALID" from the new studios.json. A valid address is non-null /
# non-empty, contains a digit, is NOT a pure hours/status string, and has either
# a street keyword or a ", City, ST" tail (so real streets like "Broadway" count).
GATE_METRICS="$(python3 - "${STUDIOS_JSON}" <<'PY'
import json, re, sys
try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError
except Exception:
    print("0 0"); sys.exit(0)
total = len(data)
STREET = re.compile(r"(?i)\b(?:st|street|ave|avenue|blvd|boulevard|dr|drive|rd|road|way|ln|lane|"
                    r"pkwy|parkway|pike|hwy|highway|ct|court|pl|place|ter|terrace|cir|circle|"
                    r"ste|suite|unit|trail|trl|loop|sq|square)\b")
HAS_DIGIT  = re.compile(r"\d")
CITY_STATE = re.compile(r",\s*[A-Za-z .]+,\s*[A-Z]{2}\b")
STATUS     = re.compile(r"(?i)\b(?:open|closed|opens|closes|hours|sleeps|temporarily|permanently)\b"
                        r"|\b\d{1,2}(?::\d{2})?\s*[ap]m\b")
def is_valid(a):
    if not a or not a.strip():
        return False
    s = a.strip()
    if not HAS_DIGIT.search(s):
        return False
    if STATUS.search(s) and not CITY_STATE.search(s):   # pure hours/status string
        return False
    return bool(STREET.search(s) or CITY_STATE.search(s))
valid = sum(1 for s in data if is_valid(s.get("address")))
print(total, valid)
PY
)"
read -r TOTAL VALID <<< "${GATE_METRICS}"

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Guard: empty / unreadable studios.json — never push nothing.
if [ -z "${TOTAL:-}" ] || [ "${TOTAL}" -eq 0 ]; then
    echo "[${TS}] QUALITY GATE FAILED: studios.json empty or unreadable (total=0). Push aborted." >> "${GATE_LOG}"
    log "QUALITY GATE FAILED: studios.json empty or unreadable. Push aborted."
    exit 1
fi

RATE=$(( VALID * 100 / TOTAL ))

# Previous count from the last successful run (empty on first run).
PREV=""
if [ -f "${COUNT_FILE}" ]; then
    PREV="$(tr -dc '0-9' < "${COUNT_FILE}")"
fi

GATE_FAILED=0
FAIL_MSG=""

# ── CHECK 1 — valid-address rate >= 60% ─────────────────────────────────────
if [ $(( VALID * 100 )) -lt $(( TOTAL * MIN_ADDRESS_RATE )) ]; then
    GATE_FAILED=1
    FAIL_MSG="QUALITY GATE FAILED: valid address rate ${RATE}% below ${MIN_ADDRESS_RATE}% threshold. Push aborted."
fi

# ── CHECK 2 — studio-count regression vs last run (skipped on first run) ─────
if [ "${GATE_FAILED}" -eq 0 ] && [ -n "${PREV}" ] && [ "${PREV}" -gt 0 ]; then
    # "dropped more than 40%" ⇔ new < (100-40)% of prev ⇔ new*100 < prev*(100-MAX_DROP_PCT)
    if [ $(( TOTAL * 100 )) -lt $(( PREV * (100 - MAX_DROP_PCT) )) ]; then
        DROP=$(( (PREV - TOTAL) * 100 / PREV ))
        GATE_FAILED=1
        FAIL_MSG="QUALITY GATE FAILED: studio count dropped from ${PREV} to ${TOTAL} (${DROP}% drop). Push aborted."
    fi
fi

# ── ABORT ───────────────────────────────────────────────────────────────────
if [ "${GATE_FAILED}" -eq 1 ]; then
    {
        echo "[${TS}] ${FAIL_MSG}"
        echo "    metrics: total=${TOTAL} valid=${VALID} rate=${RATE}% prev=${PREV:-none}"
    } >> "${GATE_LOG}"
    log "${FAIL_MSG}"
    log "studios.json left intact on disk and in git; not committing."
    exit 1
fi

# ── PASS — record the new count and proceed ─────────────────────────────────
echo "${TOTAL}" > "${COUNT_FILE}"
echo "[${TS}] QUALITY GATE PASSED: ${VALID}/${TOTAL} valid addresses (${RATE}%), ${TOTAL} studios (prev: ${PREV:-none})" >> "${GATE_LOG}"
log "QUALITY GATE PASSED: ${VALID}/${TOTAL} valid addresses (${RATE}%), ${TOTAL} studios (prev: ${PREV:-none})"

# 5. Commit and push only if outputs changed
cd "${WORK_DIR}"
git add studios.json questions.json

if git diff --cached --quiet; then
    log "No changes in studios.json / questions.json — nothing to commit."
    log "=== Done (no-op). ==="
    exit 0
fi

log "Data changed — committing..."
git -c user.name="toyedeji" \
    -c user.email="toyedeji@users.noreply.github.com" \
    commit -m "data: weekly studio refresh $(date -u +%Y-%m-%d)"

git push
log "Committed and pushed."

# 6. Ping IndexNow so Bing/Yandex re-crawl promptly (only on real data changes)
bash "${SCRAPER_DIR}/indexnow_ping.sh" \
    "https://icesoak.com/sitemap.xml" \
    "https://icesoak.com/" \
    "https://icesoak.com/cold-plunge/denver" \
    "https://icesoak.com/cold-plunge/dallas-fort-worth" \
    "https://icesoak.com/cold-plunge/philadelphia" \
    || log "IndexNow ping failed (non-fatal)"

log "=== Done. ==="
