#!/usr/bin/env bash
# post_study_tiktok.sh CONFIG.json MP4 CAPTION.txt SLUG [DATE]
#   Stage a science-brand study video for viralwatch (its own lane), then DIRECT_POST it to
#   TikTok @your-handle via Upload-Post, and poll to the live URL.
#
#   1. stage_viralwatch.py  -> stage mp4 + sidecar under video-study/final (stem
#                            video-study-<slug>-<date>, no collision with dream-desk)
#   2. upload_post.py post -> DIRECT_POST to @your-handle, --aigc (synthetic voice),
#                             --tag local-video-app-study, archives into published/ + ledger
#   3. poll status --request-id until terminal, print the TikTok URL
#
# Env: TIKTOK_USER (default your-handle), ENVFILE (default ~/.agents/.env).
# Outward-facing/irreversible — run only with the user's explicit go-ahead. On cap/error
# it leaves the clip staged and exits non-zero (retry later, delete nothing).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
UP="$HOME/.agents/skills/upload-post/scripts/upload_post.py"
CFG="${1:?usage: post_study_tiktok.sh CONFIG.json MP4 CAPTION.txt SLUG [DATE]}"
MP4="${2:?need MP4}"
CAP="${3:?need CAPTION.txt}"
SLUG="${4:?need SLUG}"
DATE="${5:-}"
USER="${TIKTOK_USER:-your-handle}"
ENVFILE="${ENVFILE:-$HOME/.agents/.env}"
LEDGER="${POSTS_LEDGER:-$HOME/.agents/runs/posts.jsonl}"

set -a; . "$ENVFILE"; set +a

STAGED=$(python3 "$HERE/stage_viralwatch.py" "$CFG" "$MP4" --slug "$SLUG" ${DATE:+--date "$DATE"})
echo "staged: $STAGED"
ARCHIVED="$(dirname "$STAGED")/published/$(basename "$STAGED")"

resp=$(python3 "$UP" post --user "$USER" --platform tiktok \
  --file "$STAGED" --caption "$(cat "$CAP")" \
  --aigc --tag local-video-app-study --wait 2>&1)
echo "$resp"

rid=$(printf '%s' "$resp" | grep -oE 'up_[a-z0-9]+' | head -1 || true)
if [ -z "$rid" ]; then
  echo "no request_id in response — inspect above (post may have failed)"; exit 1
fi

for i in $(seq 1 16); do
  out=$(python3 "$UP" status --request-id "$rid" 2>/dev/null || true)
  st=$(printf '%s' "$out" | python3 -c "import json,sys;print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
  echo "status[$i]: ${st:-?}"
  case "$st" in
    completed|success|done)
      python3 - "$out" "$ARCHIVED" "$USER" "$rid" "$LEDGER" << 'PY'
import json, os, sys, datetime
out, archived, user, rid, ledger = sys.argv[1:6]
r = (json.loads(out).get("results") or [{}])[0]
url = (r.get("post_url") or "").strip()
if url.startswith("http"):
    rec = {
        "posted_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline": "upload-post", "skill": "local-video-app-study", "account": user,
        "platforms": ["tiktok"], "status": "feed", "delivery": "feed",
        "request_id": rid, "post_id": r.get("platform_post_id"), "post_url": url,
        "file_archived": archived, "tag": "local-video-app-study", "aigc": True,
    }
    rec = {k: v for k, v in rec.items() if v is not None}
    with open(os.path.expanduser(ledger), "a") as f:
        f.write(json.dumps(rec) + "\n")
    print("POSTED ->", url, "(ledger updated with live URL — viralwatch will show the link)")
else:
    print("POSTED -> no public URL yet (status:", r.get("status"), ") — ledger left as-is")
PY
      exit 0 ;;
    failed|error)
      echo "POST FAILED:"; echo "$out"; exit 1 ;;
    *) sleep 15 ;;
  esac
done
echo "still processing after polling — check later: $UP status --request-id $rid"
