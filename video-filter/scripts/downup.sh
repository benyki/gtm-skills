#!/usr/bin/env bash
# Downscale to 540p then upscale back. Softens fine detail where AI artifacts live.
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

IN="${1:?usage: downup.sh /abs/path/input.mp4}"
OUT="${IN%.*}.downup.mp4"

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

# Downscale to ~540p preserving aspect, then back up with lanczos.
DOWN_H=540
"$FF" -y -i "$IN" \
  -vf "scale=-2:${DOWN_H},scale=${W}:${H}:flags=lanczos" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a copy -movflags +faststart \
  "$OUT"

echo "$OUT"
