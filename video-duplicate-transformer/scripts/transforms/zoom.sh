#!/usr/bin/env bash
# Center-zoom by a small percentage (default +3%). Every pixel moves; the
# perceptual hash shifts noticeably while the eye sees no change.
# Flags: --pct N  (zoom amount in percent, default 3, range 2–4)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

PCT=3
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --pct) PCT="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: zoom.sh [--pct N] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.zoom.mp4}"

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

Z=$(awk -v p="$PCT" 'BEGIN { printf "%.4f", 1 + p/100 }')

"$FF" -y -i "$IN" \
  -vf "scale=w=iw*${Z}:h=ih*${Z}:flags=lanczos,crop=${W}:${H}" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
