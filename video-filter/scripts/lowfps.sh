#!/usr/bin/env bash
# Drop framerate to remove the unnaturally-smooth motion of AI-rendered video.
# Optional flag: --fps N (default 15).
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

FPS=15
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --fps) FPS="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: lowfps.sh [--fps N] /abs/path/input.mp4}"
OUT="${IN%.*}.lowfps.mp4"

"$FF" -y -i "$IN" \
  -vf "fps=${FPS}" \
  -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p \
  -c:a copy -movflags +faststart \
  "$OUT"

echo "$OUT"
