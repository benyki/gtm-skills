#!/usr/bin/env bash
# Clean re-encode with fresh metadata. Strips encoder tags, sets a new
# creation_time, and produces a fresh container hash. Always the FINAL step
# of any duplicate chain.
# Flags:
#   --crf N  x264 quality (default 20, range 18–24)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

CRF=20
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --crf) CRF="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: reencode.sh [--crf N] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.reenc.mp4}"

NOW=$(date -u +%Y-%m-%dT%H:%M:%S)

"$FF" -y -i "$IN" \
  -map_metadata -1 \
  -metadata creation_time="$NOW" \
  -c:v libx264 -crf "$CRF" -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
