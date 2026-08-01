# Video template — {{THEME}}

Generated: {{DATE}}

## Three-line floating-text contract

| Line | Role | Content rule |
|---|---|---|
| 1 | **Hook** | Recurring across the series. Builds identity. Include the part/day counter. e.g. `"<Series> part <n>"` |
| 2 | **Title** | The unique subject of this short. Biggest line visually. |
| 3 | **Detail** | Definition / payoff / one-line how-to. Auto-wraps at the alphabet's char limit. |

### Current values

- **Line 1 template:** `<FILL — e.g. "English is Beautiful part <n>">`
- **Line 2 template:** `<FILL — e.g. "<phrase>">`
- **Line 3 template:** `<FILL — e.g. "<definition>">`

### Char limits (defer to `$ffmpeg-text-overlay-style`)

- Latin: 28 / line
- RTL: 20 / line
- Abugida: 22 / line
- CJK: 13 / line

## Background video sources

| Source | URL / search keywords | Notes |
|---|---|---|
| primary | `<FILL>` | |
| secondary | `<FILL>` | |

All sources downloaded into `clips/`, then sliced into 9:16 90s clips in `clips/90s/`. See `scripts/slice-90s.sh` in `$video-factory-floating-text-short`.

## Style overrides

Defaults from `$ffmpeg-text-overlay-style` (TikTok Sans SemiBold, white, black outline, 33% from top, libass `\an5`).

Override only if art direction requires it:

- font: `<default>`
- color: `<default>`
- position from top: `33%`
- shadow: `0`

## Visual hierarchy (locked)

Each video has three logical lines with a fixed size hierarchy:

| Line | Role | Size × base | Notes |
|---|---|---|---|
| 1 | Hook | `0.60` (small) | Recurring identity, deliberately quiet |
| 2 | Title | `1.10` (normal / hero) | Biggest — the subject of this short |
| 3 | Detail | `0.60` (small) | Definition / payoff, matches line 1 for symmetry |

Multipliers apply to `base_font_size` from the shared `$ffmpeg-text-overlay-style` config. Override per entry only if explicitly required — the defaults *are* the series identity.

## Optional title styling

Set per-entry in `payload.json` under `style`:

- `style.title_caps: true` — uppercase line 2 (e.g. `flâner` → `FLÂNER`). Poster-typography feel.
- `style.title_font: "<font name>"` — different display font for line 2 only. The font must be installed on the system.

This factory's default: `<title_caps: ?>` / `<title_font: ?>` — `<FILL>`.

## Target audience

`<FILL>`
