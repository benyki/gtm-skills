# ElevenLabs API reference

Base URL: `https://api.elevenlabs.io`
Auth header (every request): `xi-api-key: $ELEVENLABS_API_KEY`

## Features we use

| Feature | Endpoint | Purpose |
|---------|----------|---------|
| Text to Speech | `POST /v1/text-to-speech/{voice_id}` | Generate speech (returns audio bytes) |
| TTS w/ timestamps | `POST /v1/text-to-speech/{voice_id}/with-timestamps` | Audio + per-character alignment (for captions) |
| TTS streaming | `POST /v1/text-to-speech/{voice_id}/stream` | Low-latency streamed audio |
| Sound effects | `POST /v1/sound-generation` | Generate a sound effect from a text prompt |
| List voices | `GET /v1/voices` | All voices on the account |
| Get voice | `GET /v1/voices/{voice_id}` | One voice's metadata/settings |
| Models | `GET /v1/models` | Available models + language support |
| User / quota | `GET /v1/user/subscription` | Remaining character quota |

## Text to Speech — request body

```json
{
  "text": "Bonjour le monde.",
  "model_id": "eleven_multilingual_v2",
  "language_code": "fr",
  "voice_settings": {
    "stability": 0.45,
    "similarity_boost": 0.80,
    "style": 0.0,
    "use_speaker_boost": true,
    "speed": 1.0
  }
}
```

- `text` — the words to speak (required).
- `model_id` — see Models below.
- `language_code` — optional ISO code; enforces a language (supported on some models).
- `voice_settings` — optional; omit to use the voice's saved defaults.

### voice_settings fields

| Field | Range | Effect |
|-------|-------|--------|
| `stability` | 0.0–1.0 | Low = more expressive/variable, high = flatter/consistent. ~0.4–0.5 typical. |
| `similarity_boost` | 0.0–1.0 | Adherence to the original voice timbre. ~0.75–0.85 typical. |
| `style` | 0.0–1.0 | Style exaggeration (v2+). Higher = more dramatic, slower. 0 for clean reads. |
| `use_speaker_boost` | bool | Boosts similarity to the speaker. Usually `true`. |
| `speed` | 0.7–1.2 | Playback speed (where supported). 1.0 = natural. |

## Models

| `model_id` | When |
|------------|------|
| `eleven_multilingual_v2` | **Default.** Mixed-language scripts (e.g. EN question + FR answer). High quality. |
| `eleven_turbo_v2_5` | Fast + cheaper, single language, ~32 languages. |
| `eleven_flash_v2_5` | Lowest latency (real-time). |
| `eleven_v3` | Highest expressiveness (alpha). Hero clips. |

## Output formats (`?output_format=`)

Query param on TTS endpoints. We default to `mp3_44100_128`.

| Value | Notes |
|-------|-------|
| `mp3_44100_128` | **Default.** 44.1kHz / 128kbps MP3. |
| `mp3_44100_192` | Higher-bitrate MP3 (needs paid tier). |
| `pcm_44100` | Raw PCM, for further DSP. |
| `pcm_16000` / `pcm_24000` | Lower-rate PCM. |
| `ulaw_8000` | Telephony. |

## Sound effects — `POST /v1/sound-generation`

```json
{
  "text": "soft ticking clock, close mic",
  "duration_seconds": 4,
  "prompt_influence": 0.5
}
```
Returns audio bytes. `duration_seconds` 0.5–22 (or omit to auto-pick). Use this only when no suitable file exists in `sound-effects.json`.

## Response handling

- TTS / sound-generation: the **response body is the raw audio** — write straight to a file (`curl -o out.mp3`).
- `with-timestamps`: returns JSON `{ "audio_base64": "...", "alignment": {...} }` — decode base64 for audio, use `alignment` for captions.
- Errors: non-200 returns JSON `{ "detail": ... }`. Always check the HTTP status (`curl -w '%{http_code}'`).

## Limits / gotchas

- Quota is billed per **character** of `text`. Check with `GET /v1/user/subscription`.
- Timing **cannot** be controlled inside one request — for fixed timestamps, generate per-line clips and place them with ffmpeg (see `examples.md`).
- Some output formats / `language_code` require specific models or paid tiers.
