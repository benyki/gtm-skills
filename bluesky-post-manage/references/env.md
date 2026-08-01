# Env loading

## Where creds live

- **Live secrets:** `~/.agents/.env` (never committed)
- **Public template:** `~/.agents/.env.example` and `~/.agents/skills/bluesky-post-manage/assets/env.example`

## Naming convention

```
BSKY_ACCOUNT_<NAME>_HANDLE=...
BSKY_ACCOUNT_<NAME>_APP_PASSWORD=...
BSKY_ACCOUNT_<NAME>_DID=...               # optional
BSKY_ACCOUNT_<NAME>_PDS_URL=...           # optional, defaults to https://bsky.social
```

`<NAME>` is any uppercase identifier (`MAIN`, `BOT`, `BRAND`, `PERSONAL`, …).
The scripts call `accountEnv(name)` and resolve the four vars by prefix.

## Loading the env

All scripts assume `process.env` is already populated. The preferred path is
Node's built-in `--env-file` flag (Node 20.6+, **no dotenv package required**):

```bash
node --env-file=~/.agents/.env \
  ~/.agents/skills/bluesky-post-manage/scripts/post.mjs --account MAIN --text "hi"
```

Alternatives:

- Load with the `dotenv` package and run `node -r dotenv/config script.mjs`
- Export vars in the shell: `source ~/.agents/.env && node script.mjs ...`
- Use `direnv`, `mise`, `1password` CLI, etc. — the script doesn't care.

## Quick check

```bash
node --env-file=~/.agents/.env \
  ~/.agents/skills/bluesky-post-manage/scripts/list-accounts.mjs
```

Prints every account discovered (`BSKY_ACCOUNT_*_HANDLE`) and whether login succeeded.
