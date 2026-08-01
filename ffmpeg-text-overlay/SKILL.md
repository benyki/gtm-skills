---
name: ffmpeg-text-overlay
description: Shared default ffmpeg/libass text overlay style for short-form / event promo videos. Use when a skill or workflow needs the standard TikTok-Sans subtitle or hook-overlay look, a stable default sans-serif font, reusable command templates, or a helper script instead of inlining force_style props. Bundles the helper script (SRT→ASS, libass burn-in), the machine-readable style JSON, and the bundled TikTok Sans + Inter font assets.
user-invocable: true
---

# FFmpeg Text Overlay

Use this support skill whenever a workflow needs the shared short-form / event text-overlay look (white TikTok-Sans SemiBold with black outline, centered at 33% from top, scaled from the video width).

This skill centralizes:
- the machine-readable style contract (`ressources/text-overlay-style.json`)
- the shared SRT-to-ASS conversion step
- the shared default font choice and bundled font asset resolution
- a reusable helper script for subtitle burn-in
- copy-paste command templates

## Support-skill role

This is a reusable support skill. Final video skills should call this helper script instead of repeating long inline `force_style` strings or rebuilding the ASS layout rules from memory.

Originally lived as `ffmpeg-text-overlay-style` inside `next-factory/skills-v1/`; promoted to `_shared/skills/` so every machine and every project gets the same overlay look.

## Default style contract

Machine-readable authority file:
- `./ressources/text-overlay-style.json`

Default family:
- font family: `TikTok Sans`
- bundled default font file: `./ressources/TikTokSans/TikTokSans-VariableFont_opsz,slnt,wdth,wght.ttf`
- PlayRes: resolved from the input video
- anchor position: `33%` from the top
- font size: `74` at `1080` width, scaled from the input width
- primary color: white
- outline color: black
- border style: `1`
- wrap style: `2`
- outline: `5` at `1080` width, scaled from the input width
- letter spacing: `-2.2` at `1080` width, scaled from the input width
- line height: `1.18x` font size
- paragraph gap for manual blank-line paragraph breaks (`\n\n`): `0.5x` font size
- single manual `\n` stays in the same paragraph and does not add extra vertical gap
- shadow: `0`
- explicit position: each generated ASS dialogue line gets `\pos(x,y)`
- weight: `SemiBold (600)`

Shared reflow limits:
- Latin/default: `28` chars per line
- RTL: `20` chars per line
- Abugida: `22` chars per line
- CJK: `13` chars per line

Bundled TikTok Sans assets:
- `./ressources/TikTokSans/TikTokSans-VariableFont_opsz,slnt,wdth,wght.ttf`
- `./ressources/TikTokSans/TikTokSans-Medium.ttf`
- `./ressources/TikTokSans/TikTokSans12pt-Regular.ttf`
- `./ressources/TikTokSans/TikTokSans12pt-Bold.ttf`
- `./ressources/TikTokSans/TikTokSans12pt-RegularItalic.ttf`
- `./ressources/TikTokSans/TikTokSans12pt-BoldItalic.ttf`
- `./ressources/TikTokSans/OFL.txt`

## Preferred helper script

Use the helper script when you want the shared default styling without rewriting the ffmpeg filter by hand:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py \
  --input /abs/path/in.mp4 \
  --subtitles /abs/path/subtitles.srt \
  --out /abs/path/out.mp4
```

The helper now converts SRT to a temporary ASS file internally, reads the shared style values from `./ressources/text-overlay-style.json`, and then burns that resolved ASS file through ffmpeg/libass.
Every render also writes sidecar analysis files next to the output by default:
- `{out.stem}.resolved.ass`
- `{out.stem}.overlay-log.json`
- `{out.stem}.ffmpeg.log`

Print the exact resolved style and optional font path:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py --print-style
```

Override the default `33%` vertical anchor if art direction needs it:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py \
  --input /abs/path/in.mp4 \
  --subtitles /abs/path/subtitles.srt \
  --out /abs/path/out.mp4 \
  --overlay-position-pct 30
```

Write the generated ASS file if you want to inspect the exact resolved script:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py \
  --input /abs/path/in.mp4 \
  --subtitles /abs/path/subtitles.srt \
  --out /abs/path/out.mp4 \
  --write-resolved-ass /abs/path/resolved.ass
```

Override the default sidecar log paths only when a workflow needs them elsewhere:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py \
  --input /abs/path/in.mp4 \
  --subtitles /abs/path/subtitles.srt \
  --out /abs/path/out.mp4 \
  --log-json-path /abs/path/out.overlay-log.json \
  --ffmpeg-log-path /abs/path/out.ffmpeg.log
```

Run the smoke test to verify ffmpeg/libass resolves the shared default to the bundled `TikTokSans-VariableFont_opsz,slnt,wdth,wght.ttf` asset:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/test_default_tiktok_font.py
```

Run the layout test to verify the shared ASS generation, wrapping, and explicit positioning rules:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/test_ass_overlay_layout.py
```

Run the portrait render test to verify a long sentence reflows correctly, sidecar files are written, and a preview frame can be extracted from the rendered output:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/test_portrait_long_text_render.py
```

When you run this visual test, always share the generated preview screenshot in chat using the `preview_frame_path` reported by the script.

Run this regression command every time this skill changes so the font-resolution path, ASS layout contract, and end-to-end portrait render stay covered:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/test_default_tiktok_font.py && \
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/test_ass_overlay_layout.py && \
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/test_portrait_long_text_render.py
```

## Raw ffmpeg template

If a workflow needs a raw ffmpeg command instead of the helper script, first generate the resolved ASS file with the helper. Do not rebuild the shared ASS layout rules from memory.

## Rules

- All video creators that use this look must call `scripts/render_subtitles_with_default_style.py` or shared functions defined in that file.
- Treat this skill as the source of truth for the default event subtitle and hook-overlay look.
- Do not duplicate the ASS layout config inside `event-*` skill docs.
- Do not replace the shared libass burn with local `drawtext` or ad hoc subtitle filter assembly.
- Prefer the helper script for examples in other skills.
- Keep any optional custom font assets here instead of pretending each event skill bundles its own font folder.
- If the default style changes, update this skill first, then update any runtime code that intentionally mirrors it.

## Alphabet Mapping Instructions

These mappings are documentation only for now. The shared helper does not auto-switch fonts for non-Latin scripts yet.

- Hebrew: `NotoSansHebrew-Bold.ttf`
- Arabic: `NotoSansArabic-Bold.ttf`
- Urdu: `NotoSansArabic-Bold.ttf`
- Hindi: `NotoSansDevanagari-Bold.ttf`
- Bengali: `NotoSansDevanagari-Bold.ttf`
- Japanese: `NotoSansJP-Bold.ttf`
- Korean: `NotoSansKR-Bold.ttf`
- Chinese: `NotoSansJP-Bold.ttf`
- Thai: `NotoSansThai-Bold.ttf`
