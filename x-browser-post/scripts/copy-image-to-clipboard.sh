#!/usr/bin/env bash
# Copy a PNG (or JPEG) file to the macOS clipboard as raw image data,
# so the next `cmd+v` in a browser composer pastes the image inline.
#
# Usage: copy-image-to-clipboard.sh /abs/path/to/image.png
#
# Supports: PNG, JPEG. (GIF would need a different osascript class.)

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: copy-image-to-clipboard.sh <absolute-path-to-image>" >&2
  exit 1
fi

IMG="$1"

if [ ! -f "$IMG" ]; then
  echo "file not found: $IMG" >&2
  exit 1
fi

# Resolve to absolute path
case "$IMG" in
  /*) ABS="$IMG" ;;
  *)  ABS="$PWD/$IMG" ;;
esac

# Pick AppleScript class based on extension
ext_lower=$(echo "${IMG##*.}" | tr '[:upper:]' '[:lower:]')
case "$ext_lower" in
  png)        CLASS='«class PNGf»' ;;
  jpg|jpeg)   CLASS='«class JPEG»' ;;
  *)
    echo "unsupported extension: .$ext_lower (only png/jpg)" >&2
    exit 1
    ;;
esac

osascript -e "set the clipboard to (read (POSIX file \"$ABS\") as $CLASS)"

echo "copied to clipboard: $ABS"
