#!/usr/bin/env bash
# dup-15.sh — produce 15 visually-similar but perceptual-hash-distinct
# duplicates of the input video. "Heavy spam" preset.
#
# Canonical "heavy" stack:
#
#   zoom → rotate → border → color-shift → noise-overlay → updown-cycle → reencode
#
# Every variant carries ALL SIX axes; per-axis parameters vary widely.
# Ranges: zoom 2–7%, rotate ±0.7–3.0°, border 2–6px, brightness ±0.05,
# contrast 0.92–1.07, saturation 0.92–1.08, noise 5–14, updown intermediate
# 1080 / 1440 / 1800 / 2160 / 2880.
#
# Six independent axes × 15 unique parameter tuples → high pairwise hash
# distance by construction. The updown-cycle pass (lanczos upscale then
# downscale) rebuilds high-frequency detail rather than just shifting it.
#
# Output: <input-dir>/dup-out/<basename>.v01..v15.mp4  (or [outdir] if given)
#
# Render time: ~30–50s per variant on M-series Mac → ~10–14 min total.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T="$SCRIPT_DIR/transforms"

IN="${1:?usage: dup-15.sh /abs/path/input.mp4 [/abs/path/outdir]}"
DIR="$(dirname "$IN")"
BASE="$(basename "${IN%.*}")"
OUTDIR="${2:-$DIR/dup-out}"
WORK="$OUTDIR/.work-$$"
mkdir -p "$OUTDIR" "$WORK"
trap 'rm -rf "$WORK"' EXIT

run_chain() {
  local idx="$1"; shift
  local label="$(printf "v%02d" "$idx")"
  local cur="$IN"
  local step=0
  for op in "$@"; do
    step=$((step+1))
    local stage="$WORK/${label}.s${step}.mp4"
    eval "$op --out '$stage' '$cur'" >/dev/null
    cur="$stage"
  done
  mv "$cur" "$OUTDIR/${BASE}.${label}.mp4"
  echo "$OUTDIR/${BASE}.${label}.mp4"
}

run_chain  1 \
  "bash '$T/zoom.sh' --pct 2" \
  "bash '$T/rotate.sh' --deg 0.7" \
  "bash '$T/border.sh' --px 2 --color '#1a2b3c'" \
  "bash '$T/color-shift.sh' --b 0.01 --c 1.02 --s 1.02" \
  "bash '$T/noise-overlay.sh' --strength 5" \
  "bash '$T/updown-cycle.sh' --h 1080" \
  "bash '$T/reencode.sh'"

run_chain  2 \
  "bash '$T/zoom.sh' --pct 2.4" \
  "bash '$T/rotate.sh' --deg -1.1" \
  "bash '$T/border.sh' --px 3 --color '#3c2a1b'" \
  "bash '$T/color-shift.sh' --b -0.015 --c 1.04 --s 1.01" \
  "bash '$T/noise-overlay.sh' --strength 6" \
  "bash '$T/updown-cycle.sh' --h 1440" \
  "bash '$T/reencode.sh'"

run_chain  3 \
  "bash '$T/zoom.sh' --pct 2.8" \
  "bash '$T/rotate.sh' --deg 1.6" \
  "bash '$T/border.sh' --px 4 --color '#0f3a2d'" \
  "bash '$T/color-shift.sh' --b 0.025 --c 0.97 --s 1.04" \
  "bash '$T/noise-overlay.sh' --strength 8" \
  "bash '$T/updown-cycle.sh' --h 1800" \
  "bash '$T/reencode.sh'"

run_chain  4 \
  "bash '$T/zoom.sh' --pct 3.2" \
  "bash '$T/rotate.sh' --deg -2.1" \
  "bash '$T/border.sh' --px 5 --color '#2d0f3a'" \
  "bash '$T/color-shift.sh' --b -0.03 --c 1.05 --s 0.95" \
  "bash '$T/noise-overlay.sh' --strength 10" \
  "bash '$T/updown-cycle.sh' --h 2160" \
  "bash '$T/reencode.sh'"

run_chain  5 \
  "bash '$T/zoom.sh' --pct 3.6" \
  "bash '$T/rotate.sh' --deg 2.6" \
  "bash '$T/border.sh' --px 6 --color '#3a2d0f'" \
  "bash '$T/color-shift.sh' --b 0.04 --c 0.94 --s 1.07" \
  "bash '$T/noise-overlay.sh' --strength 12" \
  "bash '$T/updown-cycle.sh' --h 2880" \
  "bash '$T/reencode.sh'"

run_chain  6 \
  "bash '$T/zoom.sh' --pct 4" \
  "bash '$T/rotate.sh' --deg -2.8" \
  "bash '$T/border.sh' --px 2 --color '#3a0f2d'" \
  "bash '$T/color-shift.sh' --b -0.045 --c 1.06 --s 1.05" \
  "bash '$T/noise-overlay.sh' --strength 7" \
  "bash '$T/updown-cycle.sh' --h 1080" \
  "bash '$T/reencode.sh'"

run_chain  7 \
  "bash '$T/zoom.sh' --pct 4.4" \
  "bash '$T/rotate.sh' --deg 0.9" \
  "bash '$T/border.sh' --px 3 --color '#0f2d3a'" \
  "bash '$T/color-shift.sh' --b 0.05 --c 0.93 --s 0.93" \
  "bash '$T/noise-overlay.sh' --strength 14" \
  "bash '$T/updown-cycle.sh' --h 1440" \
  "bash '$T/reencode.sh'"

run_chain  8 \
  "bash '$T/zoom.sh' --pct 4.8" \
  "bash '$T/rotate.sh' --deg -1.4" \
  "bash '$T/border.sh' --px 4 --color '#2d3a0f'" \
  "bash '$T/color-shift.sh' --b -0.02 --c 1.01 --s 1.03" \
  "bash '$T/noise-overlay.sh' --strength 5" \
  "bash '$T/updown-cycle.sh' --h 1800" \
  "bash '$T/reencode.sh'"

run_chain  9 \
  "bash '$T/zoom.sh' --pct 5.2" \
  "bash '$T/rotate.sh' --deg 1.9" \
  "bash '$T/border.sh' --px 5 --color '#3a1a0f'" \
  "bash '$T/color-shift.sh' --b 0.022 --c 1.03 --s 0.99" \
  "bash '$T/noise-overlay.sh' --strength 9" \
  "bash '$T/updown-cycle.sh' --h 2160" \
  "bash '$T/reencode.sh'"

run_chain 10 \
  "bash '$T/zoom.sh' --pct 5.6" \
  "bash '$T/rotate.sh' --deg -2.3" \
  "bash '$T/border.sh' --px 6 --color '#1a3a0f'" \
  "bash '$T/color-shift.sh' --b -0.035 --c 1.07 --s 1.08" \
  "bash '$T/noise-overlay.sh' --strength 11" \
  "bash '$T/updown-cycle.sh' --h 2880" \
  "bash '$T/reencode.sh'"

run_chain 11 \
  "bash '$T/zoom.sh' --pct 6" \
  "bash '$T/rotate.sh' --deg 2.9" \
  "bash '$T/border.sh' --px 2 --color '#0f1a3a'" \
  "bash '$T/color-shift.sh' --b 0.005 --c 0.92 --s 1.06" \
  "bash '$T/noise-overlay.sh' --strength 13" \
  "bash '$T/updown-cycle.sh' --h 1080" \
  "bash '$T/reencode.sh'"

run_chain 12 \
  "bash '$T/zoom.sh' --pct 6.4" \
  "bash '$T/rotate.sh' --deg -0.8" \
  "bash '$T/border.sh' --px 3 --color '#3a0f1a'" \
  "bash '$T/color-shift.sh' --b -0.008 --c 0.99 --s 0.96" \
  "bash '$T/noise-overlay.sh' --strength 6" \
  "bash '$T/updown-cycle.sh' --h 1440" \
  "bash '$T/reencode.sh'"

run_chain 13 \
  "bash '$T/zoom.sh' --pct 6.8" \
  "bash '$T/rotate.sh' --deg 1.2" \
  "bash '$T/border.sh' --px 4 --color '#2a1b3c'" \
  "bash '$T/color-shift.sh' --b 0.018 --c 1.04 --s 0.98" \
  "bash '$T/noise-overlay.sh' --strength 8" \
  "bash '$T/updown-cycle.sh' --h 1800" \
  "bash '$T/reencode.sh'"

run_chain 14 \
  "bash '$T/zoom.sh' --pct 7" \
  "bash '$T/rotate.sh' --deg -1.6" \
  "bash '$T/border.sh' --px 5 --color '#1b3c2a'" \
  "bash '$T/color-shift.sh' --b -0.012 --c 0.96 --s 1.04" \
  "bash '$T/noise-overlay.sh' --strength 10" \
  "bash '$T/updown-cycle.sh' --h 2160" \
  "bash '$T/reencode.sh'"

run_chain 15 \
  "bash '$T/zoom.sh' --pct 2.2" \
  "bash '$T/rotate.sh' --deg 2.2" \
  "bash '$T/border.sh' --px 6 --color '#3c1b2a'" \
  "bash '$T/color-shift.sh' --b 0.03 --c 0.98 --s 0.92" \
  "bash '$T/noise-overlay.sh' --strength 12" \
  "bash '$T/updown-cycle.sh' --h 2880" \
  "bash '$T/reencode.sh'"

ls -1 "$OUTDIR/${BASE}.v"*.mp4
