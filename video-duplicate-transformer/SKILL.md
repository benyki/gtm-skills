---
name: video-duplicate-transformer
description: Produce visually-near-identical but perceptual-hash-distinct duplicates of a source video by stacking pixel-level transforms (zoom, rotate, border, color/gamma/hue shift, noise overlay, downscale-upscale cycle, speed wobble, edge trim, audio pitch shift, fresh metadata). Ships 12+ atomic transform scripts and three batch presets — `dup-1.sh` for one clean republish copy, `dup-5.sh` for five variations, and `dup-15.sh` for fifteen variations, each pre-tuned so every output stays under the ~80% perceptual-similarity threshold that platforms like TikTok / Instagram use to bury reposts. Use when the user asks to "duplicate a video", "make N versions of this video", "bypass duplicate detection", "make this video unique", "republish without getting flagged", "anti-duplicate", "perceptual hash", or anything similar.
---

# Video Duplicate Transformer

Turn one source video into N copies that look identical to a human but produce different perceptual hashes (pHash, dHash, aHash, video-keyframe hashes). Designed for republishing winning short-form content (TikTok, Reels, Shorts) without it being collapsed as a duplicate.

The core insight from reverse-engineering platform duplicate detection: **single-axis transforms (flip, crop, rotate alone, filter alone) no longer move you under the ~80–85% similarity threshold**. You have to stack 3–5 small per-pixel perturbations so that the combined hash drifts past the cutoff, while each individual change stays imperceptible.

All scripts use `/opt/homebrew/bin/ffmpeg` (override with `FFMPEG_BIN` / `FFPROBE_BIN`). Inputs are absolute paths to MP4. Outputs land beside the input with a suffix.

## When to use

- User has one source MP4 and wants 1, 5, or 15 variants of it ready to upload.
- User says "duplicate this", "make N copies", "anti-duplicate", "make these unique", "rehash this video", "republish without getting flagged", "perceptual hash bypass".
- User is spamming the same creative across multiple accounts or days and needs each upload to register as fresh.

Do NOT use for: image-only slideshow inputs (use an image variant of the same idea), or videos that have a baked-in human voice the user wants pitch-preserved (the audio-pitch transform shifts pitch slightly).

## The three presets

| Preset | Variants | Method |
|---|---|---|
| `scripts/dup-1.sh INPUT.mp4` | 1 | Stream-copy re-mux with fresh metadata + faststart. Pixels bit-identical, container hash different. Use when you just want "a clean copy I can re-upload" without re-encoding artifacts. |
| `scripts/dup-5.sh INPUT.mp4` | 5 | Each variant stacks 3 atomic transforms from the medium pool (zoom + color + noise, etc). Tuned so cross-similarity stays under ~80%. |
| `scripts/dup-15.sh INPUT.mp4` | 15 | Each variant stacks 4–5 transforms drawn deterministically from the full pool, with a per-variant seed so no two are alike. Stays under ~80% pairwise. |

All three default to `<input-dir>/dup-out/<basename>.vNN.mp4`. Pass an explicit output directory as the second positional arg to override.

```bash
bash scripts/dup-1.sh  /abs/path/video.mp4                  # → dup-out/video.v01.mp4
bash scripts/dup-5.sh  /abs/path/video.mp4                  # → dup-out/video.v01..v05.mp4
bash scripts/dup-15.sh /abs/path/video.mp4                  # → dup-out/video.v01..v15.mp4

# Custom output dir — useful when running multiple batches on the same source:
bash scripts/dup-5.sh  /abs/path/video.mp4 /abs/path/dup5/   # → dup5/video.v01..v05.mp4
bash scripts/dup-15.sh /abs/path/video.mp4 /abs/path/dup15/  # → dup15/video.v01..v15.mp4
```

**Parallel-safe**: every batch isolates intermediate stages in its own `.work-$$` directory and passes `--out` to each transform, so you can run `dup-5` and `dup-15` on the same source video at the same time without collisions.

**Verify after every batch — non-optional**: run `phash-check.sh` immediately after every `dup-N` invocation and **always communicate the result percentages back to the user**. The dupes are not "done" until they're verified. See the [verification section below](#verifying-the-dupes-phash-checksh).

```bash
bash scripts/dup-5.sh       /abs/path/video.mp4 /abs/path/dup5/
bash scripts/phash-check.sh /abs/path/video.mp4 /abs/path/dup5/
```

### What to report back to the user after every run

After running any `dup-N` preset, report concisely:

1. **Per-variant pHash vs source** — the worst-frame value for each variant. E.g. `v01: 84% · v02: 75% · v03: 81% ...`
2. **Spread** — min / max / range. Wide range means imbalanced variants.
3. **Worst pairwise similarity** — the most-similar pair across all variants. E.g. `worst pair: v03↔v05 at 94%`.
4. **Verdict line** — pass / marginal / fail, using the same thresholds the script uses (✓ <85% pass, ⚠ 85–94% marginal, ❌ ≥95% collision).

This is what the user actually cares about — knowing whether the dupes will survive the platform's duplicate-detection pass. Don't just say "render done" — always include the % numbers.

## Atomic transforms

Each lives in `scripts/transforms/`. Each takes an MP4 input and writes a sibling with a suffix. They can be chained — feed the output of one into the next.

Every transform accepts a universal `--out /abs/path/out.mp4` flag that overrides the default sibling-suffix path. Use this when chaining or running in parallel, so intermediate files land in a unique work directory and can't collide.

| Script | What it does | Why it shifts the hash |
|---|---|---|
| `transforms/zoom.sh`            | Center-zoom +2–7% (default 3%)              | Every pixel moves; edge pixels disappear |
| `transforms/rotate.sh`          | Rotate ±0.7–3.0° (default 1.3°), aspect-aware inset crop | Sub-degree rotation rewrites every pixel |
| `transforms/border.sh`          | Add 2–6 px solid border of a random color   | Adds new pixels at the frame edge |
| `transforms/color-shift.sh`     | Brightness ±0.05, contrast 0.92–1.07, saturation 0.92–1.08 | Lifts the whole color histogram |
| `transforms/hue-shift.sh`       | Rotate hue by 2–6°                          | All hues drift, but eye doesn't notice <8° |
| `transforms/gamma.sh`           | Gamma shift ±0.05                           | Midtones move without crushing blacks/whites |
| `transforms/noise-overlay.sh`   | Add temporal noise strength 5–14            | Per-frame pixel-level randomness; invisible |
| `transforms/downup-cycle.sh`    | Downscale to 540p then back, lanczos        | Reconstructs detail; destroys high-freq fingerprint |
| `transforms/updown-cycle.sh`    | Upscale to 4K then back, lanczos            | Heavier reconstruction; for the hardest dupe spam |
| `transforms/speed-shift.sh`     | Speed ±1–3% (default 1.02×)                 | Shifts every keyframe in time; audio pitch follows |
| `transforms/trim-edges.sh`      | Drop 1–3 frames from start AND end          | Shifts the entire frame timeline |
| `transforms/audio-pitch.sh`     | Pitch shift audio ±2–4 cents                | Audio fingerprint changes; ear can't tell |
| `transforms/reencode.sh`        | Clean re-encode with fresh metadata         | Strips ID3-like tags; new container hash |

### Notes per transform

- **`zoom`, `rotate`**: these always re-render; you cannot stack them losslessly. Stack them early in a chain so subsequent passes work on the new pixels.
- **`border`**: changes output dimensions slightly. Run AFTER any zoom/rotate so it doesn't get cropped out.
- **`color-shift`, `hue-shift`, `gamma`**: each is one filter pass; they can be inlined into a single filter chain. The provided scripts run them as separate passes for clarity — fine for batches under 30.
- **`noise-overlay`**: always run LAST among visual transforms. Its randomness is per-frame; if you run another transform after it, the noise gets smoothed by the next scale/crop.
- **`downup-cycle` / `updown-cycle`**: do not run both. Pick one. `updown-cycle` is slower (4K intermediate) but obliterates the hash more aggressively.
- **`speed-shift`**: also shifts audio. If audio pitch matters, set `--pitch-preserve 1` (uses `atempo` instead of `asetpts`).
- **`audio-pitch`**: separate from `speed-shift` — use this when you want video timing unchanged but audio fingerprint shifted.
- **`reencode`**: always the final step in a chain. Sets a new `creation_time`, strips any `comment` / `encoder` tags that platforms read.

## Recommended stacks

The presets follow the canonical workflow from reverse-engineering platform duplicate detection: **stack all axes simultaneously, vary parameters per variant**. Picking subsets of the core stack (e.g. "zoom only" or "rotate + filter") is what *doesn't* work — the platform sees through single-axis edits.

**Medium** — the stack used by `dup-5.sh`. Five axes, all applied to every variant:
```
zoom → rotate → border → color-shift → noise-overlay → reencode
```

**Heavy spam** — the stack used by `dup-15.sh`. Adds an upscale-cycle on top, which rebuilds high-frequency detail (the part perceptual hashes lock onto) instead of just shifting it:
```
zoom → rotate → border → color-shift → noise-overlay → updown-cycle → reencode
```

Variation between variants comes from changing **per-axis parameter values**, not from swapping transforms in and out. `dup-5.sh` and `dup-15.sh` are hand-tuned so no two variants share a value on any axis — read the scripts to see the param grid.

### What the presets do NOT use, and why

The skill also ships `hue-shift`, `gamma`, `speed-shift`, `trim-edges`, and `audio-pitch` as atomic scripts. The canonical thread doesn't include them, and they're omitted from the presets to keep every variant on the proven 5-/6-axis stack. Use them by hand when you have a specific reason:

- `hue-shift` — when the source has a strong dominant color (a brand logo, an outfit) you want to drift to avoid logo/color-feature matching.
- `gamma` — alternative to `color-shift` if midtones matter more than overall brightness.
- `speed-shift` — when video duration matters (e.g. you want to dodge timing-based fingerprints).
- `trim-edges` — when keyframe-position hashes are in play (some video pipelines).
- `audio-pitch` — when audio fingerprinting (Shazam-style) is the bigger risk than visual hash.

## Caveats & limits

- **Audio re-encoding**: every script re-encodes audio to AAC unless told otherwise (`-c:a copy` is only safe when the container and codec haven't changed). Platforms also do audio fingerprinting (Shazam / NCS-style) — for music spam you need `audio-pitch.sh` in the stack.
- **Watermarks**: if the source has a TikTok / IG watermark in the corner, none of these techniques remove it. Use `ffmpeg`'s `delogo` filter separately or crop first.
- **CapCut-style trusted metadata**: not handled here. Run the output through a CapCut export if you want the device-trust signal.
- **The 80% similarity claim is approximate**: it varies by platform, content, and detection model. The presets are tuned to give 5+ axes of pixel divergence, which empirically lands well below 80% similarity — but if you have access to a perceptual-hash diff tool (e.g. `imagehash` on extracted keyframes), test before scaling.
- **Don't stack the same transform twice in a row**: e.g. zoom→zoom — the second pass mostly undoes the first's hash shift since the resampling is symmetric.

## Verifying the dupes: `phash-check.sh`

Always run this after `dup-5` or `dup-15` to confirm the outputs actually break perceptual hashing. The script extracts frames from the source and every variant, then computes pHash, dHash, aHash, and wavelet hash. It reports the **worst** (most-similar) result across multiple sampled timestamps — single-frame pHash is unreliable because uniform sections of a video can hash identically across very different variants.

```bash
# Standard run — samples t=1s, 5s, 10s
bash scripts/phash-check.sh /abs/path/source.mp4 /abs/path/dup-out/

# Pass explicit files
bash scripts/phash-check.sh /abs/path/source.mp4 /abs/path/dup-out/*.mp4

# Custom sample timestamps (comma-separated seconds, recommended: ≥3 points)
bash scripts/phash-check.sh --frames 0.5,3,7,12,18 /abs/path/source.mp4 /abs/path/dup-out/
```

**One-time dep install** (Python 3 + imagehash):
```bash
pip3 install --break-system-packages imagehash Pillow
```

### Reading the output

```
─ vs source (worst across sampled frames) ─────────
  variant         pHash   dHash   aHash   wHash  verdict
  source.v01      84.4%   90.6%   98.4%  100.0%  ✓ <85%  ⚠ <80%
  ...

─ pairwise pHash similarity (worst across sampled frames) ─
  worst pair: v01↔v05 at 100.0% (at t=5s)  ❌ collision
```

- **`✓ <85%`** — variant clears the thread's stated TikTok threshold. Safe to upload.
- **`⚠ <80%`** — variant is still above the strict 80% target but under the 85% threshold. Acceptable.
- **`❌ ≥85%`** — variant too similar to source. Re-render with wider parameter envelope.
- **pairwise**: any pair ≥95% (`collision`) means two variants will be grouped together as the same content by the platform — counts as one dupe slot used, not two.

### When `phash-check` flags issues

Each finding suggests a different fix:

| Finding | Likely cause | Fix |
|---|---|---|
| Multiple variants above 85% vs source | Stack too conservative | Widen envelopes; add `updown-cycle` or `gamma` to the stack |
| pHash spread too narrow (range < 5pp) | All variants pushing the same axes | Use a Latin-square parameter assignment (see `dup-5.sh`) |
| Pairwise collision at 100% | pHash blind to your axes (saturation, hue, fine noise on uniform sections) | Add composition-changing transforms (asymmetric border, pan, larger zoom/rotate) |
| wHash always 100% | wavelet is too lenient for short clips — ignore | — |

### Important caveat about pHash on video

pHash works on a 32×32 grayscale DCT of one frame. It is:
- **Blind** to: hue rotation, saturation, fine noise, sub-pixel shifts, audio.
- **Sensitive** to: zoom, rotation, brightness, contrast, gamma, large composition shifts, scale-cycle reconstruction.

If two of your variants both apply mostly pHash-blind perturbations (e.g. both just shift saturation and noise differently), their pHash will collide even though the bytes differ. Platforms use pHash + audio fingerprint + color hash + object detection — busting just pHash is necessary but not sufficient. The `phash-check.sh` output is a **lower bound on uniqueness**, not a guarantee of platform-side undetectability.

## File layout

```
video-duplicate-transformer/
├── SKILL.md
└── scripts/
    ├── dup-1.sh
    ├── dup-5.sh
    ├── dup-15.sh
    ├── phash-check.sh
    └── transforms/
        ├── zoom.sh
        ├── rotate.sh
        ├── border.sh
        ├── color-shift.sh
        ├── hue-shift.sh
        ├── gamma.sh
        ├── noise-overlay.sh
        ├── downup-cycle.sh
        ├── updown-cycle.sh
        ├── speed-shift.sh
        ├── trim-edges.sh
        ├── audio-pitch.sh
        └── reencode.sh
```
