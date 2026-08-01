#!/usr/bin/env bash
# Speed up or slow down the clip by 1–3 percent. Every keyframe moves on
# the timeline; both video and audio fingerprints shift.
# Flags:
#   --speed F           speed multiplier (default 1.02, range 0.97–1.03)
#   --pitch-preserve N  1 keeps audio pitch (atempo), 0 lets pitch drift (default 0)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

SPEED=1.02
PRESERVE=0
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --speed)          SPEED="$2"; shift 2 ;;
    --pitch-preserve) PRESERVE="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: speed-shift.sh [--speed F] [--pitch-preserve 0|1] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.speed.mp4}"

V_PTS=$(awk -v s="$SPEED" 'BEGIN { printf "%.6f", 1/s }')

if [[ "$PRESERVE" == "1" ]]; then
  AFILT="atempo=${SPEED}"
else
  A_PTS=$(awk -v s="$SPEED" 'BEGIN { printf "%.6f", 1/s }')
  AFILT="asetpts=${A_PTS}*PTS,aresample=async=1"
fi

"$FF" -y -i "$IN" \
  -filter_complex "[0:v]setpts=${V_PTS}*PTS[v];[0:a]${AFILT}[a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
