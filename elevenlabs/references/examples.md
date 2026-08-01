# Examples — what we build with ElevenLabs

Concrete recipes. Each points to a runnable script template in `../scripts/`.

## 1. Single line → audio file

One phrase, one voice. → `scripts/tts.sh`

```bash
set -a; . .env.local; set +a
VOICE=amelie scripts/tts.sh "Bonjour, je voudrais un café." out.mp3
```

## 2. List the account's voices

→ `scripts/list-voices.sh`

```bash
set -a; . .env.local; set +a
scripts/list-voices.sh            # id  name  language
```

## 3. Timed multi-line video audio (the flagship pattern)

"How do we say X in French?" TikTok-style: phrases at **exact timestamps**, with a
tick/clock SFX bed in each guess-gap. Because TTS has no intra-request timing, we:

1. Generate **one clip per line**.
2. Lay each clip onto a silent timeline at an absolute start with `ffmpeg adelay + amix`.
3. Mix a trimmed SFX into each gap.

→ Generic template: `scripts/timed-multiline.sh`
→ Full working instance: `~/code/<project>/video-app/scripts/french-phrases-tts/build.sh`

Key ffmpeg move — place `clip.mp3` at 4.6s on a silent base, summing without volume drop:

```bash
ffmpeg -i base.mp3 -i clip.mp3 \
  -filter_complex "[1:a]adelay=4600:all=1[d];[0:a][d]amix=inputs=2:normalize=0[out]" \
  -map "[out]" output.mp3
```

Trim a 5s SFX to 2.3s before placing it (so it fills the gap, not the next line):

```bash
[i:a]atrim=0:2.3,asetpts=PTS-STARTPTS,adelay=2000:all=1[di]
```

## 4. Captions from alignment

Use `/with-timestamps`, decode `audio_base64`, and turn `alignment.characters` +
`character_start_times_seconds` into SRT/ASS. (No script yet — build per project.)

## 5. Generate a missing SFX

When no file in `sound-effects.json` fits:

```bash
TMP=$(mktemp); trap 'rm -f "$TMP"' EXIT
jq -n '{text:"soft ticking clock, close mic", duration_seconds:4, prompt_influence:0.5}' > "$TMP"
curl -sS -X POST "https://api.elevenlabs.io/v1/sound-generation" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" -H "Content-Type: application/json" \
  --data-binary @"$TMP" -o new-sfx.mp3
```
