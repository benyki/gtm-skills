---
name: video-factory-floating-text-short
description: Bootstrap a complete short-form (9:16) video factory workflow for a new theme — interactively agree on a 3-line floating-text template (hook / title / detail) and content keywords with the user, scaffold a working folder, download YouTube background sources, slice them into 100+ 90s vertical clips, generate a recurring content-search prompt, and produce a payload.json + runs.json pipeline that mass-produces coherent on-theme TikTok/Reels/Shorts videos. Trigger when the user says "spin up a video factory", "start a new short video workflow", "set up a video pipeline for <theme>", "I want to make a lot of short videos about X", or anything similar.
---

# video-factory-floating-text-short

A **bootstrap skill**: when the user wants to start producing a high volume of short, on-theme 9:16 videos with a consistent floating-text identity, this skill spins up the entire workflow scaffolding, gets the user to **approve the template and the keywords** before any heavy work, and hands the project a clean pipeline (`payload.json` → render → `runs.json`).

It does **not** itself render videos — it sets up the factory so that subsequent agent runs (cron, `/loop`, manual) can churn through `payload.json` reliably.

## When to use this skill

- User wants to launch a recurring short-video campaign around a coherent theme (e.g. "beautiful English words", "deep-sleep hacks day N", "fact-of-the-day about Roman emperors").
- User has a target audience and an app/product but no rendering pipeline yet.
- User says something like *"set up a video factory"*, *"start a new short-video workflow"*, *"I want to produce 100 TikToks about X"*.

Do **not** trigger for one-off videos — for those, jump straight to `$video-definition` (template-style render) or `$video-pov` (UGC + screen recording).

## The 5-phase workflow

Phases are linear. Do not skip ahead — the user must **approve the template and keywords** before any download happens.

### Phase 1 — Inputs & user confirmation

Collect these inputs from the user. If anything is missing, **ask via `AskUserQuestion` before doing any work**:

| Input | Required | Default if missing |
|---|---|---|
| Theme name (slug, kebab-case) | yes | derive from app/product name |
| Target audience | yes | — |
| Working folder | no | `~/runs/<theme-name>` |
| 3-line template (hook / title / detail) | yes | propose 3 candidates and ask |
| YouTube source(s): URLs or search keywords | yes | propose 3 candidates and ask |
| Searchable content theme keywords | yes | propose 3 candidates and ask |
| Optional background music | no | none |
| Optional ffmpeg filters | no | none |
| Text overlay style | no | `$ffmpeg-text-overlay-style` defaults |

**Template structure (locked):**

```
line 1 → HOOK              (recurring, builds series identity, e.g. "English is Beautiful part <n>")
line 2 → TITLE             (the subject of this specific short, e.g. "<phrase>")
line 3 → DETAIL            (description / definition / payoff, e.g. "<definition>")
```

Examples to propose to the user, adapted to *their* product:

| Product | Line 1 (hook) | Line 2 (title) | Line 3 (detail) |
|---|---|---|---|
| Language-learning app | `English is Beautiful part <n>` | `<phrase>` | `<definition>` |
| Sleep tracker | `Day <n> of finding the best hacks for deep sleep` | `<hack name>` | `<short how-to>` |
| Caffeine tracker | `Day <n> of fixing your sleep with science` | `<rule>` | `<one-line proof>` |
| Workout app | `30 days to your first pull-up — day <n>` | `<drill>` | `<form cue>` |
| Productivity app | `Stoic habits in 60s — part <n>` | `<habit>` | `<why it works>` |

**Always show the user the resolved template and the keyword list and get explicit approval (`AskUserQuestion`) before moving on.** No downloads, no slicing, no rendering before approval.

**While you're already asking, also surface the optional design choices** — don't decide them silently. A single `AskUserQuestion` round (or two) with the items below is usually enough, and it's much friendlier than guessing:

- **Title in ALL CAPS?** (`style.title_caps`) — gives the hero line a poster-typography feel. Default: off. Nudge the user with a one-line preview of both options.
- **Different display font for the title line?** (`style.title_font`) — e.g. a serif against a sans body. Default: shared font. Mention that the font must be installed locally; offer 2–3 popular options that ship with macOS or are already in the user's font folder.
- **Custom hierarchy multipliers?** (`style.hierarchy`) — defaults are `0.60 / 1.10 / 0.60` (small / hero / small). Most users will keep the defaults; only ask if they hint at wanting a different feel (e.g. "make the title even bigger", "I want a more even look").
- **Subagent-driven web verification of every content item?** (see Phase 4) — strongly recommended; ask once with the cost/benefit and remember the user's answer for the rest of the session.

These choices land in `video-template.md` (project defaults) and/or per-entry in `payload.json`. Re-asking later is cheap; over-deciding silently is not.

### Phase 2 — Scaffold working folder

Once template and keywords are approved, create:

```
<working-folder>/
  video-template.md           ← human-readable template + background video origin
  online-search-prompt.md     ← prompt usable in a cron/routine to search fresh content
  payload.json                ← queue of overlays ready to render (status: pending|done)
  runs.json                   ← progress log, IDs mirror payload.json
  clips/                      ← long source videos (yt-dlp output)
  clips/90s/                  ← 90s 1080x1920 portrait clips, ready to use as backgrounds
  final/                      ← rendered shorts (output)
  music/                      ← optional background music tracks
```

Use the script `scripts/init-workflow.sh <working-folder> <theme-name>` to scaffold this in one shot. The script copies the templates from `references/` and substitutes the theme name.

### Phase 3 — Source download & 90s slicing

1. **Download long YouTube videos** into `<working-folder>/clips/` using `$yt-dlp`. The factory needs enough source minutes to yield **at least 100 × 90s clips**. Rule of thumb: download `ceil(100 × 90 / 60 / video_minutes)` videos, biased toward visually coherent long-form footage (drone, drive, ambient, slow B-roll).

   ```bash
   yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" \
     -o "<working-folder>/clips/%(id)s.%(ext)s" \
     "<URL_OR_ytsearch1:keywords>"
   ```

   For a search-only flow:
   ```bash
   yt-dlp "ytsearch5:<source-keywords>" \
     -f "bv*[height<=1080]+ba/b[height<=1080]" \
     -o "<working-folder>/clips/%(id)s.%(ext)s"
   ```

2. **Slice into 90s vertical (9:16) clips** with `scripts/slice-90s.sh <clips-dir> <out-90s-dir> [min-clips]`. The script:
   - Probes every `*.mp4` in `clips/` with ffprobe.
   - Cuts non-overlapping 90s segments, skipping the first and last 60s of each source (intros/outros).
   - Center-crops 1920×1080 → 608×1080 then scales to 1080×1920 (same crop math as `$video-definition`).
   - Names each output `<sourceID> - clip<NN> (<sourceSec>s).mp4` — mirrors the convention already in `~/videos/highway/90s/`.
   - **Round-robins across sources** — emits clip01 of every source, then clip02 of every source, etc., instead of draining one source at a time. With 6 sources and a 100-clip target this yields ~17 clips/source instead of e.g. 48/38/11/3/0/0. Critical for visual variety in long payloads.
   - Stops once it has produced at least `min-clips` (default 100). Counts both newly cut and pre-existing clips so the script stays idempotent.
   - Skips clips already present (safe to re-run).

   Refer to `$ffmpeg` for the binary discovery and `$ffmpeg-text-overlay-style` for any text styling defaults.

### Phase 4 — Content research & payload generation

This is the loop that keeps the factory fed.

> 🔎 **Strong default — back every payload row with a live web-research pass.**
>
> The model's training data is stale, regionally biased, and silently wrong about spelling, accents, dates, attributions, and definitions. One wrong accent (`crepuscule` vs `crépuscule`, `s'epanouir` vs `s'épanouir`) or one misattributed fact is a public mistake that costs a video and erodes the series — so the default behavior is to verify.
>
> **Recommended mechanism:** spawn a subagent (`$Agent` with `subagent_type: "general-purpose"`, or `$Explore` for lighter lookups) per batch, briefed to call `$WebSearch` + `$WebFetch` and confirm every line of every row against **at least two independent reputable sources** (e.g. Larousse + Le Robert for French; Merriam-Webster + OED for English; Britannica + a primary source for facts). The subagent returns a fully verified batch which the orchestrator appends to `payload.json`.
>
> **Ask the user in Phase 1 whether to enforce verification for this factory** — most will say yes, but for low-stakes themes (e.g. mood boards, abstract aesthetics) they may want to skip it. If the user opts out, record that choice in `video-template.md` so it isn't re-litigated every batch. When the user says "just go" mid-flow, surface the trade-off once and let them choose — don't unilaterally bypass and don't unilaterally enforce.

1. **`online-search-prompt.md`** lives in the working folder. It is a self-contained prompt that an agent (or a cron job via `$schedule` / `$loop`) can run to produce **N new on-theme content items** that fit the 3-line template. The template in `references/online-search-prompt.md.tpl` has these slots:
   - `{{THEME}}` — theme name
   - `{{TARGET_AUDIENCE}}` — who the videos are for
   - `{{LINE_1_TEMPLATE}}` `{{LINE_2_TEMPLATE}}` `{{LINE_3_TEMPLATE}}`
   - `{{SEARCH_KEYWORDS}}` — comma-separated content keywords
   - `{{COHERENCE_NOTES}}` — what makes items belong to the same series

   Skills the search prompt can delegate to (in priority order, web-search first):
   - `$WebSearch` / `$WebFetch` — **primary tools.** Required for spelling, accent, definition, attribution, and fact verification on every row.
   - `$apify-trend-analysis` — current trends around the theme.
   - `$apify-ultimate-scraper` — pull source content from any platform.
   - `$apify-content-analytics` — see what's working in the space.
   - `$apify-competitor-intelligence` — see what competing creators publish.
   - `$mcp__plugin_context7_context7__query-docs` — only if the theme is a tech library.

   **Subagent invocation template** (paste into the orchestrator at content-generation time):

   ```
   Agent({
     description: "Verify {{N}} on-theme rows for {{THEME}}",
     subagent_type: "general-purpose",
     prompt: "You are extending the {{THEME}} short-video series. Produce {{N}}
       new payload rows. Per row you MUST:
       1. Use WebSearch to find ≥ 2 independent reputable sources (cite URLs).
       2. Use WebFetch to read each source — never rely on snippets alone.
       3. Confirm exact spelling, accents, capitalization, and meaning.
       4. If sources disagree or you cannot find 2 → drop the candidate.
       5. Return a JSON array of fully-verified rows matching payload.json schema.
       Do NOT use prior knowledge as a substitute for a live source. Report any
       row you dropped and why. Under 800 words of prose; the JSON is the deliverable."
   })
   ```

2. **`payload.json` schema** — append-only queue. Each entry:

   ```json
   {
     "id": "english-is-beautiful-part-001-serendipity",
     "status": "pending",
     "overlay": {
       "line_1": "English is Beautiful part 1",
       "line_2": "Serendipity",
       "line_3": "A pleasant surprise"
     },
     "background_video": "clips/90s/-Xh4BNbxpI8 - clip01 (2803s).mp4",
     "music": null,
     "filters": [],
     "style": {
       "title_caps": false,
       "title_font": null,
       "hierarchy": null
     },
     "notes": "first entry, archetype"
   }
   ```

   - `id` is a slug (kebab-case) and matches the eventual `runs.json` row.
   - `status` starts as `"pending"`, becomes `"done"` after render.
   - `background_video` is **relative** to the working folder.
   - `music` is `null` or a path relative to `music/`.
   - `filters` is an optional list, e.g. `["grain", "vignette"]` — see `$video-filter`.
   - `style` is **optional**. Omit to use factory defaults (small / normal / small hierarchy, no caps, default font, asymmetric gaps). When present:
     - `style.title_caps: bool` — uppercase line 2 only.
     - `style.title_font: str | null` — fontname override for line 2 only. Must be installed.
     - `style.hierarchy: {line_1: float, line_2: float, line_3: float} | null` — override the size multipliers. Use sparingly; the defaults are the series identity.
     - `style.paragraph_gap_scale: {"line_1_to_line_2": float, "line_2_to_line_3": float} | null` — override the asymmetric gap scale (defaults `1.8` / `0.6`). Use to tune breathing room when the title is unusually long/short.
     - `style.font_weight: int (100–900) | null` — variable-font weight applied via libass `\b<weight>`. The shared default is `600` (semibold); typical bumps are `700` (bold) or `800` (extrabold).
     - `style.outline_scale: float | dict | null` — multiplier on the computed black stroke thickness (default `1.0`). Either a scalar (applies to all lines) or a dict keyed by role: `{"line_1": 0, "line_2": 0.7, "line_3": 0.7}`. A value of exactly `0` disables the stroke for that line.
     - `style.hook_suffix: str` — text appended to line_1 only (e.g. `" · part 1"`). **Never put a color emoji here** — libass 0.17.4 can't render sbix/COLR bitmap glyphs reliably (they come out as `.notdef` boxes). For flag icons, use `hook_emoji_image` instead.
     - `style.hook_emoji_image: str | null` — path or shortcut to a PNG that gets overlaid next to the hook text in a second ffmpeg pass. Accepts: a 2-letter shortcut (`"fr"` → `references/flags/fr.png` shipped with the skill), an absolute path, or a path relative to the skill's `references/` dir. Bypasses libass's broken color-emoji rendering.
     - `style.hook_emoji_size_ratio: float` — icon height as a fraction of the hook font size (default `0.9`).
     - `style.hook_emoji_gap_px: int` — horizontal gap between the hook text and the icon (default `14`).
     - `style.hook_duration_s: float | null` — cap line_1's on-screen time in seconds. After this, only the title + detail remain visible. The hook-emoji overlay vanishes at the same moment.
     - `style.alignment: str | dict` — `"center"` (default, `\an5`) or `"left"` (`\an4`, anchored ~7.5% from left edge). Either a single string (applies to all lines) or a dict keyed by role.

3. **Workspace-wide style defaults** live in a top-level `defaults.style` block in `payload.json`:

   ```json
   {
     "theme": "...",
     "defaults": {
       "style": {
         "font_weight": 700,
         "outline_scale": 0.7,
         "title_caps": true
       }
     },
     "entries": [ ... ]
   }
   ```

   The renderer merges `defaults.style` into every entry's `style` (per-entry wins on conflict). Use this for changes that apply across the whole series — like a font-weight bump or stroke thinning — so you don't have to copy the same block onto every row.

   Generation rule: every new content item from the search prompt produces **one** payload row. Background videos can be reused — assign in round-robin or randomly.

### Phase 5 — Render & track

A render run consumes `payload.json` and writes to `final/`.

1. Use `scripts/render-from-payload.py --working-folder <dir> [-n N] [--force]`:
   - Picks the first `N` entries with `status: "pending"` (or any if `--force`).
   - Calls `$ffmpeg-text-overlay-style`'s `render_subtitles_with_default_style.py` helper — **do not write a new ffmpeg invocation**, use the shared one.
   - Output filename: `final/<id>.mp4`.
   - On success, sets `status: "done"` in `payload.json` (incremental write — crash-safe).
   - Appends a row to `runs.json` with `{id, video, rendered_at, source_clip, duration_s}`.

2. **`runs.json` schema:**

   ```json
   {
     "runs": [
       {
         "id": "english-is-beautiful-part-001-serendipity",
         "video": "final/english-is-beautiful-part-001-serendipity.mp4",
         "rendered_at": "2026-05-21T10:14:00Z",
         "source_clip": "clips/90s/-Xh4BNbxpI8 - clip01 (2803s).mp4",
         "duration_s": 90
       }
     ]
   }
   ```

   `runs.json` is the source of truth for "what has shipped". Distribution skills (`$x-browser-post`, `$bluesky-post-manage`, `$caffeine-app-tweet-simulation`) can read it to pick the next unposted item.

## Text overlay rules

- **Always use `$ffmpeg-text-overlay-style`** for colors, default font, outline, line-height ratio, and overlay vertical position. Do not inline `force_style` strings in this skill or in `payload.json`. If the user wants something different, override **once** in `video-template.md` and the helper will pick it up.
- **Max characters per line** (defaults from `$ffmpeg-text-overlay-style`):
  - Latin: 28
  - RTL: 20
  - Abugida: 22
  - CJK: 13

### Visual hierarchy (default — discuss in Phase 1)

Each entry produces three logical lines with a size hierarchy. `render-from-payload.py` applies this by emitting a per-line-sized `.ass` document (the shared helper is used in `.ass`-passthrough mode for the actual burn-in).

| Line | Role | Default multiplier on `base_font_size` | Why |
|---|---|---|---|
| 1 | **HOOK** | `0.75` — small | Recurring identity, deliberately quiet but readable. |
| 2 | **TITLE** | `1.10` — normal / hero | The biggest line; the subject of this short. |
| 3 | **DETAIL** | `0.75` — small | Definition / payoff; sized to match line 1 for symmetry. |

Paragraph gaps are asymmetric (the hook breathes above the title; the detail hugs the title):

| Gap | Default scale on `paragraph_gap_ratio` | Effect |
|---|---|---|
| `line_1 → line_2` (hook → title) | `1.8×` | Visual breath between identity and subject |
| `line_2 → line_3` (title → detail) | `0.6×` | Detail reads as part of the title block |

Defaults live in `DEFAULT_HIERARCHY` and `DEFAULT_PARAGRAPH_GAP_SCALE` in `scripts/render-from-payload.py`. Treat them as good starting values, not a contract — surface them in Phase 1 if the user has any hint of a different visual feel in mind, and let them override globally in `video-template.md` or per-entry via `style.hierarchy` / `style.paragraph_gap_scale` in `payload.json`.

The one thing that *is* locked: don't change the hierarchy mid-series silently. If the user wants a new look, agree on it explicitly and write it into `video-template.md` so every future entry inherits the choice.

### Optional title styling (per entry, via `style` in `payload.json`)

- `style.title_caps: bool` — uppercase line 2 (e.g. `flâner` → `FLÂNER`). Gives the title a poster/serif-typography feel. Defaults to `false`. **Ask the user in Phase 1.**
- `style.title_font: str | null` — override the fontname for line 2 only (a different *display* font for the hero line, e.g. a serif against the body's sans). The font must be installed on the system or available through the shared helper's `fontsdir`; the renderer will not auto-install fonts. Defaults to the shared font (`TikTok Sans`). **Ask the user in Phase 1**, and if they want a font swap, offer 2–3 specific options you know are installed (check `~/Library/Fonts` and `/Library/Fonts`).

Both options are per-entry and additive — you can have all-caps without a font swap, a font swap without caps, both, or neither.

### Line role contract (do not deviate)

  - Line 1 — **HOOK**: short, recurring across the series, must include the part/day counter when applicable. Builds identity.
  - Line 2 — **TITLE**: the unique subject of this short. The biggest line visually.
  - Line 3 — **DETAIL**: definition / payoff / one-line how-to. Auto-wraps at the alphabet limit above.
- **Position**: 33% from top (default of the shared style). Override per-project in `video-template.md` only if art direction requires it.
- **Style defaults**: TikTok Sans SemiBold, white text, 5px black outline, libass `BorderStyle=1`, `\an5`. All resolved by `$ffmpeg-text-overlay-style`.

When the user proposes a custom font/style, confirm via `AskUserQuestion` and then write it into `video-template.md` so the render helper can read it.

## Naming conventions (locked)

- **Everything kebab-case.** Folders, slugs, payload IDs.
- **IDs are slugs**, derived as `<series-slug>-part-<NNN>-<title-slug>`. Zero-pad the counter to 3 digits.
- Background-clip filenames mirror the existing `~/videos/highway/90s/` convention: `<sourceID> - clip<NN> (<sourceSec>s).mp4`. Do not rename them — downstream skills grep for this pattern.
- Final video filename = `<id>.mp4`. No spaces, no uppercase.

## Resources, skills, and secrets — quick reference

So the next agent doesn't hit a roadblock:

### Companion skills (call these, don't reinvent)

| Need | Skill |
|---|---|
| Download long YouTube videos | `$yt-dlp` |
| Find ffmpeg / libass / ffprobe on this machine | `$ffmpeg` |
| Standard floating-text style + render helper | `$ffmpeg-text-overlay-style` |
| Apply post filters (grain, vignette, shake, UGC look) | `$video-filter` |
| Plan/structure the video concept first | `$video-structure-plan` |
| Existing 3-line template example (same shape) | `$video-definition` |
| Voiceover variant of this factory | `$video-voice-template`, `$video-voice-template`, `$video-voice-persona` |
| Content research | `$apify-trend-analysis`, `$apify-ultimate-scraper`, `$apify-content-analytics`, `$apify-competitor-intelligence`, `$apify-market-research` |
| Web research fallback | `$WebSearch`, `$WebFetch` |
| Schedule the search prompt as a cron | `$schedule` |
| Run the render loop on a recurring interval | `$loop` |
| Post finals to X | `$x-browser-post` |
| Post finals to Bluesky | `$bluesky-post-manage` |
| Pinterest / Pexels B-roll fallback if YouTube is dry | `$pinterest-download-videos`, `$pexel-video-downloader`, `$anthropic-skills:pexels-video-search` |
| Storage / hosting if videos must be served | `$use-railway`, `$railway-deploy` |
| Discord progress pings | `$discord-delivery` |

### Default paths

- Working folder: `~/runs/<theme-name>/`
- Shared 90s clip pool (read-only reference convention): `~/videos/<theme-slug>/90s/`
- TikTok Sans + Noto fonts already installed on this machine (see `$ffmpeg-text-overlay-style`).

### Secrets

This skill itself uses **no secrets**. Downstream skills do:

- API keys / tokens — read names from `.env.example`, values via the rules in `$local-secrets`. **Never read `.env` / `.env.local` directly.**
- Apify token — managed via `$local-secrets`, used by every `apify-*` skill.
- Mapbox token — only relevant if the theme uses maps; see `$mapbox-token-security`.
- X / Bluesky — handled by `$x-browser-post` (browser session, no API key) and `$bluesky-post-manage` (atproto session).
- Discord — see `$discord-delivery`.

## Scripts

- `scripts/init-workflow.sh <working-folder> <theme-name>` — scaffolds the working folder and copies templates from `references/`, substituting `{{THEME}}` and date.
- `scripts/slice-90s.sh <clips-dir> <out-90s-dir> [min-clips]` — slices long videos into 9:16 90s clips, skipping intros/outros, idempotent.
- `scripts/render-from-payload.py --working-folder <dir> [-n N] [--force]` — drains `payload.json` into `final/`, updates `runs.json`. Delegates the actual ffmpeg call to `$ffmpeg-text-overlay-style`.

## References

- `references/video-template.md.tpl` — three-line template + background origin + style overrides.
- `references/online-search-prompt.md.tpl` — the recurring research prompt; designed to be invoked by `$schedule` or `$loop`.
- `references/payload.json.tpl` — empty payload skeleton with one example entry.
- `references/runs.json.tpl` — empty runs log.

## Rules

- **Never download, slice, or render before the user has approved the template AND the keywords.** Use `AskUserQuestion`.
- **Never bake project-specific paths into this skill.** Every script takes the working folder as an argument.
- **Never duplicate ffmpeg/libass styling here** — always defer to `$ffmpeg-text-overlay-style`.
- **Always kebab-case** for slugs, IDs, folder names, filenames.
- **Always use `~/` in paths shown to the user**, never `~/`.
- **Append-only for `payload.json` / `runs.json`** — never rewrite history; flip `status` in place when a render succeeds.
- **Idempotency**: every script must be safe to re-run. Skip already-done work.
