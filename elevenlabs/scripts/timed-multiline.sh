#!/usr/bin/env bash
#
# timed-multiline.sh — place many TTS lines at EXACT timestamps, with an SFX bed
# in each gap. The flagship "How do we say X?" pattern, generalized & config-driven.
#
# Why per-line: ElevenLabs has no intra-request timing control. So we generate one
# clip per line and lay each onto a silent timeline with ffmpeg (adelay + amix).
#
# Usage:   set -a; . .env.local; set +a
#          scripts/timed-multiline.sh config.json out.mp3
#
# config.json shape:
# {
#   "voice": "amelie",                  // key from references/voices.json or raw id
#   "model": "eleven_multilingual_v2",
#   "total_seconds": 61,
#   "sfx": { "file": "clock-tac-soft.mp3", "trim_s": 2.3, "starts": [2.0, 8.0] },
#   "lines": [ { "id":"q1", "start":0.0, "text":"How do we say ...?" }, ... ]
# }
# sfx.file is looked up in ~/.agents/skills/elevenlabs/assets/sounds/ (or an absolute path).
# Omit "sfx" for a clean voice-only timeline.
#
# DRY_RUN=1 makes silent placeholder clips (no API calls) so you can test assembly.
#
set -euo pipefail

CONFIG="${1:?usage: timed-multiline.sh config.json out.mp3}"
FINAL="${2:?usage: timed-multiline.sh config.json out.mp3}"
DRY_RUN="${DRY_RUN:-0}"

HERE="$(cd "$(dirname "$0")" && pwd)"
VOICES="$HERE/../references/voices.json"
SOUNDS_DIR="$HOME/code/_shared/medias/sounds"

VOICE="$(jq -r '.voice // "amelie"' "$CONFIG")"
MODEL="$(jq -r '.model // "eleven_multilingual_v2"' "$CONFIG")"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-mp3_44100_128}"
TOTAL="$(jq -r '.total_seconds // 61' "$CONFIG")"
VOICE_ID="$(jq -r --arg v "$VOICE" '.voices[$v].voice_id // empty' "$VOICES")"; [ -z "$VOICE_ID" ] && VOICE_ID="$VOICE"

CLIPS="$(dirname "$FINAL")/clips"; mkdir -p "$CLIPS"

# --- Step 1: one clip per line -------------------------------------------------
echo ">> generating clips (DRY_RUN=$DRY_RUN, voice=$VOICE)"
n=$(jq '.lines | length' "$CONFIG")
for ((k=0; k<n; k++)); do
  id="$(jq -r ".lines[$k].id" "$CONFIG")"
  text="$(jq -r ".lines[$k].text" "$CONFIG")"
  out="$CLIPS/$id.mp3"
  if [ "$DRY_RUN" = "1" ]; then
    ffmpeg -hide_banner -loglevel error -y -f lavfi -i "anullsrc=r=44100:cl=stereo" -t 1.5 -c:a libmp3lame -q:a 4 "$out"
  else
    : "${ELEVENLABS_API_KEY:?Load it: set -a; . .env.local; set +a}"
    body="$(jq -n --arg t "$text" --arg m "$MODEL" \
      '{text:$t, model_id:$m, voice_settings:{stability:0.45, similarity_boost:0.80, style:0.0, use_speaker_boost:true}}')"
    http=$(curl -sS -w '%{http_code}' -X POST \
      "https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}?output_format=${OUTPUT_FORMAT}" \
      -H "xi-api-key: ${ELEVENLABS_API_KEY}" -H "Content-Type: application/json" -d "$body" -o "$out")
    [ "$http" != "200" ] && { echo "ERROR $id HTTP $http"; cat "$out"; exit 1; }
  fi
  printf '   %-6s @ %ss  "%s"\n' "$id" "$(jq -r ".lines[$k].start" "$CONFIG")" "$text"
done

# --- Step 2: lay clips + SFX onto a silent timeline ----------------------------
inputs=(); filters=(); mixlabels=""; i=0
add_clip() { # file start [trim] [volume]
  local ms; ms=$(awk "BEGIN{printf \"%d\", $2*1000}")
  local volf=""; [ -n "${4:-}" ] && volf=",volume=${4}"   # optional per-clip gain (default: unchanged)
  if [ -n "${3:-}" ]; then filters+=("[$i:a]atrim=0:${3},asetpts=PTS-STARTPTS,adelay=${ms}:all=1${volf}[d$i]")
  else filters+=("[$i:a]adelay=${ms}:all=1${volf}[d$i]"); fi
  inputs+=(-i "$1"); mixlabels+="[d$i]"; i=$((i+1))
}

for ((k=0; k<n; k++)); do
  add_clip "$CLIPS/$(jq -r ".lines[$k].id" "$CONFIG").mp3" "$(jq -r ".lines[$k].start" "$CONFIG")"
done

if [ "$(jq -r 'has("sfx")' "$CONFIG")" = "true" ]; then
  sfx_file="$(jq -r '.sfx.file' "$CONFIG")"; [ "${sfx_file:0:1}" = "/" ] || sfx_file="$SOUNDS_DIR/$sfx_file"
  sfx_trim="$(jq -r '.sfx.trim_s // empty' "$CONFIG")"
  sfx_vol="$(jq -r '.sfx.volume // empty' "$CONFIG")"   # optional sfx gain (e.g. 0.7 = 30% quieter); voice unaffected
  if [ -f "$sfx_file" ]; then
    for s in $(jq -r '.sfx.starts[]' "$CONFIG"); do add_clip "$sfx_file" "$s" "$sfx_trim" "$sfx_vol"; done
  else echo "   (sfx not found: $sfx_file — skipping)"; fi
fi

graph="$(IFS=';'; echo "${filters[*]}");${mixlabels}amix=inputs=${i}:normalize=0:dropout_transition=0[mix];[mix]apad,atrim=0:${TOTAL},aformat=channel_layouts=stereo[out]"
ffmpeg -hide_banner -loglevel error -y "${inputs[@]}" -filter_complex "$graph" -map "[out]" -c:a libmp3lame -q:a 2 "$FINAL"
echo ">> wrote $FINAL ($(ffprobe -hide_banner -i "$FINAL" 2>&1 | grep -oE 'Duration: [0-9:.]+'))"
