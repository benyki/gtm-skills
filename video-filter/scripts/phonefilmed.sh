#!/usr/bin/env bash
# Simulate a phone-filmed-off-a-screen look: slight rotation, vignette, contrast,
# temporal noise, plus phone-mic-style audio EQ. Extremely effective disguise.
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

IN="${1:?usage: phonefilmed.sh /abs/path/input.mp4}"
OUT="${IN%.*}.phonefilmed.mp4"

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

CROP_W=$((W - 20))
CROP_H=$((H - 40))

"$FF" -y -i "$IN" \
  -vf "scale=${W}:${H},rotate=0.015:c=black:ow=rotw(0.015):oh=roth(0.015),crop=${CROP_W}:${CROP_H},scale=${W}:${H},eq=contrast=1.1:brightness=-0.02:saturation=0.9,noise=alls=10:allf=t,vignette=PI/4.5" \
  -af "highpass=f=200,lowpass=f=3500,acompressor=threshold=-20dB:ratio=4" \
  -c:v libx264 -crf 28 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 96k \
  -movflags +faststart \
  "$OUT"

echo "$OUT"
