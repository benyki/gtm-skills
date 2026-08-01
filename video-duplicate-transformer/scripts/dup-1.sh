#!/usr/bin/env bash
# dup-1.sh — produce 1 perfect-pixel duplicate of the input video.
#
# Strategy: stream-copy re-mux into a fresh MP4 container. All video and
# audio bytes are bit-identical to the source; only the container is rewritten
# with stripped metadata and a fresh creation_time. The file SHA changes,
# but a frame-by-frame PSNR vs the original is infinite.
#
# Use this when you want a "clean copy" to re-upload as-is without
# re-encoding artifacts, OR as the first step before manually picking a
# transform chain.
#
# Output: <input-dir>/dup-out/<basename>.v01.mp4
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

IN="${1:?usage: dup-1.sh /abs/path/input.mp4 [/abs/path/outdir]}"
DIR="$(dirname "$IN")"
BASE="$(basename "${IN%.*}")"
OUTDIR="${2:-$DIR/dup-out}"
mkdir -p "$OUTDIR"
OUT="$OUTDIR/${BASE}.v01.mp4"

NOW=$(date -u +%Y-%m-%dT%H:%M:%S)

"$FF" -y -i "$IN" \
  -c copy \
  -map_metadata -1 \
  -metadata creation_time="$NOW" \
  -movflags +faststart \
  "$OUT"

echo "$OUT"
