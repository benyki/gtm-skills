---
name: tiktok-post-finder
description: Find TikTok posts where people share their favorite words/expressions in a foreign language (or one they're learning) — for content research and engagement — then report the top picks to Discord with ready-to-paste comments. Config-driven and project-agnostic: niche, search queries, result count, comment templates and Discord target all live in a post-finder-config.md (default ships for your project; override per project). Two collection methods: Apify API (DEFAULT — fast, structured, ranked by likes) and the Claude-in-Chrome browser plugin (fallback). Trigger when the user says "find tiktok posts about favorite words", "tiktok post finder", "search tiktok for foreign-language word posts", "find comment targets", or anything similar.
---

# TikTok Post Finder

Collect TikTok posts where a real person names favorite words/expressions in a
foreign or being-learned language, then optionally report the best ones to
Discord with ready-to-comment text.

**The skill carries no project-specific content** — queries, result count,
comment templates, niche and Discord target all come from a config file. Defaults
ship for your project; override per project.

## Configuration (read this first)

Config is a markdown file with one fenced ```json block. Resolution order
(first hit wins):

1. `CONFIG=/path/...` env
2. `POST_FINDER_CONFIG=/path/...` env
3. `./yard/tiktok/post-finder-config.md` — walking up from the current directory (**project config**)
4. `references/post-finder-config.md` — shipped default (example)

**To use for a project**, create `code/<project-name>/yard/tiktok/post-finder-config.md`
(copy `references/post-finder-config.md` and edit). Scripts auto-discover it when
run anywhere under that project. The project instance already exists at
`~/code/<project>/yard/tiktok/post-finder-config.md`.

Config keys: `niche`, `searchQueries`, `maxResults` (**default 10**),
`reportTitle`, `commentHeader`, `commentTemplates`, `discord.channel`,
`discord.account`. See `references/post-finder-config.md` for details.

## Two methods (Apify is the default)

| | 🥇 Apify API (default) | 🥈 Browser plugin (fallback) |
|---|---|---|
| When | Almost always. Structured, rankable, repeatable. | No actor fits / need a logged-in session / region-gated / want $0 cost / Apify errors or returns 0. |
| Speed | ~10–15s, one call. | ~2–3 min, several round-trips. |
| Clues | `url`, `likes`, caption + hashtags → rank by engagement. | Captions only, no reliable metrics; URLs DOM-scraped. |
| Cost | ~$0.0035/result (pay-per-event) → ~$0.04 for 10. | $0 marginal. |

**Decision rule:** start with Apify. Fall back to the browser only if Apify
errors/returns nothing, content is private/region-locked, or the user wants no
spend. Browser steps: `references/browser-method.md`.

## Credentials

- Apify key: **`~/.agents/.env`** → **`APIFY_API_KEY`**; names-only template at
  **`~/.agents/.env.example`**.
- **local-secrets rule:** read `.env.example` for names only; NEVER read/print
  `~/.agents/.env`. `apify_search.sh` extracts *only* `APIFY_API_KEY` at runtime
  (it does not `source` the file — that previously crashed on a malformed line).
- Discord: your agent runtime, already configured. The `default` discord account is the
  `@your-bot` bot. No token handling.

## Workflow

```
- [ ] 1. Collect  → scripts/apify_search.sh   (default)  |  references/browser-method.md (fallback)
- [ ] 2. Curate the top picks (relevance + likes), write a posts JSON
- [ ] 3. Report   → scripts/report_to_discord.sh   (preview, then --send)
```

### Step 1 — Collect (default: Apify)

```bash
# Uses config searchQueries + maxResults (default 10):
~/.agents/skills/tiktok-post-finder/scripts/apify_search.sh

# Or override queries on the CLI:
~/.agents/skills/tiktok-post-finder/scripts/apify_search.sh "favorite italian words" "fav spanish word"
```

Ranks candidates by **engagement + recency** (config `ranking` weights; higher =
more interactions AND more recent) and prints a TSV
(`date \t likes \t views \t comments \t score% \t url \t caption`). Writes
top-`maxResults` JSON (`[{url,likes,views,comments,shares,collects,engagement,date,score,caption}]`)
to `/tmp/tiktok-post-finder-results.json`. Override count with `RESULTS=20`. On
Apify error or 0 results it tells you to use the browser method.

### Step 2 — Curate

Pick the strongest matches per `niche`. The search already ranks by **engagement
+ recency** (more recent & more engaged = higher), so the top rows are usually the
best comment targets — but still sanity-check niche fit (e.g. a high-view post
tagged with a language but not actually *naming a favorite word*). Favor language
variety. The simplest curation is `jq '.[0:5]' results.json > top5.json`; or
hand-write a posts JSON, array of `{url, likes, note, ...}` (keep `date`/`views`/
`comments` from the search to show them in the report; a curated `note` overrides
the raw `caption`):

```json
[
  { "url": "https://www.tiktok.com/@example_user/video/1234567890123456789", "likes": 92900, "note": "Arabic 'Hayya' = let's go, with CTA" }
]
```

### Step 3 — Report to Discord (posts as @your-bot)

```bash
# Preview (no send):
~/.agents/skills/tiktok-post-finder/scripts/report_to_discord.sh /tmp/tiktok-post-finder-top5.json
# Send for real:
~/.agents/skills/tiktok-post-finder/scripts/report_to_discord.sh /tmp/tiktok-post-finder-top5.json --send
```

- Title, comment header, comment templates and target come from config.
- Delivers **verbatim** via `your-agent message send` as the `@your-bot` bot (the
  `default` discord account). The `agent --deliver` path is intentionally NOT used
  — the local model rewrites/questions instead of relaying. See
  `references/troubleshooting.md` §3–4.
- Posting = sending on the user's behalf → **previews by default; only sends with
  `--send`.** Confirm with the user before `--send`.

## References

- `references/post-finder-config.md` — default config + how project overrides work.
- `references/browser-method.md` — Claude-in-Chrome fallback steps.
- `references/discord-report.md` — exact your agent runtime delivery command + report format.
- `references/troubleshooting.md` — failure modes already solved (secrets, delivery, accounts, config).
