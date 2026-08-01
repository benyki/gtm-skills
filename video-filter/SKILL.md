---
name: video-filter
description: Apply ffmpeg post-processing filters to AI-generated or stock videos — downscale/upscale softening, heavy compression, film grain, framerate drop, simulated phone-filmed look, vignette, TikTok-style solid-box captions, and smooth punch-zoom. Use when an AI-rendered clip looks too clean or "too HD" and needs to read as phone-shot UGC, or when a dynamic clip needs added energy via a timed zoom-in beat.
---

# Video Filter

A collection of ffmpeg recipes that post-process a video to either (a) reduce visible fidelity so AI artifacts become less noticeable, or (b) add motion energy to make a clip feel more dynamic. Each technique is shipped as a standalone script under `scripts/` and can be chained.

All scripts use `/opt/homebrew/bin/ffmpeg` and assume an MP4 input (any resolution, any framerate).

## When to use

Use this skill when a clip:
- Was rendered by an AI model (Seedance, Sora, Runway, Veo, Kling, etc.)
- Looks "too clean" — perfect skin, glassy eyes, weirdly smooth motion
- Needs to land on TikTok/IG/Shorts and read as UGC, not as obvious AI output

Use the **techniques in combination** — any one alone is noticeable; 3–4 stacked reads as "phone video."

## Techniques

Each technique below has a matching script in `scripts/`. Pick one, or run several in sequence (output of one becomes input of the next).

### 1. Downscale + upscale (`scripts/downup.sh`)

Resize the clip down to 480p–540p, then back up to original resolution. Destroys fine detail in the exact regions where AI artifacts live: hair strands, finger boundaries, eye glints, lip edges, text. The clip still "fits" the original canvas but no longer has the resolution to show the giveaway.

```bash
bash scripts/downup.sh /abs/path/input.mp4
# → input.downup.mp4 (downscaled to 540p, upscaled back with lanczos)
```

Filter: `scale=-2:540,scale=W:H:flags=lanczos`

### 2. Heavy compression (`scripts/compressed.sh`)

Re-encode at low bitrate (~1 Mbps) with low-bitrate AAC audio. Mimics the look of a phone-recorded video that has been uploaded to TikTok and re-compressed by their pipeline. AI artifacts get smeared by macroblocks just like organic detail does.

```bash
bash scripts/compressed.sh /abs/path/input.mp4
```

Filter: none — pure encoder settings. `-crf 32 -b:v 1000k -maxrate 1200k -b:a 64k`

### 3. Film grain / digital noise (`scripts/grain.sh`)

Overlay temporal noise on every frame. Hides smooth AI textures (plastic skin, painted backgrounds), breaks up flat edges, and gives the brain something organic to latch onto.

```bash
bash scripts/grain.sh /abs/path/input.mp4
```

Filter: `noise=alls=18:allf=t+u`
- `alls=18` — strength (try 10–25)
- `allf=t+u` — temporal + uniform; t alone is too uniform, t+u looks like sensor noise

### 4. Framerate drop (`scripts/lowfps.sh`)

Drop from 24/30/60fps down to 15fps. Removes the unnaturally-smooth motion AI models produce, especially in eye saccades and finger movement. Reads as "old phone" or "compressed clip."

```bash
bash scripts/lowfps.sh /abs/path/input.mp4
```

Filter: `fps=15`

### 5. Simulated phone-filmed (`scripts/phonefilmed.sh`)

Composite effect: slight rotation, crop, contrast bump, soft vignette, temporal noise, plus audio EQ that simulates a phone mic picking up sound from a speaker. Mimics the look of someone re-filming the clip off a phone or laptop screen — extremely effective because that exact pipeline genuinely happens in the wild.

```bash
bash scripts/phonefilmed.sh /abs/path/input.mp4
```

Filter chain:
```
scale=W:H,rotate=0.015:c=black:ow=rotw(0.015):oh=roth(0.015),
crop=iw-20:ih-40,scale=W:H,
eq=contrast=1.1:brightness=-0.02:saturation=0.9,
noise=alls=10:allf=t,
vignette=PI/4.5
```
Audio: `highpass=f=200,lowpass=f=3500,acompressor=threshold=-20dB:ratio=4`

### 6. Vignette + breathing light (`scripts/vignette.sh`)

Soft vignette plus a slow sinusoidal brightness oscillation that mimics natural ambient lighting changes (sun behind clouds, indoor flicker). Distracts from the static, perfect lighting that AI clips usually have, and darkens the edges of the frame where artifacts (background people, hands) usually fail.

```bash
bash scripts/vignette.sh /abs/path/input.mp4
```

Filter: `vignette=PI/4,eq=brightness='0.05*sin(2*PI*t/3)':saturation=1.05,noise=alls=8:allf=t`

### 7. TikTok caption (`scripts/caption.sh`)

Burn a solid-background caption box at ~25% from the top, in the style of viral TikTok/IG Reels hooks ("NEW ACTING CHALLENGE!", "Do Not Post on Instagram Until You See This Secret Hack…", "3 Natural Supplements to Reduce Appetite"). The caption is the single strongest disguise: viewers' eyes go to the text, and any AI weirdness in the frame becomes peripheral.

```bash
bash scripts/caption.sh /abs/path/input.mp4 "Do Not Post on Instagram Until You See This Secret Hack"
bash scripts/caption.sh --style blue  /abs/path/input.mp4 "NEW ACTING CHALLENGE!"
bash scripts/caption.sh --style red   /abs/path/input.mp4 "Do Not Post Until You See This"
bash scripts/caption.sh --style white /abs/path/input.mp4 "3 Natural Supplements to Reduce Appetite"
bash scripts/caption.sh --y 0.17 --wrap 18 /abs/path/input.mp4 "Your hook here"
```

See `references/caption-style.md` for the full visual spec (colors, padding, font, line-wrap rules).

### 8. Punch zoom (`scripts/zoom.sh`)

Smoothly zooms the frame **in** by +40% (default) over a configurable active window, then back to 1×. No rotation, no drift — just a clean dynamic source-zoom that ramps in via a cosine ease, holds, and ramps out. Great as a subtle hype beat on B-roll, product reveals, or any moment where you want the subject to "lean in" without breaking the frame.

Timeline (default):
```
t < START                            : 1× (unchanged)
START → START+RAMP                   : ramps up to 1.4×
START+RAMP → START+RAMP+DURATION     : holds at 1.4×
... → ... + RAMP                     : ramps back to 1×
thereafter                           : 1×
```

Implemented with `scale=...:eval=frame` for per-frame dynamic scaling, plus a center crop whose offset is computed directly from `t` (the only reliable way given that `crop`'s `iw`/`ih` evaluate only at init).

```bash
bash scripts/zoom.sh /abs/path/input.mp4                # default: +40%, start 1.0s, hold 5.6s
bash scripts/zoom.sh --zoom-in 0.6 input.mp4            # +60% punch
bash scripts/zoom.sh --duration 3 input.mp4             # shorter hold
bash scripts/zoom.sh --start 0.5 --ramp 0.6 input.mp4   # earlier and smoother
```

Flags:
- `--zoom-in F`    extra zoom at peak (default 0.4 = +40%)
- `--start S`      time to begin ramping in (default 1.0)
- `--duration S`   how long to HOLD at peak zoom (default 5.6)
- `--ramp S`       ramp-in/ramp-out duration each (default 0.4)

## Stacking guidance

Each script writes a new MP4 next to the input with a suffix (e.g. `clip.grain.mp4`). To stack, just feed the output of one into the next:

```bash
bash scripts/downup.sh      input.mp4         # → input.downup.mp4
bash scripts/lowfps.sh      input.downup.mp4  # → input.downup.lowfps.mp4
bash scripts/grain.sh       input.downup.lowfps.mp4
bash scripts/compressed.sh  input.downup.lowfps.grain.mp4
bash scripts/caption.sh --style white input.downup.lowfps.grain.compressed.mp4 "wait for it…"
```

**Recommended combos:**
- *Phone-shot UGC:* `phonefilmed` → `compressed` → `caption`
- *TikTok recycled clip:* `downup` → `lowfps` → `compressed` → `caption`
- *Cinematic vibe:* `vignette` → `grain` → `compressed`

## Binary resolution

Scripts use `/opt/homebrew/bin/ffmpeg` directly. Override with `FFMPEG_BIN=/path/to/ffmpeg bash scripts/...`.

## References

- `references/caption-style.md` — full caption spec with color/padding/font values matched to the reference screenshots.
