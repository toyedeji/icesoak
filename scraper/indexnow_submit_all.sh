#!/usr/bin/env bash
# Submit every IceSoak URL to Bing/Yandex via IndexNow in one batch call.
# Called by run_scrape.sh after a successful data push.
# Safe to run standalone: ./scraper/indexnow_submit_all.sh
set -euo pipefail

WORK_DIR="${ICESOAK_WORK_DIR:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo /opt/icesoak)}"
HOST="icesoak.com"
KEY="556dd95d467282715541d2d05a4f9e203b8415c6"
KEY_LOCATION="https://${HOST}/${KEY}.txt"
ENDPOINT="https://api.indexnow.org/indexnow"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [indexnow] $*"; }

log "Generating URL list from ${WORK_DIR}/studios.json and ${WORK_DIR}/data/metros.json …"

PAYLOAD=$(python3 - "${WORK_DIR}" "${HOST}" "${KEY}" "${KEY_LOCATION}" <<'PY'
import json, sys

work_dir, host, key, key_location = sys.argv[1:5]
base = f"https://{host}"
urls = []

# Static pages
urls += [
    f"{base}/",
    f"{base}/cold-plunge-vs-ice-bath/",
    f"{base}/infrared-vs-traditional-sauna/",
    f"{base}/guides/",
]

# Metro pages (8 URL patterns per metro)
metros = json.load(open(f"{work_dir}/data/metros.json"))
for m in metros:
    s = m["slug"]
    urls += [
        f"{base}/cold-plunge/{s}/",
        f"{base}/cold-plunge/{s}/communal/",
        f"{base}/cold-plunge/{s}/day-pass/",
        f"{base}/cold-plunge/{s}/open-late/",
        f"{base}/sauna/{s}/",
        f"{base}/contrast-therapy/{s}/",
        f"{base}/infrared-sauna/{s}/",
        f"{base}/best-cold-plunge-{s}/",
    ]

# Guide pages
for q in json.load(open(f"{work_dir}/questions.json")):
    urls.append(f"{base}/guides/{q['slug']}/")

# Studio pages
for studio in json.load(open(f"{work_dir}/studios.json")):
    urls.append(f"{base}/studio/{studio['id']}/")

payload = {
    "host": host,
    "key": key,
    "keyLocation": key_location,
    "urlList": urls,
}
print(json.dumps(payload))
import sys; print(f"[url_count={len(urls)}]", file=sys.stderr)
PY
)

URL_COUNT=$(echo "${PAYLOAD}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['urlList']))")
log "Submitting ${URL_COUNT} URLs to IndexNow …"

HTTP_STATUS=$(curl -s -o /tmp/indexnow_all_resp.txt -w "%{http_code}" \
    -X POST "${ENDPOINT}" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "${PAYLOAD}")

RESP=$(cat /tmp/indexnow_all_resp.txt 2>/dev/null || echo "")
if [[ "${HTTP_STATUS}" == "200" || "${HTTP_STATUS}" == "202" ]]; then
    log "OK (HTTP ${HTTP_STATUS}): submitted ${URL_COUNT} URLs${RESP:+ — ${RESP}}"
else
    log "WARNING: IndexNow returned HTTP ${HTTP_STATUS}: ${RESP}"
    exit 1
fi
