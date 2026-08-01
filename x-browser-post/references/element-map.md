# X composer — element reference map

Frozen mapping of the X.com composer UI to `find` queries and observed element shapes. Verified 2026-05-19 (post layout circa late 2025 / early 2026).

X ships UI changes frequently; if a query returns nothing or the wrong element, fall back to `read_page(filter:"interactive")` and search by characteristic text.

## Top-level composer

| Step | `find` query | Observed shape | Fallback |
|------|---|---|---|
| Open composer (from any x.com page) | `compose new post button` | `link "Post" (href="/compose/post")` | Look in left rail for the dark circular pencil icon |
| Open composer (mobile-style nav) | `Post button in left sidebar` | same | Hit URL `https://x.com/compose/post` directly |
| Text area | `tweet text area "What's happening"` | `textbox "Post text"` | Look for placeholder "What's happening?" |
| Character counter / Post button (single) | screenshot bottom-right | `button "Post"` (filled black) | `find(query:"Post button to publish")` |
| Post button when thread is staged | screenshot bottom-right | `button "Post all"` | `find(query:"Post all button")` |
| Drafts link | `Drafts link top-right of composer` | `link "Drafts"` | Avoid clicking; just informational |

## Image / media

| Step | `find` query | Observed shape | Notes |
|------|---|---|---|
| Media picker toolbar icon | `media/photo icon in composer toolbar` | `button "Add photos or video"` | Clicking opens **native file picker** which the agent can't see |
| Hidden file input | `hidden file input for image upload` | `button "(unlabeled)" (file)` | `file_upload` returns `{"code":-32000,"message":"Not allowed"}` |
| Image preview area (after paste) | screenshot | `img` with overlaid `Edit` button and `×` (remove) | The `ALT` badge appears bottom-left after alt text is saved |
| Add alt text | `"Add description" link for image alt text` | `link "Add description" (href="/compose/post/media")` | Only visible once an image is attached |
| First-time alt intro modal | screenshot | `Add descriptions` heading + `Sure` / `No, thanks` buttons | Coordinates: `Sure` ≈ `(636, 562)` at 1273x966 viewport. Only shows on first use per session |
| Alt textbox | screenshot | `textbox "Description"` (1000-char limit, counter top-right) | Coords ≈ `(636, 790)` |
| Save alt | screenshot | top-right `Save` button | Coords ≈ `(847, 70)` |
| Tag people | n/a | `link "Tag people"` | We never use this — skip |

## Threading

| Step | `find` query | Observed shape | Notes |
|------|---|---|---|
| Add post to thread (the `+`) | `"+" button to add another post to thread` | `button "Add post"` | Becomes visible once main post has text and/or media |
| New reply textbox | `Add another post textbox` | `textbox` placeholder "Add another post" | Click somewhere inside the staged reply card before typing |
| Remove a staged reply | screenshot | `button` with `×` icon at top-right of the reply card | Don't accidentally click — it deletes |

## Confirmations & post-publish

| Step | What to look for | Notes |
|------|---|---|
| Success toast | bottom-of-viewport blue toast: `"Your post was sent"` or `"Your posts were sent"` (with "View" link) | This is the only signal that publishing succeeded |
| Profile post count | sidebar / profile header increments | Useful sanity check if toast was missed |
| Composer modal dismiss | the modal closes automatically on success | If it stays open, the post failed — read any inline error |

## Layout coordinates (1273×966 viewport, default Chrome zoom)

Use `find` first. These are last-resort fallbacks; they're brittle to zoom level and viewport size.

| Element | Coords |
|---|---|
| Composer text area (top-left of caption) | `(420, 122)` |
| Toolbar — `+` Add post | `(797, 620)` |
| Toolbar — Post / Post all (right of toolbar) | `(847, 620)` / `(838, 726)` once thread staged |
| Alt intro modal — Sure button | `(636, 562)` |
| Alt edit — Description textbox | `(636, 790)` |
| Alt edit — Save (top-right) | `(847, 70)` |

If the viewport differs, screenshot first and recompute by ratio. Don't rely on these in code.

## Anti-patterns

- **Don't click the photo/media button in the toolbar** to attach a file — it opens a native file picker the agent can't interact with.
- **Don't try `file_upload`** on the hidden input — it's blocked.
- **Don't use coordinate clicks** when `find` returns a clean ref. Refs survive layout shifts; coords don't.
- **Don't navigate away** mid-flow. Closing the composer discards the draft unless you explicitly save it; X has prompted "Are you sure?" inconsistently.
