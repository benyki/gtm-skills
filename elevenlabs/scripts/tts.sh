#!/usr/bin/env bash
#
# tts.sh — generate one audio file from one line of text.
#
# Usage:  VOICE=amelie scripts/tts.sh "Le texte à dire." out.mp3
#
# VOICE can be a key from references/voices.json (amelie|kevan|sara|adam|...)
# or a raw ElevenLabs voice_id. Env overrides: MODEL, OUTPUT_FORMAT, STABILITY,
# SIMILARITY, STYLE, SPEAKER_BOOST.
#
# Load the key first:  set -a; . .env.local; set +a
#
set -euo pipefail

TEXT="${1:?usage: tts.sh \"text\" out.mp3}"
OUT="${2:?usage: tts.sh \"text\" out.mp3}"
: "${ELEVENLABS_API_KEY:?Load it: set -a; . .env.local; set +a}"

HERE="$(cd "$(dirname "$0")" && pwd)"
VOICES="$HERE/../references/voices.json"

VOICE="${VOICE:-amelie}"
MODEL="${MODEL:-eleven_multilingual_v2}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-mp3_44100_128}"
STABILITY="${STABILITY:-0.45}"
SIMILARITY="${SIMILARITY:-0.80}"
STYLE="${STYLE:-0.0}"
SPEAKER_BOOST="${SPEAKER_BOOST:-true}"

# Resolve VOICE: if it's a known key use its id, else treat it as a raw id.
VOICE_ID="$(jq -r --arg v "$VOICE" '.voices[$v].voice_id // empty' "$VOICES" 2>/dev/null || true)"
[ -z "$VOICE_ID" ] && VOICE_ID="$VOICE"

body="$(jq -n --arg t "$TEXT" --arg m "$MODEL" \
  --argjson st "$STABILITY" --argjson sim "$SIMILARITY" \
  --argjson sty "$STYLE" --argjson sb "$SPEAKER_BOOST" \
  '{text:$t, model_id:$m, voice_settings:{stability:$st, similarity_boost:$sim, style:$sty, use_speaker_boost:$sb}}')"

http=$(curl -sS -w '%{http_code}' -X POST \
  "https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}?output_format=${OUTPUT_FORMAT}" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" -H "Content-Type: application/json" \
  -d "$body" -o "$OUT")

if [ "$http" != "200" ]; then echo "ERROR HTTP $http:"; cat "$OUT"; echo; exit 1; fi
echo "wrote $OUT  (voice=$VOICE id=$VOICE_ID model=$MODEL)"
