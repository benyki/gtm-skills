#!/usr/bin/env bash
# dup-5.sh — produce 5 visually-similar but perceptual-hash-distinct
# duplicates of the input video.
#
# Stack (8 steps):
#
#   zoom → rotate → border → color-shift → gamma → noise → updown-cycle → reencode
#
# pHash works on a 32×32 grayscale DCT; it's blind to saturation, hue, fine
# noise, and small border deltas. The axes it actually responds to are
# zoom, rotate, brightness, contrast, gamma, and detail reconstruction
# (updown-cycle). This stack ensures every variant perturbs ALL of them.
#
# Tight envelopes (per user request): zoom 2.0–4.0%, rotate ±0.8–2.5°.
# Other axes: border 2–6 px, brightness ±0.05, contrast 0.93–1.06,
# saturation 0.93–1.07, gamma 0.93–1.07, noise 5–13, updown intermediate
# 1080/1440/1800/2160/2880.
#
# Parameter assignment is a MAGIC LATIN SQUARE on 7 ranked axes (every
# axis Latin, every variant's rank-sum = 21 → equal perturbation effort).
# Saturation, border color, and updown height get independent Latin
# assignments. No two variants share a value on any axis.
#
# Rank → value:
#   zoom %:        1→2.0  2→2.5  3→3.0  4→3.5  5→4.0
#   rotate °:      1→0.8  2→1.5  3→1.7  4→2.4  5→2.5  (signs alternate)
#   border px:     1→2    2→3    3→4    4→5    5→6
#   brightness:    1→0.01 2→0.02 3→0.03 4→0.04 5→0.05 (signs alternate)
#   contrast:      1→1.02 2→0.97 3→1.04 4→0.93 5→1.06
#   gamma:         1→1.02 2→0.97 3→1.04 4→0.93 5→1.06
#   noise:         1→5    2→7    3→9    4→11   5→13
#
# Magic square (col Latin, row-sum=21):
#       zoom rot bdr  b    c   γ  noise   sum
# v01:   2   3   5    4    1   1   5      21
# v02:   4   5   2    1    3   2   4      21
# v03:   1   4   3    5    2   3   3      21
# v04:   3   1   4    2    5   4   2      21
# v05:   5   2   1    3    4   5   1      21
#
# Output: <input-dir>/dup-out/<basename>.v01..v05.mp4  (or [outdir] if given)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T="$SCRIPT_DIR/transforms"

IN="${1:?usage: dup-5.sh /abs/path/input.mp4 [/abs/path/outdir]}"
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

run_chain 1 \
  "bash '$T/zoom.sh' --pct 2.5" \
  "bash '$T/rotate.sh' --deg 1.7" \
  "bash '$T/border.sh' --px 6 --color '#1a2b3c'" \
  "bash '$T/color-shift.sh' --b -0.04 --c 1.02 --s 1.03" \
  "bash '$T/gamma.sh' --g 1.02" \
  "bash '$T/noise-overlay.sh' --strength 13" \
  "bash '$T/updown-cycle.sh' --h 1080" \
  "bash '$T/reencode.sh'"

run_chain 2 \
  "bash '$T/zoom.sh' --pct 3.5" \
  "bash '$T/rotate.sh' --deg -2.5" \
  "bash '$T/border.sh' --px 3 --color '#3c2a1b'" \
  "bash '$T/color-shift.sh' --b 0.01 --c 1.04 --s 0.97" \
  "bash '$T/gamma.sh' --g 0.97" \
  "bash '$T/noise-overlay.sh' --strength 11" \
  "bash '$T/updown-cycle.sh' --h 1440" \
  "bash '$T/reencode.sh'"

run_chain 3 \
  "bash '$T/zoom.sh' --pct 2.0" \
  "bash '$T/rotate.sh' --deg 2.4" \
  "bash '$T/border.sh' --px 4 --color '#0f3a2d'" \
  "bash '$T/color-shift.sh' --b -0.05 --c 0.97 --s 0.93" \
  "bash '$T/gamma.sh' --g 1.04" \
  "bash '$T/noise-overlay.sh' --strength 9" \
  "bash '$T/updown-cycle.sh' --h 1800" \
  "bash '$T/reencode.sh'"

run_chain 4 \
  "bash '$T/zoom.sh' --pct 3.0" \
  "bash '$T/rotate.sh' --deg -0.8" \
  "bash '$T/border.sh' --px 5 --color '#2d0f3a'" \
  "bash '$T/color-shift.sh' --b 0.02 --c 1.06 --s 1.05" \
  "bash '$T/gamma.sh' --g 0.93" \
  "bash '$T/noise-overlay.sh' --strength 7" \
  "bash '$T/updown-cycle.sh' --h 2160" \
  "bash '$T/reencode.sh'"

run_chain 5 \
  "bash '$T/zoom.sh' --pct 4.0" \
  "bash '$T/rotate.sh' --deg 1.5" \
  "bash '$T/border.sh' --px 2 --color '#3a2d0f'" \
  "bash '$T/color-shift.sh' --b -0.03 --c 0.93 --s 1.07" \
  "bash '$T/gamma.sh' --g 1.06" \
  "bash '$T/noise-overlay.sh' --strength 5" \
  "bash '$T/updown-cycle.sh' --h 2880" \
  "bash '$T/reencode.sh'"

ls -1 "$OUTDIR/${BASE}.v"*.mp4
