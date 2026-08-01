#!/usr/bin/env bash
# Heavy re-compression. Mimics TikTok/IG re-encoded UGC.
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

IN="${1:?usage: compressed.sh /abs/path/input.mp4}"
OUT="${IN%.*}.compressed.mp4"

"$FF" -y -i "$IN" \
  -c:v libx264 -crf 32 -preset veryfast \
  -b:v 1000k -maxrate 1200k -bufsize 1500k \
  -pix_fmt yuv420p \
  -c:a aac -b:a 64k -ac 2 \
  -movflags +faststart \
  "$OUT"

echo "$OUT"
