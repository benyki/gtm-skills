# POST — Korean series-a (post ONE video/run to TikTok, then report)

Self-contained cron routine. Posts **one** Korean series-a video to the Korean TikTok
account via the upload-post skill, then reports to Discord. Runs on this machine, fresh context.

**One rule above all: post at most ONE video per run, and never the same theme twice.**

---

## CONFIG (the only lines you change per-account)
```bash
KR_HANDLE="your-korean-handle"     # the connected TikTok handle to post to (no leading @)
                                   # ⚠️ must EXACTLY match the connected Korean account in
                                   # Upload-Post. If the Korean account is connected under a
                                   # different handle, set it here.
FINAL=~/code/<project>/world/videos/series-a-ko/final   # KOREAN-ONLY library
WEBHOOK="https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
UP=~/.agents/skills/upload-post/scripts/upload_post.py
```
⚠️ `FINAL` must contain **only Korean** clips. Never point it at another language's render
folder (`series-a/final` = French, `series-a-sp/final` = Spanish, `series-a-jp/final`
= Japanese, `series-a-ar/final` = Arabic) — that would post the wrong language to this
account. Posted clips are auto-moved to `$FINAL/published/`.

⚠️ PREREQUISITE: a Korean TikTok account must be connected in Upload-Post. If `$KR_HANDLE`
isn't connected, this routine **STOPs and reports** — it never falls back to another account.

## 1. SETUP
```bash
set -a; . ~/.agents/.env; set +a     # needs UPLOADPOST_API_KEY
```
If the key is missing, stop and report the error.

## 2. RESOLVE THE PROFILE
```bash
PROFILE=$(python3 "$UP" profiles --json \
  | jq -r --arg h "${KR_HANDLE#@}" '(.profiles // .)[] |
      select((.social_accounts.tiktok.handle // "" | ascii_downcase) == ($h | ascii_downcase))
      | .username')
```
If `$PROFILE` is empty → **STOP**, report: `"$KR_HANDLE not connected in Upload-Post — connect it in the dashboard first."`

## 3. PICK A VIDEO — run this block, then act on its output
Dedupe **by theme, not filename**: the renderer sometimes re-renders a posted theme under a new
timestamp, so a filename check would let it post twice. A theme counts as posted if its slug is in
`published/` **or** in the append-only `posted-themes.log` (which survives `published/` being cleaned).
```bash
posted=$( { ls "$FINAL"/published/*.mp4 2>/dev/null | sed -E 's#.*/##; s/-20[0-9]{6}T.*//';
            cat "$FINAL/posted-themes.log" 2>/dev/null; } | sort -u )
CHOSEN=""; THEME=""
while IFS= read -r f; do
  t=$(basename "$f" | sed -E 's/-20[0-9]{6}T.*//')          # slug before the -<timestamp>
  grep -qxF "$t" <<<"$posted" && continue                    # already posted → skip
  CHOSEN="$f"; THEME="$t"; break                             # oldest un-posted wins
done < <(ls -tr "$FINAL"/*.mp4 2>/dev/null)                  # oldest-first, top-level only
if [ -z "$CHOSEN" ]; then
  ls "$FINAL"/*.mp4 >/dev/null 2>&1 && echo "NONE all-posted" || echo "NONE queue-empty"
else
  echo "PICK $CHOSEN $THEME"
fi
```
- `NONE queue-empty` → report `"queue empty — nothing to post"`, stop cleanly.
- `NONE all-posted` → report `"nothing NEW to post (all remaining themes already posted)"`, stop cleanly.
- `PICK <file> <theme>` → that's your video; continue.

## 4. WRITE A KOREAN CAPTION (vary it run to run, match the video's concept)
Short, natural caption for the theme + 4–6 hashtags. The library is single-concept per clip
(food OR love — never blended), so match the caption to the concept:
- **Food themes** → `#한국어 #learnkorean #korean #koreanfood #먹방 #fyp` + 1–2 theme tags.
  > e.g. `korean-bbq` → `삼겹살 먹으러 가자 🥓🇰🇷 #한국어 #learnkorean #koreanfood #kbbq #fyp`
- **Love themes** → `#한국어 #learnkorean #korean #kdrama #연애 #fyp` + 1–2 theme tags.
  > e.g. `confession` → `좋아하는 사람한테 써봐 ❤️🇰🇷 #한국어 #learnkorean #korean #kdrama #fyp`
(The exact on-screen words are in the clip's sidecar `${CHOSEN%.mp4}.json` → `.words[]` — each has
`prompt`/`answer`/`native` (Hangul); the theme slug tells you food vs love.)

## 5. POST (publish now, wait for the result)
```bash
python3 "$UP" post --file "$CHOSEN" --user "$PROFILE" --caption "<caption>" --when now --async --wait
```
- **Success (public feed):** the skill moves the file into `$FINAL/published/`. Record the theme so a
  future re-render is still caught even if `published/` is later cleaned:
  ```bash
  grep -qxF "$THEME" "$FINAL/posted-themes.log" 2>/dev/null || echo "$THEME" >> "$FINAL/posted-themes.log"
  ```
- **⚠️ INBOX fallback** (`delivery=INBOX` / "Video sent to Inbox" = the app-wide active-user cap):
  it did **not** reach the public feed. Still log the theme (the clip was consumed), but say so
  explicitly in the report so it isn't mistaken for a live post.
- **Failure:** capture the first error line; do **not** move the file; do **not** log the theme; report it.

## 6. REPORT (one Discord message, <1900 chars, no mp4 attached)
```bash
N=$(ls "$FINAL"/*.mp4 2>/dev/null | wc -l | tr -d ' ')
TMP=$(mktemp); cat > "$TMP" <<JSON
{"content":"📲 $KR_HANDLE — $(date -u +%H:%MZ)\n<✅ posted: $THEME — <sizeMB>MB — req <id>  |  ⚠️ inbox: $THEME (not on feed)  |  ❌ $THEME: <error>  |  ℹ️ <queue empty / nothing new>>\nRemaining in queue: $N"}
JSON
curl -sS -X POST -H "Content-Type: application/json" --data-binary @"$TMP" "$WEBHOOK"; rm -f "$TMP"
```

## NOTES
- **One video per run.** Keep the cron interval **≥ 6h** (TikTok/Upload-Post guidance: 3–4 posts/day
  max per account) so the account doesn't read as a bot.
- `published/` + `posted-themes.log` are the single source of truth for "already posted" — never repost.
- Posting via the upload-post skill keeps the publish ledger correct: `published/` + the sidecar
  `<stem>.json` move together and `platform-status.json` is updated.
- Scheduling: create a scheduled task pointing at this file by absolute path; hit **Run now** once to
  pre-approve the tools. Sibling routine `GENERATE-korean.md` keeps the queue full.
