#!/usr/bin/env bash
# Nightly IceSoak scrape — invoked by n8n (CT 170).
# Regenerates studios.json and questions.json then commits + pushes.
set -euo pipefail

IMAGE="${ICESOAK_IMAGE:-icesoak-scraper:latest}"
WORK_DIR="${ICESOAK_WORK_DIR:-/opt/icesoak}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

log "Starting IceSoak scrape (image: $IMAGE)"

# The whole repo is mounted at /work; scrape.py now lives in scraper/ and writes
# studios.json + questions.json to the repo root (/work).
podman run --rm \
    --shm-size=1g \
    -v "${WORK_DIR}:/work" \
    -w /work \
    "${IMAGE}" \
    python scraper/scrape.py

log "Scrape complete. Committing results..."

cd "${WORK_DIR}"

# Only commit if outputs actually changed
if git diff --quiet studios.json questions.json 2>/dev/null; then
    log "No changes in outputs — skipping commit."
else
    git add studios.json questions.json
    git commit -m "data: nightly studio refresh $(date -u +%Y-%m-%d)"
    git push
    log "Committed and pushed."
fi

log "Done."
