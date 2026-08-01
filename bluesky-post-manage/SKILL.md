---
name: bluesky-post-manage
description: Post to Bluesky and manage multiple Bluesky accounts via the AT Protocol (atproto) API. Trigger when the user asks to post, reply, quote, delete, schedule, or read content on Bluesky/bsky/atproto; configure or switch between Bluesky accounts; or build a bot/automation on top of @atproto/api. Covers text + rich text + images + video + threads + quote posts + firehose reads.
version: 1.0.0
---

# bluesky-post-manage

Operational skill for Bluesky / AT Protocol integration. Provides ready-to-run scripts for posting, account management, and reading, plus reference docs for the full XRPC surface.

## What this skill does

- Posts text, rich text, images, threads, replies, and quote posts to one or many Bluesky accounts
- Manages multiple accounts via env-var prefix convention (`BSKY_ACCOUNT_<NAME>_*`)
- Reads timelines and notifications
- Deletes any record (post / like / repost / follow)
- Resolves handles to DIDs

## Where things live

- Skill root: `~/.agents/skills/bluesky-post-manage/`
- Scripts: `~/.agents/skills/bluesky-post-manage/scripts/`
- Reference docs: `~/.agents/skills/bluesky-post-manage/references/`
- Env template: `~/.agents/skills/bluesky-post-manage/assets/env.example` (and `~/.agents/.env.example`)
- Live credentials: `~/.agents/.env` (user-managed, never commit)
- Account registry: `~/.agents/skills/bluesky-post-manage/references/accounts.md`

## Prerequisites

- **Node.js 20.6+** (uses built-in `--env-file` flag; no dotenv dependency needed)
- **`@atproto/api`** installed in the working project: `npm install @atproto/api`
- An app password for each account (Bluesky Settings → Privacy and Security → App Passwords). Format: `xxxx-xxxx-xxxx-xxxx`.

## Operational instructions for the agent

When the user asks to post / manage Bluesky:

1. **Verify credentials are loaded.** Confirm `~/.agents/.env` exists and contains `BSKY_ACCOUNT_<NAME>_*` vars for the target account. If missing, point the user at `~/.agents/skills/bluesky-post-manage/assets/env.example` and `references/accounts.md`.
2. **Choose the right script** from the table below.
3. **Run the script** with `node --env-file=~/.agents/.env ~/.agents/skills/bluesky-post-manage/scripts/<script>.mjs <args>`.
4. **Consult references** when the user asks something not directly covered by a script (firehose, OAuth, custom embeds, etc.).
5. **Never write the user's app password to disk** outside `~/.agents/.env`. Never log full JWTs.

## Scripts (entrypoints)

All scripts live under `~/.agents/skills/bluesky-post-manage/scripts/`. Each takes `--help` to print usage.

| Script | Purpose | Example |
|---|---|---|
| `post.mjs` | Post text (optionally as reply or quote) | `node --env-file=~/.agents/.env scripts/post.mjs --account MAIN --text "Hello!"` |
| `post-image.mjs` | Post text + 1–4 images | `node --env-file=~/.agents/.env scripts/post-image.mjs --account MAIN --text "..." --image ./pic.jpg --alt "A cat"` |
| `delete-record.mjs` | Delete any record by `at://` URI | `node --env-file=~/.agents/.env scripts/delete-record.mjs --account MAIN --uri "at://did:plc:abc/app.bsky.feed.post/xyz"` |
| `list-accounts.mjs` | Enumerate configured accounts and verify login | `node --env-file=~/.agents/.env scripts/list-accounts.mjs` |
| `read-timeline.mjs` | Print N most recent posts in home timeline | `node --env-file=~/.agents/.env scripts/read-timeline.mjs --account MAIN --limit 20` |
| `read-notifications.mjs` | Print notifications (optionally mark as seen) | `node --env-file=~/.agents/.env scripts/read-notifications.mjs --account MAIN --mark-seen` |
| `resolve-did.sh` | Resolve a handle → DID (no auth needed) | `bash scripts/resolve-did.sh alice.bsky.social` |

### Input shapes (per script)

**`post.mjs` arguments:**
```
--account <NAME>            required. Maps to BSKY_ACCOUNT_<NAME>_* env vars.
--text "<post text>"        required. Max 300 graphemes. Rich text auto-detected.
--reply-to <at-uri>         optional. URI of post to reply to.
--reply-cid <cid>           optional. CID of parent post (required with --reply-to).
--reply-root-uri <at-uri>   optional. Thread root URI (defaults to --reply-to).
--reply-root-cid <cid>      optional. Thread root CID (defaults to --reply-cid).
--quote <at-uri>            optional. URI of post to quote.
--quote-cid <cid>           optional. CID of quoted post (required with --quote).
--lang <code>               optional. Language tag, default "en".
```

**`post-image.mjs` arguments:**
```
--account <NAME>            required.
--text "<post text>"        required (may be empty string).
--image <path>              required. Repeatable up to 4 times.
--alt "<description>"       required, repeatable. Must match --image count and order.
```

**`delete-record.mjs` arguments:**
```
--account <NAME>            required.
--uri <at-uri>              required. Any at:// URI from the account.
```

**`read-timeline.mjs` arguments:**
```
--account <NAME>            required.
--limit <n>                 optional, default 30, max 100.
```

**`read-notifications.mjs` arguments:**
```
--account <NAME>            required.
--limit <n>                 optional, default 30.
--mark-seen                 optional. Marks all retrieved notifications as seen.
```

**`resolve-did.sh` arguments:**
```
$1                          required. Handle (e.g. alice.bsky.social).
```

## References

Consult these in `~/.agents/skills/bluesky-post-manage/references/` before answering deeper questions:

- `auth.md` — app passwords, OAuth+DPoP, session lifecycle, multi-account pattern
- `posting.md` — full posting surface (rich text, threads, quotes, images, video, link cards, deleting)
- `accounts.md` — the registry of configured accounts and env-var binding convention
- `endpoints.md` — XRPC endpoint catalog, rate limits, AppView vs PDS routing
- `env.md` — env-var conventions and the loading pattern used by every script

## Key constraints (agents: read before posting)

- **Text:** max **300 graphemes** (not bytes, not chars). The SDK enforces this.
- **Images:** max **4 per post**, max **1,000,000 bytes (~1 MB) per image**, max **2,000,000 bytes total** per post.
- **Video:** max **100 MB**, max **3 minutes**.
- **Tags field:** max **8 entries**, each max **64 graphemes / 640 bytes**.
- **Facets** (mentions/links/hashtags) index into **UTF-8 bytes**, never JS string offsets. Use `RichText.detectFacets()`.
- **Writes** go to PDS (`https://bsky.social`). **Public reads** can use `https://public.api.bsky.app` (no auth).
- **Rate limits:** CREATE=3pts, UPDATE=2pts, DELETE=1pt. 5,000 pts/hour, 35,000 pts/day per account.
- **`AtpAgent`** is current. `BskyAgent` is deprecated.

## SDK install

```bash
npm install @atproto/api
# OAuth (only if building a user-facing app, not a bot):
# npm install @atproto/oauth-client-node     # server-side
# npm install @atproto/oauth-client-browser  # browser
```

## OpenAI agent metadata

See `~/.agents/skills/bluesky-post-manage/agents/openai.yaml`.
