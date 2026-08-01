#!/usr/bin/env bash
# Post a word-backstory thread to Bluesky, fully chained:
#   post 1 = opener, post 2..n = body, last = CTA reply.
# Each post replies to the previous one; the thread root stays the opener.
#
# Usage:
#   post-bluesky-thread.sh --label <label> [--account MAIN] [--strip-md] [--dry-run]
#
# Reads the rendered posts from render-thread.mjs (same dir), so the text
# posted is exactly what the preview showed.

set -euo pipefail

ACCOUNT="MAIN"
LABEL=""
STRIP=""
DRY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --account) ACCOUNT="$2"; shift 2 ;;
    --label) LABEL="$2"; shift 2 ;;
    --strip-md) STRIP="--strip-md"; shift ;;
    --dry-run) DRY="1"; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -14; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

[ -z "$LABEL" ] && { echo "missing --label" >&2; exit 1; }

HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$HOME/.agents/.env"
BSKY="$HOME/.agents/skills/bluesky-post-manage/scripts"
[ -f "$ENV_FILE" ] || { echo "missing $ENV_FILE" >&2; exit 1; }

# Pull the ordered posts as a JSON array.
POSTS_JSON=$(node "$HERE/render-thread.mjs" "$LABEL" --json $STRIP)
COUNT=$(echo "$POSTS_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>console.log(JSON.parse(s).length))')

echo "→ posting $COUNT-part thread for \"$LABEL\" to Bluesky account $ACCOUNT"
[ -n "$DRY" ] && { echo "$POSTS_JSON"; echo "(dry run — nothing posted)"; exit 0; }

get_post() { echo "$POSTS_JSON" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>process.stdout.write(JSON.parse(s)[$1]))"; }

ROOT_URI=""; ROOT_CID=""; PREV_URI=""; PREV_CID=""
for ((i=0; i<COUNT; i++)); do
  TEXT="$(get_post "$i")"
  if [ "$i" -eq 0 ]; then
    OUT=$(node --env-file="$ENV_FILE" "$BSKY/post.mjs" --account "$ACCOUNT" --text "$TEXT")
  else
    OUT=$(node --env-file="$ENV_FILE" "$BSKY/post.mjs" --account "$ACCOUNT" --text "$TEXT" \
      --reply-to "$PREV_URI" --reply-cid "$PREV_CID" \
      --reply-root-uri "$ROOT_URI" --reply-root-cid "$ROOT_CID")
  fi
  URI=$(echo "$OUT" | grep -oE 'at://[^ ]+' | head -1)
  CID=$(echo "$OUT" | grep -oE 'cid: [^ ]+' | head -1 | awk '{print $2}')
  [ -z "$URI" ] || [ -z "$CID" ] && { echo "failed to parse post $i:" >&2; echo "$OUT" >&2; exit 1; }
  echo "  ✓ post $((i+1))/$COUNT  $URI"
  PREV_URI="$URI"; PREV_CID="$CID"
  if [ "$i" -eq 0 ]; then ROOT_URI="$URI"; ROOT_CID="$CID"; fi
done

POST_ID=$(echo "$ROOT_URI" | awk -F/ '{print $NF}')
HANDLE=$(grep "BSKY_ACCOUNT_${ACCOUNT}_HANDLE" "$ENV_FILE" | head -1 | cut -d= -f2)
echo ""
echo "✓ thread live: https://bsky.app/profile/${HANDLE}/post/${POST_ID}"
