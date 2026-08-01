# Buffer Accounts & Channels — TEMPLATE

> Fill this in with your own Buffer account, organization, and channels. The rows below
> are placeholders showing the format.

Buffer account: **you@example.com**  (`YOUR_BUFFER_ACCOUNT_ID`)
Organization: **Your Organization**  (`YOUR_BUFFER_ORG_ID`)

> The organization id is needed for the `channels(input: { organizationId })` query.
> If all your channels belong to a single org, the helper script auto-resolves it.

## Channels

| Name             | Service | Channel ID          | Timezone     | Status    |
|------------------|---------|---------------------|--------------|-----------|
| `your-account-1` | tiktok  | `YOUR_CHANNEL_ID_1` | Europe/Paris | connected |
| `your-account-2` | tiktok  | `YOUR_CHANNEL_ID_2` | Europe/Paris | connected |
| `your-account-3` | tiktok  | `YOUR_CHANNEL_ID_3` | Europe/Paris | connected |

## Refresh this list

This table is a snapshot. Re-generate it any time channels are added/removed/reconnected:

```bash
set -a; . ~/.agents/.env; set +a
python3 ~/.agents/skills/buffer-videos/scripts/buffer.py channels
```

Last verified: YYYY-MM-DD
