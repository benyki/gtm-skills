# post-finder config — default (example)

This is the **shipped default** configuration for `tiktok-post-finder`. It holds
all project-specific filter/content so the scripts stay generic.

## Per-project overrides

To use this skill for a project, create a dedicated config in that project's repo:

```
code/<project-name>/yard/tiktok/post-finder-config.md
```

Copy the block below into it and edit. The scripts auto-discover
`yard/tiktok/post-finder-config.md` by walking up from the current directory; if
none is found they fall back to this file. You can also force one with
`CONFIG=/path/to/post-finder-config.md` or `POST_FINDER_CONFIG=...`.

## Parsed values

Only the fenced ```json block below is read by the scripts. Everything else is
for humans.

- `niche` — one-line description of what a matching post looks like (for curation).
- `searchQueries` — default TikTok search queries (CLI args to `apify_search.sh` override these).
- `maxResults` — default number of results to fetch & show (env `RESULTS` overrides). **Default 10.**
- `maxAgeDays` — only keep posts newer than this many days (env `MAX_AGE_DAYS` overrides). Omit / `null` = no cutoff. TikTok search is relevance-ranked (not date), so a cutoff is enforced client-side after fetching.
- `fetchOversample` — when `maxAgeDays` is set, fetch `maxResults × fetchOversample` candidates (capped at 50/query) so enough recent posts survive the filter (env `OVERSAMPLE`; default 4). Higher = more recent posts found, but more cost.
- `ranking` — how candidates are scored (higher = better). `engagementWeight` + `recencyWeight` blend two 0–1 signals: engagement (likes+comments+shares+saves, normalized within the result set) and recency (linear decay over `recencyWindowDays`; posts older than the window contribute 0 recency). Tune to taste — e.g. raise `recencyWeight` to favor fresh posts, raise `engagementWeight` to favor viral ones.
- `reportTitle` — heading for the Discord report (`(top N)` is appended automatically).
- `commentHeader` — exact heading for the ready-to-comment block.
- `commentTemplates` — sub-10-word comments, rotated across the posts.
- `discord.channel` / `discord.account` — delivery target (env `CHANNEL` / `ACCOUNT` override). `account` is the your agent runtime discord account; `default` = the `@your-bot` bot.

```json
{
  "niche": "A real person naming their favorite word(s) or expression(s) in a foreign language or one they're learning",
  "searchQueries": [
    "favorite word in the language im learning",
    "favorite word in a foreign language"
  ],
  "maxResults": 10,
  "maxAgeDays": 15,
  "fetchOversample": 4,
  "ranking": {
    "engagementWeight": 0.6,
    "recencyWeight": 0.4,
    "recencyWindowDays": 540
  },
  "reportTitle": "🎯 TikTok — favorite words/expressions in a foreign language",
  "commentHeader": "Here is for each post a recommended ready to comment text :",
  "commentTemplates": [
    "added to my collection thx",
    "adding it to my collection in the app haha",
    "word collector too here, add me in the app! @your-username",
    "ok that word is too pretty, going straight into my collection",
    "saving this to the app rn",
    "the kind of word i hoard in the app",
    "adding this one to my app tyyy",
    "stop it's so good adding rn to my collection",
    "word collector here 🤝 i keep all mine in the app wbu?",
    "word collector here! what's your favorite one so far?",
    "adding to my collection rn!!"
  ],
  "discord": {
    "channel": "123456789012345678",
    "account": "default"
  }
}
```
