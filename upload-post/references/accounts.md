# Upload-Post accounts (profiles) — TEMPLATE

Upload-Post groups connected social accounts under **profiles**. You target a
profile by its **username** with `--user <name>` when posting.

> Fill this table in with your own profiles (run the `profiles` command below and
> record the output here). The rows are placeholders showing the format. Note that
> one profile can have several platforms connected — list each on its own row.
> `--user` is case-sensitive — use the exact **Profile username**.

| Profile username (`--user`) | Platform  | Handle          | Display name   | Notes |
|-----------------------------|-----------|-----------------|----------------|-------|
| `your-profile-1`            | TikTok    | @your-handle-1  | Your Name 1    | your niche |
| `your-profile-2`            | TikTok    | @your-handle-2  | Your Name 2    | another niche |
| `your-profile-2`            | YouTube   | @your-handle-2  | Your Name 2    | same profile, YouTube also connected |

Refresh this list any time with:

```bash
set -a; . ~/.agents/.env; set +a
python3 ~/.agents/skills/upload-post/scripts/upload_post.py profiles
```

## Connecting a TikTok account to a profile

1. Log in to the Upload-Post dashboard.
2. Create a profile (or pick an existing one) — its **username** is the value you
   pass to `--user`.
3. Connect the TikTok account to that profile via the in-dashboard OAuth flow
   (official TikTok authorization — the sanctioned route, not a credential dump).
4. Run `profiles` above to confirm it shows up, then record it here.

> Posting to TikTok requires the account to have completed TikTok's OAuth
> authorization. A profile with no connected TikTok account will fail at post time.
