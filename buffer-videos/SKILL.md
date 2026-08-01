---
name: buffer-videos
description: Publish and schedule TikTok videos (and other video posts) through Buffer. Use when the user wants to publish, schedule, queue, or draft a VIDEO to one of their Buffer TikTok channels (your-account-fr, your-account-en, your-account-alt), list those accounts, or check what's queued. For general Buffer API/auth/schema questions use the `buffer` skill instead.
---

# Buffer — Videos & TikTok

Push **TikTok videos** (and other video posts) to Buffer channels: publish now, queue,
schedule, or draft. This is the video/TikTok workflow layer on top of the **`buffer`**
skill — see [[buffer]] for the API, auth, GraphQL schema, and non-video features.

## When to Use This Skill

- "Post / schedule / queue this TikTok to <channel>"
- "Publish this video to your-account-fr / your-account-en / your-account-alt"
- "Add this video to my Buffer queue" / "save it as a draft"
- "Which TikTok accounts do I have on Buffer?"

## Key Facts

- **Channels:** your connected TikTok accounts (e.g. `your-account-fr`, `your-account-en`, `your-account-alt`).
  Full list with IDs in [references/accounts.md](references/accounts.md).
- **Auth:** `BUFFER_API_KEY` in `~/.agents/.env`. Source it (absolute path) before any
  run — never read `.env` directly:
  ```bash
  set -a; . ~/.agents/.env; set +a
  ```
  (Relative `. .env` fails because the shell cwd can reset — use the absolute path.)
- **No upload endpoint.** Buffer fetches media from a public HTTPS URL; it cannot accept
  a local file. The script handles this for you (uploads `--file` to a public bucket).
- **API rate limit — 100 requests / 24h (hard).** Buffer's API key allows **100 req/15min,
  100 req/24h, 3000 req/30days** — the **24h/100** ceiling is the one you'll hit. Going over
  returns `HTTP 429 RATE_LIMIT_EXCEEDED` on **every** call (reads included) until the rolling
  window clears. **Every request counts** — each status poll, channel lookup, and post. To
  stay cheap:
  - **Pass the channel _id_, not the name** (`--channel YOUR_CHANNEL_ID`). The
    script then skips the account+channels lookups (saves 2 req/post). IDs are in
    [references/accounts.md](references/accounts.md).
  - **Avoid `--wait` in loops/batches** unless you need the `sent` confirmation — each poll
    is a request. The source video is archived to `published/` regardless of `--wait`, so
    dropping it does not break the archive rule (only the bucket auto-cleanup is skipped).
  - With id + no `--wait`, a post costs **1 request**. The 6h cron (4/day) then uses ~4 req/day.
  - Don't hammer on 429 — it cannot succeed until the window rolls off (~24h). Schedule a
    retry instead.
- **Published archive rule:** after a video is published, its local source file is moved
  into a `published/` folder beside it (see below).
- **Music catalog:** background tracks for laying under a clip with ffmpeg before posting
  (Buffer/TikTok's API can't attach a TikTok *sound* — see step 2a):
  - `~/videos/music/geo/<language>/` — **language-specific** tracks, one folder per language
    (`french`, `spanish`, `italian`, …). This is the canonical per-language source and what
    the lockscreen renders use.
  - `~/videos/music/tiktok/` — generic trending-style beds (use when there's no language match).
  - Note: the old `~/videos/music/french/` is **deprecated/empty** — French music moved to
    `~/videos/music/geo/french/`.

## Instructions

### 1. Confirm the channel

If the user is vague about which TikTok account, ask. Verify the live list:

```bash
python3 ~/.agents/skills/buffer-videos/scripts/buffer.py channels
```

### 2a. (Optional) Add background music

Buffer/TikTok's API can't attach an official TikTok *sound* — the only fields it exposes
are title + `isAiGenerated`. To get audio on an otherwise-silent clip (or a music bed
under a voiceover), mix in a track from the music catalog with ffmpeg *before* posting.
This is the same pattern the `*-video-*` skills use (loop to cover the video, scale volume,
fade out, `-shortest`). **Use language-matched music**: a `--catalog <language>` resolves to
`~/videos/music/geo/<language>/` — so French clips get French tracks, etc.

> Note: the lockscreen renders are usually **already given a language-matched music bed** by
> `videos-lockscreen`'s own `add-music.sh` (which also reads `~/videos/music/geo/<lang>/`).
> Only add music here if a clip is still silent.

Use the helper — it picks a random track from the catalog, handles silent vs.
voiceover clips automatically, keeps the original duration, and prints the new file path:

```bash
# Random track from the French catalog (geo/french) under a silent lockscreen-fr clip
MUSIC_OUT=$(~/.agents/skills/buffer-videos/scripts/add-music.sh \
  ~/code/<project>/world/videos/lockscreen-fr/outputs/fr-047.mp4 --catalog french)

# Spanish / Italian clips: just name the language
... add-music.sh ~/clip-es.mp4 --catalog spanish
... add-music.sh ~/clip-it.mp4 --catalog italian

# Generic TikTok bed, quieter, mixed UNDER an existing voiceover
... add-music.sh ~/clip.mp4 --catalog tiktok --volume 0.35

# A specific track, overwriting the source in place
... add-music.sh ~/clip.mp4 --music ~/videos/music/geo/french/"Alors on danse #shorts.mp3" --inplace
```

`--catalog tiktok | <language> | <path-with-slash>` (default `tiktok`; a bare name →
`~/videos/music/geo/<name>/`) · `--music <file>` (exact track) · `--volume` (default `0.5`) ·
`--fade` seconds (default `1.0`) · `--out <path>` · `--inplace`. Default output is
`<stem>-music.mp4` next to the source. Then post `$MUSIC_OUT` with `--file` in step 2.
(Match the language; keep `--volume` low — ~0.3–0.4 — when there's a voiceover.)

### 2. Post the video

The script resolves the channel name → id, uploads media if needed, runs the mutation,
archives the source, and (with `--wait`) polls until `sent`:

```bash
# Publish a LOCAL file now and wait for confirmation (recommended)
python3 ~/.agents/skills/buffer-videos/scripts/buffer.py post \
  --channel your-account-en \
  --file ~/code/<project>/world/videos/lockscreen-es/outputs/clip.mp4 \
  --caption "POV: you learned Spanish from your lockscreen 🇪🇸 #fyp" \
  --title "learn Spanish from your lockscreen" \
  --when now --wait

# Queue an already-public URL
... post --channel your-account-fr --video "https://.../v.mp4" --caption "..." --when queue

# Schedule for a specific time (ISO 8601 UTC)
... post --channel your-account-alt --video "https://.../v.mp4" --caption "..." \
  --when 2026-06-20T15:00:00Z

# Save as a draft (not published, not archived)
... post --channel your-account-en --file ~/clip.mp4 --caption "..." --draft
```

`--when`: `queue` (default) · `now` · `next` · ISO datetime.

- **`--file`** uploads to `gs://your-bucket/buffer` (override with `--bucket`) and posts the
  resulting public URL. With `--wait`, the bucket copy is deleted once the post is `sent`
  (`--keep` to retain it).
- **`--video`** posts an already-public URL as-is.

### 3. Published archive rule (automatic)

Every time a **`--file`** video is successfully published (any non-draft post), the
script **moves the local source into a `published/` folder next to it**, creating the
folder if it doesn't exist:

```
.../outputs/clip.mp4   →   .../outputs/published/clip.mp4
```

This keeps already-posted clips out of the "to post" pool so the same video isn't
published twice. Drafts are not archived (nothing went out); `--video <url>` posts have
no local file to move. Override the folder name with `--published-dir <name>`, or skip
with `--no-archive`.

### 4. Check status

A `now` post takes ~30–90s to go `sending → sent`. `--wait` handles this; otherwise:

```bash
python3 ~/.agents/skills/buffer-videos/scripts/buffer.py status --id <postId> --wait
```

### Direct publish vs. reminder

- Default is **automatic** → Buffer publishes directly to TikTok (needs the channel/plan
  to support TikTok direct publishing).
- `--notify` uses **notification** publishing: Buffer sends a phone reminder and you
  finish in the TikTok app. The script suggests this if a post fails with a
  permission/plan-looking error.

### Caption & title

- `--caption` is the post text (hashtags go here).
- `--title` sets the TikTok video title metadata and the asset title.
- For product posts, draw from [references/tiktok-descriptions.md](references/tiktok-descriptions.md).
  **Important:** some captions there only fit a specific *type* of video (e.g. the
  "books/reading" ones). Always pick or adapt a caption that **matches what's actually in
  the video** — never reuse a book-themed caption on an unrelated clip.

### Multiple organizations

One org here, auto-detected. If an account ever has several, the script lists them — pass
`--org <name|id>` (top-level flag, before the subcommand).

## Scripts

- `scripts/buffer.py` — video posting tool. Subcommands:
  - `channels` — list channels (id, service, name)
  - `whoami` — account + organizations
  - `post` — publish a video. Media: `--video <url>` or `--file <local path>`. Plus
    `--caption --title --thumbnail --when --notify --draft --wait --keep --timeout
    --bucket --published-dir --no-archive`.
  - `status --id <postId> [--wait]` — show / poll a post's status.

  Always `set -a; . ~/.agents/.env; set +a` (absolute path) first. The script retries
  transient 5xx/network errors, archives published `--file` sources, and cleans up bucket
  uploads on `sent` (with `--wait`).
- `scripts/add-music.sh <video>` — lay a background track under a clip with ffmpeg before
  posting (step 2a). `--catalog tiktok | <language> | <path-with-slash>` picks a random
  track (a bare language name → `~/videos/music/geo/<language>/`); `--music <file>` uses an
  exact one. Auto-detects whether the source has audio (mixes under a voiceover vs. becomes
  the track), loops/volume/fades the music, preserves the video duration, and prints the
  output path. Flags: `--volume --fade --out --inplace`.

## References

- `references/accounts.md` — the Buffer account, organization id, and the TikTok channel
  list with IDs. Refresh with `buffer.py channels` whenever channels change.
- `references/tiktok-descriptions.md` — example captions, grouped by which video
  type they fit. Match the caption to the video before posting.

For the underlying API (endpoint, auth, GraphQL schema, all Buffer features and docs),
see the **`buffer`** skill — [[buffer]].
