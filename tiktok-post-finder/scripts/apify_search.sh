#!/usr/bin/env bash
# tiktok-post-finder :: Apify collection (DEFAULT method)
#
# Searches TikTok via clockworks/tiktok-scraper, prints a ranked list (by likes),
# and writes the top results as JSON. Queries, result count and niche come from
# the resolved post-finder-config.md (see references/post-finder-config.md).
#
# Usage:
#   apify_search.sh                       # use config searchQueries
#   apify_search.sh "query one" ["q2" ...]# override queries (config queries ignored)
#
# Env overrides:
#   RESULTS=10        max results to keep (default: config.maxResults, else 10)
#   OUT=/path.json    output JSON path (default /tmp/tiktok-post-finder-results.json)
#   CONFIG=...        force a specific post-finder-config.md
#
# Credentials: APIFY_API_KEY is read (only that key) from ~/.agents/.env at
# runtime and is NEVER printed. Per local-secrets: read ~/.agents/.env.example
# for variable names only; never read/print the real .env.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
# shellcheck source=_config.sh
. "$SCRIPT_DIR/_config.sh"

CFG_FILE="$(pf_resolve_config "$SKILL_DIR")"
CFG="$(pf_config_json "$CFG_FILE")"

# --- Credentials (extract ONLY the needed key; never source the whole file) ---
ENV_FILE="$HOME/.agents/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "error: $ENV_FILE not found. APIFY_API_KEY must live there (see ~/.agents/.env.example)." >&2
  exit 1
fi
APIFY_API_KEY="$(grep -E '^[[:space:]]*APIFY_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '"'\''[:space:]')"
if [ -z "${APIFY_API_KEY:-}" ]; then
  echo "error: APIFY_API_KEY not set (or empty) in $ENV_FILE" >&2
  exit 1
fi

# --- Resolve queries + result count -------------------------------------------
MAX="${RESULTS:-$(printf '%s' "$CFG" | jq -r '.maxResults // 10')}"
case "$MAX" in ''|*[!0-9]*) MAX=10 ;; esac

# Optional recency cutoff (days). Empty/0/null = no cutoff. Env overrides config.
MAXAGE="${MAX_AGE_DAYS:-$(printf '%s' "$CFG" | jq -r '.maxAgeDays // empty')}"
case "$MAXAGE" in *[!0-9]*) MAXAGE="" ;; esac   # ignore non-integers (incl. null)

# Oversample factor: TikTok search returns by relevance, not date, so when a
# cutoff is active we fetch more candidates so enough recent ones survive.
OVERSAMPLE="${OVERSAMPLE:-$(printf '%s' "$CFG" | jq -r '.fetchOversample // 4')}"
case "$OVERSAMPLE" in ''|*[!0-9]*) OVERSAMPLE=4 ;; esac

if [ "$#" -ge 1 ]; then
  QUERIES_JSON="$(printf '%s\n' "$@" | jq -R . | jq -s .)"
else
  QUERIES_JSON="$(printf '%s' "$CFG" | jq -c '.searchQueries // []')"
fi
NQ="$(printf '%s' "$QUERIES_JSON" | jq 'length')"
if [ "$NQ" -eq 0 ]; then
  echo "error: no search queries. Pass them as args or set searchQueries in $CFG_FILE." >&2
  exit 1
fi

# Per-query fetch so the union is roughly MAX (kept small to control cost).
# With a recency cutoff active, oversample (most relevance-ranked hits will be
# older than the cutoff and get filtered out), capped to keep cost sane.
if [ -n "$MAXAGE" ]; then
  TARGET=$(( MAX * OVERSAMPLE ))
  PER_QUERY=$(( (TARGET + NQ - 1) / NQ ))
  [ "$PER_QUERY" -gt 50 ] && PER_QUERY=50
else
  PER_QUERY=$(( (MAX + NQ - 1) / NQ ))
fi
[ "$PER_QUERY" -lt 1 ] && PER_QUERY=1

OUT="${OUT:-/tmp/tiktok-post-finder-results.json}"
RAW="$(mktemp)"; trap 'rm -f "$RAW"' EXIT

INPUT="$(jq -n --argjson q "$QUERIES_JSON" --argjson n "$PER_QUERY" '{
  searchQueries: $q,
  resultsPerPage: $n,
  shouldDownloadVideos: false,
  shouldDownloadCovers: false,
  shouldDownloadSubtitles: false,
  proxyCountryCode: "None"
}')"

echo "→ Searching TikTok via Apify (clockworks/tiktok-scraper)" >&2
echo "  config:  $CFG_FILE" >&2
echo "  queries: $(printf '%s' "$QUERIES_JSON" | jq -r 'join(" | ")')" >&2
echo "  max results: $MAX  (resultsPerPage=$PER_QUERY × $NQ queries)" >&2
[ -n "$MAXAGE" ] && echo "  recency cutoff: last $MAXAGE days (oversampling ×$OVERSAMPLE)" >&2

HTTP="$(curl -sS --max-time 180 --retry 2 --retry-delay 3 \
  -w '%{http_code}' -o "$RAW" \
  -X POST "https://api.apify.com/v2/acts/clockworks~tiktok-scraper/run-sync-get-dataset-items?token=${APIFY_API_KEY}" \
  -H "Content-Type: application/json" -d "$INPUT" || echo 000)"

if [ "$HTTP" != "200" ] && [ "$HTTP" != "201" ]; then
  echo "error: Apify request failed (HTTP $HTTP)." >&2
  jq -r '.error.message // .' "$RAW" 2>/dev/null | head -5 >&2 || head -5 "$RAW" >&2
  echo "Hint: check the API key, or fall back to the browser method (references/browser-method.md)." >&2
  exit 1
fi
if ! jq -e 'type == "array"' "$RAW" >/dev/null 2>&1; then
  echo "error: unexpected response shape (see below):" >&2
  jq -r '.error.message // .' "$RAW" 2>/dev/null | head -5 >&2 || head -5 "$RAW" >&2
  exit 1
fi

# Ranking weights + recency window (config-tunable). Higher score = better:
# more engagement AND more recent.
NOW="$(date +%s)"
WIN="$(printf '%s' "$CFG"  | jq -r '.ranking.recencyWindowDays // 540')"
WE="$(printf '%s'  "$CFG"  | jq -r '.ranking.engagementWeight  // 0.6')"
WR="$(printf '%s'  "$CFG"  | jq -r '.ranking.recencyWeight     // 0.4')"

# Recency cutoff for jq: CUT = cutoff days, STRICT = 1 when a cutoff is active.
if [ -n "$MAXAGE" ]; then CUT="$MAXAGE"; STRICT=1; else CUT=100000; STRICT=0; fi

# Build records, score by engagement (normalized within set) + recency, keep top MAX.
jq --argjson max "$MAX" --argjson now "$NOW" --argjson win "$WIN" \
   --argjson we "$WE" --argjson wr "$WR" --argjson cut "$CUT" --argjson strict "$STRICT" '
  [ .[] | select(.webVideoUrl) | {
      url: .webVideoUrl,
      likes:    (.diggCount    // 0),
      views:    (.playCount    // 0),
      comments: (.commentCount // 0),
      shares:   (.shareCount   // 0),
      collects: (.collectCount // 0),
      date:       ((.createTimeISO // "") | .[0:10]),
      createTime: (.createTime // 0),
      caption: ((.text // "") | gsub("[\n\t]"; " "))
    }
    | .engagement = (.likes + .comments + .shares + .collects)
  ]
  | unique_by(.url)
  | (([.[].engagement] | max) // 0) as $maxEng
  | map(
      .engScore = (if $maxEng > 0 then (.engagement / $maxEng) else 0 end)
      | .ageDays = (if .createTime > 0 then (($now - .createTime) / 86400) else $win end)
      | .recScore = ([ ([ (1 - (.ageDays / $win)), 1 ] | min), 0 ] | max)
      | .score = (($we * .engScore) + ($wr * .recScore))
    )
  | map(select( ($strict == 0) or (.createTime > 0 and .ageDays <= $cut) ))
  | sort_by(-.score)
  | .[0:$max]
' "$RAW" > "$OUT"

COUNT="$(jq 'length' "$OUT")"
if [ "$COUNT" -eq 0 ]; then
  if [ -n "$MAXAGE" ]; then
    echo "⚠ 0 results within the last $MAXAGE days. Widen maxAgeDays, raise OVERSAMPLE, change queries, or use the browser method." >&2
  else
    echo "⚠ 0 results. Try different queries, or use the browser method (references/browser-method.md)." >&2
  fi
  exit 0
fi
if [ -n "$MAXAGE" ] && [ "$COUNT" -lt "$MAX" ]; then
  echo "⚠ only $COUNT post(s) within the last $MAXAGE days (wanted $MAX). Raise OVERSAMPLE or widen maxAgeDays for more." >&2
fi

WINMSG="window ${WIN}d"; [ -n "$MAXAGE" ] && WINMSG="cutoff ${MAXAGE}d"
echo "✓ $COUNT results → $OUT  (ranked: ${WE}×engagement + ${WR}×recency, ${WINMSG})" >&2
echo >&2
echo "Ranked by score (date  likes  views  comments  score%  url  caption):" >&2
jq -r '.[] | [ .date, .likes, .views, .comments, ((.score * 100) | floor), .url, (.caption | .[0:80]) ] | @tsv' "$OUT"
