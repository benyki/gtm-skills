#!/usr/bin/env bash
# Burn a viral-TikTok-style solid-box caption at ~25% from the top.
#
# Uses libass (ASS subtitles with BorderStyle=3 opaque box) rather than
# drawtext, because drawtext renders the newline character as the font's
# .notdef glyph (literally "NO GLYPH" in Inter), and libass also gives
# proper per-line boxes that hug each line of text — matching the
# reference screenshot style.
#
# Usage:
#   bash caption.sh /abs/path/input.mp4 "Your hook text"
#   bash caption.sh --style blue  /abs/path/input.mp4 "NEW ACTING CHALLENGE!"
#   bash caption.sh --style red   /abs/path/input.mp4 "Do Not Post on Instagram Until You See This Secret Hack"
#   bash caption.sh --style white /abs/path/input.mp4 "3 Natural Supplements to Reduce Appetite"
#   bash caption.sh --y 0.25 --wrap 18 --style blue /abs/path/input.mp4 "Text"
#
# Styles:
#   white  (default) — white box, black bold text
#   blue            — TikTok blue box,   white bold text
#   red             — bold red box,      white bold text
#
# Position: top of caption sits at --y * height (default 0.22).
# Wrapping: text is word-wrapped at --wrap chars per line (default 22).
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"
FP="${FFPROBE_BIN:-/opt/homebrew/bin/ffprobe}"

STYLE="white"
Y_FRAC="0.17"
WRAP=22
FONT_NAME="${CAPTION_FONT_NAME:-Inter}"

while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --style) STYLE="$2"; shift 2 ;;
    --y)     Y_FRAC="$2"; shift 2 ;;
    --wrap)  WRAP="$2"; shift 2 ;;
    --font)  FONT_NAME="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

IN="${1:?usage: caption.sh [--style white|blue|red] [--y 0.22] [--wrap 22] input.mp4 \"text\"}"
TEXT="${2:?caption text required}"
OUT="${IN%.*}.caption.mp4"

# ASS colors are &HAABBGGRR (alpha=00 means fully opaque).
# With BorderStyle=3 (opaque box), OutlineColour is the box fill — not BackColour.
case "$STYLE" in
  white) BOX_COLOR="&H00FFFFFF"; TEXT_COLOR="&H00000000" ;;
  blue)  BOX_COLOR="&H00FF8D3A"; TEXT_COLOR="&H00FFFFFF" ;;   # #3A8DFF
  red)   BOX_COLOR="&H004639E6"; TEXT_COLOR="&H00FFFFFF" ;;   # #E63946
  *) echo "unknown style: $STYLE (use white|blue|red)" >&2; exit 1 ;;
esac

read W H < <("$FP" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$IN" | tr 'x' ' ')

FONTSIZE=$(( W / 16 ))
[ "$FONTSIZE" -lt 28 ] && FONTSIZE=28

# Outline in BorderStyle=3 acts as box padding around the text.
PAD=$(( FONTSIZE / 2 ))

# Vertical margin: distance from top of frame to top of caption box.
# Using bash floating math via awk.
MARGIN_V=$(awk -v h="$H" -v y="$Y_FRAC" 'BEGIN { printf "%d", h * y }')

# Word-wrap text, then convert real newlines into ASS \N line breaks.
WRAPPED=$(printf "%s" "$TEXT" | fold -s -w "$WRAP" | sed 's/[[:space:]]*$//')
ASS_TEXT=$(printf "%s" "$WRAPPED" | awk 'BEGIN{ORS=""} {if (NR>1) printf "\\N"; print}')

ASS_FILE=$(mktemp -t caption.XXXXXX.ass)
trap 'rm -f "$ASS_FILE"' EXIT

# Note: in libass, Outline value gives padding inside the opaque box (BorderStyle=3).
# Alignment=8 = top-center. MarginV = pixels from top of PlayResY-sized canvas.
cat > "$ASS_FILE" <<EOF
[Script Info]
ScriptType: v4.00+
PlayResX: $W
PlayResY: $H
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,${FONT_NAME},${FONTSIZE},${TEXT_COLOR},&H000000FF,${BOX_COLOR},&H00000000,-1,0,0,0,100,100,0,0,3,${PAD},0,8,40,40,${MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,9:59:59.99,Hook,,0,0,0,,${ASS_TEXT}
EOF

# Escape filter path for ffmpeg filter graph.
ESCAPED_ASS=$(printf "%s" "$ASS_FILE" | sed "s/'/\\\\'/g")

"$FF" -y -i "$IN" \
  -vf "ass='${ESCAPED_ASS}'" \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a copy -movflags +faststart \
  "$OUT"

echo "$OUT"
