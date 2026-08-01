#!/usr/bin/env bash
# Shared config loader for tiktok-post-finder.
#
# Config is a markdown file (post-finder-config.md) with one fenced ```json
# block. Prose around the block is for humans; only the JSON is parsed.
#
# Resolution order (first hit wins):
#   1. $CONFIG               explicit path (e.g. --config handled by caller)
#   2. $POST_FINDER_CONFIG   env override
#   3. ./yard/tiktok/post-finder-config.md  walking up from $PWD (project config)
#   4. <skill>/references/post-finder-config.md  (shipped default)

pf_resolve_config() {
  local skill_dir="$1"
  if [ -n "${CONFIG:-}" ]; then echo "$CONFIG"; return; fi
  if [ -n "${POST_FINDER_CONFIG:-}" ] && [ -f "$POST_FINDER_CONFIG" ]; then
    echo "$POST_FINDER_CONFIG"; return
  fi
  local d="$PWD"
  while [ -n "$d" ] && [ "$d" != "/" ]; do
    if [ -f "$d/yard/tiktok/post-finder-config.md" ]; then
      echo "$d/yard/tiktok/post-finder-config.md"; return
    fi
    d="$(dirname "$d")"
  done
  echo "$skill_dir/references/post-finder-config.md"
}

# Extract the first fenced ```json block from a markdown file (echoes JSON, or {}).
pf_config_json() {
  local f="$1"
  [ -f "$f" ] || { echo "{}"; return; }
  local json
  json="$(awk 'BEGIN{f=0} /^```json[[:space:]]*$/{f=1;next} /^```/{if(f)exit} f{print}' "$f")"
  if [ -z "$json" ] || ! printf '%s' "$json" | jq -e . >/dev/null 2>&1; then
    echo "{}"
  else
    printf '%s' "$json"
  fi
}
