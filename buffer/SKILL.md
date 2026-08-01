---
name: buffer
description: Buffer API foundation — auth, endpoint, GraphQL schema, channels/orgs, scheduling, drafts/ideas, metrics, and all Buffer features & API docs. Use for any Buffer API question or non-video task. For the ready-made TikTok/video posting workflow (script, accounts, /published rule) use the `buffer-videos` skill.
---

# Buffer (API & Features)

Foundation skill for the **Buffer GraphQL API**: authentication, the schema, and how to
do anything Buffer exposes — list channels, create/edit/delete posts, drafts and ideas,
read posting limits and metrics, set per-network metadata.

> Posting **videos to TikTok** has a dedicated workflow (a CLI that handles public-URL
> upload, the `/published` archive rule, and the account list): use **`buffer-videos`** —
> [[buffer-videos]]. This skill is everything else / the underlying API.

## When to Use This Skill

- "How does the Buffer API work / authenticate?"
- "Write/adjust a Buffer API call (channels, posts, drafts, ideas, metrics, limits)."
- "Edit or delete a scheduled post", "read what's queued", "check posting limits."
- Any Buffer feature that isn't the canned video-posting flow.

## Authentication

- **Endpoint:** `POST https://api.buffer.com` (single GraphQL endpoint).
- **Header:** `Authorization: Bearer $BUFFER_API_KEY` on every request.
- **Credential:** `BUFFER_API_KEY` in `~/.agents/.env`. Source it (absolute path) — never
  read `.env` directly (see local-secrets):
  ```bash
  set -a; . ~/.agents/.env; set +a
  ```
  Use the **absolute path**: a relative `. .env` fails because the shell cwd can reset.
- An **API key** (Settings → API) and an **OAuth access token** are used identically;
  the key is permanent until rotated. OAuth tokens expire (~3600s) and need refresh.

Minimal request:

```bash
set -a; . ~/.agents/.env; set +a
TMP=$(mktemp)
echo '{"query":"query { account { email organizations { id name } } }"}' > "$TMP"
 curl -s https://api.buffer.com -H "Authorization: Bearer $BUFFER_API_KEY" \
   -H "Content-Type: application/json" --data-binary @"$TMP"
```

(Leading space keeps it out of shell history. Use `--data-binary @file` so the token is
never on the command line.)

## Data Model

`account` → one or more `organizations` → each org has `channels` (connected social
profiles) and `ideas` (draft content). A **channel** is one connected profile (a TikTok,
an Instagram, etc.). **Posts** belong to a channel.

## Reference

See [references/api.md](references/api.md) for the full, introspection-verified schema:
queries, mutations, `CreatePostInput`, asset/metadata input types, enums, and the union
return shape. Re-introspect any time the API changes (the doc explains how).

## Discovering the schema

The API is fully introspectable — don't guess field names (several plausible ones don't
exist). Example, list a type's fields:

```bash
set -a; . ~/.agents/.env; set +a
TMP=$(mktemp)
echo '{"query":"query { __type(name: \"Channel\") { fields { name } } }"}' > "$TMP"
 curl -s https://api.buffer.com -H "Authorization: Bearer $BUFFER_API_KEY" \
   -H "Content-Type: application/json" --data-binary @"$TMP"
```

Swap `Mutation`, `CreatePostInput`, `AssetInput`, etc. for `name` to inspect those.

## Gotchas (learned the hard way)

- **No media upload endpoint.** There is no upload/asset mutation — media is referenced
  by a **public URL** (`VideoAssetInput.url` / `ImageAssetInput.url`); Buffer fetches it.
  Anything to publish must be hosted publicly first.
- **Union returns need inline fragments:** `createPost` returns `PostActionSuccess` |
  `MutationError`; select with `... on PostActionSuccess { post { ... } }`.
- **Object fields need subfield selections:** e.g. `post.error` is a `PostPublishingError`
  — query `error { message }`, not bare `error`.
- **`dueAt` is required** when `mode: customScheduled`.
- Validation/logic errors come back in a `200` body under `errors[]` — check for it.

## Related

- **`buffer-videos`** ([[buffer-videos]]) — TikTok/video posting CLI, account list,
  `/published` archive rule. Its `scripts/buffer.py` is a working reference implementation
  of the queries/mutations documented here.
