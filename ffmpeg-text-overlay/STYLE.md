# Default Style Reference

Use this file when you need the exact shared text-overlay style or a raw ffmpeg command template.

The machine-readable source of truth is `./ressources/text-overlay-style.json`.
The shared style defaults to the bundled `TikTok Sans` variable font asset at `./ressources/TikTokSans/TikTokSans-VariableFont_opsz,slnt,wdth,wght.ttf`. The helper resolves that file automatically, converts SRT to a temporary ASS file, applies the shared semibold `\b600` weight override, and passes the font directory into ffmpeg/libass.
Each render also leaves three sidecars next to the output by default:
- `{out.stem}.resolved.ass`
- `{out.stem}.overlay-log.json`
- `{out.stem}.ffmpeg.log`

## Shared ASS Defaults

```text
Fontname=TikTok Sans
PlayRes=video width x video height
Overlay position=33% from the top
Fontsize=74 at 1080 width, scaled from width
Outline=5 at 1080 width, scaled from width
Spacing=-2.2 at 1080 width, scaled from width
Line height=1.18x font size
Paragraph gap=0.5x font size for blank-line paragraph breaks (`\n\n`)
WrapStyle=2
BorderStyle=1
Shadow=0
Weight=SemiBold (600)
```

## Default font directory

```text
Use the directory that contains `./ressources/TikTokSans/TikTokSans-VariableFont_opsz,slnt,wdth,wght.ttf`. The helper script resolves this automatically; override `fontsdir` only when you intentionally want a different bundle.
```

## Raw ffmpeg template

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py \
  --input /abs/path/in.mp4 \
  --subtitles /abs/path/subtitles.srt \
  --out /abs/path/out.mp4 \
  --write-resolved-ass /abs/path/resolved.ass

"${FFMPEG_BIN:-ffmpeg}" -y \
  -i /abs/path/in.mp4 \
  -vf "subtitles=filename='/abs/path/resolved.ass':fontsdir='~/.agents/skills/ffmpeg-text-overlay/ressources/TikTokSans'" \
  -c:v libx264 -preset slow -crf 18 -c:a copy -movflags +faststart \
  /abs/path/out.mp4
```

## Helper-script template

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py \
  --input /abs/path/in.mp4 \
  --subtitles /abs/path/subtitles.srt \
  --out /abs/path/out.mp4
```

Inspect the exact style math and sidecar paths:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py --print-style
```

Adjust the shared anchor position when needed:

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/render_subtitles_with_default_style.py \
  --input /abs/path/in.mp4 \
  --subtitles /abs/path/subtitles.srt \
  --out /abs/path/out.mp4 \
  --overlay-position-pct 30
```

## Smoke test

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/test_default_tiktok_font.py
```

## Layout test

```bash
python3 ~/.agents/skills/ffmpeg-text-overlay/scripts/test_ass_overlay_layout.py
```

## Hook-overlay workflow

If you need to burn one short hook line rather than an existing SRT:

1. Write a temporary one-cue `.srt`.
2. Run the helper script with that SRT.
3. Delete the temporary file if you no longer need it.
