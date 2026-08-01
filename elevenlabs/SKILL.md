---
name: elevenlabs
description: ElevenLabs text-to-speech & sound generation — features, command/script templates, and our voice IDs + SFX. Use before any ElevenLabs API call, when picking a voice, or when building timed/voiceover audio.
---

# ElevenLabs

Generate speech and sound effects via the ElevenLabs API. This skill is modular:
**SKILL.md = how (features + templates)**, **`references/` = data (voices, SFX, full
API) + examples**, **`scripts/` = runnable command templates**.

## When to use

- Any text-to-speech / voiceover (single line or full scripts).
- Picking a voice — use our defaults from `references/voices.json`, don't invent IDs.
- Timed multi-line audio (language videos, "how do we say X" formats) with SFX beds.
- Generating a sound effect from a prompt.

## Secrets (always first)

The key lives in `.env.local`. Load it into the process env — never echo or hardcode:

```bash
set -a; . .env.local; set +a
```

(Use the `local-secrets` skill rules. Verify without revealing: `[[ -n "$ELEVENLABS_API_KEY" ]] && echo set`.)

## Features at a glance

| Feature | How |
|---------|-----|
| Single line → file | `scripts/tts.sh` |
| List account voices | `scripts/list-voices.sh` |
| Timed multi-line + SFX | `scripts/timed-multiline.sh` (config-driven) |
| Sound effect from prompt | `POST /v1/sound-generation` (see `references/api-reference.md`) |
| Captions / alignment | `/with-timestamps` (see `references/examples.md` §4) |

Full endpoint list, models, output formats, and `voice_settings` semantics:
→ **`references/api-reference.md`**

## Command templates

**One line of speech** (VOICE = key from voices.json or a raw id):
```bash
set -a; . .env.local; set +a
VOICE=amelie scripts/tts.sh "Bonjour, je voudrais un café." out.mp3
```

**Raw curl** (the underlying call — body via jq so apostrophes are safe):
```bash
body="$(jq -n --arg t "Le texte." --arg m "eleven_multilingual_v2" \
  '{text:$t, model_id:$m, voice_settings:{stability:0.45, similarity_boost:0.80, style:0.0, use_speaker_boost:true}}')"
curl -sS -X POST "https://api.elevenlabs.io/v1/text-to-speech/$VOICE_ID?output_format=mp3_44100_128" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" -H "Content-Type: application/json" \
  -d "$body" -o out.mp3
```

**Timed multi-line video audio** (phrases at exact timestamps + tick bed):
```bash
set -a; . .env.local; set +a
scripts/timed-multiline.sh my-config.json out.mp3   # DRY_RUN=1 for a free silent test
```

## Data (never hardcode — read these)

- **Voices & defaults** → `references/voices.json`
  Defaults: FR female = **Amelie**, FR male = **Kevan**, EN female = Sara, EN male = Adam.
  Resolve a key to an id: `jq -r '.voices.amelie.voice_id' references/voices.json`.
- **Sound effects** → `references/sound-effects.json` (in `~/.agents/skills/elevenlabs/assets/sounds/`)
  Default guess-pause bed = **clock-tac-soft.mp3** (5s; trim to ~2.3s per gap).

## Defaults we use

- Model: `eleven_multilingual_v2` (mixed EN+FR). Output: `mp3_44100_128`.
- voice_settings: stability 0.45, similarity 0.80, style 0.0, speaker_boost true.

## Key principle — timing

TTS has **no intra-request timing control**. For fixed timestamps, generate one clip
per line and place each with `ffmpeg adelay + amix` (`normalize=0` to sum cleanly).
Full recipe + working instance in **`references/examples.md`**.

## Returning media

After producing an audio/video file, include an embedded play command, e.g.:
```bash
afplay /absolute/path/to/out.mp3
```
