#!/usr/bin/env bash
# Downscale to 540p then upscale back to original. High-frequency detail —
# the part of the image perceptual hashes focus on — is reconstructed by
# lanczos rather than preserved.
# Flags: --h H  (intermediate height, default 540, range 360–720)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

DOWN_H=540
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --h) DOWN_H="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: downup-cycle.sh [--h H] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.downup.mp4}"

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

"$FF" -y -i "$IN" \
  -vf "scale=-2:${DOWN_H},scale=${W}:${H}:flags=lanczos" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
