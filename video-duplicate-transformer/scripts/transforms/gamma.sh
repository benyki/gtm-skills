#!/usr/bin/env bash
# Gamma shift. Pushes midtones up or down without crushing blacks or whites.
# Flags: --g F  (gamma value, default 1.05, range 0.95–1.05)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

G=1.05
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --g) G="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: gamma.sh [--g F] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.gamma.mp4}"

"$FF" -y -i "$IN" \
  -vf "eq=gamma=${G}" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
