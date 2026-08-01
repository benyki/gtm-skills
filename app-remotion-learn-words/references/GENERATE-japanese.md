# GENERATE — Japanese series-a (generate + render, NO posting)

Self-contained routine prompt. Makes N Japanese "series-a" videos with the
`vocab-remotion` skill + `templates/japan.json`, tracks them, posts one
Discord report. Runs with fresh context — assume no memory. Generate-only: do NOT post.

## SETUP
- `cd ~/code/<project>/video-app`
- Load secrets: `set -a; . "$PWD/.env.local"; set +a` (needs ELEVENLABS_API_KEY, PEXELS_API_KEY). If missing, stop and report to Discord.
- `SKILL=~/.agents/skills/vocab-remotion`
- `WORK=~/code/<project>/world/videos/series-a-jp` ; `mkdir -p "$WORK"/final "$WORK"/configs`
- Tracking in $WORK: `themes-done.json`, `runs.json` (create as `[]` if absent).

## PICK CONTENT (N videos, default N=2)
- For each video invent ONE coherent, image-able theme NOT in `themes-done.json`
  (e.g. numbers, days, family, weather, directions, shopping, train station, konbini,
  temple, money, time, body, emotions, hobbies, animals, colors, clothing, airport,
  café, cooking, school, work, phone, travel, seasons). Prefer fresh themes.
- For that theme pick **9** useful Japanese words/phrases a beginner would say. For each:
  - `prompt` = short ENGLISH gloss shown on screen (≤44 chars).
  - `answer` = **ROMAJI** (Latin, revealed green = the phonetics). **Keep ≤13 chars so it
    stays ONE line** — past 13 it wraps and crowds the native line. Use Hepburn romaji.
  - `native` = the Japanese script (hiragana / katakana / kanji) shown smaller beneath.
  - Skip any `answer` (romaji) already in `$SKILL/references/words-done.json` (.answer).
- Use 9 items. With two-line answers the vertical stack is tight, so the ≤13-char one-line
  romaji rule above is REQUIRED at 9 — a wrapping answer will crowd the row below it.

## BUILD EACH VIDEO
- Write `"$WORK/configs/<theme-slug>-<UTC-stamp>.json"` containing ONLY:
  ```json
  { "bg_query": "<Japanese Pexels keyword>",
    "items": [ {"prompt":"...","answer":"<romaji>","native":"<日本語>"}, ... x9 ] }
  ```
  (language Japanese, voice sara, the chinese-girl character, the JP flag, model + outro all
  come from `templates/japan.json` — do NOT repeat them.)
  ⚠️ `bg_query` must be a **Japanese** scene that exists on Pexels (there is NO versatile-japanese
  fallback — a miss would pull a French image). Safe queries: "Tokyo street", "Tokyo street crossing
  night", "Japanese izakaya restaurant", "Japanese temple", "cherry blossom Tokyo", "Shibuya crossing",
  "Kyoto street", "Japanese convenience store", "Mount Fuji", "Japanese train station", "Osaka night".
- Render: `bash "$SKILL/scripts/build.sh" "$SKILL/templates/japan.json" "$WORK/configs/<slug>-<stamp>.json" "$WORK/final/<slug>-<stamp>.mp4"`
  build.sh feeds the **native** Japanese to ElevenLabs for pronunciation, derives timing/duration,
  caches the bg under `assets/<slug>.jpg`, and updates `words-done.json` (deduped by language+answer).
- On failure capture the first error line, continue with the other video (never abort the batch).

## TRACK
- On success: append theme to `themes-done.json` (dedup) and `{stamp,theme,bg_query,output,sizeMB,status:"ok"}` to `runs.json`.
- On failure: append `{stamp,theme,status:"error",error:"<first line>"}`.

## REPORT TO DISCORD (one message, <1900 chars, no mp4 attached)
```
TMP=$(mktemp); cat > "$TMP" <<JSON
{"content":"🎌 series-a JP — <UTC time>\n✅ <n_ok>/<N> · ❌ <n_err>\n<one line per video: ✅ <theme> — <sizeMB>MB | ❌ <theme> — <error>>\nTotal: <sumMB>MB"}
JSON
curl -sS -X POST -H "Content-Type: application/json" --data-binary @"$TMP" "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"; rm -f "$TMP"
```

## Scheduling this as a cron
Create a scheduled task whose prompt is "Run the routine at
`~/.agents/skills/vocab-remotion/references/GENERATE-japanese.md` autonomously,
N=2, generate-only (do NOT post)." Daily (`0 9 * * *`) keeps an unposted buffer ahead of a
1/day poster. Click "Run now" once to pre-approve tools.
