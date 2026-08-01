#!/usr/bin/env bash
# Vignette + slow breathing brightness + light grain. Darkens edges where AI fails.
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

IN="${1:?usage: vignette.sh /abs/path/input.mp4}"
OUT="${IN%.*}.vignette.mp4"

"$FF" -y -i "$IN" \
  -vf "vignette=PI/4,eq=brightness='0.05*sin(2*PI*t/3)':saturation=1.05,noise=alls=8:allf=t" \
  -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p \
  -c:a copy -movflags +faststart \
  "$OUT"

echo "$OUT"
