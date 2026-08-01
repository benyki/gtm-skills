# Adding a new video workflow

This walkthrough shows how to take a fresh idea — a hook, a data set, a vibe — and turn it into a runnable template in this skill. Use it any time you spin up a new "look" (a new floating-text video format with its own fonts/copy/background).

> **Mental model**: one template JSON = one look. The engine never grows; new looks come from new files in `templates/`.

---

## Before you start

You need three things, even loosely sketched:

1. **A hook idea.** The line at the top of every video. Usually hardcoded (with a `Part {idx}` counter if it's an evergreen series).
2. **A data source.** A JSON file with a list of items. Each item provides the per-video copy (e.g. one item = one dream symbol with its meaning). The engine will not mutate it.
3. **B-roll clips.** One or more directories on disk. The engine center-crops 16:9 → 9:16, so the visual subject should sit near horizontal center of the source.

If any of these is missing, stop and produce it first — you'll iterate faster with real material than with placeholders.

---

## Step 1 — Pick (or design) a layout

Open [`references/styles.md`](references/styles.md) and pick the layout that matches the shape you want. v1 ships only `anchored` (hook on top, anchor element locked at a fixed Y, body elements below). If your idea needs a new shape (bottom-aligned, side-by-side, full-screen single line), add a section to `styles.md` describing the geometry, then a branch in `scripts/render.py:build_ass()` selected by `layout: "<new-name>"`. **Don't** bake style-specific numbers into the engine — every knob lives in the template.

---

## Step 2 — Sketch the data file

Decide the JSON shape of your data source. The engine pulls items from one list via the `data.items_path` dot-path. For each video, fields are looked up by `data_key` on each element.

Minimal example for a "Dream symbols" workflow:

```json
{
  "symbols": [
    { "symbol": "Falling", "meaning": "You feel out of control in a waking situation." },
    { "symbol": "Teeth falling out", "meaning": "A loss of confidence or fear of aging." }
  ]
}
```

Pick a `name_key` (here `symbol`) — the engine uses it for filenames AND as the dedup key in the registry. Choose a field that's unique per item.

---

## Step 3 — Discover available fonts

The template's `font` strings are resolved by libass through fontconfig. Before committing a font choice, verify it actually resolves:

```bash
fc-match "PT Serif:style=italic"
fc-match "Inter 24pt:weight=black"
```

If `fc-match` returns a fallback (e.g. you asked for "MyFont" and got "DejaVu Sans"), the family isn't installed — install it under `~/Library/Fonts/` or pick another.

For a quick visual try-out before writing the template, copy `templates/poetry-caps.json`, swap a font, and run a 1-item dry-run.

---

## Step 4 — Author the template

Create `templates/<name>.json`. Use kebab-case (e.g. `dream-symbols`, `poetry-caps`). Naming convention: `<project>-<look>`.

Minimum required fields:

```jsonc
{
  "description": "One-line summary of the look.",

  "output": {
    "dir": "~/code/<project>/world/videos/<batch>/ready",
    "filename_pattern": "{idx:02d}-{slug}.mp4"
  },

  "background": {
    "paths": ["~/videos/<source>"],   // one or more dirs
    "recursive": false,               // true if you want to walk subdirs
    "extensions": [".mp4"],
    "random": true,
    "seed": 42
  },

  "data": {
    "path": "~/code/<project>/.../items.json",
    "items_path": "items",
    "name_key": "subject"
  },

  "layout": "anchored",
  "geometry": { "phrase_center_y": 830, "gap_px": 180 },
  "outline_px": 1,
  "spacer_size": 70,
  "crop": { "w": 608, "h": 1080 },

  "elements": [
    { "name": "hook",    "source": "literal", "value": "Your hook here Part {idx}",
      "split_before": " Part", "font": "PT Serif", "size": 70, "italic": true },
    { "name": "subject", "source": "data", "data_key": "subject",
      "font": "Inter 24pt", "size": 120, "bold": true, "case": "upper", "max_chars": 38 },
    { "name": "body",    "source": "data", "data_key": "body",
      "font": "Inter 24pt", "size": 70, "bold": true, "wrap_chars": 28, "max_lines": 3 }
  ]
}
```

See [`SKILL.md`](SKILL.md) for the full schema reference (all element knobs, all layout fields).

### Element copy-paste recipes

**Hardcoded hook with a Part counter:**
```json
{ "name": "hook", "source": "literal",
  "value": "<Your evergreen line> Part {idx}", "split_before": " Part",
  "font": "PT Serif", "size": 70, "italic": true }
```

**Subject pulled from `entry["term"]`, uppercased, capped at 38 chars:**
```json
{ "name": "subject", "source": "data", "data_key": "term",
  "font": "Inter 24pt", "size": 120, "bold": true, "case": "upper", "max_chars": 38 }
```

**Definition pulled from `entry["why"]`, taking only text before the em-dash:**
```json
{ "name": "definition", "source": "data", "data_key": "why",
  "transform": "before_emdash", "wrap_chars": 28, "max_lines": 3,
  "font": "Inter 24pt", "size": 70, "bold": true }
```

---

## Step 5 — Dry-run to validate

Before encoding anything, do a dry-run. The engine will load the data, resolve every element, and print exactly what would be drawn:

```bash
python3 ~/.agents/skills/video-floating-text/scripts/render.py \
  --template <name> --dry-run -n 5
```

Inspect the output:

- Does the hook break at the right spot?
- Does any line get unexpectedly truncated by `max_chars` / `max_lines`?
- Are the chosen clips appropriate (no cultural mismatch — adjust `background.exclude_substrings` if needed)?
- Are the filenames sensible?

Iterate on the template until the dry-run reads clean.

---

## Step 6 — Render one, eyeball it

```bash
python3 ~/.agents/skills/video-floating-text/scripts/render.py \
  --template <name> -n 1
```

Open the produced mp4. Check:

- Vertical balance (is the hook too close to the top? too close to the phrase? — adjust `geometry.phrase_center_y` and `geometry.gap_px`)
- Font weight + outline (is the stroke too chunky? — adjust `outline_px`)
- Wrapping (does the longest item still fit? — try with one of your widest data items)

If something's off, tweak the template and re-run. Each render writes its choices into the registry, so the next run picks the next item automatically — no manual indexing.

---

## Step 7 — Batch

```bash
python3 ~/.agents/skills/video-floating-text/scripts/render.py \
  --template <name> -n 200
```

The engine renders up to `-n` pending items, picking unused clips first, and updates the registry after each video.

If you change the template *visually* and want to re-render existing items, reset the registry with `--force`. That re-emits all items into the same filenames (overwriting). Existing mp4s are not pre-deleted.

---

## The registry — what it tracks and why

`state/<template>.json` is the source of truth for "what's done." It contains:

- `used_data_keys` — every `name_key` value already rendered for this template
- `used_clips` — every absolute clip path already used
- `renders` — per-render audit log (timestamp, idx, key, clip path, output path, resolved element lines)

Why it matters:

- **No duplicates**: subsequent runs skip items in `used_data_keys`.
- **No clip reuse** (until the pool is exhausted): subsequent runs prefer clips not in `used_clips`.
- **Forensics**: you can answer "what did 07 say? which clip?" without re-rendering.

The data JSON is never touched. If you need a per-item caption or status to land in a project file, do that in a separate post-processing step that reads the registry.

---

## Common pitfalls

- **Font fallback silently**: `fc-match "X"` returning a totally different family means it'll work but look wrong. Test before batching.
- **`exclude_substrings` over-matching**: substring matching is naïve. Be specific (e.g. `"-Xh4BNbxpI8"` not just `"Tokyo"`).
- **Same data file, two templates, same `out_dir`**: outputs collide. Give each template a distinct `output.dir`.
- **Crop mismatch**: the engine assumes 1920×1080 landscape source. If your clips are already portrait or square, set `crop.w` / `crop.h` accordingly — or pre-process them outside this skill.
- **Long items**: a `subject` with 60 chars will overflow at `size: 120`. Either set `max_chars`, or curate the data to fit.

---

## When NOT to add a template here

This skill is for **floating-text + B-roll** videos. Don't use it for:

- Videos with voiceover (use the existing `local-video-app-voice-*` skills)
- Multi-clip storyboards (use `video-factory-floating-text-short` or a video-structure planner)
- Anything that needs cuts, transitions, or shot composition beyond one continuous B-roll clip

A good rule: if you can describe the video in one sentence — "a clip with N text lines overlaid" — this skill fits. Otherwise reach for a heavier tool.
