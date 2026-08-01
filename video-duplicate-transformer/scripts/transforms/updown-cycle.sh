#!/usr/bin/env bash
# Upscale to 4K (or configured intermediate) then downscale back to original.
# Heavier reconstruction than downup-cycle — the lanczos kernel paints in
# new edge pixels that weren't there. Slower (4K intermediate).
# Flags: --h H  (intermediate height, default 2160, range 1440–2160)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

UP_H=2160
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --h) UP_H="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: updown-cycle.sh [--h H] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.updown.mp4}"

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

"$FF" -y -i "$IN" \
  -vf "scale=-2:${UP_H}:flags=lanczos,scale=${W}:${H}:flags=lanczos" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
