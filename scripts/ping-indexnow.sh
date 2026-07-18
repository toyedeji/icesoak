#!/bin/bash
# IceSoak IndexNow ping — handles sitemap index + child sitemaps
KEY=556dd95d467282715541d2d05a4f9e203b8415c6
HOST=icesoak.com
SITEMAP=https://icesoak.com/sitemap_index.xml
LOG=/var/log/icesoak-indexnow.log
TS=$(date -Iseconds)

fetch_urls() {
  local sm="$1"
  local body
  body=$(curl -sSL "$sm") || return
  # If sitemap index, recurse into each child sitemap
  if grep -q "<sitemapindex" <<< "$body"; then
    while IFS= read -r child; do
      [ -n "$child" ] && fetch_urls "$child"
    done < <(grep -oE "<loc>[^<]+</loc>" <<< "$body" | sed -E "s|</?loc>||g")
  else
    grep -oE "<loc>[^<]+</loc>" <<< "$body" | sed -E "s|</?loc>||g"
  fi
}

URLS=$(fetch_urls "$SITEMAP" | awk "NF" | head -10000)
COUNT=$(printf "%s" "$URLS" | grep -c .)
if [ "$COUNT" -eq 0 ]; then
  echo "[$TS] ERROR: no URLs from $SITEMAP" | tee -a $LOG
  exit 1
fi

JSON=$(printf "%s" "$URLS" | python3 -c "import json,sys; urls=[l.strip() for l in sys.stdin if l.strip()]; print(json.dumps({\"host\":\"$HOST\",\"key\":\"$KEY\",\"urlList\":urls}))")

RESPONSE=$(curl -sS -o /tmp/indexnow-resp.txt -w "%{http_code}" -X POST \
  "https://api.indexnow.org/IndexNow" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$JSON")

echo "[$TS] IceSoak IndexNow: submitted $COUNT urls, http=$RESPONSE, body=$(cat /tmp/indexnow-resp.txt | head -c 200)" | tee -a $LOG
