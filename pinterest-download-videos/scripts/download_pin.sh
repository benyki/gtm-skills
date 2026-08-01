#!/usr/bin/env bash
# Download a single Pinterest video pin into <out_dir>.
# Usage: download_pin.sh <pin_id> <out_dir>
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: $0 <pin_id> <out_dir>" >&2
  exit 2
fi

PIN_ID="$1"
OUT_DIR="$2"
mkdir -p "$OUT_DIR"

cd "$OUT_DIR"
yt-dlp \
  --no-warnings \
  --no-progress \
  -o "pinterest-%(id)s.%(ext)s" \
  "https://www.pinterest.com/pin/${PIN_ID}/"
