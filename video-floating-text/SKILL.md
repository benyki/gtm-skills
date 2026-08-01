---
name: video-floating-text
description: Generic 9:16 floating-text video factory. Renders short-form (TikTok/Reels/Shorts) videos with 1–4 typographic text elements floating over a B-roll background clip. Each element can be hardcoded (e.g. a fixed hook) or pulled from a JSON data source; each has its own font, size, weight, case, wrap, and truncation rules. Background clips, output dir, and the data source are all declared in a per-look template JSON; the engine tracks used data items + used clips in a registry so the same content is never rendered twice. Trigger when the user says "make a floating-text video", "render the next batch of <template> videos", "add a new floating-text template", or anything similar.
---

# video-floating-text

A small, template-driven video factory for the "centered floating typography over slow B-roll" pattern. The engine in `scripts/render.py` is domain-agnostic; every look — a definition card, a dream symbol, whatever you add next — lives as a JSON file in `templates/`.

## Goals

- **1–4 text elements per video**, each with its own style (font, size, weight, italic, case, wrap, truncation).
- **Mixed sources**: a hook can be hardcoded, the next element pulled from JSON field A, the next from JSON field B (or even from a different JSON). The hook commonly is hardcoded with an `{idx}` placeholder.
- **Background clips** are pulled from one or more directories, optionally recursive, optionally randomized. Substring-based exclusions are supported.
- **No content reuse**: a registry per template tracks which data items have been rendered and which background clips have been used. Subsequent runs only pick up new work.
- **No data mutation**: the data JSON is read-only as far as this engine is concerned. The registry is the single source of truth for "what's already done."

## Directory layout

```
~/.agents/skills/video-floating-text/
├── SKILL.md                  # this file
├── references/
│   └── styles.md             # available typographic layouts (anchored, …)
├── templates/
│   ├── poetry-caps.json
│   └── dream-symbols.json
├── scripts/
│   └── render.py             # thin engine
└── state/                    # auto-populated registries, one per template
    ├── example.json          # fictional sample registry showing the schema
    └── <template>.json
```

## How to run

```bash
# Render up to 10 not-yet-done items from a template:
python3 ~/.agents/skills/video-floating-text/scripts/render.py \
  --template poetry-caps \
  -n 10

# Dry-run: see resolved text + chosen clips without encoding:
python3 ~/.agents/skills/video-floating-text/scripts/render.py \
  --template dream-symbols --dry-run -n 5

# Reset the registry and re-render everything:
python3 ~/.agents/skills/video-floating-text/scripts/render.py \
  --template poetry-caps --force -n 200
```

## Template schema

```jsonc
{
  "description": "Human label.",

  "duration_s": 15,                              // output length in seconds. Default: 15. Clip is trimmed to min(clip_length, duration_s).

  "output": {
    "dir": "~/code/<project>/world/videos/<batch>/ready",
    "filename_pattern": "{idx:02d}-{slug}.mp4"
  },

  "background": {
    "paths": ["~/videos/highway/90s"],         // one or more dirs
    "recursive": false,                        // glob ** if true
    "extensions": [".mp4", ".mov", ".m4v"],
    "random": true,                            // false = sorted iteration
    "seed": 42,
    "exclude_substrings": ["-Xh4BNbxpI8"]      // skip clip names containing any of these
  },

  "data": {
    "path": "~/code/<project>/.../items.json",
    "items_path": "items",                     // dot-path to the list inside the JSON
    "name_key": "phrase"                       // field used for slug + dedup key
  },

  "crop": { "w": 608, "h": 1080 },             // center-crop landscape source to portrait
  "outline_px": 1,                              // libass border thickness
  "spacer_size": 70,                            // spacer between stacked body elements
  "layout": "anchored",                         // see references/styles.md

  "geometry": {                                 // layout-specific knobs (anchored)
    "phrase_center_y": 830,
    "gap_px": 180
  },

  "elements": [
    {
      "name": "hook",                           // free label, used in dry-run output
      "source": "literal",                      // "literal" | "data"
      "value": "English words that sound like poetry Part {idx}",
      "split_before": " Part",                  // optional: break this single-line element at substring
      "font": "PT Serif",
      "size": 70,
      "italic": true
    },
    {
      "name": "phrase",
      "source": "data",
      "data_key": "phrase",
      "font": "Inter 24pt",
      "size": 120,
      "bold": true,
      "case": "upper"
    },
    {
      "name": "definition",
      "source": "data",
      "data_key": "why",
      "transform": "before_emdash",             // pre-process the raw value
      "font": "Inter 24pt",
      "size": 70,
      "bold": true,
      "wrap_chars": 28,                         // wrap at N chars
      "max_lines": 3                            // truncate with ellipsis if needed
    }
  ]
}
```

### Element knobs

| Field | Type | Notes |
|---|---|---|
| `source` | `"literal"` \| `"data"` | where the value comes from |
| `value` | string | for `literal`; supports `{idx}` placeholder |
| `data_key` | string | for `data`; field in the current item |
| `transform` | `"none"` \| `"before_emdash"` | pre-processing |
| `font` | string | libass font family (resolved via fontconfig) |
| `size` | int | pt |
| `bold` | bool | adds `\b1` |
| `italic` | bool | adds `\i1` |
| `case` | `"preserve"` \| `"upper"` \| `"lower"` \| `"title"` | post-transform case |
| `max_chars` | int | hard truncate before wrap |
| `wrap_chars` | int | textwrap width |
| `max_lines` | int | after wrap, truncate with `…` |
| `split_before` | string | only on single-line elements; break before this substring |

## Layouts

See [references/styles.md](references/styles.md). v1 ships `anchored` only.

## Registry

State lives at `state/<template>.json` (overridable via the optional top-level `registry` field in the template). A fictional sample lives at `state/example.json`. Shape:

```jsonc
{
  "renders": [
    {
      "ts": "2026-05-23T17:50:00+00:00",
      "idx": 7,
      "data_key": "serendipity",
      "clip": "~/videos/highway/90s/aOqEX5wJ_tE - clip29 (486s).mp4",
      "output": "~/code/<project>/.../07-serendipity.mp4",
      "elements": [ { "name": "hook", "lines": [...] }, ... ]
    }
  ],
  "used_data_keys": ["serendipity", "petrichor", ...],
  "used_clips": ["/abs/path.mp4", ...]
}
```

- Default behavior: on each run, `pending = data_items.where(key not in used_data_keys)`. The engine picks the first `-n` pending items and renders them.
- Clip picking prefers unused clips. Once exhausted, it warns and falls back to reusing.
- `--force` wipes the registry in-memory and re-renders all `-n` items (the on-disk file is overwritten only after each successful render). Existing output mp4s are not deleted — they're overwritten if the filename collides.

## Ports + bundled templates

- **`poetry-caps`** — A typographic "definition card" look: fonts, geometry and case rules driven from this generic engine. Set its output path in the template. Note: it renders only — it does not write captions back into any source file.
- **`dream-symbols`** — Hardcoded "Dream symbols you should not ignore" hook, dream-symbol subject (max 38 chars), meaning (wrap 28, max 3 lines). Pulls from `~/code/<project>/world/videos/dream-symbols/symbols.json` (which the user populates with shape `{ "symbols": [ { "symbol": "...", "meaning": "..." }, ... ] }`). B-roll: `~/videos/ugc/bed/` + `~/videos/chill/` (recursive).

## Adding a new template

1. Drop a JSON in `templates/<name>.json` following the schema above.
2. If you need a layout that doesn't exist yet, add a section to `references/styles.md` and a branch in `scripts/render.py:build_ass()` — don't bake style-specific values into the engine.
3. Run with `--dry-run` first to verify resolved text + clip selection look right.

## Rules

- The engine never mutates the data JSON. The registry is the source of truth.
- Data file is expected to exist before running — the engine errors helpfully if it doesn't.
- Never embed project-specific paths inside `scripts/render.py`. All paths live in templates.
- One template = one look. Don't make a single template branch on flags; copy it and edit.
- Per-template `max_chars` / `wrap_chars` / `max_lines` are content-validation knobs — set them so a fat data item still produces a clean frame.
