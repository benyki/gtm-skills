# Quirks, gotchas, and policy

Things that aren't obvious from the workflow doc and would otherwise be rediscovered the hard way.

## Login policy — agents do NOT sign in

If the target X account isn't already logged in to the connected browser, **stop**. Don't:
- Click "Sign in"
- Type the user's password (even if the user typed it earlier in chat)
- Use SSO / "Sign in with Google/Apple" flows
- Bypass MFA or accept emergency-recovery offers

Instead: surface this to the user with a single sentence (e.g. *"`@<handle>` is not signed in on the connected browser — please sign in, then say go."*).

Reasoning: account access is the user's responsibility and a sensitive action per the agent safety rules. Posting from the wrong account, or being tricked by a phishing flow that looks like X, is an irreversible mistake.

## `file_upload` is blocked

Documented in [image-upload.md](image-upload.md). Don't waste tool calls trying — go straight to clipboard paste.

## The composer is one big modal

- The composer is a React modal rendered on top of the page. The underlying page is still scrollable but its elements are not interactive.
- If `find` returns elements from the underlying page (e.g. a "Post" link from the left nav) instead of the composer, the modal probably hasn't opened yet — give it another `wait(2)` and re-query.
- Closing the modal (clicking the `×` top-left, or pressing Escape) **discards the draft** unless you explicitly clicked "Drafts" to save it. Don't escape mid-flow.

## Alt-text intro modal is one-shot per session

The first time you click "Add description" in a session, X shows an introductory modal explaining what alt text is. Click "Sure" (≈ `(636, 562)` at 1273×966) to dismiss it. On subsequent images that same session, the modal is skipped — you land directly in the Description editor.

## `cmd+v` requires composer focus

If the cursor focus has drifted (e.g. you clicked a tooltip), `cmd+v` does nothing. Click somewhere inside the modal's body before pasting. Don't click on toolbar icons — that may trigger their action (emoji picker, GIF picker) and steal focus.

## Threads: the button label changes

- Before adding a reply: button says **`Post`**.
- After clicking `+` and adding even an empty reply: button changes to **`Post all`**.
- The `Post all` button publishes every staged post in order.
- You can stage up to ~25 posts per thread (X limit; not relevant here).

If you only see `Post` after clicking `+`, the reply wasn't actually added — the textbox shows but no real post got staged. Type at least one character to commit the reply card.

## URL autolinks consume display chars but not character count

`yourapp.com` typed into the body gets auto-hyperlinked. It displays as the URL but counts as 23 chars regardless of actual length (X's t.co rule). For our short CTAs this never matters.

## Rate limits (rough)

X doesn't publish exact numbers. Observed safe ceilings for browser-driven posting:

- ~50–100 posts/day per account (above this, expect soft rate-limit notices)
- ~5–10 posts/hour for new-ish accounts (treat a recently created account as new-ish)
- Threads count as N separate posts toward the daily total

If a post fails with "You are over the daily limit", stop and tell the user — retrying won't help, and repeated attempts can escalate to a temporary lock.

## Drafts behaviour

X auto-saves to Drafts when you close the composer with content. The Drafts link is top-right of the composer modal. Useful if a flow gets interrupted — you can resume by clicking Drafts and selecting the half-written post. Not used in the standard workflow.

## What changes when

The X UI shifts. As of 2026-05-19:
- Composer modal layout is stable
- Element queries above all returned single matches
- The `×` (close) icon is top-left; "Drafts" is top-right

If queries start returning multiple matches or zero matches, take a fresh screenshot and `read_page(filter:"interactive")` to remap.

## What we explicitly never do

- Like, retweet, follow, or reply from a recommended-tweet sidebar item — the user didn't ask for engagement actions.
- Submit to "Edit post" (X Premium feature) — out of scope.
- Schedule posts via X's native scheduler — we have our own `schedule` skill for that orchestration.
- Touch DM (Messages) — outside this skill's scope.
