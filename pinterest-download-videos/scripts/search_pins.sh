#!/usr/bin/env bash
# Print the first N video pin IDs for a Pinterest keyword to stdout.
# Usage: search_pins.sh "<keyword>" <count>
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: $0 \"<keyword>\" <count>" >&2
  exit 2
fi

KEYWORD="$1"
COUNT="$2"
PAGE_SIZE=$((COUNT * 2 + 5))  # over-fetch to survive non-video results

# URL-encode the keyword for source_url
ENCODED_KW=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$KEYWORD")

DATA_JSON=$(python3 -c '
import json, sys
q = sys.argv[1]
n = int(sys.argv[2])
print(json.dumps({"options":{"query":q,"scope":"videos","page_size":n},"context":{}}))
' "$KEYWORD" "$PAGE_SIZE")

curl -sG "https://www.pinterest.com/resource/BaseSearchResource/get/" \
  --data-urlencode "source_url=/search/videos/?q=${ENCODED_KW}" \
  --data-urlencode "data=${DATA_JSON}" \
  -H "user-agent: Mozilla/5.0" \
  -H "x-pinterest-pws-handler: www/search/[scope].js" \
  -H "accept: application/json" \
| python3 -c '
import sys, json
d = json.load(sys.stdin)
results = d.get("resource_response", {}).get("data", {}).get("results", []) or []
count = int(sys.argv[1])
emitted = 0
for r in results:
    if not isinstance(r, dict):
        continue
    if not r.get("videos"):
        continue
    pid = r.get("id")
    if not pid:
        continue
    print(pid)
    emitted += 1
    if emitted >= count:
        break
if emitted == 0:
    sys.exit("no video results for query")
' "$COUNT"
