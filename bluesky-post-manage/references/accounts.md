# Accounts Registry

Source of truth for every configured Bluesky account.
Credentials live in `~/.agents/.env`. This file lists the metadata.

---

## Env var naming convention

For each account named `<NAME>` (uppercase, e.g. `MAIN`, `BOT`, `BRAND`):

```
BSKY_ACCOUNT_<NAME>_HANDLE=handle.bsky.social
BSKY_ACCOUNT_<NAME>_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
BSKY_ACCOUNT_<NAME>_DID=did:plc:...
BSKY_ACCOUNT_<NAME>_PDS_URL=https://bsky.social
```

| Var | Required | Notes |
|-----|----------|-------|
| `HANDLE` | yes | Bluesky handle, e.g. `alice.bsky.social` or custom-domain `alice.com` |
| `APP_PASSWORD` | yes | Created in Settings → Privacy and Security → App Passwords |
| `DID` | no | `did:plc:...` — useful for `repo` field in raw XRPC. Auto-discoverable. |
| `PDS_URL` | no | Defaults to `https://bsky.social`; set only for custom PDS hosts |

All scripts in `~/.agents/skills/bluesky-post-manage/scripts/` resolve credentials through this convention via `_lib.mjs::accountEnv(name)`.

---

## Adding a new account

1. Generate an app password in Bluesky UI.
2. Resolve the DID:
   ```bash
   bash ~/.agents/skills/bluesky-post-manage/scripts/resolve-did.sh alice.bsky.social
   ```
3. Add the four `BSKY_ACCOUNT_<NAME>_*` vars to `~/.agents/.env`.
4. Add a row to the **Registered accounts** table below.
5. Verify:
   ```bash
   node --env-file=~/.agents/.env \
     ~/.agents/skills/bluesky-post-manage/scripts/list-accounts.mjs
   ```

---

## Registered accounts

> Update this table whenever an account is added/removed.

| NAME | Handle | DID | Purpose | PDS |
|------|--------|-----|---------|-----|
| `MAIN` | *(fill in)* | *(fill in)* | Primary / personal | https://bsky.social |

Example row once filled:

| `MAIN` | `alice.bsky.social` | `did:plc:abc123def456ghi789jkl012` | Personal posting | https://bsky.social |

---

## Account hygiene

- Rotate app passwords periodically. Revoke immediately if a bot leaks logs.
- One app password per script/automation — that way revoke is granular.
- Don't reuse the account password as the app password.
- Don't commit `~/.agents/.env`. The repo's `.env.example` is the public template.
