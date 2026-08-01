#!/usr/bin/env bash
# End-to-end: search Pinterest for <keyword> and download the first <count> videos into <out_dir>.
# Usage: search_and_download.sh "<keyword>" <count> <out_dir>
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "usage: $0 \"<keyword>\" <count> <out_dir>" >&2
  exit 2
fi

KEYWORD="$1"
COUNT="$2"
OUT_DIR="$3"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$OUT_DIR"

echo "[pinterest-download-videos] searching: \"$KEYWORD\" (count=$COUNT)" >&2
PIN_IDS=$(bash "$SKILL_DIR/scripts/search_pins.sh" "$KEYWORD" "$COUNT")

if [ -z "$PIN_IDS" ]; then
  echo "no pins found" >&2
  exit 1
fi

echo "[pinterest-download-videos] pins: $(echo "$PIN_IDS" | tr '\n' ' ')" >&2

while IFS= read -r PIN_ID; do
  [ -z "$PIN_ID" ] && continue
  echo "[pinterest-download-videos] downloading $PIN_ID" >&2
  bash "$SKILL_DIR/scripts/download_pin.sh" "$PIN_ID" "$OUT_DIR" || {
    echo "[pinterest-download-videos] WARN: failed $PIN_ID" >&2
  }
done <<< "$PIN_IDS"

echo "[pinterest-download-videos] done → $OUT_DIR" >&2
ls -1 "$OUT_DIR"/pinterest-*.mp4 2>/dev/null | tail -n "$COUNT"
