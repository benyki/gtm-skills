# Troubleshooting

## Check actual binary resolution

```bash
which ffmpeg
which ffprobe
python3 - <<'PY'
import os, shutil
print('PATH=', os.environ.get('PATH'))
print('ffmpeg=', shutil.which('ffmpeg'))
print('ffprobe=', shutil.which('ffprobe'))
PY
```

If reliability matters, bypass PATH entirely:

```bash
export FFMPEG_BIN="/opt/homebrew/bin/ffmpeg"
export FFPROBE_BIN="/opt/homebrew/bin/ffprobe"
```

## Confirm build flags

```bash
/opt/homebrew/bin/ffmpeg -version
```

Look for:

```text
--enable-libass
```

## Confirm required filters

```bash
/opt/homebrew/bin/ffmpeg -filters 2>/dev/null | rg '(^| )subtitles|(^| )ass|(^| )drawtext|(^| )overlay'
```

## If a job works in Terminal but fails in cron or an agent

Assume PATH mismatch first.

Fix options:
1. use absolute binary paths
2. export `FFMPEG_BIN` and `FFPROBE_BIN`
3. update the calling script to resolve binaries explicitly

## If ffmpeg breaks a shell loop that is reading file paths

Cause:
- ffmpeg can consume stdin and interfere with `while read` loops or piped file lists

Fix:
- add `-nostdin` to ffmpeg invocations inside helper scripts
- prefer `find ... -print0` plus `read -d ''` for batch path handling
- avoid feeding a long path list to a subprocess that may read from the same stdin stream

## If stream copy output is broken

Cause:
- cuts did not land on useful keyframes
- codec/container combination is fragile

Fix:
- re-encode instead of copying
- place `-ss` after `-i` for more accurate trimming when re-encoding

## If the output does not play in browsers or chat apps

Fix checklist:
- use `-c:v libx264`
- use `-pix_fmt yuv420p`
- use AAC audio for MP4
- add `-movflags +faststart`

## If subtitles are missing or badly styled

Read `subtitles.md`.

High-probability causes:
- wrong ffmpeg binary
- missing libass support
- bad quoting in `-vf`
- font mismatch
- trying to force complex layout through plain SRT when ASS is the right tool

## If concat fails

Use concat demuxer only when all clips match on codec and main stream properties.
If they differ, normalize or re-encode first.
