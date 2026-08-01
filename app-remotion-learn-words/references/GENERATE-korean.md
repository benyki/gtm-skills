# GENERATE — Korean series-a (generate + render, NO posting)

Self-contained routine prompt. Makes N Korean "series-a" videos with the
`vocab-remotion` skill + `templates/korea.json`, tracks them, posts one
Discord report. Runs with fresh context — assume no memory. Generate-only: do NOT post.

## SETUP
- `cd ~/code/<project>/video-app`
- Load secrets: `set -a; . "$PWD/.env.local"; set +a` (needs ELEVENLABS_API_KEY, PEXELS_API_KEY). If missing, stop and report to Discord.
- `SKILL=~/.agents/skills/vocab-remotion`
- `WORK=~/code/<project>/world/videos/series-a-ko` ; `mkdir -p "$WORK"/final "$WORK"/configs`
- Tracking in $WORK: `themes-done.json`, `runs.json` (create as `[]` if absent).

## THE CONFIG LIBRARY (pre-built — render from this pool first)
A curated single-theme config library already lives under `$WORK/configs/`, split by concept:
- `$WORK/configs/food/*.json` — **50** food videos (fruits, bbq, noodles, street food, coffee,
  desserts, ordering, delivery, taste words, …).
- `$WORK/configs/love/*.json`  — **12** love/dating videos (confession, compliments, missing
  you, flirting, first date, pet names, texting, making up, forever, …).

**Two hard content rules baked into every config — keep them when you add more:**
1. **One concept per video. Never blend distant themes** (e.g. love + food in the same clip is
   wrong — a "love" video must be *all* love phrases, a "food" video *all* food).
2. **`bg_query` MUST match the video's concept.** A food video gets a food scene; a love video
   gets a romantic scene (couple / sunset / cherry blossom). Do NOT put, say, raw meat behind
   "I love you". Each config already carries a theme-matched `bg_query`.

**Default mode = render the pool (skip-done, resumable).** Prefer rendering un-rendered library
configs over inventing new themes:
```bash
for cfg in "$WORK"/configs/food/*.json "$WORK"/configs/love/*.json; do
  slug=$(basename "$cfg" | sed -E 's/-20[0-9]{6}T.*//')
  ls "$WORK"/final/"$slug"-*.mp4 >/dev/null 2>&1 && continue      # skip-done
  out="$WORK/final/$(basename "${cfg%.json}").mp4"
  timeout 300 bash "$SKILL/scripts/build.sh" "$SKILL/templates/korea.json" "$cfg" "$out" \
    || echo "FAILED $slug (continue)"                              # one hang must not stall the batch
  # render only N per run if you want to pace it (break after N)
done
```
`timeout 300` + skip-done is REQUIRED: the ffmpeg audio-mix step deadlocks ~1 in 6 renders and
clears on a re-run — a resumable loop just picks it up next pass.

## ADDING NEW THEMES (only once the pool is exhausted / to top up)
- Invent ONE coherent, image-able theme in the **same concept family** (a new food theme → save
  under `configs/food/`; a new love/dating theme → `configs/love/`). Keep the two rules above.
- Pick **9** natural spoken Korean phrases. For each item:
  - `prompt` = short ENGLISH gloss (≤44 chars).
  - `answer` = **Revised Romanization** (official, pronunciation-based, Latin, green). **Keep ≤13
    chars so it stays ONE line** — past ~13 it wraps and crowds the Hangul beneath. Prefer short
    natural forms.
  - `native` = the **Hangul** (한글).
  - Skip any `answer` already in `$SKILL/references/words-done.json` (.answer); all 9 romanizations
    distinct within the video; verify every phrase is real, natural spoken Korean (correct Hangul,
    correct romanization, right politeness level).
- Write `"$WORK/configs/<food|love>/<theme-slug>-<UTC-stamp>.json"` containing ONLY:
  ```json
  { "bg_query": "<theme-matched Korean Pexels keyword>",
    "items": [ {"prompt":"...","answer":"<romanization>","native":"<한글>"}, ... x9 ] }
  ```
  (language Korean, voice hanabad, the chinese-girl character, the KR flag, model + outro all
  come from `templates/korea.json` — do NOT repeat them.) Then render it with the loop above.
- ⚠️ **ABSOLUTE output path** — build.sh cd's into remotion/, so a relative path lands under the
  skill dir. build.sh feeds the **native** Hangul to ElevenLabs (hanabad reads Hangul natively,
  verified), derives timing/duration, caches the bg, writes the sidecar `<out>.json` (with
  `native` in words[]), and updates `words-done.json`.
- `bg_query` should be a Korean scene that fits the concept. A Pexels miss falls back to the
  curated `assets/versatile-korean/` pool (never pulls a wrong-country image). Reliable food
  queries: "korean barbecue", "korean street food", "korean food", "fruit market", "coffee shop",
  "korean noodles", "soju", "korean dessert". Reliable love queries: "couple sunset", "korean
  couple", "cherry blossom couple", "couple city night", "couple cafe date", "romantic city lights".

## TRACK
- On success: append theme to `themes-done.json` (dedup) and `{stamp,theme,bg_query,output,sizeMB,status:"ok"}` to `runs.json`.
- On failure: append `{stamp,theme,status:"error",error:"<first line>"}`.

## REPORT TO DISCORD (one message, <1900 chars, no mp4 attached)
```
TMP=$(mktemp); cat > "$TMP" <<JSON
{"content":"🇰🇷 series-a KO — <UTC time>\n✅ <n_ok>/<N> · ❌ <n_err>\n<one line per video: ✅ <theme> — <sizeMB>MB | ❌ <theme> — <error>>\nTotal: <sumMB>MB"}
JSON
curl -sS -X POST -H "Content-Type: application/json" --data-binary @"$TMP" "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"; rm -f "$TMP"
```

## Scheduling this as a cron
Create a scheduled task whose prompt is "Run the routine at
`~/.agents/skills/vocab-remotion/references/GENERATE-korean.md` autonomously,
N=2, generate-only (do NOT post)." Daily (`0 9 * * *`) keeps an unposted buffer ahead of a
1/day poster. Click "Run now" once to pre-approve tools.
