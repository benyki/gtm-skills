# Common commands

Use the preferred binaries on this machine:

```bash
FFMPEG_BIN=/opt/homebrew/bin/ffmpeg
FFPROBE_BIN=/opt/homebrew/bin/ffprobe
```

## Verify build and subtitle support

```bash
$FFMPEG_BIN -version
$FFMPEG_BIN -filters 2>/dev/null | rg '(^| )subtitles|(^| )ass|(^| )drawtext|(^| )overlay'
```

Look for `--enable-libass` and filters such as `subtitles` and `ass`.

## Probe duration

```bash
$FFPROBE_BIN -v error \
  -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  input.mp4
```

## Probe main stream info

```bash
$FFPROBE_BIN -v error \
  -select_streams v:0 \
  -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt \
  -of default=noprint_wrappers=1 \
  input.mp4
```

## List streams

```bash
$FFPROBE_BIN -v error -show_streams -show_format input.mp4
```

## Trim and re-encode

```bash
$FFMPEG_BIN -y \
  -i input.mp4 \
  -ss 00:00:02 \
  -t 4 \
  -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4
```

## Fast trim with stream copy

Use only when cut accuracy is acceptable and no filters are applied.

```bash
$FFMPEG_BIN -y \
  -ss 00:00:02 -i input.mp4 -t 4 \
  -c copy \
  output.mp4
```

## Scale and pad to vertical 1080x1920

```bash
$FFMPEG_BIN -y \
  -i input.mp4 \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4
```

## Crop

```bash
$FFMPEG_BIN -y \
  -i input.mp4 \
  -vf "crop=1080:1080:420:0" \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a copy \
  output.mp4
```

## Extract audio

```bash
$FFMPEG_BIN -y -i input.mp4 -vn -c:a mp3 -b:a 192k output.mp3
```

## Replace audio with background track

```bash
$FFMPEG_BIN -y \
  -i video.mp4 \
  -stream_loop -1 -i music.mp3 \
  -filter_complex "[1:a]volume=0.08[a]" \
  -map 0:v -map "[a]" \
  -c:v copy \
  -c:a aac -b:a 128k \
  -shortest \
  -movflags +faststart \
  output.mp4
```

## Mix original audio with music

```bash
$FFMPEG_BIN -y \
  -i video.mp4 \
  -stream_loop -1 -i music.mp3 \
  -filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.08[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4
```

## Capture a frame

```bash
$FFMPEG_BIN -y -ss 00:00:03 -i input.mp4 -frames:v 1 frame.png
```

## Extract a clip preview GIF

```bash
$FFMPEG_BIN -y \
  -ss 00:00:02 -t 3 -i input.mp4 \
  -vf "fps=12,scale=480:-1:flags=lanczos" \
  preview.gif
```

## Concatenate matching MP4 files

First create a list file:

```text
file '/abs/path/clip1.mp4'
file '/abs/path/clip2.mp4'
file '/abs/path/clip3.mp4'
```

Then run:

```bash
$FFMPEG_BIN -y -f concat -safe 0 -i list.txt -c copy merged.mp4
```

If codecs or parameters do not match, re-encode instead of copying.

## Speed up a clip

Use the helper script for the quickest path:

```bash
bash ~/.agents/skills/ffmpeg/scripts/speed-up-clip.sh --factor 2 /abs/path/input.mp4
bash ~/.agents/skills/ffmpeg/scripts/speed-up-clip.sh --factor 5 /abs/path/input.mp4
bash ~/.agents/skills/ffmpeg/scripts/speed-up-clip.sh --factor 10 /abs/path/input.mp4
```

Raw ffmpeg pattern:

```bash
$FFMPEG_BIN -y \
  -i input.mp4 \
  -filter_complex "[0:v]setpts=PTS/2[v];[0:a]atempo=2.0[a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 160k \
  -movflags +faststart \
  output.mp4
```

For factors above 2, chain `atempo`, for example x5:

```bash
[0:a]atempo=2.0,atempo=2.0,atempo=1.25[a]
```

## Zoom-fill center crop

Use the helper script when the clip should take the full frame without padding:

```bash
bash ~/.agents/skills/ffmpeg/scripts/zoom-fill-center.sh --target 9x16 /abs/path/input.mp4
bash ~/.agents/skills/ffmpeg/scripts/zoom-fill-center.sh --target square /abs/path/input.mp4
```

Raw ffmpeg pattern:

```bash
$FFMPEG_BIN -y \
  -i input.mp4 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 160k \
  -movflags +faststart \
  output.mp4
```

This keeps the crop centered by default.

## Convert to audio waveform video or silent proxy

### Silent proxy

```bash
$FFMPEG_BIN -y -i input.mov -an -c:v libx264 -preset veryfast -crf 24 proxy.mp4
```

### Audio waveform render

```bash
$FFMPEG_BIN -y -i input.mp3 \
  -filter_complex "showwaves=s=1280x720:mode=line:colors=white,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 22 \
  -c:a aac -b:a 192k \
  output.mp4
```
