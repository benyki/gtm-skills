---
name: app-remotion-learn-words
description: Render a 9:16 TikTok-style "how do we say X in [language]?" vocab video for your project using Remotion (React) — stacked English prompts, a per-word green progress bar (starts 1.5s in) + clock tick during the guess gap, then the translation revealed in green, over a slow zoom+pan background with a character and a real flag strip. Modular & multi-language: pick a template (France, Spain, …) or supply your own; a config needs only language + {prompt, answer} pairs. THIS IS THE CANONICAL / PRODUCTION series-a skill. Use when the user says "make a series-a video", "remotion learn words", "how-do-we-say video", or gives words/phrases (or a TikTok link) to turn into this format in any language.
---

# vocab-remotion

Remotion (React) version of the series-a video, and the **canonical / production**
one (the nightly cron uses it). Smooth animated progress bar via `interpolate`, CSS
layout, real flag images, slow zoom + left→right pan, rendered with headless Chromium.

**Modular by language.** One engine, per-language **templates** under `templates/`. A
template fixes the look (flags, character, voice, outro, background fallback) and ships
demo phrases; you override `items[]` with your own. Adding a language = one template file.

## A config is just this

The **only required** fields are `language` and a list of `{prompt, answer}` pairs
(legacy `{en, fr}` is still accepted). The skill derives all timing, the spoken lines,
the duration, and falls back for the background.

```json
{
  "language": "Spanish",
  "voice": "melissa",
  "character": "~/code/<project>/assets/universe/latina-2-no-bg.png",
  "flags": ["mx", "co", "ar", "us", "es"],
  "bg_query": "spanish market",
  "outro": "Follow me to learn Spanish every day",
  "items": [
    { "prompt": "Good morning", "answer": "Buenos días" },
    { "prompt": "How much is it?", "answer": "¿Cuánto cuesta?" }
  ]
}
```

`prompt` = phrase shown on screen (English). `answer` = translation revealed in green.
(9 items is the sweet spot; each `prompt`/`answer` must be ≤44 chars.)

## Editorial guidance (what makes a good video)

These are content rules, independent of language. Follow them whether you're rendering the
demo phrases, a one-off request, or mass-producing a library.

- **One concept per video — never blend distant themes.** A "food" video is *all* food; a
  "love" video is *all* love. Do not mix love + food (or greetings + directions, etc.) in one
  clip — a single coherent theme reads clearly and the viewer knows what they're learning.
- **The background must match the concept.** Food → a food scene; love → a romantic scene
  (couple / sunset / cherry blossom); city life → a street scene. A mismatched backdrop (e.g.
  raw meat behind "I love you") looks broken. Set `bg_query` to fit the theme, and confirm it
  returns an on-theme image (a curated `versatile-<language>` pool catches Pexels misses so you
  never pull a wrong-country/off-topic image).
- **Broad, universally-appealing topics are worth MANY videos each — mine them repeatedly with
  FRESH words.** Food, love & dating, greetings, going out, emotions, K-drama/K-pop, family,
  friendship, compliments are evergreen: it's better to make 50 food videos (each 9 *new* words)
  than to reach for one obscure one-off theme. Repetition of a proven topic beats novelty of a
  weak one. Split a big topic into granular sub-themes (fruits, bbq, noodles, street food,
  coffee, desserts, ordering, delivery…) so each video stays distinct.
- **Within a single video all 9 words must be distinct.** Across videos, default to fresh
  vocabulary so a viewer bingeing your food videos keeps learning — but it's fine to deliberately
  re-use a word that performed really well before. (`references/words-done.json` tracks what's
  been used if you want to check, but treat it as a guide, not a hard block.)
- **Bias to what people care about, not dry utility.** Favor food, love, emotions, nightlife,
  pop culture over airport/paperwork/utility vocab. Keep each phrase real, natural, spoken
  language at a consistent politeness level.

(A worked example of this at scale: the Korean workspace `~/code/<project>/world/videos/
series-a-ko/configs/` ships **50 food** + **12 love** single-concept configs, each with a
theme-matched background — see `references/GENERATE-korean.md`.)

## Run

```bash
# from a repo whose .env.local has ELEVENLABS_API_KEY and PEXELS_API_KEY

# a template's built-in demo phrases:
bash ~/.agents/skills/vocab-remotion/scripts/build.sh templates/spain.json out.mp4

# a template + your own phrases (overrides deep-merged on top):
bash ~/.agents/skills/vocab-remotion/scripts/build.sh \
     templates/spain.json my-phrases.json out.mp4

# back-compat (the cron form) — a single config, no template:
bash ~/.agents/skills/vocab-remotion/scripts/build.sh my-config.json out.mp4
```

`build.sh BASE [OVERRIDES.json] [out.mp4]`:
1. **Merge** — deep-merges OVERRIDES onto BASE (`items[]` replaced by yours). One `.json`
   arg = BASE only; a 2nd `.json` = overrides; a non-`.json` arg = output path.
2. **Normalize** — derives `q`/`a` cadence, `q_text`/`a_text`, `total_seconds` (see Inputs).
3. **Audio** — `elevenlabs` `timed-multiline.sh` (voice at `q`/`a` + clock tick) → `public/audio.mp3`.
4. **Background** — explicit path > Pexels `bg_query` > curated `versatile-<language>` fallback.
5. **Flags** — downloads real PNGs from flagcdn.com → `public/flags/` (cached in `assets/flags/`).
6. **Props + render** — writes `props.json`, `remotion render LearnWords … --video-bitrate=1100k` (~6–10MB).

Preview/iterate live: `cd remotion && pnpm exec remotion studio`.

## Templates

- `templates/france.json` — french-no-bg, `flags:["fr"]`, voice **amelie**.
- `templates/spain.json` — latina, `flags:["mx","co","ar","us","es"]`, voice **melissa**,
  Spanish background fallback pool.
- `templates/japan.json` — chinese-girl, `flags:["jp"]`, voice **kazuha**. Dual-script:
  `answer` = romaji (green), `native` = Japanese script beneath; voiceover reads the native.
  `fonts:[]` (OS CJK fallback). 7 items. Refs: `references/GENERATE-japanese.md`, `POST-japanese.md`.
- `templates/arabic.json` — middle-east character, `flags:["eg","lb","jo","sy","ps"]` (multi-country
  row = "many dialects"), voice **salma** (Levantine female), `model eleven_multilingual_v2`. Dual-script
  RTL: `answer` = transliteration (green, keep ≤13 chars), `native` = **Arabic script** beneath (RTL,
  joined via bundled `fonts:["Cairo.ttf"]`); voiceover reads the native Arabic. MIXES Egyptian +
  Levantine everyday vocab, never labelled on screen. `versatile-arabic` fallback pool. 7 items.
  Refs: `references/GENERATE-arabic.md`, `POST-arabic.md`.
- `templates/korea.json` — chinese-girl (same as japan), `flags:["kr"]`, voice **hanabad**
  (Seoul female), `model eleven_multilingual_v2`. Dual-script: `answer` = Revised Romanization
  (green, keep ≤13 chars = one line), `native` = **Hangul** beneath; voiceover reads the native
  Hangul. `fonts:[]` (OS CJK fallback — no tofu, verified). `versatile-korean` fallback pool.
  9 items. Refs: `references/GENERATE-korean.md`, `POST-korean.md`.
- New language = copy a template; set `language`, `voice`, `character`, `flags`, `outro`,
  `bg_query`; set `fonts` if the script isn't Latin (see Fonts); supply `items[]`.

## Flags

- `flags`: list of ISO-3166 alpha-2 codes → **real flag images**, centered row at top
  (a list of one = a single flag). Cached after first download; offline-safe thereafter.
- If `flags` is omitted, the legacy CSS **tricolor** `flag:{left,mid,right}` is used
  (default French blue-white-red) — this is what the existing cron config gets, unchanged.

## Fonts (non-Latin scripts) ⚠️ — Remotion's advantage

Unlike the ffmpeg edition, **Chromium substitutes missing glyphs per-character** down the
CSS `font-family` stack. The stack is `PoppinsExtraBold, <your extras>, sans-serif`, so:
- Latin prompts/answers render in Poppins (the brand face).
- A Japanese / Russian / Arabic `answer` falls through to a covering face automatically —
  the trailing `sans-serif` alone already resolves to the OS font (no tofu) on this machine.
- For a **portable / deterministic** render, bundle a webfont: drop e.g. `NotoSansJP-Bold.otf`
  (SIL OFL) into `assets/fonts/`, set `"fonts": ["NotoSansJP-Bold.otf"]` in the template.
  build.sh copies it to `public/fonts/` and `font.ts` registers it into the stack.

## Inputs (derived; override any if needed)

- `q` = `i × cadence.gap` (default **6.5s**), `a` = `q + cadence.guess` (default **4.6s**).
- `q_text` (spoken question) = `"How do we say <prompt> in <language>?"`.
- `a_text` (spoken answer) = `answer`, with a terminal `.` added if it has none.
- `total_seconds` = last `a` + 5.
- Per-item `q`/`a`/`q_text`/`a_text`, or top-level `cadence:{gap,guess}` / `total_seconds`, override.

**Text rules:** hard cap **44 chars** per `prompt`/`answer` (build.sh refuses to render
otherwise). Aim for **≤13 chars** per field so it fits one clean centered line; over **13
chars** wraps onto two balanced lines; keep ≤9 rows.

## Intake: raw words or a TikTok link → config → todo

When the user sends **raw material** ("make a Spanish video from these words", a bare list,
or a TikTok link), convert it **before** rendering. Same flow for any language.

1. **Gather.** Accepts a bare word/phrase list, or a **TikTok URL** — pull words from
   caption + description + subtitles via
   `yt-dlp --write-auto-subs --write-subs --write-description --skip-download <url>`, or the
   `tikapi` skill; transcribe (whisper/ElevenLabs) or OCR if words are only spoken/on-screen.
   Dedupe; keep teachable words; drop filler.
2. **Transform into `items[]`.** `prompt` = short English gloss; `answer` = target-language
   phrase (≤44 chars). If input is target-language only, write the English `prompt`; if
   English only, translate for `answer`. Pick a theme-matching `bg_query`.
3. **Write an overrides JSON** (`configs/<theme>-<UTC-stamp>.json`) with `bg_query`, optional
   `outro`, and `items[]`. The template supplies character/flags/voice.
4. **Add it to the todo** — queue `build.sh templates/<lang>.json configs/<…>.json out.mp4`
   rather than rendering blindly. Confirm the formatted list if anything's ambiguous
   (slang, region, a phrase that won't fit the gap).

## Inputs sidecar (for downstream viewers)

On a successful render, build.sh writes **`<out>.json` next to the mp4** (same stem) — a
snapshot `{timestamp, language, duration, bg_query, outro, words:[{prompt,answer}], config}`.
When the clip is posted, `upload-post`'s archiver moves this sidecar into `published/`
alongside the mp4, so any viewer or archive tool resolves the exact inputs with a single
rule: **`published/<stem>.json`**. Mirrors `videos-lockscreen`. Don't rename the
mp4 without renaming its `.json`.

## Registry & reuse

- `references/words-done.json` — every phrase turned into a video. build.sh warns on repeats
  and appends new ones, **deduped by `(language, answer)`** (so Spanish "café" ≠ French "café").
  Legacy entries (keyed `fr`, no language) are read as French.
- `assets/<query-slug>.jpg` — every Pexels background ever fetched, cached (+ `.credit.txt`).
  A repeat `bg_query` reuses it with **no API call**. Delete to force a refresh.
- `assets/flags/<code>.png` — flag image cache.
- `assets/versatile-<language>/` — curated generic backgrounds (e.g. `versatile-french`,
  `versatile-spanish`) used as the random fallback so a render never fails for lack of a BG.

**`assets/` ships empty.** It's a cache plus your own media, not part of the skill:

| Path | How it gets filled |
|---|---|
| `assets/<slug>.jpg`, `assets/flags/` | automatically, on first run |
| `assets/sounds/clock-tick.mp3` | **you supply it** — any short tick, or set `CLOCK=/abs/path.mp3` |
| `assets/versatile-<language>/` | **you supply it** — a handful of on-theme images per language |
| `assets/fonts/` | only for non-Latin scripts, per the font note above |

Without a versatile pool, every config needs `background_image` or `bg_query`;
build.sh exits with `no versatile fallback found` rather than rendering a blank.

## Gotchas (baked in)

- **Install:** if your project root has a `pnpm-workspace.yaml`, always
  `pnpm install --ignore-workspace` (build.sh does this).
- **CLI:** `npx remotion …` fails under pnpm — use `pnpm exec remotion …`.
- **Size:** `--video-bitrate=1100k --audio-bitrate=128k` → ~6–10MB (vs ~50MB default).
- **Font load:** Poppins + extras load via `delayRender` until ready (`remotion/src/font.ts`).
- Secrets via `set -a; . .env.local; set +a` (see `local-secrets`); never hardcode keys.

## Dependencies

`elevenlabs` skill (voices: FR **amelie**, ES **melissa**, ES storytelling backup **fiona**),
`pnpm`, `ffmpeg`, `jq`, Chrome/Chromium (Remotion), `ELEVENLABS_API_KEY`, `PEXELS_API_KEY`.

## Theme suggestions

`references/themes-suggested.json` — 178 curated themes. The scheduled task reads
`themes-done.json` to skip used ones; pick any entry absent from that list.

## Returning the video

```bash
open out.mp4
```

## Relation to the ffmpeg edition

An earlier edition of this format rendered with ffmpeg instead of Remotion. It is
**deprecated**: ffmpeg can't do real per-glyph font fallback (a hard blocker for CJK)
and animates the bar in steps, while Remotion does both cleanly. Configs are the
same shape, so an old config still runs here.
