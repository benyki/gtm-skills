---
name: app-video-study
description: Turn any recent study or science insight into a ~60-second vertical "explainer + question-yourself" video in the science brand visual style (Remotion + ElevenLabs), then optionally post it to TikTok @your-handle (viralwatch-friendly, AIGC-disclosed). Use for "make a video about this study", "turn this paper/finding into a science-brand video", "science insight video", or a one-off science dispatch in the Dream Desk look.
---

# science-brand Video — Study / Science Insight

Take **one** recent study or science insight and turn it into a ~60-second, 9:16
video that (1) explains the finding in plain language with accurate numbers and
(2) turns it back on the viewer with a reflective "ask yourself" question — in the
exact **Dream Desk** visual identity (purple accent, `river-faith` voice, count-ups,
bar charts, big-number cards). Optionally publish to TikTok **@your-handle**, staged
so the **viralwatch** desktop app shows it correctly.

This skill is **topic-agnostic**: sleep, memory, longevity, psychology, physics,
climate, nutrition — any field. It reuses the Dream Desk render pipeline; you supply
the study and the words.

## When to Use This Skill
- "Make a science-brand video about this study / paper / finding"
- "Turn this science insight into a video like the dream desk ones"
- "Find a recent [field] study and make a 1-minute explainer video"
- A one-off science dispatch in the Dream Desk look (not the weekly dream-trends run —
  that is [[app-dream-desk]]).

## The Core Idea — every video is two moves
1. **Explain** the finding honestly: the setup, the headline number, the effect.
2. **Question** the viewer: end on a reflective prompt that makes the finding personal.
That second move is the signature of this format. Never skip it.

## Output Location
```
~/code/<project>/world/video-study/runs/<slug>-<YYYY-MM-DD>/
  video.config.json     the whole video (script + text + footage + voice)
  <slug>.mp4            the rendered video
  caption.txt           the TikTok caption (only if posting)
  source.md            1-paragraph note: the study, link, and every number used
```
`<slug>` is a short kebab-case tag for the study (e.g. `dream-incubation`,
`ozempic-memory`, `4-day-week`). Use the date from context.

## Instructions

### 1. Find & verify the insight (research)
- If the user named a study/link, fetch it. Otherwise scan the curated feeds (see
  `references/rss-feeds.md`) and pick the finding with the best "scroll-stop" number and
  a natural self-reflection angle:
  ```bash
  python3 ~/.agents/skills/local-video-app-study/scripts/fetch_feeds.py --limit 8 --since-days 21
  python3 ~/.agents/skills/local-video-app-study/scripts/fetch_feeds.py --only neuro --limit 12
  ```
  If a feed 403s/rate-limits, fall back to `WebSearch` for a recent striking finding.
- **`WebFetch` the primary source** (or a solid write-up) and extract EXACT figures:
  institution, journal + year, sample size, the headline stat, the comparison
  (effect vs control / before vs after), and the one human/uncanny detail.
- Write `source.md`: the finding in one paragraph, the URL, and a bullet list of
  every number you will put on screen. **Every on-screen number must trace to here.**
- **Name the CORE PAYLOAD** (one line in `source.md`): the single thing a viewer must
  *see* to get it — the list of types, both comparison numbers, the ranked items. This is
  what a scene must show as on-screen text. See RULE 0 in `references/scene-arc.md`: never
  let it slip to voiceover-only or get shrunk to a summary number to fit a layout. For a
  named typology ("9 types of X"), show **all** the names via a `grid` scene.
- Honesty bar: cultural/curiosity framing only — **no medical, clinical, or financial
  advice**, no overclaiming beyond what the study shows. Correlation is not cause.

### 2. Scaffold the run folder
```bash
python3 ~/.agents/skills/local-video-app-study/scripts/new_study.py \
  --slug <slug> --date <YYYY-MM-DD>
# -> creates the run folder and drops in a starter video.config.json from the template
```

### 3. Write the video config (the craft)
Read `references/scene-arc.md` (RULE 0 + the 7-beat arc and how to adapt it to ANY study)
and `references/video-config.md` (every field, including the `grid` layout), then edit
`video.config.json`. Fill each scene's `vo` (spoken line), on-screen text, and Pexels
`query` from your `source.md`. **First place the core payload on screen** (e.g. a `grid`
of all the types), then build the rest of the arc around it.

Fixed points (the brand): 9:16, accent `#9A90F5`, voice `river-faith`, the count-up /
bars / big-number / surprising layouts. Everything else — hook, arc, footage,
framing — is yours to fit the study.

Two hard writing rules (carried from the Dream Desk):
- **VOICEOVER RULE** — never write comma-separated lists in any `vo`; the TTS reads
  them choppily. Unfold anything list-like into flowing spoken sentences. On-screen
  text may stay terse.
- **TEXT RULE (do not use em dashes or middle dots):** never put an em dash (—) or a
  middle-dot/bullet character (• ·) in any on-screen string (titles, subs, kickers,
  bar/chip/counter labels) or in the caption. They look templated and clutter the frame.
  Rephrase instead: use a comma, a colon, the word "or"/"vs", or split onto two lines or
  two sentences.

### 4. Render
```bash
D=~/code/<project>/world/video-study/runs/<slug>-<date>
# free silent timing/layout preview first (no ElevenLabs credits):
DRY=1 bash ~/.agents/skills/app-dream-desk/scripts/video/build_video.sh $D/video.config.json /tmp/preview.mp4
# real render (ElevenLabs voice -> Pexels clips -> Remotion, 1080x1920):
bash ~/.agents/skills/app-dream-desk/scripts/video/build_video.sh $D/video.config.json $D/<slug>.mp4
```
The render pipeline is shared with [[app-dream-desk]] and is fully data-driven.
Aim for **55–75s**. Watch the DRY timing; trim `vo` if it runs long.

### 5. (Optional) Post to TikTok @your-handle — viralwatch-friendly
Posting is **outward-facing** — only with the user's explicit go-ahead. First write
`caption.txt` per `references/caption.md`, then:
```bash
bash ~/.agents/skills/local-video-app-study/scripts/post_study_tiktok.sh \
  $D/video.config.json  $D/<slug>.mp4  $D/caption.txt  <slug>  <date>
```
This stages the clip in its own **viralwatch lane** (`video-study/final`, stem
`video-study-<slug>-<date>` — so it never collides with the weekly dream-desk stems),
DIRECT_POSTs to @your-handle via Upload-Post with `--aigc` (the narration is
synthetic, so we disclose it) and tag `local-video-app-study`, archives into `published/`,
appends the shared posts ledger, and polls the async upload to the live TikTok URL.
On a cap/error it leaves the clip staged and exits non-zero — retry later, delete
nothing.

### 6. Report back
Summarize the study (one line + link), the arc you built, the duration, the run
folder, and — if posted — the live TikTok URL. End with an `open` command for the mp4.

## Scripts
- `scripts/fetch_feeds.py` — pull recent items from the curated science/neuroscience RSS
  feeds (stdlib only) so you can pick a study. Flags: `--only neuro|science --limit
  --since-days --list --json`.
- `scripts/new_study.py` — scaffold `~/code/<project>/world/video-study/runs/<slug>-<date>/`
  and copy the template config in. Flags: `--slug --date [--outdir]`.
- `scripts/stage_viralwatch.py` — stage a rendered mp4 + write the viralwatch sidecar in
  the study lane (`~/code/<project>/world/videos/video-study/final/`). Adapted from the
  Dream Desk stager; keeps study videos in their own lane.
- `scripts/post_study_tiktok.sh` — one-command publish: `post_study_tiktok.sh CONFIG
  MP4 CAPTION.txt SLUG [DATE]`. Stages for viralwatch, DIRECT_POSTs to @your-handle
  (`--aigc`, `--tag local-video-app-study`), archives + ledgers, polls to the URL.
  Outward-facing — explicit go-ahead only. Env: `TIKTOK_USER` (default `your-handle`),
  `ENVFILE` (default `~/.agents/.env`).
- **Rendering reuses** `~/.agents/skills/app-dream-desk/scripts/video/build_video.sh`
  (config-driven; nothing study-specific in it).

## References
- `references/rss-feeds.md` — curated top science + neuroscience RSS feeds (two tiers:
  write-ups and primary journals) and how to pick a study for this format. Paired with
  `scripts/fetch_feeds.py`. **Read/scan first when no study was named.**
- `references/scene-arc.md` — the canonical 7-beat arc (hook → study → headline number
  → comparison → striking detail → **ask yourself** → outro) and how to bend it to any
  study shape. **Read before writing the config.**
- `references/video-config.md` — every config field, study-specific notes, and the
  writing rules. Defers to the Dream Desk config reference for the shared layout docs.
- `references/caption.md` — how to write the @your-handle caption for a study video.
  **Read before posting.**
- `templates/study.config.template.json` — a ready-to-edit starter config with the full
  arc and placeholder content (the worked `dream-incubation` example, lightly genericized).

## Notes
- The template is a **scaffold, not a script** — every study is different. Some have a
  clean treatment-vs-control (use the `bars` scene); some are a single number (drop bars,
  add a second `bignum` or `chips`); some have several vivid examples (use `surprising`).
  Keep the two moves (explain + question) and the brand; change everything else.
- Accuracy is the whole game: if the number on screen doesn't match `source.md`, the
  video is wrong. Keep caption, on-screen text, and source in agreement.
- Secrets (ElevenLabs, Pexels, Upload-Post) come from `~/code/<project>/video-app/.env.local`
  and `~/.agents/.env` — never printed. See [[app-dream-desk]] for the shared pipeline.
