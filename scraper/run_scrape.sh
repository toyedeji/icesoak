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

# 3b. Auto-clean — purge junk records and merge duplicates before quality gate
log "Running auto-cleaner..."
python3 "${SCRAPER_DIR}/auto_clean.py" || log "Auto-cleaner failed (non-fatal)"
log "Auto-clean complete."

# 4. Quality gate — validate the freshly generated studios.json BEFORE any git
#    commit/push (and therefore before the Netlify deploy).
#
#    This now DELEGATES to scraper/processors/quality_gate.py instead of
#    reimplementing the thresholds inline.
#
#    Why that matters: this script used to carry its own ~120-line bash copy of
#    the gate and never called quality_gate.py at all — the module's only
#    consumer was merger.py importing is_valid_studio_name() from it. Two gates
#    existed, only one ran, and the one that ran was the one nobody edited. That
#    is the same defect shape as the studios.json write path itself: a guard
#    living on a branch the scheduled run never takes. Editing
#    MAX_DROP_FRACTION in the module would have had zero production effect.
#
#    ABORT checks (exit 2 -> no push):
#      - valid-address rate < 60%
#      - CHURN > 5% of the previous studios disappeared, computed on
#        disappearances alone regardless of additions. The net-total check below
#        cannot see substitution: the 2026-07-26 run removed 23 and added 26, a
#        NET GAIN, and passed. Replayed against real history the churn check
#        aborts both the 07-19 (18.8%) and 07-26 (10.0%) runs.
#      - net total dropped > 40% vs HEAD
#      - >= 50% of records not re-observed by this crawl (retention's blind
#        spot: a dead crawl reproduces last week's file with a perfect total and
#        zero churn)
#      - ALL three launch metros below the 3-studio floor
#    WARN checks (logged, push proceeds):
#      - geocoded rate < 50%; address rate 60-80%; >= 25% not re-observed;
#        a single launch metro below the floor (that page goes noindex)
#
#    The address validator inside quality_gate.py was ported verbatim from the
#    bash version it replaces, so the verdict does not shift: both score the
#    live 232-record dataset at 225 valid (97%).
STUDIOS_JSON="${WORK_DIR}/studios.json"
COUNT_FILE="${SCRAPER_DIR}/.last_studio_count"
GATE_LOG="${SCRAPER_DIR}/quality_gate.log"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

log "Running quality gate..."

# `set -e` would kill the script before the log is written, so capture the code.
GATE_OUTPUT="$(python3 "${SCRAPER_DIR}/processors/quality_gate.py" "${STUDIOS_JSON}" 2>&1)" && GATE_RC=0 || GATE_RC=$?

echo "${GATE_OUTPUT}"
{
    echo "[${TS}] quality gate rc=${GATE_RC}"
    echo "${GATE_OUTPUT}" | sed 's/^/    /'
} >> "${GATE_LOG}"

if [ "${GATE_RC}" -ne 0 ]; then
    log "QUALITY GATE FAILED (rc=${GATE_RC}). studios.json left intact on disk; not committing."
    log "To accept a run whose removals have been reviewed and are genuine:"
    log "  ICESOAK_MAX_CHURN_FRACTION=0.25 bash ${SCRAPER_DIR}/run_scrape.sh"
    exit 1
fi

# Record the count for operator reference. No longer load-bearing: the gate reads
# HEAD:studios.json directly, which lets it diff ID SETS rather than just counts.
TOTAL="$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))))" "${STUDIOS_JSON}")"
echo "${TOTAL}" > "${COUNT_FILE}"
log "QUALITY GATE PASSED: ${TOTAL} studios."

# 5. Commit and push only if outputs changed
cd "${WORK_DIR}"
# slug_registry.json pins each studio's live URL to its identity. If it is
# not committed the registry resets every run and slug churn silently
# returns — see processors/identity.py.
git add studios.json questions.json slug_registry.json

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

# 6. Submit all URLs to IndexNow so Bing/Yandex re-crawl promptly (only on real data changes)
ICESOAK_WORK_DIR="${WORK_DIR}" bash "${SCRAPER_DIR}/indexnow_submit_all.sh" \
    || log "IndexNow submission failed (non-fatal)"

log "=== Done. ==="
