#!/usr/bin/env bash
# Scaffold a new video factory working folder.
# Usage: init-workflow.sh <working-folder> <theme-name>
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <working-folder> <theme-name>" >&2
  exit 1
fi

WORK_DIR="${1/#\~/$HOME}"
THEME="$2"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REF="$SKILL_DIR/references"
DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

mkdir -p \
  "$WORK_DIR/clips/90s" \
  "$WORK_DIR/final" \
  "$WORK_DIR/music"

substitute() {
  sed -e "s|{{THEME}}|$THEME|g" -e "s|{{DATE}}|$DATE|g" "$1"
}

if [[ ! -f "$WORK_DIR/video-template.md" ]]; then
  substitute "$REF/video-template.md.tpl" > "$WORK_DIR/video-template.md"
  echo "wrote $WORK_DIR/video-template.md"
else
  echo "skip   $WORK_DIR/video-template.md (exists)"
fi

if [[ ! -f "$WORK_DIR/online-search-prompt.md" ]]; then
  substitute "$REF/online-search-prompt.md.tpl" > "$WORK_DIR/online-search-prompt.md"
  echo "wrote $WORK_DIR/online-search-prompt.md"
else
  echo "skip   $WORK_DIR/online-search-prompt.md (exists)"
fi

if [[ ! -f "$WORK_DIR/payload.json" ]]; then
  substitute "$REF/payload.json.tpl" > "$WORK_DIR/payload.json"
  echo "wrote $WORK_DIR/payload.json"
else
  echo "skip   $WORK_DIR/payload.json (exists)"
fi

if [[ ! -f "$WORK_DIR/runs.json" ]]; then
  substitute "$REF/runs.json.tpl" > "$WORK_DIR/runs.json"
  echo "wrote $WORK_DIR/runs.json"
else
  echo "skip   $WORK_DIR/runs.json (exists)"
fi

echo
echo "factory scaffolded at $WORK_DIR"
echo "next steps:"
echo "  1. edit $WORK_DIR/video-template.md with the approved 3-line template"
echo "  2. download backgrounds:  yt-dlp ... -o '$WORK_DIR/clips/%(id)s.%(ext)s'"
echo "  3. slice 90s clips:       $SKILL_DIR/scripts/slice-90s.sh '$WORK_DIR/clips' '$WORK_DIR/clips/90s'"
echo "  4. run the search prompt to fill payload.json"
echo "  5. render:                $SKILL_DIR/scripts/render-from-payload.py --working-folder '$WORK_DIR' -n 10"
