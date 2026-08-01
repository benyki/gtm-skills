---
name: app-thread-backstory
description: Publish word-etymology "backstory" threads for the brand to X/Twitter and Bluesky. Reads the backlog at ~/code/<project>/world/threads/inputs/thread-inputs.json — each entry is a ready-to-post thread that opens with a scroll-stopping hook and then tells the true origin and deeper meaning of one everyday word. Picks an unposted thread, renders it, posts the chain to Bluesky (bluesky-post-manage) and/or X (x-browser-post), and marks it done. Use when the user says "post the next word-backstory thread", "ship an etymology thread", "do a word thread", or anything similar.
---

# app-thread-backstory

End-to-end workflow that turns one entry in the word-backstory backlog into a posted thread on
**X/Twitter** and/or **Bluesky**. Each thread starts with one of four canonical hook tweets, then
explains the etymology and true meaning of a single everyday word.

## When to use

- "Post the next word-backstory thread"
- "Ship an etymology thread to Bluesky / X"
- "Do a word thread about <word>"
- Any request to draft, render, or post one of the threads in the backlog

## Where everything lives

- **Workspace:** `~/code/<project>/world/threads/`
  - **Backlog:** `inputs/thread-inputs.json` — array of thread entries (`status`: `todo` | `done`)
  - **Config:** `inputs/config.md` — accounts, opener templates, schema, how to add more
  - `posted/` — optional archive of posted threads
- **This skill's scripts:** `~/.agents/skills/app-thread-backstory/scripts/`
- **Dependent skills:**
  - `bluesky-post-manage` — Bluesky XRPC client (account `MAIN`, creds in `~/.agents/.env`)
  - `x-browser-post` — X posting via the Claude-in-Chrome browser MCP (target `@your-handle`)
- **Etymology sources used to write the seed threads:** [references/etymology-sources.md](references/etymology-sources.md)

## The four opener templates

Every thread's **first post** is one of these (already rendered into each entry's `opener`):

| `template` | Use when | Shape |
|---|---|---|
| `default-1` | safe default | `"<WORD>": <X> million daily users, yet most people don't know its backstory and deeper meaning. Thread` |
| `default-2` | safe default | `Every day, around <X> million people use the word "<WORD>." Almost none of them know where it came from and why it means what it means. (thread)` |
| `surprising` | the origin is surprising | `We take the word "<WORD>" for granted. But it's hiding a meaning and a backstory most native speakers have no idea about. Thread:` |
| `weird` | the origin is weird/mysterious/a great story | `The backstory behind the word "<WORD>" is fascinating. Let me tell you how we ended up using it:` → **story-across-centuries** body |

The full thread is always: **`opener` (post 1) → each `posts[]` string (posts 2..n) → `cta_reply` (final reply)**.

## Workflow

### 1. Pick an unposted thread

```bash
node …/pick-todo.mjs --platform bluesky        # random thread still todo on Bluesky
node …/pick-todo.mjs --platform x --label clue # a specific one (any status)
node …/pick-todo.mjs --list-todos              # full per-platform status matrix
node …/pick-todo.mjs --list-todos --platform x # labels still todo on X
```

Status is **per platform**: `status = { x, bluesky, threads }`, each `todo` | `done`. Pick by the
platform you're about to post to. The user may also name the word directly with `--label`.

### 2. Render + validate

```bash
node ~/.agents/skills/app-thread-backstory/scripts/render-thread.mjs <label>
```

Prints the numbered posts with per-post character counts (validates against the 280-char X limit;
Bluesky allows 300). Add `--strip-md` to drop the `*italic*` asterisks, `--json` to emit the raw
ordered array. **If any post is flagged OVER, trim it in `thread-inputs.json` before posting.**

### 3. Show the user, get a go

Always paste the full rendered thread (opener → body → reply) to the user and wait for explicit
approval. **Posting is public and irreversible.** Also confirm the destination(s): Bluesky, X, or both.

### 4a. Post to Bluesky

```bash
bash ~/.agents/skills/app-thread-backstory/scripts/post-bluesky-thread.sh --label <label>
#   --account MAIN   (default)   --strip-md   (drop * asterisks)   --dry-run (print, don't post)
```

The script reads the same rendered posts, then posts the **fully chained** thread: post 1 is the
opener, every later post replies to the previous one, and the thread root stays the opener. It prints
the live `bsky.app` URL.

> First run of a session: confirm `~/.agents/.env` has `BSKY_ACCOUNT_MAIN_*` set and that `MAIN` is
> the intended account (`node --env-file=~/.agents/.env ~/.agents/skills/bluesky-post-manage/scripts/list-accounts.mjs`).

### 4b. Post to X / Twitter

Follow the `x-browser-post` skill against `@your-handle`. There is no API — it drives the logged-in
browser. Outline:

1. Connect the browser; navigate to `https://x.com/<your-handle>`; confirm logged in as your-handle.
2. Open the composer and type **post 1** (the `opener`).
3. For each remaining post, click the `+` (Add another post) to stage a new box and type it — one box
   per `posts[]` entry, then the `cta_reply` last. Get the exact text from
   `render-thread.mjs <label> --json` so it matches the Bluesky version verbatim.
4. Click **Post all**; verify the "Your posts were sent" toast.

Full element-ref map + the clipboard image-upload workaround (not needed here — these threads are
text-only): [../x-browser-post/SKILL.md](../x-browser-post/SKILL.md).

### 5. Mark done — per platform

Right after a platform's post lands, mark only that platform:

```bash
node …/mark-done.mjs <label> --platform bluesky --url <bsky-url>
node …/mark-done.mjs <label> --platform x --url <x-url>
node …/mark-done.mjs <label> --platform x,threads          # comma list if you did several
```

Sets `status[platform] = "done"` and records the URL in `posted[platform]`. A thread is fully
shipped only when `x`, `bluesky`, and `threads` are all `done`.

## Rules

- **Never mark a platform `done` before that platform's post is live.** Status is per-platform
  (`x` / `bluesky` / `threads`); mark each one only when its own post lands.
- **Always preview + get a go before posting.** Public and irreversible.
- **Etymology must be true.** Per project memory ([verify-foreign-phrases]), never trust English
  "untranslatable / surprising word origin" listicles — verify against the Online Etymology
  Dictionary, OED, or Wiktionary before adding a new thread. A catchy-but-false folk etymology
  (e.g. "sincere = without wax") is disqualifying unless the thread explicitly debunks it.
- **One link only**, in the `cta_reply`. No link in the body posts (hurts reach).
- **No em dashes (`—`)** in any post. If you spot one in a backlog entry, fix it before posting.
- **Keep the two platforms identical** — same text in the same order, so the thread reads the same on
  X and Bluesky. Decide once per thread whether to keep or strip the `*` asterisks and be consistent.
- **`<X>` is approximate.** The daily-usage figure is illustrative and always softened with "~"/"around".

## Adding more threads (scaling to hundreds)

See the "Adding more threads" section of [the config](file://~/code/<project>/world/threads/inputs/config.md)
and the candidate backlog there. Process: pick a word with a verified, well-attested etymology →
choose the opener template by how the origin feels → write 3–6 tight body posts (≤280 chars each) →
end on the payoff → append with `status: "todo"`.

## Files

- [SKILL.md](SKILL.md) — this file
- [references/etymology-sources.md](references/etymology-sources.md) — source notes for the 10 seed threads
- [scripts/pick-todo.mjs](scripts/pick-todo.mjs) — pick a random / named / list todo threads
- [scripts/render-thread.mjs](scripts/render-thread.mjs) — render + char-count a thread (`--json`, `--strip-md`)
- [scripts/post-bluesky-thread.sh](scripts/post-bluesky-thread.sh) — post the chained thread to Bluesky
- [scripts/mark-done.mjs](scripts/mark-done.mjs) — flip `status` to `done`

## Accounts

- Bluesky: `MAIN` (handle + app password in `~/.agents/.env`)
- X/Twitter: `@your-handle` (whatever account is logged into the connected Chrome browser)
