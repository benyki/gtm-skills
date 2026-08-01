#!/usr/bin/env bash
# Add a thin solid-color border (default 3px) of a deterministic-but-varied
# color. Frame dimensions change slightly; edge pixels of the original are
# pushed inward.
# Flags:
#   --px N         border thickness in pixels (default 3, range 2–4)
#   --color HEX    border color (default: pseudo-random from input mtime)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

PX=3
COLOR=""
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --px)    PX="$2"; shift 2 ;;
    --color) COLOR="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: border.sh [--px N] [--color HEX] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.border.mp4}"

if [[ -z "$COLOR" ]]; then
  # Pseudo-random hex color seeded by input filename + size
  SEED=$(echo -n "$IN$(stat -f %z "$IN" 2>/dev/null || stat -c %s "$IN" 2>/dev/null)" | shasum | head -c 6)
  COLOR="#${SEED}"
fi

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

# scale the original down by 2*PX in each axis, then pad with color back to W×H.
NEW_W=$(( W - 2*PX ))
NEW_H=$(( H - 2*PX ))

"$FF" -y -i "$IN" \
  -vf "scale=${NEW_W}:${NEW_H}:flags=lanczos,pad=${W}:${H}:${PX}:${PX}:color=${COLOR}" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
