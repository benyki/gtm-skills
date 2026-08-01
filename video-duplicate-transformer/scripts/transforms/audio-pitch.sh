#!/usr/bin/env bash
# Shift audio pitch by a few cents, keep timing. Music/voice fingerprints
# change; the human ear cannot detect a shift under ~10 cents.
# Flags: --cents C  (semitone-cents, default 5, range 2–10; negative allowed)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

CENTS=5
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --cents) CENTS="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: audio-pitch.sh [--cents C] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.pitch.mp4}"

# 100 cents = 1 semitone; pitch ratio = 2^(cents/1200)
RATIO=$(awk -v c="$CENTS" 'BEGIN { printf "%.8f", 2^(c/1200) }')
# Use asetrate to retune, then atempo to restore duration.
SR_BASE=44100
SR_NEW=$(awk -v r="$RATIO" -v b="$SR_BASE" 'BEGIN { printf "%d", b*r }')
INV=$(awk -v r="$RATIO" 'BEGIN { printf "%.8f", 1/r }')

"$FF" -y -i "$IN" \
  -c:v copy \
  -af "asetrate=${SR_NEW},aresample=${SR_BASE},atempo=${INV}" \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
