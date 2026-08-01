#!/usr/bin/env bash
# Rotate by a small angle (default 1.3°) then crop back to original frame.
# Sub-degree rotation rewrites every pixel via bilinear resampling.
# Flags: --deg D  (rotation in degrees, default 1.3, range -2 to 2)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

DEG=1.3
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --out) OUT_OVERRIDE="$2"; shift 2 ;;
    --deg) DEG="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: rotate.sh [--deg D] /abs/path/input.mp4}"
OUT="${OUT_OVERRIDE:-${IN%.*}.rotate.mp4}"

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

# Rotate, then center-crop the largest aspect-preserving rectangle inside
# the rotated frame to hide the black corner wedges. Analytic inset:
#   scale = 1 / (|cos θ| + |sin θ| * max(w/h, h/w))   with 2% safety margin
# Works for any aspect ratio and any |θ| ≲ 30°.
RAD=$(awk -v d="$DEG" 'BEGIN { printf "%.6f", d * 3.14159265/180 }')
INSET=$(awk -v d="$DEG" -v w="$W" -v h="$H" 'BEGIN {
  rad = (d<0?-d:d) * 3.14159265/180
  s = sin(rad); c = cos(rad)
  r = (w>h ? w/h : h/w)
  printf "%.4f", (1/(c + s*r)) * 0.98
}')
CW=$(awk -v w="$W" -v i="$INSET" 'BEGIN { printf "%d", int(w*i/2)*2 }')
CH=$(awk -v h="$H" -v i="$INSET" 'BEGIN { printf "%d", int(h*i/2)*2 }')

"$FF" -y -i "$IN" \
  -vf "rotate=${RAD}:ow=iw:oh=ih:c=black,crop=${CW}:${CH},scale=${W}:${H}:flags=lanczos" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  "$OUT"

echo "$OUT"
