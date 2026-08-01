#!/usr/bin/env bash
# Tweak brightness / contrast / saturation by small percentages. Lifts the
# whole color histogram off its original position.
# Flags:
#   --b F   brightness delta in [-0.05, 0.05] (default 0.02)
#   --c F   contrast multiplier near 1 (default 1.03, range 0.96–1.04)
#   --s F   saturation multiplier near 1 (default 1.03, range 0.96–1.05)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

B=0.02
C=1.03
S=1.03
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --b) B="$2"; shift 2 ;;
    --c) C="$2"; shift 2 ;;
    --s) S="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: color-shift.sh [--b F] [--c F] [--s F] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.color.mp4}"

"$FF" -y -i "$IN" \
  -vf "eq=brightness=${B}:contrast=${C}:saturation=${S}" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
