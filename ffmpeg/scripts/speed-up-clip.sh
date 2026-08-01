#!/usr/bin/env bash
set -euo pipefail

VIDEO_CRF="${VIDEO_CRF:-18}"
VIDEO_PRESET="${VIDEO_PRESET:-medium}"
AUDIO_BITRATE="${AUDIO_BITRATE:-160k}"
OUTPUT_SUFFIX_PREFIX="${OUTPUT_SUFFIX_PREFIX:-speed}"

resolve_binary() {
  local env_name="$1"
  local preferred_path="$2"
  local fallback_name="$3"
  if [[ -n "${!env_name:-}" ]]; then
    printf '%s\n' "${!env_name}"
  elif [[ -x "$preferred_path" ]]; then
    printf '%s\n' "$preferred_path"
  else
    command -v "$fallback_name"
  fi
}

FFMPEG_BIN="$(resolve_binary FFMPEG_BIN /opt/homebrew/bin/ffmpeg ffmpeg)"

_die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

finder_selection_nul() {
  osascript <<'APPLESCRIPT' | perl -pe 'chomp if eof'
tell application "Finder"
  set sel to selection
  if sel is {} then return ""
  set outList to {}
  repeat with anItem in sel
    set end of outList to POSIX path of (anItem as alias)
  end repeat
end tell
set oldDelims to AppleScript's text item delimiters
set AppleScript's text item delimiters to ASCII character 0
set joined to outList as text
set AppleScript's text item delimiters to oldDelims
return joined
APPLESCRIPT
}

is_video_path() {
  case "$1" in
    *.[Mm][Pp]4|*.[Mm][Oo][Vv]|*.[Mm][Kk][Vv]|*.[Mm]4[Vv]|*.[Ww][Ee][Bb][Mm]|*.[Aa][Vv][Ii]) return 0 ;;
    *) return 1 ;;
  esac
}

build_atempo_chain() {
  local factor="$1"
  python3 - "$factor" <<'PY'
import sys
factor = float(sys.argv[1])
parts = []
while factor > 2.0:
    parts.append("atempo=2.0")
    factor /= 2.0
parts.append(f"atempo={factor:.6f}".rstrip('0').rstrip('.'))
print(','.join(parts))
PY
}

main() {
  local factor=""
  local inputs=()

  if [[ "$#" -gt 0 && "$1" != --* ]]; then
    factor="$1"
    shift
  fi

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --factor)
        [[ "$#" -ge 2 ]] || _die "--factor requires a value"
        factor="$2"
        shift 2
        ;;
      --help|-h)
        cat <<'EOF'
Usage:
  speed-up-clip.sh --factor 2 /abs/path/video.mp4
  speed-up-clip.sh --factor 5
  speed-up-clip.sh 10 /abs/path/video.mp4

Notes:
  - Supports x2, x5, x10 directly and other numeric factors > 1.
  - Uses selected Finder video(s) if no path is provided.
EOF
        exit 0
        ;;
      *)
        inputs+=("$1")
        shift
        ;;
    esac
  done

  [[ -n "$factor" ]] || _die "Missing speed factor"
  [[ "$factor" =~ ^([0-9]+)(\.[0-9]+)?$ ]] || _die "Factor must be numeric"

  python3 - "$factor" <<'PY' >/dev/null
import sys
f = float(sys.argv[1])
assert f > 1.0
PY

  if [[ "${#inputs[@]}" -eq 0 ]]; then
    while IFS= read -r -d '' path; do
      inputs+=("$path")
    done < <(finder_selection_nul)
  fi
  [[ "${#inputs[@]}" -gt 0 ]] || _die "No input files found. Select videos in Finder or pass them explicitly."

  local atempo
  atempo="$(build_atempo_chain "$factor")"

  local input dir base output suffix
  suffix="$(printf '%s' "$factor" | tr '.' '_')x"
  for input in "${inputs[@]}"; do
    is_video_path "$input" || continue
    [[ -f "$input" ]] || _die "Input video does not exist: $input"
    dir="$(cd "$(dirname "$input")" && pwd)"
    base="$(basename "$input")"
    base="${base%.*}"
    output="$dir/$base.$OUTPUT_SUFFIX_PREFIX-$suffix.mp4"

    "$FFMPEG_BIN" -nostdin -y -hide_banner -loglevel error \
      -i "$input" \
      -filter_complex "[0:v]setpts=PTS/${factor}[v];[0:a]${atempo}[a]" \
      -map "[v]" -map "[a]" \
      -c:v libx264 -preset "$VIDEO_PRESET" -crf "$VIDEO_CRF" -pix_fmt yuv420p \
      -c:a aac -b:a "$AUDIO_BITRATE" \
      -movflags +faststart \
      "$output"

    printf '%s\n' "$output"
  done
}

main "$@"
