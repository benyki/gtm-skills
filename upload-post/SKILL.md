---
name: upload-post
description: Publish and schedule videos to TikTok, YouTube, Instagram, X, Threads, Facebook and Bluesky through the Upload-Post API. Use when an agent or the user wants to post/upload/schedule a VIDEO to one of our Upload-Post profiles, cross-post a clip to more platforms, list connected accounts, or check an upload's status. Upload-Post posts via each platform's official API (for TikTok, the sanctioned Content Posting API). Follows the post → confirm → record workflow that keeps published/platform-status.json (read by viralwatch) up to date so nothing is ever reposted.
---

# Upload-Post — Videos & TikTok

Post **videos to TikTok** (and Instagram, YouTube, Facebook, X, etc.) via the
[Upload-Post API](https://docs.upload-post.com/) with a single API call. Built for
agents to publish programmatically across many accounts. Upload-Post posts through
TikTok's **official Content Posting API** (OAuth-authorized) — no reverse-engineering,
no ToS/ban risk from the connection method.

## When to Use This Skill

- "Post / publish / schedule this video to <profile>"
- "Upload this TikTok for <account_one> / <account_two>"
- "Which Upload-Post accounts do we have?" / "list profiles"
- "Did that upload go through?" (check status)

## Key Facts

- **Profiles:** your connected profiles (e.g. `your-profile-1`, `your-profile-2`) are
  listed in [references/accounts.md](references/accounts.md). You target one with
  `--user <profile-username>` (case-sensitive). Refresh the live list + handles with
  the `profiles` command.
- **Auth:** `UPLOADPOST_API_KEY` in `~/.agents/.env`. Source it (absolute path) before
  any run — never read `.env` directly:
  ```bash
  set -a; . ~/.agents/.env; set +a
  ```
  (Relative `. .env` fails because the shell cwd can reset — use the absolute path.)
- **Direct file upload.** Unlike Buffer, Upload-Post accepts a **local file** directly
  (multipart) — no public bucket needed. Pass `--file <path>`.
- **Default platform is `tiktok`.** Add more with repeated `--platform` (e.g.
  `--platform tiktok --platform instagram`).
- **Direct post is the default** (`--post-mode DIRECT_POST`): the video publishes
  straight to the public feed, with `--privacy PUBLIC_TO_EVERYONE` (TikTok *requires* a
  privacy level for direct posts — without one it falls back to the inbox). Use
  `--inbox` (alias `--draft`, i.e. `--post-mode MEDIA_UPLOAD`) to send to the TikTok
  inbox/drafts to finish in-app instead.
- **⚠️ Inbox fallback you can't control (`reached_active_user_cap`):** TikTok caps the
  number of **daily active users for the *whole Upload-Post application*** — a "daily
  active user" is anyone who touches the TikTok API through Upload-Post that day, and
  TikTok limits how many unique users a single app may have. The cap is **shared across
  all Upload-Post customers**, so it can be exhausted by *their* traffic even if *you*
  posted nothing — it is **not** your per-account quota, and nothing you did "used it up"
  today. Upload-Post notes they hit it because of "the rapid growth of our user
  community." When the cap is hit, even a `DIRECT_POST` request is **silently delivered to
  your TikTok inbox** (`post_url: "Video sent to Inbox"`, `platform_post_id: v_inbox_…`;
  the underlying API returns `{"code":"reached_active_user_cap"}`) — you then finish
  publishing from the TikTok app. The script **detects this and prints a loud
  `delivery=INBOX` warning** so a "success" isn't mistaken for a live post.
  - **Recovery (per the docs):** the cap **resets every 24h**, so (a) wait a few hours and
    re-try the direct post, or (b) intentionally send to drafts now with `--inbox`
    (`post_mode=MEDIA_UPLOAD`) and publish in-app. There is **no flag to force** a direct
    post past the cap. For guaranteed direct publishing, `buffer-videos` is the alternative
    path (it doesn't go through Upload-Post's shared TikTok app).
  - Guide: https://docs.upload-post.com/guides/reached-active-user-cap-error
- **Captions:** for your project videos, draw the caption from
  `~/.claude/skills/buffer-videos/references/tiktok-descriptions.md` — the **same
  descriptions used for Buffer posts** — so both pipelines read consistently. Match the
  caption to what's on screen (the 4 *lockscreen* captions for lockscreen clips; never a
  books caption on an unrelated clip). `--aigc` discloses AI-generated content.
- **Volume:** unlimited uploads on our plan. Each account should post **3–4 videos/day
  max** — keep timing/content varied so accounts don't read as bots (behavioral risk
  exists even on the official API).
- **Published archive rule:** after a non-scheduled post is accepted, the local source
  file is moved into a `published/` folder beside it (same convention as `buffer-videos`),
  so the same clip isn't posted twice. Disable with `--no-archive`.

## Instructions

### 1. Confirm the profile

If the user is vague about which account, ask. Verify the live list:

```bash
set -a; . ~/.agents/.env; set +a
python3 ~/.agents/skills/upload-post/scripts/upload_post.py profiles
```

(If it says "No profiles connected yet", the TikTok accounts still need to be connected
in the Upload-Post dashboard — see [references/accounts.md](references/accounts.md).)

### 2. Post the video

Always source the env first, then run `post`:

```bash
set -a; . ~/.agents/.env; set +a

# Publish NOW directly to the TikTok public feed and wait (recommended).
# Direct post is the DEFAULT — no flag needed; --privacy defaults to PUBLIC_TO_EVERYONE.
python3 ~/.agents/skills/upload-post/scripts/upload_post.py post \
  --file ~/videos/out/clip.mp4 \
  --user account_one \
  --caption "It is the translation app I use now. The words you translate go into your collection automatically, and you end up learning French just by looking at your screen." \
  --aigc \
  --when now --async --wait

# Send to the TikTok inbox/drafts instead (finish in-app)
... post --file ~/clip.mp4 --user account_one --caption "..." --inbox

# Schedule for a specific local time (nice-to-have)
... post --file ~/clip.mp4 --user account_two \
  --caption "..." --when 2026-06-21T15:00:00 --timezone Europe/Paris

# Cross-post the same video to several platforms
... post --file ~/clip.mp4 --user account_one --caption "..." \
  --platform tiktok --platform instagram --platform youtube

# TikTok privacy / interaction controls
... post --file ~/clip.mp4 --user account_one --caption "..." \
  --privacy PUBLIC_TO_EVERYONE --disable-duet --disable-stitch
```

- **`--post-mode` / `--inbox`**: `DIRECT_POST` (default) publishes to the public feed;
  `--inbox` (= `MEDIA_UPLOAD`) sends to the inbox/drafts to finish in-app. Note the
  app-wide cap above can force inbox delivery even for a direct post — watch for the
  `delivery=INBOX` warning the script prints.
- **`--when`**: `now` (default) or an ISO-8601 datetime to schedule (with `--timezone`).
- **`--async --wait`**: process in the background and poll until the upload reaches a
  terminal state. Scheduled posts are always async. Uploads that take >59s auto-switch
  to async server-side regardless.
- **`--caption`** is the post text (hashtags go here too) — pull it from the Buffer
  descriptions file (see Key Facts). `--description` is extended text (ignored by TikTok);
  `--first-comment` auto-posts a comment after publishing; `--aigc` discloses AI content.

### 3. Check status (async) — and confirm into platform-status.json

```bash
set -a; . ~/.agents/.env; set +a
python3 ~/.agents/skills/upload-post/scripts/upload_post.py status --request-id <id> --wait \
  --file "<…/published/<stem>.mp4>"   # optional: confirm the outcome into platform-status.json
```

The `post` command prints the `request_id`; reuse it here. With `--file` pointing at the
archived clip, a successful terminal status **writes each platform's confirmed status + live
URL** into the sibling `platform-status.json` (step 2 of the workflow below).

## Posting to the other platforms (YouTube, Instagram, X, Threads, Facebook, Bluesky)

Same command, more `--platform` flags — Upload-Post fans one upload out to every listed
platform **the profile has connected** (connect accounts per profile in the Upload-Post
dashboard; check with `profiles --json`). `--caption` is the universal fallback text/title;
each platform has an optional override. Use the canonical key **`x`** (the script translates
to the API's `twitter` on the wire and records `x` everywhere).

```bash
# Cross-post one clip to TikTok + YouTube + Instagram + X + Threads + Bluesky
python3 ~/.agents/skills/upload-post/scripts/upload_post.py post \
  --file ~/videos/final/clip.mp4 --user account_one \
  --caption "It is the translation app I use now. #languagelearning" --aigc \
  --platform tiktok --platform youtube --platform instagram \
  --platform x --platform threads --platform bluesky \
  --youtube-title "Learn 6 French words from your lock screen" \
  --when now --async --wait
```

Per-platform notes & flags (all optional unless marked):

| Platform | Flags | Notes |
|---|---|---|
| **YouTube** | `--youtube-title`, `--youtube-privacy public\|unlisted\|private`, `--youtube-tag` (repeatable) | 9:16 videos land as Shorts. Result returns a `video_id`; the script derives the watch URL from it. |
| **Instagram** | `--ig-title`, `--ig-media-type REELS\|STORIES` (default REELS) | Reels appear on the profile grid. |
| **X** | `--x-title`, `--x-long-text` | Free-tier X caps video posts; keep captions ≤280 chars unless the account has Premium (`--x-long-text`). |
| **Threads** | `--threads-title`, `--threads-topic` | Topic tag is Threads' hashtag-like discovery tag. |
| **Facebook** | `--facebook-page-id` (**required**, or `$FACEBOOK_PAGE_ID`), `--facebook-title`, `--facebook-media-type REELS\|STORIES\|VIDEO` | Posts to a **Page**, not a personal profile. |
| **Bluesky** | `--bluesky-title` | ≤300 chars, keep videos short (≤60s / ≤100MB is safe). |

- **TikTok flags (`--privacy`, `--inbox`, `--aigc`, `--disable-*`) only affect TikTok** —
  they're ignored for the rest, and the inbox-cap fallback is TikTok-only: a cross-post can
  land `tiktok=inbox` while every other platform published fine. The script records each
  platform separately.
- Captions travel to every platform. If per-platform text should differ meaningfully
  (e.g. hashtags for TikTok, plain text for Bluesky), pass the per-platform title overrides.

## The posting workflow (ALWAYS follow — prevents double-posting)

Every posting run — cron or manual, any platform — is **post → confirm → record**:

1. **Post to the platform(s)** with `post … --async --wait`. On accepted non-scheduled posts
   the script archives the mp4 (+ its `<stem>.json` sidecar) into `published/` and appends
   the posts ledger, exactly as before.
2. **Confirm it went live.** With `--wait` the script polls to a terminal state and writes
   each platform's status into `published/platform-status.json` next to the clip
   (`posted` + live URL when the API returned one, `inbox` for the TikTok cap-fallback,
   `pending` if no terminal state was reached). If it printed a `PENDING` warning, finish
   the confirmation later with:
   `status --request-id <id> --wait --file <…/published/<stem>.mp4>`
3. **Record it viralwatch-friendly.** `platform-status.json` **is** that record (schema in the
   `viralwatch-friendly` skill) — viralwatch reads it to show platform logos on each clip's
   preview and link buttons to every live URL. Steps 1–2 maintain it automatically for
   Upload-Post runs; for posts made outside Upload-Post (Bluesky via `bluesky-post-manage`,
   X via `x-browser-post`, …) record them with:
   ```bash
   python3 ~/.agents/skills/viralwatch-friendly/scripts/platform_status.py mark \
     "<…/published/<stem>.mp4>" --platform bluesky --status posted \
     --url "https://bsky.app/profile/…/post/…" --account <handle>
   ```

**Before posting, check the record.** A clip already inside `published/` may only be posted
to a platform whose entry in `platform-status.json` is missing or `not_posted` — treat
`posted`, `pending`, `inbox` and `scheduled` as **do not repost on that platform**. Quick check:

```bash
python3 ~/.agents/skills/viralwatch-friendly/scripts/platform_status.py show "<published-dir>"
```

(No `platform-status.json` yet? Seed the whole tree from the posts ledger:
`platform_status.py backfill`.)

## Scripts

- `scripts/upload_post.py` — the posting tool (stdlib only, no pip installs). Subcommands:
  - `profiles [--json]` — list connected profiles/accounts.
  - `post --file <v> --user <name>` — upload a video. Plus `--platform` (repeatable,
    default `tiktok`; use `x` not `twitter`), `--caption --description --first-comment`,
    `--when --timezone`,
    TikTok flags `--post-mode {DIRECT_POST,MEDIA_UPLOAD}` / `--inbox` (alias `--draft`),
    `--privacy` (default `PUBLIC_TO_EVERYONE`), `--aigc`,
    `--disable-comment --disable-duet --disable-stitch`,
    per-platform flags `--youtube-title --youtube-privacy --youtube-tag`,
    `--ig-title --ig-media-type`, `--x-title --x-long-text`,
    `--threads-title --threads-topic`,
    `--facebook-page-id --facebook-title --facebook-media-type`, `--bluesky-title`,
    `--async --wait --timeout`, `--request-id`, `--no-archive --published-dir`.
    On `--wait` it detects inbox fallback and prints a `delivery=INBOX` warning, and it
    writes each platform's outcome into the archived clip's `platform-status.json`.
  - `status --request-id <id> [--wait] [--timeout] [--file <published mp4>]` — poll an
    async upload; with `--file`, confirm the per-platform outcome (status + live URL)
    into the clip's sibling `platform-status.json`.

  Always `set -a; . ~/.agents/.env; set +a` (absolute path) first. The script retries
  transient 5xx/network errors and archives accepted `--file` sources to `published/`.

## References

- `references/accounts.md` — your Upload-Post profiles (usernames → TikTok handles →
  project) and how to connect a TikTok account to a profile. Refresh with `profiles`.

## API reference (for changes)

- Base URL: `https://api.upload-post.com`
- Auth header: `Authorization: Apikey <UPLOADPOST_API_KEY>`
- `POST /api/upload` — video post (multipart: `user`, `platform[]`, `video`, `title`,
  `description`, `scheduled_date`, `timezone`, `async_upload`, `request_id`,
  `first_comment`). TikTok fields are **un-prefixed** (the `tiktok_`-prefixed names are
  silently ignored): `post_mode` (`DIRECT_POST` | `MEDIA_UPLOAD`, default `DIRECT_POST`),
  `privacy_level` (`PUBLIC_TO_EVERYONE` | `MUTUAL_FOLLOW_FRIENDS` | `FOLLOWER_OF_CREATOR`
  | `SELF_ONLY`), `disable_comment`, `disable_duet`, `disable_stitch`, `is_aigc`,
  `cover_timestamp`, `brand_content_toggle`, `brand_organic_toggle`. The only TikTok
  field that *is* prefixed is `tiktok_title`. Direct post needs a `privacy_level` or it
  falls back to the inbox; the app-wide `reached_active_user_cap` also forces inbox.
- `GET /api/uploadposts/users` — list profiles · `GET /api/uploadposts/status?request_id=` — status.
- Full docs: https://docs.upload-post.com/ · inbox-fallback guide (`reached_active_user_cap`,
  error code `{"code":"reached_active_user_cap"}`, app-wide & resets every 24h):
  https://docs.upload-post.com/guides/reached-active-user-cap-error
