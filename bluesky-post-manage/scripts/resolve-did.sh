#!/usr/bin/env bash
# Resolve a Bluesky handle to its DID. No auth required.
#
# Usage:
#   bash resolve-did.sh alice.bsky.social
#   ./resolve-did.sh alice.bsky.social

set -euo pipefail

if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  echo "usage: resolve-did.sh <handle>"
  echo "example: resolve-did.sh alice.bsky.social"
  exit 1
fi

HANDLE="$1"
URL="https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle?handle=${HANDLE}"

# Try to use jq if present for pretty extraction; otherwise print raw JSON.
if command -v jq >/dev/null 2>&1; then
  curl -fsSL "$URL" | jq -r '.did'
else
  curl -fsSL "$URL"
  echo
fi
