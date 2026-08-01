#!/usr/bin/env bash
# Temporal film grain / sensor noise. Hides smooth AI textures and plastic skin.
# Optional flag: --strength N (default 18, range 5–40).
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

STRENGTH=18
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --strength) STRENGTH="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: grain.sh [--strength N] /abs/path/input.mp4}"
OUT="${IN%.*}.grain.mp4"

"$FF" -y -i "$IN" \
  -vf "noise=alls=${STRENGTH}:allf=t+u" \
  -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p \
  -c:a copy -movflags +faststart \
  "$OUT"

echo "$OUT"
