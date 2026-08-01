#!/usr/bin/env bash
# Fetch title, description, and caption from a social media URL.
# Prints a JSON object to stdout.
# Usage: ./fetch-social-meta.sh <url>
# Returns: { "title": "...", "description": "...", "duration": 0, "author": "...", "platform": "..." }
# Falls back to empty strings on failure — never exits non-zero so the caller can degrade gracefully.

set -euo pipefail

URL="${1:-}"
if [[ -z "$URL" ]]; then
  echo '{"error":"no url provided","title":"","description":"","duration":0,"author":"","platform":""}'
  exit 0
fi

# Detect platform from URL
platform="unknown"
if echo "$URL" | grep -qi "tiktok.com";       then platform="tiktok"; fi
if echo "$URL" | grep -qi "instagram.com";    then platform="instagram"; fi
if echo "$URL" | grep -qi "youtube.com\|youtu.be"; then platform="youtube"; fi
if echo "$URL" | grep -qi "twitter.com\|x.com";    then platform="twitter"; fi
if echo "$URL" | grep -qi "reddit.com";       then platform="reddit"; fi

# Try yt-dlp first (covers TikTok, YouTube, Instagram Reels, Twitter/X video)
YT_DLP="$(command -v yt-dlp 2>/dev/null || echo "")"
if [[ -n "$YT_DLP" ]]; then
  meta="$("$YT_DLP" \
    --no-warnings \
    --skip-download \
    --print-json \
    --no-playlist \
    "$URL" 2>/dev/null)" || meta=""

  if [[ -n "$meta" ]]; then
    title=$(echo "$meta"       | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title',''))"       2>/dev/null || echo "")
    description=$(echo "$meta" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('description',''))" 2>/dev/null || echo "")
    duration=$(echo "$meta"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('duration',0))"     2>/dev/null || echo "0")
    author=$(echo "$meta"      | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('uploader','') or d.get('channel',''))" 2>/dev/null || echo "")

    python3 -c "
import json, sys
print(json.dumps({
  'title': sys.argv[1],
  'description': sys.argv[2],
  'duration': float(sys.argv[3]) if sys.argv[3] else 0,
  'author': sys.argv[4],
  'platform': sys.argv[5]
}))
" "$title" "$description" "$duration" "$author" "$platform"
    exit 0
  fi
fi

# Fallback: emit empty result so the caller can use agent-browser instead
echo "{\"title\":\"\",\"description\":\"\",\"duration\":0,\"author\":\"\",\"platform\":\"$platform\",\"fallback\":true}"
