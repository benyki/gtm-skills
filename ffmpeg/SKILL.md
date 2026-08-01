---
name: ffmpeg
description: Practical FFmpeg and FFprobe skill for this machine. Use when an agent needs to inspect media, trim or concatenate clips, resize or reformat video, extract or replace audio, convert formats, capture frames, speed up a clip, zoom-fill and center-crop a clip to a target canvas, burn in subtitles, work with SRT or ASS subtitle styling, or reliably resolve the correct ffmpeg/libass-enabled binaries in local, cron, or agent environments.
---

# FFmpeg

Use this skill to get productive with ffmpeg quickly on this machine.

It covers the most common operations:
- probe media with ffprobe
- trim, crop, scale, pad, and transcode video
- extract, replace, mix, or normalize audio
- capture still frames or short clips
- concatenate clips safely
- speed up clips
- zoom-fill and center-crop clips to a target canvas
- burn subtitles with SRT or ASS
- handle machine-specific ffmpeg binary resolution

## Machine-specific binary rule

Prefer these binaries on this machine:

```bash
/opt/homebrew/bin/ffmpeg
/opt/homebrew/bin/ffprobe
```

Why:
- the installed Homebrew ffmpeg build includes `libass`
- subtitle workflows need `subtitles` and `ass` filters
- agent and cron environments may not have the same PATH as interactive shells

Do not assume plain `ffmpeg` resolves correctly in unattended runs.

## Resolution order

Resolve binaries in this order:
1. `FFMPEG_BIN` and `FFPROBE_BIN`
2. `/opt/homebrew/bin/ffmpeg` and `/opt/homebrew/bin/ffprobe`
3. shell PATH lookup

If reliability matters, use absolute paths or explicit env vars.

## Start here

1. Read `references/common-commands.md` for the fastest useful commands.
2. Read `references/subtitles.md` before any subtitle burn-in or styling work.
3. Use `scripts/speed-up-clip.sh` when the task is specifically to speed a clip up by x2, x5, x10, or another factor above 1.
4. Use `scripts/zoom-fill-center.sh` when the task is to make a clip fill the whole frame while keeping the crop centered.
5. If a workflow needs the shared event text-overlay style, also use the existing `ffmpeg-text-overlay-style` support skill.
6. If ffmpeg behaves differently in cron, app, or agent contexts, read `references/troubleshooting.md`.

## Core rules

- Use `ffprobe` for metadata, not string parsing from ffmpeg logs.
- Re-encode when filters are applied.
- Use `-c:v copy` or `-c:a copy` only when that stream is untouched.
- Add `-movflags +faststart` for final MP4 files intended for web delivery.
- Prefer H.264 + AAC + `yuv420p` unless a task clearly needs another format.
- Use absolute paths in automation.
- Treat subtitle styling as a libass problem, not a drawtext hack, unless the task truly wants free-position text overlays.

## Included scripts

### `scripts/speed-up-clip.sh`

Use for simple clip acceleration.

Examples:

```bash
bash scripts/speed-up-clip.sh --factor 2 /abs/path/input.mp4
bash scripts/speed-up-clip.sh --factor 5 /abs/path/input.mp4
bash scripts/speed-up-clip.sh 10 /abs/path/input.mp4
```

Behavior:
- speeds video with `setpts=PTS/factor`
- speeds audio with chained `atempo` filters when needed
- writes `<name>.speed-<factor>x.mp4`

### `scripts/zoom-fill-center.sh`

Use when the clip should fill a target canvas fully, with centered crop instead of letterboxing.

Examples:

```bash
bash scripts/zoom-fill-center.sh --target 9x16 /abs/path/input.mp4
bash scripts/zoom-fill-center.sh --target square /abs/path/input.mp4
bash scripts/zoom-fill-center.sh 16x9 /abs/path/input.mp4
```

Behavior:
- scales with `force_original_aspect_ratio=increase`
- center-crops to the final canvas
- writes `<name>.zoom-fill-<target>.mp4`

## Subtitle guidance

For subtitles, choose among three paths:

1. **Burn SRT quickly** using `subtitles=`
   - best for straightforward caption burn-in
2. **Burn ASS** using `ass=`
   - best for precise styling and positioning
3. **Use `ffmpeg-text-overlay-style`**
   - best for the shared event-promo look on this machine

Read `references/subtitles.md` for quoting, font, style, and debugging details.

## References

- `references/common-commands.md`
  - day-one ffmpeg and ffprobe commands
- `references/subtitles.md`
  - SRT, ASS, libass, styling, and subtitle burn-in patterns
- `references/troubleshooting.md`
  - PATH issues, missing filters, and failure diagnosis
