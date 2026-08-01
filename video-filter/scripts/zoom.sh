#!/usr/bin/env bash
# Punch zoom — smoothly zooms IN by +40% (default) over the active window,
# holds, then smoothly zooms back to 1×. No rotation, no drift. Useful as a
# subtle hype beat on B-roll, product reveals, or anywhere you want the
# subject to "lean in" without breaking the frame.
#
# Timeline (default):
#   t < START                          : source at 1× (unchanged)
#   START → START+RAMP                 : ramps up to 1.4× via cosine ease
#   START+RAMP → START+RAMP+DURATION   : holds at 1.4×
#   ... → ... + RAMP                   : ramps back to 1×
#   thereafter                         : source at 1×
#
# Usage:
#   bash zoom.sh /abs/path/input.mp4                     # default: +40%, start 1.0s, 5.6s hold
#   bash zoom.sh --zoom-in 0.6 input.mp4                 # +60% punch
#   bash zoom.sh --duration 3 input.mp4                  # shorter hold
#   bash zoom.sh --start 0.5 --ramp 0.6 input.mp4        # earlier, smoother in/out
#
# Flags:
#   --zoom-in F    extra zoom at peak (default 0.4 = +40%)
#   --start S      time to begin ramping in (default 1.0)
#   --duration S   how long to HOLD at peak zoom (default 5.6)
#   --ramp S       ramp-in/ramp-out duration each (default 0.4)
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

ZOOM_IN=0.4
START=1.0
DURATION=5.6
RAMP=0.4

while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --zoom-in)  ZOOM_IN="$2"; shift 2 ;;
    --start)    START="$2"; shift 2 ;;
    --duration) DURATION="$2"; shift 2 ;;
    --ramp)     RAMP="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: zoom.sh [flags] /abs/path/input.mp4}"
OUT="${IN%.*}.zoom.mp4"

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

# Activity envelope: 0 before START, ramps to 1 over RAMP, holds, ramps back.
RAMP_OUT_START=$(awk -v s="$START" -v r="$RAMP" -v d="$DURATION" 'BEGIN { printf "%.4f", s + r + d }')
ACTIVITY="0.5*(1-cos(PI*clip((t-${START})/${RAMP}\\,0\\,1)))-0.5*(1-cos(PI*clip((t-${RAMP_OUT_START})/${RAMP}\\,0\\,1)))"

SRC_ZOOM="(1+${ZOOM_IN}*(${ACTIVITY}))"

# Scale to ZOOM*W × ZOOM*H with per-frame evaluation, then center-crop W × H.
# Crop offset is computed directly from t (not iw) because eval=frame makes the
# input dimensions vary per frame, and crop's iw is init-time only.
SCALE_W_EXPR="${SRC_ZOOM}*${W}"
SCALE_H_EXPR="${SRC_ZOOM}*${H}"
CROP_X_EXPR="${W}*(${SRC_ZOOM}-1)/2"
CROP_Y_EXPR="${H}*(${SRC_ZOOM}-1)/2"

FILTER="scale=w='${SCALE_W_EXPR}':h='${SCALE_H_EXPR}':eval=frame,crop=w=${W}:h=${H}:x='${CROP_X_EXPR}':y='${CROP_Y_EXPR}'"

"$FF" -y -i "$IN" \
  -vf "$FILTER" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a copy -movflags +faststart \
  "$OUT"

echo "$OUT"
