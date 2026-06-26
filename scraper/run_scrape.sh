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

# 4. Commit and push only if outputs changed
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
log "=== Done. ==="
