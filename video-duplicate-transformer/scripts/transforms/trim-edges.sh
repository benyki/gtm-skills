#!/usr/bin/env bash
# Drop N frames from the start AND end of the clip (default 2 each).
# Shifts the entire frame timeline — keyframe-based hashes recompute against
# different reference frames.
# Flags: --frames N  (frames to drop from each end, default 2, range 1–3)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

FRAMES=2
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --frames) FRAMES="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: trim-edges.sh [--frames N] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.trim.mp4}"

# Get framerate (numeric, e.g. 30000/1001)
FPS=$("$FP" -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$IN")
FPS_NUM=$(awk -F/ -v f="$FPS" 'BEGIN { split(f,a,"/"); printf "%.6f", a[1]/(a[2]==0?1:a[2]) }')
DUR=$("$FP" -v error -show_entries format=duration -of csv=p=0 "$IN")

OFFSET=$(awk -v n="$FRAMES" -v r="$FPS_NUM" 'BEGIN { printf "%.6f", n/r }')
NEW_DUR=$(awk -v d="$DUR" -v n="$FRAMES" -v r="$FPS_NUM" 'BEGIN { printf "%.6f", d - 2*n/r }')

"$FF" -y -ss "$OFFSET" -i "$IN" -t "$NEW_DUR" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
