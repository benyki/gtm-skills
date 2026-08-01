#!/usr/bin/env bash
# fetch_bg.sh "search query" out.jpg [cache_dir]
# High-res portrait image from Pexels. If cache_dir holds <slug>.jpg for this query
# it is reused (no API call); otherwise it's fetched and saved there for reuse.
# Needs PEXELS_API_KEY (source .env.local first) only on a cache miss.
set -euo pipefail
QUERY="${1:?usage: fetch_bg.sh \"query\" out.jpg [cache_dir]}"
OUT="${2:?usage: fetch_bg.sh \"query\" out.jpg [cache_dir]}"
CACHE="${3:-}"

slug=$(printf '%s' "$QUERY" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-*//;s/-*$//')

if [ -n "$CACHE" ] && [ -f "$CACHE/$slug.jpg" ]; then
  cp "$CACHE/$slug.jpg" "$OUT"
  echo "bg (reused cache) -> $OUT  [$slug.jpg]"
  exit 0
fi

: "${PEXELS_API_KEY:?Load it: set -a; . .env.local; set +a}"
q=$(printf '%s' "$QUERY" | jq -sRr @uri)
resp=$(curl -sS "https://api.pexels.com/v1/search?query=${q}&orientation=portrait&per_page=15&size=large" -H "Authorization: $PEXELS_API_KEY")
url=$(echo "$resp" | jq -r '.photos[0].src.original')
[ "$url" = "null" ] && { echo "no Pexels results for: $QUERY"; exit 1; }
curl -sS "${url}?auto=compress&cs=tinysrgb&fit=crop&w=1620&h=2880" -o "$OUT"

if [ -n "$CACHE" ]; then
  mkdir -p "$CACHE"
  cp "$OUT" "$CACHE/$slug.jpg"
  echo "$resp" | jq -r '"\(.photos[0].photographer) — \(.photos[0].url)"' > "$CACHE/$slug.credit.txt" 2>/dev/null || true
fi
echo "bg -> $OUT  (credit: $(echo "$resp" | jq -r '.photos[0].photographer'))${CACHE:+  [cached: $slug.jpg]}"
