# Troubleshooting & resilience notes

Lessons baked into the scripts from real failures. If something breaks, check here first.

## 1. `APIFY_API_KEY` / secret loading

- **Symptom:** `~/.agents/.env: line N: APIFY_: command not found` (or similar).
- **Cause:** `~/.agents/.env` contains a malformed/partial line; `source`-ing the
  whole file executes it as shell and crashes.
- **Fix (in `apify_search.sh`):** never `source` the file. Extract only the one key:
  `grep -E '^[[:space:]]*APIFY_API_KEY=' ~/.agents/.env | head -1 | cut -d= -f2-`.
  The value is never printed (local-secrets rule).
- If the key is missing: add `APIFY_API_KEY=...` to `~/.agents/.env` (names in
  `~/.agents/.env.example`).

## 2. Apify request failures / empty results

- The script sets `--max-time 180 --retry 2` and checks the HTTP code + that the
  body is a JSON array.
- **0 results or HTTP error** → it prints a hint to switch to the browser method
  (`references/browser-method.md`). Common causes: bad query, rate limiting,
  region gating. Try simpler/different `searchQueries`.

## 3. Discord delivery posts nothing / agent asks a question

- **Symptom:** `your-agent agent --agent your-bot --deliver` returns exit 0 but the
  channel gets no report — the agent reply was a clarifying question instead.
- **Cause:** `agent --deliver` delivers the *local model's reply*, which may
  rewrite or question rather than relay verbatim. `your-bot` is an **agent**, not a
  Discord account.
- **Fix (in `report_to_discord.sh`):** use `your-agent message send` for guaranteed
  verbatim delivery.

## 4. Which Discord account can post?

- `your-bot`'s routing is `discord accountId=default`, and the **`default` account
  is the `@your-bot` bot** (Bot id `123456789012345678`).
- It is the **only** account with send permission on channel `123456789012345678`
  (others report `Permissions: Missing Access`).
- Preflight any new channel before `--send`:
  ```bash
  your-agent channels capabilities --channel discord --target channel:<id>
  ```
  Look for `Missing required: none` under the account you intend to use.

## 5. Config not picked up

- Scripts resolve config in order: `$CONFIG` → `$POST_FINDER_CONFIG` →
  `./yard/tiktok/post-finder-config.md` (walking up from CWD) → skill default.
- Only the fenced ```json block in the `.md` is parsed; invalid JSON silently
  falls back to `{}` (then built-in defaults). Validate with:
  `scripts/_config.sh`'s `pf_config_json <file> | jq .`
