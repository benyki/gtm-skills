# Subtitles

Use subtitles when the task needs dialogue, captions, translations, or styled on-screen text synced to time.

## First principle

On this machine, subtitle burn-in depends on libass support.
Use:

```bash
/opt/homebrew/bin/ffmpeg
```

Check support:

```bash
/opt/homebrew/bin/ffmpeg -version
/opt/homebrew/bin/ffmpeg -filters 2>/dev/null | rg '(^| )subtitles|(^| )ass'
```

## Choose the right path

### SRT plus `subtitles=`

Use when:
- captions already exist as `.srt`
- simple styling is enough
- you want quick subtitle burn-in

```bash
/opt/homebrew/bin/ffmpeg -y \
  -i input.mp4 \
  -vf "subtitles=filename='/abs/path/subtitles.srt'" \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a copy \
  output.mp4
```

### SRT plus `force_style`

Use when:
- you need font, alignment, margin, outline, or weight tweaks
- ASS authoring would be overkill

```bash
/opt/homebrew/bin/ffmpeg -y \
  -i input.mp4 \
  -vf "subtitles=filename='/abs/path/subtitles.srt':force_style='Alignment=2,Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=1.2,Shadow=0,MarginL=60,MarginR=60,MarginV=70,Bold=700'" \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a copy \
  output.mp4
```

Useful `Alignment` values:
- `2` bottom-center
- `8` top-center
- `10` top-center with extended libass positioning patterns often used in examples on this machine

### ASS plus `ass=`

Use when:
- you need precise style control
- line breaks, positioning, or multiple styles matter
- the subtitles are already authored as `.ass`

```bash
/opt/homebrew/bin/ffmpeg -y \
  -i input.mp4 \
  -vf "ass=/abs/path/subtitles.ass" \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a copy \
  output.mp4
```

## Preferred subtitle workflow

1. Start with an SRT file if timing is the main need.
2. Burn with `subtitles=` when default rendering is acceptable.
3. Add `force_style` for quick typography changes.
4. Switch to ASS when exact styling or layout is required.
5. Use the `ffmpeg-text-overlay-style` support skill when the desired look is the shared event-promo overlay style.

## Quoting and path rules

Subtitle filters are fragile when filenames contain spaces, commas, apostrophes, or shell-active characters.

Safer patterns:
- prefer absolute paths
- wrap the full `-vf` expression in double quotes
- wrap subtitle filenames in single quotes inside the filter when needed

Example:

```bash
-vf "subtitles=filename='~/path with spaces/subtitles.srt'"
```

If escaping becomes painful, write files into a temporary clean path with no spaces.

## Styling tips

### Readability defaults

For general captions:
- white primary text
- black outline
- no shadow or very light shadow
- bottom-center alignment for dialogue captions
- generous left/right margins on mobile exports

### Social/video overlay defaults

For vertical videos:
- increase font size relative to canvas width
- keep two-line wraps readable
- prefer outline over blur-heavy shadow
- preview on a real frame, not only by command inspection

### When to use drawtext instead

Use `drawtext` when the task wants free text overlays not tied to subtitle timing files, such as:
- one hook line
- watermark text
- static labels
- counters or generated diagnostics

Use subtitles or ASS when the text is time-coded dialogue.

## Minimal smoke test

Use this to verify libass works before debugging styles:

```bash
tmpdir=$(mktemp -d)
printf '1\n00:00:00,000 --> 00:00:01,000\nhello libass\n' > "$tmpdir/test.srt"
/opt/homebrew/bin/ffmpeg -y -hide_banner -loglevel error \
  -f lavfi -i color=c=black:s=320x240:d=1 \
  -vf "subtitles='$tmpdir/test.srt'" \
  -frames:v 1 "$tmpdir/out.png"
ls -lh "$tmpdir/out.png"
```

If that outputs an image, subtitle rendering works.

## Common failures

### `No such filter: subtitles`

Cause:
- wrong ffmpeg binary
- libass-free build

Fix:
- use `/opt/homebrew/bin/ffmpeg`
- verify `--enable-libass`

### Font not applied

Cause:
- font name mismatch
- font unavailable to libass

Fix:
- use a font installed on the machine or a workflow that explicitly manages font assets
- prefer ASS or the `ffmpeg-text-overlay-style` support skill for bundled-font workflows

### Weird path parsing

Cause:
- shell quoting or filter quoting issue

Fix:
- simplify file paths
- use absolute paths
- reduce nested quoting

### Subtitle style looks wrong only in automation

Cause:
- different ffmpeg binary in agent/cron environment

Fix:
- use absolute `ffmpeg-full` path or `FFMPEG_BIN`

## Practical rule of thumb

- quick caption burn-in: SRT plus `subtitles=`
- quick typography change: SRT plus `force_style`
- exact art direction: ASS
- shared event style on this machine: `ffmpeg-text-overlay-style`
