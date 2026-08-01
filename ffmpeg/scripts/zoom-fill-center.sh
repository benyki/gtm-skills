#!/usr/bin/env bash
set -euo pipefail

VIDEO_CRF="${VIDEO_CRF:-18}"
VIDEO_PRESET="${VIDEO_PRESET:-medium}"
AUDIO_BITRATE="${AUDIO_BITRATE:-160k}"
OUTPUT_SUFFIX_PREFIX="${OUTPUT_SUFFIX_PREFIX:-zoom-fill}"

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

resolve_dimensions() {
  case "$1" in
    square)
      printf '1080 1080\n'
      ;;
    9x16)
      printf '1080 1920\n'
      ;;
    16x9)
      printf '1920 1080\n'
      ;;
    *)
      if [[ "$1" =~ ^([0-9]+)x([0-9]+)$ ]]; then
        printf '%s %s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
      else
        return 1
      fi
      ;;
  esac
}

main() {
  local target="9x16"
  local inputs=()

  if [[ "$#" -gt 0 && "$1" != --* ]]; then
    target="$1"
    shift
  fi

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --target)
        [[ "$#" -ge 2 ]] || _die "--target requires a value"
        target="$2"
        shift 2
        ;;
      --help|-h)
        cat <<'EOF'
Usage:
  zoom-fill-center.sh --target 9x16 /abs/path/video.mp4
  zoom-fill-center.sh --target square
  zoom-fill-center.sh 16x9 /abs/path/video.mp4

Behavior:
  Scales up and center-crops so the clip fully fills the target canvas.
EOF
        exit 0
        ;;
      *)
        inputs+=("$1")
        shift
        ;;
    esac
  done

  local width height
  read -r width height < <(resolve_dimensions "$target") || _die "Unsupported target: $target"

  if [[ "${#inputs[@]}" -eq 0 ]]; then
    while IFS= read -r -d '' path; do
      inputs+=("$path")
    done < <(finder_selection_nul)
  fi
  [[ "${#inputs[@]}" -gt 0 ]] || _die "No input files found. Select videos in Finder or pass them explicitly."

  local input dir base output suffix
  suffix="$(printf '%s' "$target" | tr -c '[:alnum:]' '-')"
  for input in "${inputs[@]}"; do
    is_video_path "$input" || continue
    [[ -f "$input" ]] || _die "Input video does not exist: $input"
    dir="$(cd "$(dirname "$input")" && pwd)"
    base="$(basename "$input")"
    base="${base%.*}"
    output="$dir/$base.$OUTPUT_SUFFIX_PREFIX-$suffix.mp4"

    "$FFMPEG_BIN" -nostdin -y -hide_banner -loglevel error \
      -i "$input" \
      -vf "scale=${width}:${height}:force_original_aspect_ratio=increase,crop=${width}:${height},format=yuv420p" \
      -c:v libx264 -preset "$VIDEO_PRESET" -crf "$VIDEO_CRF" \
      -c:a aac -b:a "$AUDIO_BITRATE" \
      -movflags +faststart \
      "$output"

    printf '%s\n' "$output"
  done
}

main "$@"
