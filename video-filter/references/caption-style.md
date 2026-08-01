# Caption style reference

The caption look mimics three common viral TikTok/Reels hook treatments seen in:

- `Screenshot 2026-05-20 at 5.42.04 PM.png` — blue box, white text, all caps ("NEW ACTING CHALLENGE!")
- `Screenshot 2026-05-20 at 5.43.00 PM.png` — red box, white text, sentence case ("Do Not Post on Instagram Until You See This Secret Hack…")
- `Screenshot 2026-05-20 at 5.42.52 PM.png` — white box, black text, sentence case ("3 Natural Supplements to Reduce Appetite")

## Visual spec

| Property        | Value                                                |
|-----------------|------------------------------------------------------|
| Position        | Top of box at ~17% from top of frame (`--y 0.17`, centered around 20%) |
| Horizontal      | Centered                                             |
| Font            | Inter Bold (`~/Library/Fonts/Inter_24pt-Bold.ttf`)   |
| Fallback font   | `/System/Library/Fonts/Supplemental/Arial Bold.ttf`  |
| Font size       | `video_width / 16`, floor 28                         |
| Padding         | `fontsize / 2` on all sides (via `boxborderw`)       |
| Line spacing    | `fontsize / 2`                                       |
| Line wrap       | 22 chars/line by default (word-boundary, `fold -s`)  |
| Alignment       | Centered (drawtext: `x=(w-text_w)/2`)                |

## Color presets

| Preset | Box color   | Text color | Notes                            |
|--------|-------------|------------|----------------------------------|
| white  | `#FFFFFF`   | black      | Default. Universal, high contrast |
| blue   | `#3A8DFF`   | white      | TikTok-blue. Reads as challenge/announcement |
| red    | `#E63946`   | white      | Urgency / warning ("Do not post…")        |

## Why these specific values

- **~20% from top**: caption sits just under the safe-area top notch of most phones but above the subject's face, so it pulls eye attention up and away from face/hands (the regions where AI artifacts are most noticeable).
- **Bold sans + solid box**: matches CapCut's default caption template — viewers' brains immediately read it as "TikTok caption," not "burned-in subtitle."
- **22 chars/line wrap**: empirically lines wrap to 2–3 rows in 720-wide vertical video, which matches the reference screenshots. Shorter wraps look chunky; longer wraps stretch beyond the safe area on iPhone Reels overlays.

## Limitations

- Corners are sharp rectangles, not rounded. The reference screenshots have ~6–8px rounded corners — to match exactly, generate a PNG caption (Pillow / sharp / SVG) and overlay it instead of using drawtext. The sharp-cornered version is close enough for most purposes and runs in pure ffmpeg with no asset pipeline.
- No drop shadow. The reference screenshots have none, so this is intentional.
- No animation (fade-in, pop-in). Add later if needed via `enable='between(t,0,3)'` for time-gated captions.
