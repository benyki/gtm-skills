# Study video — config reference

One JSON file (`video.config.json`) drives the whole video: the **script** (`vo`), the
**on-screen text**, each scene's **duration**, the **background footage**, and the
**ElevenLabs voice**. The renderer is shared with the Dream Desk, so the field docs are
identical — this file only notes what's specific to study videos. For the full field
table (every scene `kind`, layout, and option) read the shared reference:

> `~/.agents/skills/app-dream-desk/references/video-config.md`

Render (shared pipeline):
```bash
bash ~/.agents/skills/app-dream-desk/scripts/video/build_video.sh my.config.json out.mp4
DRY=1 bash ~/.agents/skills/app-dream-desk/scripts/video/build_video.sh my.config.json /tmp/p.mp4  # free silent preview
```

## Top-level fields (study defaults)
| field | study default | note |
|-------|---------------|------|
| `brand` | `"YOUR BRAND"` | watermark, top-left. May theme per topic (e.g. `"THE SLEEP LAB"`, `"THE MIND DESK"`) — keep it short, all-caps. |
| `accent` | `"#9A90F5"` | the Dream Desk purple. Keep it unless the topic really wants its own hue. |
| `voice` | `"river-faith"` | the brand narrator. `voice_fallback` `"adam-spencer"`. |
| `model` | `"eleven_multilingual_v2"` | |
| `voice_settings` | `{stability:0.6, similarity:0.85, style:0.08, speaker_boost:true}` | steady, lightly expressive. |
| `gap` | `0.4` | silence after each scene's speech. |
| `sfx` | usually omit | study videos run on narration. Add a subtle cue only if it fits. |
| `scenes[]` | the 7-beat arc | see `scene-arc.md`. |

## Scene fields you'll use most
- `id` (unique, also the clip filename) and `kind` (`hook`/`counters`/`bignum`/`bars`/
  `chips`/`grid`/`title`/`surprising`/`outro`) — required.
- `vo` — the spoken line. **Never a comma-list** (TTS reads lists badly); unfold into
  flowing sentences. Empty `""` = a silent card.
- `seconds` (exact) or `min` (floor) — timing. Hook `min: 3.2`–`5.0`, outro `min: 4.0`.
- `query` — Pexels portrait-video search (auto-picked + cached). Or `clip_file` /
  `clip_dir` to use your own footage.
- On-screen text: `kicker`, `title` (`\n` = line breaks), `sub`, and per-kind
  `counters` / `bars` / `chips` / `grid` / `bignum` / `items`. See the shared reference for shapes.

### `grid` — the enumeration layout (for "N types/categories", show them ALL)
- `kind: "grid"` with `grid: ["Worrier", "Pessimist", …]` renders a wrapping,
  auto-shrinking, **numbered** grid that holds up to ~12 short labels legibly in one 9:16
  frame (1 column for ≤4 items, 2 columns above that; font shrinks as the count grows).
- Use it whenever the list itself is the finding — never reduce a named typology to a
  `bignum` count (see RULE 0 in `scene-arc.md`). Keep each label to 1–2 words. `title` +
  `sub` frame it. Falls back to `chips` if `grid` is absent.
- `chips` (vertical stack) is for **≤5** items only; 6+ overflow — use `grid`.

## Study-specific guidance
- **Core payload on screen (RULE 0).** Decide the one thing the viewer must SEE, and make
  sure a scene shows it as text. Assume muted playback: anything only in `vo` didn't land.
  If a layout can't hold the payload, use `grid` or split scenes — never cut it silently.
- **Kicker carries the framing.** Beat 1's kicker should read `NEW STUDY: <FIELD>` (colon,
  not a dash) so "New Study" and the science area are on screen immediately.
- **Numbers must match `source.md`** and the caption. The bar labels and bignum are the
  most-screenshotted frames — get them exactly right.
- **Journal + year** belongs in the study scene's `sub` (credibility, and it dates the
  claim).
- **The `ask-yourself` scene (beat 6) is required** and authored fresh per study —
  a reflective question, never advice.

## The two hard rules (repeat, because they're the ones people break)
- **VOICEOVER RULE:** no comma-separated enumerations in any `vo`.
- **TEXT RULE (no em dashes, no middle dots):** never put an em dash (—) or a
  middle-dot/bullet (• ·) in any on-screen string or the caption. Rephrase with a comma,
  a colon, "or"/"vs", or a line break.

Output is always 1080×1920, 30fps. Keep the whole video 55–75s.
