#!/usr/bin/env bash
# Add per-frame temporal noise. Invisible to the eye at low strengths but
# every pixel value changes — destroys the perceptual hash fingerprint.
# Flags: --strength N  (default 8, range 4–18). 2–4% opacity ≈ strength 6–10.
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

STRENGTH=8
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --strength) STRENGTH="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: noise-overlay.sh [--strength N] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.noise.mp4}"

"$FF" -y -i "$IN" \
  -vf "noise=alls=${STRENGTH}:allf=t+u" \
  -c:v libx264 -crf 22 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
