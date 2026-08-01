---
name: x-browser-post
description: Post to X (formerly Twitter) via the Claude-in-Chrome browser MCP — single posts, threads, image attachments, alt text. Bypasses the X API entirely; works with whatever X account is already logged in to the connected browser. Use when the user asks to "post to X", "tweet via browser", "ship this to Twitter", "thread this on X", or when API access is unavailable / not desired. Documents exact element queries, the clipboard-paste image upload workaround, and the full posting workflow.
---

# x-browser-post

Operational skill for posting to **X** (twitter.com / x.com) using the **Claude-in-Chrome browser MCP**, since the file-upload path is blocked and the platform's UI shifts often enough to warrant a frozen, tested workflow.

## When to use

- "Post this to X"
- "Tweet from `@<handle>`"
- "Thread this on X with the image"
- Posting to an X account where API credentials aren't available — only a logged-in browser session

## Prerequisites

- Claude-in-Chrome extension installed and a browser connected (`list_connected_browsers` returns at least one device).
- The target X account is **already signed in** in that Chrome browser. This skill does NOT log in — see [references/quirks.md](references/quirks.md) on why.
- macOS for the clipboard-paste image workaround (uses `osascript`). Linux/Windows would need an equivalent — not documented here.

## High-level workflow

1. **Connect browser** → `list_connected_browsers` → `select_browser` → `tabs_context_mcp(createIfEmpty:true)`.
2. **Navigate** to `https://x.com/<handle>` (or any x.com URL) to confirm session.
3. **Open composer** → find link "compose new post button" (`href="/compose/post"`), click it.
4. **Type caption** → find textbox "tweet text area" → click → `computer type` the caption (multi-line `\n` works).
5. **Attach image** → see [references/image-upload.md](references/image-upload.md) — uses macOS clipboard (`osascript`) + `cmd+v` inside the composer body. The native file input is **blocked** with `"Not allowed"`.
6. **Alt text** (recommended) → find link "Add description" (`href="/compose/post/media"`), click → modal asks "Sure" / "No, thanks" → click "Sure" → type into Description textbox → click "Save" (top-right of the alt panel).
7. **Threaded reply** (optional) → find button "Add post" (the `+` icon in the composer toolbar) → click → "Add another post" textbox appears → click and type the reply.
8. **Publish** → click "Post" (single post) or "Post all" (when a thread is staged).
9. **Verify** → screenshot to confirm the "Your post was sent" / "Your posts were sent" toast.

A complete worked example with screenshots-worth-of-detail is in [references/posting-workflow.md](references/posting-workflow.md).

## Element reference map

Frozen here so the next agent doesn't re-discover them via `read_page`. Verified 2026-05-19.

| Goal | Use `find` query | Returned element shape |
|------|------------------|------------------------|
| Open composer | `compose new post button` | `link "Post" (href="/compose/post")` |
| Type caption | `tweet text area "What's happening"` | `textbox "Post text"` |
| Add image (don't use) | `hidden file input for image upload` | `button "(unlabeled)" (file)` — **`file_upload` returns "Not allowed"** |
| Add alt text | `"Add description" link for image alt text` | `link "Add description" (href="/compose/post/media")` |
| Add to thread | `"+" button to add another post to thread` | `button "Add post"` |
| Reply textbox (after `+`) | `Add another post textbox` | `textbox` (no fixed name; appears below the staged post) |
| Publish single | screenshot — bottom-right of composer modal | `button "Post"` (filled black) |
| Publish thread | screenshot — bottom-right after `+` clicked | `button "Post all"` |

Full table with fallback queries and known instability notes: [references/element-map.md](references/element-map.md).

## Image upload (the one tricky bit)

The composer exposes a file `<input>` but Claude-in-Chrome blocks `file_upload` on it with `{"code":-32000,"message":"Not allowed"}`. The reliable path is **clipboard paste**:

```bash
bash ~/.agents/skills/x-browser-post/scripts/copy-image-to-clipboard.sh /abs/path/to/image.png
```

Then inside the open composer, click somewhere in the **body of the composer** (e.g. just below the typed text — not on the toolbar icons) and press `cmd+v`. X will inline the image and render an `ALT` badge plus the "Add description" / "Tag people" rail under it.

Full notes (other approaches tried, why they failed): [references/image-upload.md](references/image-upload.md).

## Threads and the character limit

X enforces a **280-character limit per post** for standard (free) accounts. X Premium subscribers can post up to 25,000 chars in a single post, but **do not assume Premium** — the connected browser session may be on a free account, and a too-long caption will be silently truncated or rejected by the composer.

**Rule:** if the user provides text longer than 280 characters, split it into a thread automatically. Do not ask first — splitting is the expected behavior, not a decision point. Only ask if the user explicitly says "post this as one tweet" and it's over the limit.

### Splitting strategy

1. **Count characters, not words.** URLs count as their full visible length in the composer (X's t.co shortening happens server-side but the composer counter shows the raw string).
2. **Target ~270 chars per post** to leave headroom for the " 🧵 1/N" / "2/N" suffix and avoid edge-case off-by-one rejections.
3. **Break on sentence or paragraph boundaries first**, then on clause boundaries (`, ` / `; ` / ` — `), then on word boundaries. Never split mid-word.
4. **Don't break code blocks, URLs, or @handles** across posts — move the whole token to the next post if it would otherwise straddle a boundary.
5. **Numbering:** append ` 1/N`, ` 2/N`, … to each post when the thread has 3+ posts. For 2-post threads, numbering is optional — usually skip it and let the reply visually carry the continuation.
6. **First post is the hook.** If splitting a long-form text, rewrite the first 280 chars so it stands alone as bait, rather than dumping the original opening verbatim and trailing off mid-thought.

### Posting a thread

Each additional post is staged via the `+` "Add post" button **before** publishing — they all ship together when "Post all" is clicked. The flow scales to N posts:

```text
(after typing post 1)
for each remaining post i in 2..N:
  find(query:"Add post button +", tabId) → ref_addpost
  computer.left_click(ref:ref_addpost, tabId)
  find(query:"Add another post textbox", tabId) → ref_reply_i   # picks the newest empty box
  computer.left_click(ref:ref_reply_i, tabId)
  computer.type(text:post_i_text, tabId)

find(query:"Post all button", tabId) → ref_postall
computer.left_click(ref:ref_postall, tabId)
```

Notes:
- The textbox `find` query returns the **newest empty** textbox in the composer — re-run `find` between each post rather than caching the ref.
- The publish button label switches from **"Post"** → **"Post all"** as soon as the first `+` is clicked. Don't cache the button ref from before staging the thread.
- For very long threads (8+ posts), `computer.wait(duration:1)` between `+` clicks gives the DOM time to settle.
- Verify with a screenshot after "Post all" — the toast reads **"Your posts were sent"** (plural).

## Quick recipe — single post with image and alt text

```text
1. list_connected_browsers → select_browser(deviceId)
2. tabs_context_mcp(createIfEmpty:true) → get tabId
3. navigate(url:"https://x.com/", tabId)
4. find(query:"compose new post button", tabId) → ref_compose
5. computer.left_click(ref:ref_compose, tabId)
6. find(query:"tweet text area", tabId) → ref_text
7. computer.left_click(ref:ref_text, tabId)
8. computer.type(text:"<caption>", tabId)
9. Bash: copy-image-to-clipboard.sh /tmp/img.png
10. computer.left_click(coordinate:[<x>,<y>], tabId)   # inside composer body, below text
11. computer.key(text:"cmd+v", tabId)
12. computer.wait(duration:3, tabId)                   # give upload time
13. find(query:"Add description link", tabId) → ref_alt
14. computer.left_click(ref:ref_alt, tabId)
15. computer.left_click(coordinate:[636,562], tabId)   # "Sure" button on intro modal
16. computer.left_click(coordinate:[636,790], tabId)   # Description textbox
17. computer.type(text:"<alt>", tabId)
18. computer.left_click(coordinate:[847,70], tabId)    # Save button (top-right of alt modal)
19. find(query:"Post button to publish", tabId) → ref_post
20. computer.left_click(ref:ref_post, tabId)
21. computer.wait(duration:5, tabId)
22. computer.screenshot(tabId, save_to_disk:true)      # verify "Your post was sent"
```

For a thread (main + reply), insert between steps 18 and 19:

```text
18a. find(query:"Add post button +", tabId) → ref_addpost
18b. computer.left_click(ref:ref_addpost, tabId)
18c. computer.left_click(coordinate:[<reply textbox x>, <y>], tabId)
18d. computer.type(text:"<reply text>", tabId)
```

Then the publish button is **"Post all"** instead of **"Post"** — find with query `"Post all" button` if the position changed.

**Always batch consecutive calls into `browser_batch`** — the MCP repeatedly reminds you, and round-trips are slow.

## Rules

- **Never log in on the user's behalf.** If the target account isn't already signed in, stop and tell the user.
- **Posting is irreversible.** Show the user the caption + reply + image preview and wait for explicit confirmation before clicking the final Post / Post all button.
- **Always include alt text** when posting an image, unless the user opts out. The chart/data threads we post benefit accessibility *and* engagement.
- **Screenshot to verify.** "I clicked Post" is not the same as "X confirmed the post". Always capture the success toast.
- **Stay on x.com.** If a navigation lands on `twitter.com`, follow the redirect — never type credentials anywhere yourself.

## Files

- [SKILL.md](SKILL.md) — this file
- [references/element-map.md](references/element-map.md) — full element/selector mapping with fallback queries
- [references/posting-workflow.md](references/posting-workflow.md) — annotated end-to-end example (caffeine thread, posted 2026-05-19)
- [references/image-upload.md](references/image-upload.md) — clipboard workaround + what doesn't work
- [references/quirks.md](references/quirks.md) — login policy, file_upload blocking, layout drift, rate hints
- [scripts/copy-image-to-clipboard.sh](scripts/copy-image-to-clipboard.sh) — macOS PNG → clipboard helper
