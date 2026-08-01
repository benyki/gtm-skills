# Discord report via your agent runtime

Delivery is handled by `scripts/report_to_discord.sh`. This explains the moving
parts. (Why not the agent-relay path? See `troubleshooting.md` §3–4.)

## Identity & target

- Posts as the **`@your-bot` bot**, which is the your agent runtime **`default` discord
  account** (Bot id `123456789012345678`). `your-bot`'s routing is
  `discord accountId=default`, and `default` is the only account with send
  permission on the configured channel.
- Channel + account come from the resolved config (`discord.channel` /
  `discord.account`), overridable with `CHANNEL=` / `ACCOUNT=`.

## The command the script runs

```bash
your-agent message send \
  --channel discord \
  --account default \
  --target channel:<id> \
  --message "<verbatim report>"
```

`message send` (not `agent --deliver`) guarantees the precomposed report goes out
exactly as built — no local-model rewriting.

## Preflight (recommended before first --send to a new channel)

```bash
your-agent channels status --probe
your-agent channels capabilities --channel discord --target channel:<id>
# under the intended account, confirm: "Missing required: none"
```

## Safety

Posting to Discord = sending a message on the user's behalf. The script
**previews by default** and only posts with `--send`. Confirm before `--send`.

## Report format produced

```
<reportTitle> (top N)

1. <url>
   📅 <date> · ❤️ <likes> · ▶️ <views> · 💬 <comments>
   <note|caption>
… (×N)

<commentHeader>

1. "<template 1>"
2. "<template 2>"
3. "<template 3>"
4. "<template 1>"   ← templates rotate
…
```

The meta line shows only the fields present in the posts JSON (`date`, `views`,
`comments` come from the Apify search; counts are humanized, e.g. `415.0K`,
`3.1M`). Posts are pre-ranked by engagement + recency (see `post-finder-config.md`
→ `ranking`).

Title, header and templates all come from `post-finder-config.md` — edit there,
not in the script.
