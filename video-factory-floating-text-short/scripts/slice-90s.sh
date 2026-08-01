#!/usr/bin/env bash
# Slice every *.mp4 in <clips-dir> into 9:16 1080x1920 90s clips in <out-90s-dir>,
# skipping the first and last 60s of each source. Idempotent — re-running skips
# clips already present. Stops when at least <min-clips> (default 100) exist.
#
# Source variety: cuts are emitted in **round-robin order across sources**, not
# by draining one source at a time. With 6 sources and a 100-clip cap that
# means ~17 clips per source instead of e.g. 48/38/11/3/0/0.
#
# Filename convention (matches ~/videos/highway/90s/):
#   <sourceID> - clip<NN> (<sourceSec>s).mp4
#
# Usage: slice-90s.sh <clips-dir> <out-90s-dir> [min-clips]
set -euo pipefail

CLIPS_DIR="${1/#\~/$HOME}"
OUT_DIR="${2/#\~/$HOME}"
MIN_CLIPS="${3:-100}"
CLIP_LEN=90
TRIM_HEAD=60
TRIM_TAIL=60

if [[ ! -d "$CLIPS_DIR" ]]; then
  echo "no such dir: $CLIPS_DIR" >&2
  exit 1
fi
mkdir -p "$OUT_DIR"

count_existing() { find "$OUT_DIR" -maxdepth 1 -type f -name '*.mp4' | wc -l | tr -d ' '; }

# Center-crop 1920x1080 → 608x1080 then scale to 1080x1920 (same math as video-definition).
VF="crop=608:1080:(in_w-608)/2:(in_h-1080)/2,scale=1080:1920,setsar=1"

# Phase 1: probe every source and enumerate all possible (source, start, idx) cuts.
# Stored as "<idx>|<src>|<start>|<base>" so a numeric sort by idx interleaves sources.
declare -a JOBS=()
for src in "$CLIPS_DIR"/*.mp4; do
  [[ -e "$src" ]] || continue
  base=$(basename "$src" .mp4)
  duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$src" 2>/dev/null | awk '{printf "%d", $1}')
  if [[ -z "$duration" || "$duration" -lt $((TRIM_HEAD + TRIM_TAIL + CLIP_LEN)) ]]; then
    echo "skip $base — too short ($duration s)"
    continue
  fi
  usable_end=$((duration - TRIM_TAIL))
  idx=1
  start=$TRIM_HEAD
  while (( start + CLIP_LEN <= usable_end )); do
    JOBS+=("$(printf "%05d|%s|%d|%s" "$idx" "$src" "$start" "$base")")
    idx=$((idx + 1))
    start=$((start + CLIP_LEN))
  done
done

if [[ ${#JOBS[@]} -eq 0 ]]; then
  echo "no usable sources in $CLIPS_DIR" >&2
  exit 1
fi

# Phase 2: sort by idx asc (then by source name as tie-break). Result: clip01 of
# every source first, then clip02 of every source, etc. → round-robin across sources.
IFS=$'\n' SORTED=($(printf "%s\n" "${JOBS[@]}" | sort -t'|' -k1,1n -k2,2))
unset IFS

# Phase 3: emit. Stop as soon as we have MIN_CLIPS files on disk (counts both
# newly cut and pre-existing clips — keeps the script idempotent).
for job in "${SORTED[@]}"; do
  existing=$(count_existing)
  if (( existing >= MIN_CLIPS )); then
    echo "reached $existing clips (>= $MIN_CLIPS) — stopping."
    exit 0
  fi

  IFS='|' read -r idx_padded src start base <<<"$job"
  idx=$((10#$idx_padded))  # strip leading zeros, force base-10
  nn=$(printf "%02d" "$idx")
  out="$OUT_DIR/$base - clip$nn (${start}s).mp4"
  if [[ -f "$out" ]]; then
    echo "skip exists: $(basename "$out")"
    continue
  fi
  echo "cut  $(basename "$out")"
  ffmpeg -hide_banner -loglevel error -y \
    -ss "$start" -i "$src" -t "$CLIP_LEN" \
    -vf "$VF" \
    -c:v libx264 -crf 20 -preset veryfast \
    -c:a aac -b:a 160k \
    "$out"
done

final=$(count_existing)
echo "done — $final clips in $OUT_DIR"
if (( final < MIN_CLIPS )); then
  echo "warning: produced $final clips, target was $MIN_CLIPS — download more sources." >&2
  exit 2
fi
