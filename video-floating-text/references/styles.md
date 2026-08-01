# Floating-text styles

This file catalogs typographic layouts the `video-floating-text` engine supports. Each style describes the *shape* of the overlay; a **template** binds a style to specific fonts, sizes, colors, and a data source.

---

## 1. `anchored` — hook above, body block locked to a y-anchor

> "Floating poetry" style. Two ASS Dialogue events with absolute `\pos` positioning. The body block (subject + spacer + description) is locked so its anchor element (typically the subject/phrase line) stays at a fixed Y regardless of how many wrapped description lines exist. The hook sits above with a tunable gap.

```
┌──────────────────────────┐    y ≈ 590 (hook center)
│  English words that      │
│  sound like poetry       │  ← hook, 2 lines, light/italic serif
│  Part 7                  │
│                          │    ← gap_px = 180
│  SERENDIPITY             │  ← anchor element (phrase), locked at phrase_center_y = 830
│                          │    ← spacer
│  The pleasant surprise   │
│  of finding something    │  ← description, wrap_chars=28, max 3 lines
│  good without looking    │
└──────────────────────────┘
```

### Required template fields

| Field | Type | Purpose |
|---|---|---|
| `layout` | `"anchored"` | selects this style |
| `geometry.phrase_center_y` | int | absolute Y (px in 1920 frame) where the anchor (element[1]) center sits |
| `geometry.gap_px` | int | px between hook bottom and phrase top |
| `outline_px` | float | libass border thickness (use 1 for thin, 5 for chunky) |
| `spacer_size` | int | empty-line spacer between body elements (typically 70) |

### Element conventions

- `elements[0]` — **hook**: drawn above. Often `source: "literal"` with `{idx}` interpolation. Can carry `split_before` to break into 2 lines at a substring (e.g. `" Part"` → "... poetry / Part 7").
- `elements[1]` — **anchor**: the visually-dominant line. Its center is locked at `phrase_center_y`.
- `elements[2..3]` — **body lines** below the anchor (typically a wrapped description), separated by `spacer_size`.

### Default values used by the original `poetry-caps` template

- `phrase_center_y: 830` (vs frame center 960 — phrase sits ~130px above true center)
- `gap_px: 180`
- `outline_px: 1`
- `spacer_size: 70`
- Hook: PT Serif italic 70pt
- Anchor: Inter 24pt Black 120pt, `case: upper`
- Body: Inter 24pt Black 70pt, `wrap_chars: 28`, `max_lines: 3`

---

## 2. `centered` — single block centered on the frame

> Minimal "one big text floating" look. All elements are stacked vertically with a spacer between them and the whole block is centered on `geometry.center_y` (default 960, the true vertical center of a 1080×1920 frame). Works with 1+ elements. Element values that contain `\n` keep their line breaks verbatim — useful for pre-composed multi-line strings like `display_text`.

```
┌──────────────────────────┐
│                          │
│        in French         │
│  you don't just say      │  ← single element, data_key: "display_text",
│  "I miss you" you say:   │     newlines in the value preserved verbatim
│  "tu me manques"         │
│  "you are missing        │
│   from me"               │
│                          │
└──────────────────────────┘    block center locked at center_y (default 960)
```

### Required template fields

| Field | Type | Purpose |
|---|---|---|
| `layout` | `"centered"` | selects this style |
| `geometry.center_y` | int (optional) | absolute Y where the block center sits (default 960) |
| `outline_px` | float | libass border thickness |
| `spacer_size` | int | empty-line spacer between stacked elements (only used if 2+ elements) |

### Element conventions

- Any number of elements (1+). With one element pulling a pre-composed multi-line string (e.g. `display_text`), this is the cleanest "single text floating" shape.
- Newlines in resolved element values are preserved as visual line breaks. If `wrap_chars` is also set, each pre-split segment is independently wrapped.

---

## Adding a new style

When a new visual layout is needed (e.g. bottom-aligned caption, side-by-side, centered single-line), add:

1. A new entry in this file describing the visual shape and required template fields.
2. A new branch in `scripts/render.py:build_ass()` selected by `layout: "<name>"`.
3. At least one template demonstrating it under `templates/`.

Resist baking style-specific values into `render.py` — push knobs out into the template.
