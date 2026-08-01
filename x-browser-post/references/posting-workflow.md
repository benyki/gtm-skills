# Worked example — posting a thread with image and alt text

End-to-end run that posted a caffeine-app caffeine-curve thread from `@your-brand-handle` on 2026-05-19. Use as a literal playbook; substitute caption / image path / reply text.

## Pre-flight

```text
list_connected_browsers
→ [{"deviceId":"00000000-0000-0000-0000-000000000000","name":"Browser 1",...}]

select_browser(deviceId)
→ "Connected to browser 'Browser 1'."

tabs_context_mcp(createIfEmpty:true)
→ availableTabs: [{tabId: 1304587395, url:"chrome://newtab/"}]
```

## Navigate and confirm session

```text
navigate(url:"https://x.com/your-brand-handle", tabId:<tab-id>)
computer.screenshot(tabId, save_to_disk:true)
```

Confirm the screenshot shows the target handle's profile (not the X "Sign in" page). If unauthenticated → stop and surface to the user; do **not** log in.

## Open composer

```text
find(query:"compose new post button", tabId)
→ ref_37: link "Post" (href="/compose/post")

browser_batch([
  computer.left_click(ref:"ref_37", tabId),
  computer.wait(duration:2, tabId),
  computer.screenshot(tabId, save_to_disk:true)
])
```

Composer modal appears with textbox "What's happening?".

## Type caption

```text
find(query:"tweet text area 'What's happening' and the hidden file input for image upload", tabId)
→ ref_462: textbox "Post text"
→ ref_470: button "(unlabeled)" (file)   # do not use

browser_batch([
  computer.left_click(ref:"ref_462", tabId),
  computer.type(text:"How much caffeine is still in your blood at bedtime after a travel day?\n\nAfter a big coffee at 06:00, a Coca-Cola at 12:00 and another big coffee at 17:00, → still ~85 mg in your blood at 23:00 bedtime.", tabId)
])
```

Multi-line: `\n` works inside the `type` action. The unicode arrow `→` works.

## Attach image via clipboard paste

The agent already verified `file_upload` is blocked. So:

```bash
# Bash — copy PNG to macOS clipboard as PNG image
osascript -e 'set the clipboard to (read (POSIX file "/tmp/caffeine-app-charts/25-long-haul-flight.png") as «class PNGf»)'
```

Then inside the composer:

```text
browser_batch([
  computer.left_click(coordinate:[655, 230], tabId),   # inside composer body, below caption
  computer.key(text:"cmd+v", tabId),
  computer.wait(duration:4, tabId),
  computer.screenshot(tabId, save_to_disk:true)
])
```

Verify the image preview now sits below the caption with `Edit` button and `×`, plus a "Tag people" / "Add description" rail underneath.

## Add alt text

```text
find(query:"'Add description' link for image alt text, and the '+' button to add another post to thread", tabId)
→ ref_497: link "Add description" (href="/compose/post/media")
→ ref_500: button "Add post"

# 1. Open the alt panel
browser_batch([
  computer.left_click(ref:"ref_497", tabId),
  computer.wait(duration:2, tabId),
  computer.screenshot(tabId, save_to_disk:true)
])
```

First time per session, X shows an intro modal ("Add descriptions" / "Sure" / "No, thanks"). Click "Sure". Then the Description textbox is at the bottom of the alt panel.

```text
browser_batch([
  computer.left_click(coordinate:[636, 562], tabId),    # "Sure" button on the intro modal
  computer.wait(duration:1, tabId),
  computer.left_click(coordinate:[636, 790], tabId),    # Description textbox
  computer.type(text:"Caffeine-in-blood chart from 4am to 4am. A big coffee at 06:00 (~130mg), a Coca-Cola at 12:00 (~33mg) and another big coffee at 17:00 (~130mg) stack to an early-evening peak around 140mg, with ~85 mg still circulating at 23:00 bedtime in the amber caution zone.", tabId),
  computer.wait(duration:1, tabId),
  computer.screenshot(tabId, save_to_disk:true)
])
```

```text
# Save the alt text — the "Save" button is top-right of the modal
browser_batch([
  computer.left_click(coordinate:[847, 70], tabId),
  computer.wait(duration:2, tabId),
  computer.screenshot(tabId, save_to_disk:true)
])
```

The image now shows an `ALT` badge bottom-left, and the truncated description text under "Tag people".

## Stage the reply (thread)

```text
browser_batch([
  computer.left_click(coordinate:[797, 620], tabId),    # "+" Add post button (or use ref_500)
  computer.wait(duration:2, tabId),
  computer.screenshot(tabId, save_to_disk:true)
])
```

A new "Add another post" textbox appears below the staged main post.

```text
browser_batch([
  computer.left_click(coordinate:[655, 549], tabId),    # inside the new reply textbox
  computer.type(text:"<one or two sentences on what the app does and who it is for>.\n\nLink: yourapp.com", tabId),
  computer.wait(duration:1, tabId),
  computer.screenshot(tabId, save_to_disk:true)
])
```

The CTA link (`yourapp.com`) gets auto-hyperlinked by X — that's expected.

## Publish

The Post button now reads **"Post all"** because a thread is staged:

```text
browser_batch([
  computer.left_click(coordinate:[838, 726], tabId),
  computer.wait(duration:5, tabId),
  computer.screenshot(tabId, save_to_disk:true)
])
```

The composer closes. A blue toast appears at the bottom: `"Your posts were sent"` with a `View` link. Profile post count increments by 2 (main + reply).

## What success looks like

- ✓ Composer modal closed automatically (no inline error)
- ✓ Blue toast `"Your posts were sent"` visible briefly
- ✓ Profile post count increased by the number of staged posts
- ✓ Refreshing the profile shows the new thread at the top

## What failure looks like

- ❌ Modal stays open with red error text (rate-limited / duplicate post / image too large)
- ❌ Toast says `"Your post couldn't be sent"`
- ❌ Composer flashes but text remains — usually means the click missed the actual button (use `find` instead of coordinates)

When in doubt, take another screenshot. The X UI gives clear visual signals; trust them over assuming the action succeeded.
