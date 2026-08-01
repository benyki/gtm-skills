#!/usr/bin/env bash
# add-music.sh — lay a background-music track under a video before posting to Buffer.
#
# Usage:
#   add-music.sh <video> [--music PATH | --catalog tiktok|french | --catalog DIR]
#                        [--volume 0.5] [--fade 1.0] [--out PATH] [--inplace]
#
# Behaviour:
#   * --music PATH   : use that exact audio file.
#   * --catalog NAME : pick a RANDOM track from a catalog folder.
#                        tiktok          -> ~/videos/music/tiktok/   (generic beds)
#                        french|spanish|italian|<lang>
#                                        -> ~/videos/music/geo/<lang>/  (language-specific)
#                        a path with a / -> that exact folder of audio files.
#   * default (no --music/--catalog): random track from ~/videos/music/tiktok/.
#
#   The music is looped to cover the full video, volume-scaled (default 0.5),
#   and faded out over the last --fade seconds. If the source video already has
#   audio (e.g. a voiceover), the music is mixed UNDER it; otherwise the music
#   becomes the audio track. Output length always matches the video.
#
#   By default writes "<video-stem>-music.mp4" next to the source and prints its
#   path on stdout (so you can feed it straight to `buffer.py post --file`).
#   Use --inplace to overwrite the original instead.
set -euo pipefail

CATALOG_TIKTOK="$HOME/clips/music/tiktok"
GEO_DIR="$HOME/clips/music/geo"   # per-language tracks live in geo/<language>/

VIDEO=""; MUSIC=""; CATALOG=""; VOL="0.5"; FADE="1.0"; OUT=""; INPLACE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --music)   MUSIC="$2"; shift 2 ;;
    --catalog) CATALOG="$2"; shift 2 ;;
    --volume)  VOL="$2"; shift 2 ;;
    --fade)    FADE="$2"; shift 2 ;;
    --out)     OUT="$2"; shift 2 ;;
    --inplace) INPLACE=1; shift ;;
    -*) echo "unknown flag: $1" >&2; exit 2 ;;
    *) VIDEO="$1"; shift ;;
  esac
done

[ -n "$VIDEO" ] || { echo "usage: add-music.sh <video> [--music PATH | --catalog tiktok|french|DIR] [--volume V] [--fade S] [--out PATH] [--inplace]" >&2; exit 2; }
VIDEO="${VIDEO/#\~/$HOME}"
[ -f "$VIDEO" ] || { echo "video not found: $VIDEO" >&2; exit 2; }

# Resolve the music file.
if [ -z "$MUSIC" ]; then
  case "$CATALOG" in
    ""|tiktok) DIR="$CATALOG_TIKTOK" ;;          # generic beds
    */*)       DIR="${CATALOG/#\~/$HOME}" ;;     # explicit path (has a slash)
    *)         DIR="$GEO_DIR/$CATALOG" ;;        # bare language name -> geo/<lang>
  esac
  [ -d "$DIR" ] || { echo "music catalog not found: $DIR" >&2; exit 2; }
  # Random pick across common audio extensions.
  MUSIC="$(find "$DIR" -maxdepth 1 -type f \( -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.wav' -o -iname '*.aac' -o -iname '*.ogg' \) | sort -R | head -1)"
  [ -n "$MUSIC" ] || { echo "no audio files in $DIR" >&2; exit 2; }
fi
MUSIC="${MUSIC/#\~/$HOME}"
[ -f "$MUSIC" ] || { echo "music not found: $MUSIC" >&2; exit 2; }

# Output path.
if [ "$INPLACE" -eq 1 ]; then
  OUT="$VIDEO"
elif [ -z "$OUT" ]; then
  OUT="${VIDEO%.*}-music.mp4"
fi
OUT="${OUT/#\~/$HOME}"

DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO")"
FADE_START="$(awk -v t="$DUR" -v f="$FADE" 'BEGIN{s=t-f; if(s<0)s=0; print s}')"
HAS_AUDIO="$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$VIDEO" | head -1)"

# Loop the music to cover the video, trim to length, scale volume, fade out.
MUSIC_CHAIN="atrim=0:${DUR},asetpts=PTS-STARTPTS,volume=${VOL},afade=t=out:st=${FADE_START}:d=${FADE}"

TMP_OUT="$(mktemp -u "${TMPDIR:-/tmp}/addmusic-XXXXXX").mp4"
if [ "$HAS_AUDIO" = "audio" ]; then
  # Mix music UNDER the existing audio (keeps voiceover on top).
  ffmpeg -hide_banner -loglevel error -y \
    -i "$VIDEO" -stream_loop -1 -i "$MUSIC" \
    -filter_complex "[1:a]${MUSIC_CHAIN}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0:weights=1 ${VOL}[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$TMP_OUT"
else
  # No source audio — music becomes the track.
  ffmpeg -hide_banner -loglevel error -y \
    -i "$VIDEO" -stream_loop -1 -i "$MUSIC" \
    -filter_complex "[1:a]${MUSIC_CHAIN}[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$TMP_OUT"
fi

mv -f "$TMP_OUT" "$OUT"
echo "$OUT"
