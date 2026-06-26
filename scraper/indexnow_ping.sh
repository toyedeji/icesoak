#!/usr/bin/env bash
# Ping IndexNow after a successful data push so Bing/Yandex re-crawl promptly.
# Usage: indexnow_ping.sh [url1 url2 ...]
# With no args, pings the sitemap URL only.
set -euo pipefail

HOST="icesoak.com"
KEY="556dd95d467282715541d2d05a4f9e203b8415c6"
KEY_LOCATION="https://${HOST}/${KEY}.txt"
ENDPOINT="https://api.indexnow.org/indexnow"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [indexnow] $*"; }

# Build URL list: accept args or fall back to sitemap
if [[ $# -gt 0 ]]; then
    URL_ARGS=("$@")
else
    URL_ARGS=("https://${HOST}/sitemap.xml")
fi

# Build JSON array of URLs
URL_JSON=$(python3 -c "
import json, sys
urls = sys.argv[1:]
print(json.dumps(urls))
" "${URL_ARGS[@]}")

PAYLOAD=$(python3 -c "
import json
payload = {
    'host': '${HOST}',
    'key': '${KEY}',
    'keyLocation': '${KEY_LOCATION}',
    'urlList': ${URL_JSON},
}
print(json.dumps(payload))
")

log "Pinging IndexNow with ${#URL_ARGS[@]} URL(s)..."
HTTP_STATUS=$(curl -s -o /tmp/indexnow_resp.txt -w "%{http_code}" \
    -X POST "${ENDPOINT}" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "${PAYLOAD}")

RESP=$(cat /tmp/indexnow_resp.txt 2>/dev/null || echo "")
if [[ "${HTTP_STATUS}" == "200" || "${HTTP_STATUS}" == "202" ]]; then
    log "OK (HTTP ${HTTP_STATUS}): ${RESP}"
else
    log "WARNING: IndexNow returned HTTP ${HTTP_STATUS}: ${RESP}"
    # Non-zero exit so callers know it failed, but don't abort the parent script
    exit 1
fi
