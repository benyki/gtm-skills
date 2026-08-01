#!/usr/bin/env bash
# Rotate hue by a small angle (default 4°). All colors drift around the
# wheel; under ~8° this is invisible on photographic content.
# Flags: --deg D  (hue rotation in degrees, default 4, range 2–6)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

DEG=4
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --deg) DEG="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: hue-shift.sh [--deg D] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.hue.mp4}"

"$FF" -y -i "$IN" \
  -vf "hue=h=${DEG}" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
