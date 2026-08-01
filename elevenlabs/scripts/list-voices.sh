#!/usr/bin/env bash
#
# list-voices.sh — list every voice on the account: id  name  language
#
# Load the key first:  set -a; . .env.local; set +a
#
set -euo pipefail
: "${ELEVENLABS_API_KEY:?Load it: set -a; . .env.local; set +a}"

curl -sS https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
| jq -r '.voices[] | "\(.voice_id)\t\(.name)\t\(.labels.language // .labels.accent // "-")"'
