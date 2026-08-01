#!/usr/bin/env bash
# tiktok-post-finder :: Discord report (posts verbatim as the @your-bot bot)
#
# Builds a report from a posts JSON (links + likes + note) plus a ready-to-comment
# block, then delivers it to Discord. Title, comment header, comment templates and
# the Discord target all come from the resolved post-finder-config.md, so this
# script carries NO project-specific content.
#
# Delivery uses `your-agent message send` (not `agent --deliver`) so the precomposed
# report goes out VERBATIM — the agent-relay path lets the local model rewrite or
# ask questions instead of posting. The `default` discord account is the @your-bot
# bot and the only account with send permission on the configured channel.
#
# Usage:
#   report_to_discord.sh <posts.json>          # preview only
#   report_to_discord.sh <posts.json> --send   # actually post to Discord
#
# posts.json: array of { "url": "...", "likes": 123, "note"|"caption": "..." }
#
# Env overrides:
#   CHANNEL=<id>   Discord channel id (default: config.discord.channel)
#   ACCOUNT=<id>   your agent runtime discord account (default: config.discord.account)
#   CONFIG=...     force a specific post-finder-config.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
# shellcheck source=_config.sh
. "$SCRIPT_DIR/_config.sh"

POSTS="${1:-}"
SEND_FLAG="${2:-}"

if [ -z "$POSTS" ] || [ ! -f "$POSTS" ]; then
  echo "usage: report_to_discord.sh <posts.json> [--send]" >&2
  exit 1
fi
if ! jq -e 'type == "array" and length > 0' "$POSTS" >/dev/null 2>&1; then
  echo "error: $POSTS must be a non-empty JSON array of {url,likes,note}." >&2
  exit 1
fi

CFG_FILE="$(pf_resolve_config "$SKILL_DIR")"
CFG="$(pf_config_json "$CFG_FILE")"

CHANNEL="${CHANNEL:-$(printf '%s' "$CFG" | jq -r '.discord.channel // empty')}"
ACCOUNT="${ACCOUNT:-$(printf '%s' "$CFG" | jq -r '.discord.account // "default"')}"
TITLE="$(printf '%s' "$CFG" | jq -r '.reportTitle // "🎯 TikTok — favorite words"')"
HEADER="$(printf '%s' "$CFG" | jq -r '.commentHeader // "Here is for each post a recommended ready to comment text :"')"

if [ -z "$CHANNEL" ]; then
  echo "error: no Discord channel (set CHANNEL=... or discord.channel in $CFG_FILE)." >&2
  exit 1
fi

# Comment templates (rotated). Fall back to project defaults if config lacks them.
# (read loop instead of mapfile for bash 3.2 compatibility on macOS)
SUGGESTIONS=()
while IFS= read -r _line; do
  [ -n "$_line" ] && SUGGESTIONS+=("$_line")
done < <(printf '%s' "$CFG" | jq -r '.commentTemplates[]?')
if [ "${#SUGGESTIONS[@]}" -eq 0 ]; then
  SUGGESTIONS=(
    "added to my collection thx"
    "adding it to my collection in the app haha"
    "word collector too here, add me in the app! @your-username"
  )
fi

# Human-friendly counts (415000 → 415K, 3100000 → 3.1M).
human() {
  awk -v n="${1:-0}" 'BEGIN{
    if (n>=1000000) printf "%.1fM", n/1000000;
    else if (n>=1000) printf "%.1fK", n/1000;
    else printf "%d", n
  }'
}

# --- Build the report message -------------------------------------------------
N="$(jq 'length' "$POSTS")"
MSG="$TITLE (top $N)"$'\n'

i=0
while [ "$i" -lt "$N" ]; do
  url="$(jq -r ".[$i].url" "$POSTS")"
  likes="$(jq -r ".[$i].likes // 0" "$POSTS")"
  views="$(jq -r ".[$i] | (.views // empty)" "$POSTS")"
  comments="$(jq -r ".[$i] | (.comments // empty)" "$POSTS")"
  date="$(jq -r ".[$i] | (.date // empty)" "$POSTS")"
  note="$(jq -r ".[$i] | (.note // .caption // \"\")" "$POSTS")"
  n=$((i + 1))

  # Engagement/date meta line — only include fields that are present.
  meta="❤️ $(human "$likes")"
  [ -n "$views" ]    && meta="$meta · ▶️ $(human "$views")"
  [ -n "$comments" ] && meta="$meta · 💬 $(human "$comments")"
  [ -n "$date" ]     && meta="📅 $date · $meta"

  MSG+=$'\n'"$n. $url"$'\n'"   $meta"$'\n'"   $note"$'\n'
  i=$((i + 1))
done

MSG+=$'\n'"$HEADER"$'\n'
i=0
while [ "$i" -lt "$N" ]; do
  n=$((i + 1))
  sug="${SUGGESTIONS[$((i % ${#SUGGESTIONS[@]}))]}"
  MSG+=$'\n'"$n. \"$sug\""
  i=$((i + 1))
done

# --- Preview ------------------------------------------------------------------
echo "──────── REPORT PREVIEW ────────"
printf '%s\n' "$MSG"
echo "────────────────────────────────"
echo "config:  $CFG_FILE"
echo "channel: $CHANNEL   account: $ACCOUNT (@your-bot bot)"

if [ "$SEND_FLAG" != "--send" ]; then
  echo
  echo "(preview only — re-run with --send to post as @your-bot)"
  exit 0
fi

# --- Deliver verbatim as the @your-bot bot ------------------------------------
echo
echo "→ Posting as @your-bot (account '$ACCOUNT') to channel:$CHANNEL …"
your-agent message send \
  --channel discord \
  --account "$ACCOUNT" \
  --target "channel:$CHANNEL" \
  --message "$MSG"
