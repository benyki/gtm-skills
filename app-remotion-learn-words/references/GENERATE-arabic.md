# GENERATE — Arabic series-a (generate + render, NO posting)

Self-contained routine prompt. Makes N Arabic "series-a" videos with the
`vocab-remotion` skill + `templates/arabic.json`, tracks them, posts one
Discord report. Runs with fresh context — assume no memory. Generate-only: do NOT post.

**The hook:** every video MIXES Egyptian and Levantine everyday Arabic — and NEVER labels
which word is which dialect. Pick whichever spoken form is most natural per word and let
viewers argue "that's Egyptian!" / "that's Shami!" in the comments. The flag strip
(eg/lb/jo/sy/ps) reinforces the debate.

## SETUP
- `cd ~/code/<project>/video-app`
- Load secrets: `set -a; . "$PWD/.env.local"; set +a` (needs ELEVENLABS_API_KEY, PEXELS_API_KEY). If missing, stop and report to Discord.
- `SKILL=~/.agents/skills/vocab-remotion`
- `WORK=~/code/<project>/world/videos/series-a-ar` ; `mkdir -p "$WORK"/final "$WORK"/configs`
- Tracking in $WORK: `themes-done.json`, `runs.json` (create as `[]` if absent).

## PICK CONTENT (N videos, default N=2)
- For each video invent ONE coherent, image-able theme NOT in `themes-done.json`
  (e.g. greetings, love & flirting, family, food & eating out, café, feelings, going out,
  compliments, market/souk, weekend, wedding, coffee, sweets, weather, travel, taxi,
  phone/texting, friends). **Bias to what people care about — love, food, family,
  emotions, greetings, fun, going out — not dry utility (bank, hardware).**
- For that theme pick **7** useful Arabic words/phrases a beginner would actually say. For each:
  - `prompt` = short ENGLISH gloss shown on screen (≤44 chars).
  - `answer` = **TRANSLITERATION** in Latin letters (revealed green = the phonetics).
    **Keep ≤13 chars so it stays ONE line** — past 13 it wraps and crowds the native line.
    Avoid numerals-as-letters (write "aa"/"3"→"a", "7"→"h") so it reads clean; no ? or !.
  - `native` = the **Arabic script** shown smaller beneath (the voiceover reads THIS).
  - Skip any `answer` (transliteration) already in `$SKILL/references/words-done.json` (.answer).
- **MIX dialects, don't label.** Choose the most common everyday spoken form per word — some
  Egyptian (yalla, izzayak, helw, 3ayez→"ayez"), some Levantine (kifak, shu, mnih, ktir).
  Never write "(Egyptian)"/"(Levantine)" on screen or in the caption.
- **Verify every phrase is real, natural spoken Arabic** — not MSA textbook stiffness, not a
  bad transliteration. When unsure, drop it. (Same discipline as verifying foreign phrases
  before adding content — don't trust an English listicle.)
- Keep it to 7 items (the two-line answers need the vertical room).

## BUILD EACH VIDEO
- Write `"$WORK/configs/<theme-slug>-<UTC-stamp>.json"` containing ONLY:
  ```json
  { "bg_query": "<Arab-world Pexels keyword>",
    "items": [ {"prompt":"...","answer":"<translit>","native":"<عربى>"}, ... x7 ] }
  ```
  (language Arabic, voice **salma**, the middle-east character, the eg/lb/jo/sy/ps flag row,
  the Cairo.ttf font, model + outro all come from `templates/arabic.json` — do NOT repeat them.)
  ✅ `bg_query` should be a real Arab-world scene on Pexels: "Cairo street", "Cairo old city",
  "Beirut city night", "Damascus old city", "Dubai souk", "Amman old town", "Egyptian cafe",
  "Marrakech street", "Tunis old town", "Sahara desert dunes", "Nile river Cairo", "Petra Jordan",
  "Arabic lantern market". A Pexels miss falls back to the curated **`assets/versatile-arabic/`**
  pool (14 Arab-world images) — so a miss never pulls a wrong-region image (unlike Japanese).
- Render, wrapping each in a 300s timeout (see RESILIENCE):
  ```bash
  timeout 300 bash "$SKILL/scripts/build.sh" \
    "$SKILL/templates/arabic.json" "$WORK/configs/<slug>-<stamp>.json" "$WORK/final/<slug>-<stamp>.mp4"
  ```
  build.sh feeds the **native Arabic** to ElevenLabs (voice salma, model eleven_multilingual_v2)
  for pronunciation, derives timing/duration, caches the bg under `assets/<slug>.jpg`, bundles
  Cairo.ttf so the RTL script joins (no tofu), and updates `words-done.json` (deduped by
  language+answer). Expect **~45s** per render, not minutes.
- On failure capture the first error line, continue with the other video (never abort the batch).

## RESILIENCE (don't skip — learned the hard way)
- **`timeout 300` every render.** The ffmpeg audio-mix step intermittently deadlocks (~1 in 6);
  it clears on retry. On a timeout/kill, just re-run the SAME command once — build.sh is
  skip-done-safe per output path (an existing final/<slug>-<stamp>.mp4 means that one is done;
  skip it on a resume). A resumable batch loop:
  ```bash
  for cfg in "$WORK"/configs/*-<stamp>.json; do
    slug=$(basename "$cfg" .json); out="$WORK/final/$slug.mp4"
    [ -s "$out" ] && { echo "skip (done): $slug"; continue; }          # skip-done resume
    for try in 1 2; do
      timeout 300 bash "$SKILL/scripts/build.sh" "$SKILL/templates/arabic.json" "$cfg" "$out" && break
      echo "render $slug attempt $try failed/timed out; retrying"; sleep 2
    done
  done
  ```
- **Do NOT run this batch at the same time as another series-a batch** (Japanese, Spanish, …).
  All languages share the one Remotion project's `remotion/public/` dir, so two concurrent
  build.sh runs clobber each other's `audio.json`/clips and you get mixed-language audio.
  Schedule the Arabic cron at a different hour than the others.

## TRACK
- On success: append theme to `themes-done.json` (dedup) and `{stamp,theme,bg_query,output,sizeMB,status:"ok"}` to `runs.json`.
- On failure: append `{stamp,theme,status:"error",error:"<first line>"}`.

## REPORT TO DISCORD (one message, <1900 chars, no mp4 attached)
```
TMP=$(mktemp); cat > "$TMP" <<JSON
{"content":"🕌 series-a AR — <UTC time>\n✅ <n_ok>/<N> · ❌ <n_err>\n<one line per video: ✅ <theme> — <sizeMB>MB | ❌ <theme> — <error>>\nTotal: <sumMB>MB"}
JSON
curl -sS -X POST -H "Content-Type: application/json" --data-binary @"$TMP" "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"; rm -f "$TMP"
```

## Scheduling this as a cron
Create a scheduled task whose prompt is "Run the routine at
`~/.agents/skills/vocab-remotion/references/GENERATE-arabic.md` autonomously,
N=2, generate-only (do NOT post)." Daily keeps an unposted buffer ahead of a 1/day poster.
Pick an hour that does NOT overlap the Japanese/Spanish series-a crons (shared public dir).
Click "Run now" once to pre-approve tools.
