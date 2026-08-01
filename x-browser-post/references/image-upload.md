# Image upload — the clipboard workaround

The default browser MCP path (`file_upload` onto the composer's hidden `<input type="file">`) **does not work** on X. This file explains why and how to do it.

## What doesn't work

### `file_upload` on the hidden input

```text
find → ref_470: button "(unlabeled)" (file)
file_upload(paths:["/tmp/img.png"], ref:"ref_470", tabId)
→ {"code":-32000,"message":"Not allowed"}
```

This is a Claude-in-Chrome permission gate, not an X-side block. The extension refuses to feed arbitrary local files into web page inputs. There is currently no flag to grant it.

### Clicking the toolbar media icon

```text
computer.left_click on the photo icon
→ opens native OS file picker
→ agent cannot see/interact with the OS picker
```

Dead end — the picker is outside the browser viewport.

### `upload_image` with a previously-captured screenshot

```text
upload_image(imageId:"ss_xxx", ref:"ref_470", tabId)
```

This works only for screenshots captured **by the computer tool** or user-uploaded images attached to the conversation. It cannot reach an arbitrary file on disk. Not useful for charts we've just generated in `/tmp/`.

### Drag-and-drop with `upload_image` + coordinate

```text
upload_image(imageId, coordinate:[x,y], tabId)
```

Same limitation as above — needs an `imageId`, not a disk path. If the image is already in the conversation as an attachment, this works; otherwise no.

## What works — clipboard paste

X's composer accepts pasted image data from the clipboard. On macOS:

```bash
osascript -e 'set the clipboard to (read (POSIX file "/abs/path/to/image.png") as «class PNGf»)'
```

The `«class PNGf»` type is the AppleScript code for raw PNG image data on the clipboard. After this command runs, `cmd+V` in the composer pastes the image inline.

The repo ships a helper:

```bash
bash ~/.agents/skills/x-browser-post/scripts/copy-image-to-clipboard.sh /abs/path/to/image.png
```

Then, with the composer modal open and focused:

```text
computer.left_click(coordinate:[<x>, <y>], tabId)   # inside composer body — typically just below typed caption
computer.key(text:"cmd+v", tabId)
computer.wait(duration:3, tabId)                    # give X time to render the preview
computer.screenshot(tabId, save_to_disk:true)       # verify preview appeared
```

X will:
1. Insert an `<img>` preview below the caption.
2. Render an `Edit` button overlaid on the image (for cropping) and a `×` to remove.
3. Add a row below: `Tag people` | `Add description` — the latter is the alt-text entrypoint.

## Tips

- **Click target matters.** The paste only works if the focused element is inside the composer modal. Clicking outside the modal first (e.g. on the dimmed background) drops focus; subsequent `cmd+v` does nothing. Click on a known-empty area inside the composer body (e.g. just below the last line of typed text).
- **Wait after paste.** Large images can take a few seconds to render the preview. Screenshot too early and you'll think the paste failed.
- **Format support.** PNG and JPEG both work. Animated GIFs need a different osascript class (`«class GIFf»`) — not currently scripted.
- **Multi-image posts** (up to 4): repeat the clipboard+paste cycle. X auto-arranges into a grid.

## Why not just use the X API?

We do, when there's an API key and the account is set up for OAuth. But this skill explicitly covers the browser-only case: accounts where the user only has a logged-in browser session, no developer credentials. Useful for sub-brand handles where API access isn't worth the setup cost.

## Future improvements

If file_upload ever gets unblocked, prefer it — clipboard paste is fragile to focus changes and OS-level paste interception (1Password, clipboard managers, etc.). For now, the clipboard path is the reliable one.
