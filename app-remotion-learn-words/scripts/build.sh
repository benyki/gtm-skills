#!/usr/bin/env bash
#
# build.sh BASE [OVERRIDES.json] [out.mp4]
#
#   BASE        a config, or a templates/<lang>.json (look, voice, flags, character, phrases)
#   OVERRIDES   optional JSON deep-merged on top of BASE (e.g. your own items[] + tweaks)
#   out.mp4     optional output path (default: ./series-a.mp4)
#
# Back-compat: `build.sh config.json [out.mp4]` (the cron form) still works — a single
# .json BASE with an optional .mp4 OUT, no template needed.
#
# End-to-end Remotion "learn words" video:
#   ElevenLabs voiceover (+ hardcoded clock tick) -> Pexels/explicit/fallback background
#   -> real flag strip -> props.json -> Remotion render (~10MB).
#
# Run from a repo whose .env.local has ELEVENLABS_API_KEY and PEXELS_API_KEY.
#
set -euo pipefail

SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(dirname "$SCRIPTS")"
REM="$SKILL/remotion"
PUB="$REM/public"
ASSETS="$SKILL/assets"          # reusable Pexels image cache + flags/ + fonts/
WORDS="$SKILL/references/words-done.json"
EL="$HOME/.agents/skills/elevenlabs/scripts/timed-multiline.sh"
# Tick sound for the guess gap. Override with CLOCK=/abs/path/tick.mp3, or drop
# any short tick at assets/sounds/clock-tick.mp3.
CLOCK="${CLOCK:-$ASSETS/sounds/clock-tick.mp3}"

# --- args: BASE required; a *.json 2nd/3rd arg is OVERRIDES, anything else is OUT ---
BASE="${1:?usage: build.sh BASE [OVERRIDES.json] [out.mp4]}"
OVERRIDES=""; OUT=""
for arg in "${2:-}" "${3:-}"; do
  [ -z "$arg" ] && continue
  case "$arg" in
    *.json) OVERRIDES="$arg" ;;
    *)      OUT="$arg" ;;
  esac
done
OUT="${OUT:-$(pwd)/series-a.mp4}"

set -a; [ -f .env.local ] && . "$PWD/.env.local"; set +a

# --- merge BASE + OVERRIDES (deep merge; overrides win, arrays replaced) ---
MERGED=$(mktemp); NORM=$(mktemp); trap 'rm -f "$MERGED" "$NORM"' EXIT
if [ -n "$OVERRIDES" ]; then
  jq -s '.[0] * .[1]' "$BASE" "$OVERRIDES" > "$MERGED"
else
  cp "$BASE" "$MERGED"
fi

# 0) normalize: a config only needs language + per-item {prompt, answer}
#    (legacy {en, fr} still read). Everything below is derived unless set explicitly:
#      q       -> i * cadence.gap            (default gap 6.5s)
#      a       -> q + cadence.guess          (default guess 4.6s)
#      q_text  -> "How do we say <prompt> in <language>?"
#      a_text  -> answer, with terminal . added if it has none
#      total_seconds -> last a + 5
jq '
  (.language // "French") as $lang
  | (.cadence.gap // 6.5) as $gap
  | (.cadence.guess // 4.6) as $guess
  | ([ .items | to_entries[] | .key as $i | .value
       | (.prompt // .en // "") as $prompt
       | (.answer // .fr // "") as $answer
       | (.native // .kana // "") as $native
       | ((.q // ($i * $gap)) * 10 | round / 10) as $q
       | ((.a // ($q + $guess)) * 10 | round / 10) as $a
       | { id: ($i + 1), q: $q, a: $a, prompt: $prompt, answer: $answer, native: $native,
           q_text: (.q_text // ("How do we say " + ($prompt | gsub("[?.!]+$";"")) + " in " + $lang + "?")),
           a_text: (.a_text // ((if $native != "" then $native else $answer end) | if test("[.!?…。]$") then . else . + "." end)) } ]) as $items
  | . + { items: $items, total_seconds: (.total_seconds // (($items[-1].a) + 5 | round)) }
' "$MERGED" > "$NORM"

# 1) validate: no prompt/answer over 44 chars (≈ two wrapped lines of 22); warn on repeats
echo ">> [0/4] validate"
toolong=$(jq -r '.items[] | (.prompt, .answer) | select((. | length) > 44) | "  • (\(.|length)) \(.)"' "$NORM")
if [ -n "$toolong" ]; then
  echo "ERROR: these exceed 44 characters — shorten them:"; echo "$toolong"; exit 1
fi
if [ -f "$WORDS" ]; then
  dups=$(jq -r --slurpfile w "$WORDS" '
    ($w[0].phrases | map((.answer // .fr) | ascii_downcase)) as $done
    | .items[] | select((.answer | ascii_downcase) as $f | $done | index($f)) | "  • \(.answer)"' "$NORM")
  [ -n "$dups" ] && { echo "NOTE: already in words-done.json (possible repeat):"; echo "$dups"; }
fi

# 2) audio timeline (question + answer at q/a, clock in each gap)
#    REUSE_AUDIO=/path/to.mp3 reuses an existing track (e.g. re-skinning the overlay
#    on an already-rendered video) and skips ElevenLabs — the config is unchanged so
#    the derived timing still lines up. Default (unset) regenerates as before.
echo ">> [1/4] audio (ElevenLabs + clock tick)"
if [ -n "${REUSE_AUDIO:-}" ] && [ -f "${REUSE_AUDIO:-}" ]; then
  echo "   reusing existing audio: $REUSE_AUDIO (skipping ElevenLabs)"
  cp "$REUSE_AUDIO" "$PUB/audio.mp3"
else
  jq --arg clock "$CLOCK" '{
    voice: (.voice // "amelie"),
    model: (.model // "eleven_multilingual_v2"),
    total_seconds: .total_seconds,
    sfx: { file: $clock, trim_s: 2.3, volume: 0.7, starts: [ .items[] | (.q + 2.0) ] },
    lines: [ .items[] | ( {id:("q"+(.id|tostring)), start:.q, text:.q_text},
                          {id:("a"+(.id|tostring)), start:.a, text:.a_text} ) ]
  }' "$NORM" > "$PUB/audio.json"
  bash "$EL" "$PUB/audio.json" "$PUB/audio.mp3"
fi
char_src=$(eval echo "$(jq -r '.character' "$NORM")")

# 3) background -> public/bg.jpg  (explicit path > pexels query > versatile fallback)
echo ">> [2/4] background"
bg_path=$(jq -r '.background_image // empty' "$NORM")
bg_query=$(jq -r '.bg_query // empty' "$NORM")
lang=$(jq -r '(.language // "french") | ascii_downcase' "$NORM")
fbdir="$ASSETS/versatile-$lang"; [ -d "$fbdir" ] || fbdir="$ASSETS/versatile-french"
pick_fallback(){ local f=("$fbdir"/*.jpg); [ -e "${f[0]}" ] || return 0; printf '%s\n' "${f[RANDOM % ${#f[@]}]}"; }
if [ -n "$bg_path" ]; then
  cp "$(eval echo "$bg_path")" "$PUB/bg.jpg"
elif [ -n "$bg_query" ]; then
  bash "$SCRIPTS/fetch_bg.sh" "$bg_query" "$PUB/bg.jpg" "$ASSETS" \
    || { fb=$(pick_fallback); [ -z "$fb" ] && { echo "fetch failed and no fallback"; exit 1; }; echo "fetch failed; fallback -> $(basename "$fb")"; cp "$fb" "$PUB/bg.jpg"; }
else
  fb=$(pick_fallback); [ -z "$fb" ] && { echo "config needs background_image or bg_query (no versatile fallback found)"; exit 1; }
  echo "no background specified; fallback -> $(basename "$fb")"; cp "$fb" "$PUB/bg.jpg"
fi

# 4) flags -> public/flags/<code>.png  (real images from flagcdn.com, cached in assets/flags/)
echo ">> [2.5/4] flags"
rm -rf "$PUB/flags"; mkdir -p "$PUB/flags" "$ASSETS/flags"
avail_codes=""
for code in $(jq -r '(.flags // [])[] | ascii_downcase' "$NORM"); do
  cache="$ASSETS/flags/$code.png"
  if [ ! -f "$cache" ]; then
    echo "  flag: $code"
    curl -sS "https://flagcdn.com/w160/$code.png" -o "$cache" 2>/dev/null || rm -f "$cache"
  fi
  if [ -f "$cache" ]; then cp "$cache" "$PUB/flags/$code.png"; avail_codes="$avail_codes $code"; fi
done
flags_arr=$(printf '%s' "$avail_codes" | tr ' ' '\n' | jq -R . | jq -s 'map(select(length>0))')

# 5) fonts -> public/fonts/<file>  (optional extra faces for non-Latin scripts)
rm -rf "$PUB/fonts"; mkdir -p "$PUB/fonts"
for f in $(jq -r '(.fonts // [])[]' "$NORM"); do
  src="$(eval echo "$f")"; [ -f "$src" ] || src="$ASSETS/fonts/$(basename "$f")"
  if [ -f "$src" ]; then cp "$src" "$PUB/fonts/$(basename "$f")"; else echo "  WARN: font not found: $f"; fi
done
fonts_arr=$(jq -c '[ (.fonts // [])[] | split("/") | last ]' "$NORM")

# 6) character -> public/character.png  +  props.json
echo ">> [3/4] assets + props"
cp "$char_src" "$PUB/character.png"
jq --argjson flags "$flags_arr" --argjson fonts "$fonts_arr" '{
  totalSeconds: .total_seconds,
  character: "character.png", background: "bg.jpg", audio: "audio.mp3",
  outro: (.outro // "Follow me to learn a language every day"),
  flag: (.flag // {left:"#0055A4", mid:"#ffffff", right:"#EF4135"}),
  flags: $flags,
  fonts: $fonts,
  items: [ .items[] | {q, a, prompt, answer, native} ]
}' "$NORM" > "$REM/props.json"

# 7) render (~10MB)
echo ">> [4/4] render"
cd "$REM"
[ -d node_modules ] || pnpm install --ignore-workspace
pnpm exec remotion render LearnWords "$OUT" \
  --props=props.json --video-bitrate=1100k --audio-bitrate=128k --concurrency=4

# 7.5) inputs sidecar: <out>.json next to the rendered mp4, same stem. This is the
#      single record of what produced the clip; the posting step carries it into
#      published/ (see upload_post.py _archive) so viewers find published/<stem>.json.
#      Mirrors videos-lockscreen's snapshot. words[] = {prompt, answer,
#      native?} — native (Japanese/CJK script) is carried when the item has it, so
#      downstream viewers get the on-screen script, not just the romaji.
SNAP="${OUT%.mp4}.json"
jq --arg out "$OUT" '{
  timestamp: (now | todate),
  language: (.language // "French"),
  output: $out,
  duration: .total_seconds,
  bg_query: (.bg_query // null),
  outro: (.outro // null),
  words: [ .items[] | {prompt, answer} + (if (.native // "") != "" then {native} else {} end) ],
  config: .
}' "$NORM" > "$SNAP"
echo ">> snapshot: $SNAP"

# 8) record phrases into the registry (dedupe by language + answer, case-insensitive)
if [ -f "$WORDS" ]; then
  set_name=$(basename "${OVERRIDES:-$BASE}" .json | sed 's/-config$//')
  tmp=$(mktemp)
  jq --slurpfile cfg "$NORM" --arg set "$set_name" '
    .phrases += ($cfg[0].items | map({set:$set, language:($cfg[0].language // "French"), prompt, answer}))
    | .phrases |= unique_by(((.language // "French") + "|" + ((.answer // .fr) | ascii_downcase)))
  ' "$WORDS" > "$tmp" && mv "$tmp" "$WORDS"
  echo ">> registry updated: $WORDS"
fi
echo ">> done: $OUT"
