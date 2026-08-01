# Platform Specs

Reference for duration, aspect ratio, and CTA constraints per platform.

---

## TikTok

| Property | Value |
|----------|-------|
| `aspectRatio` | `9:16` |
| `targetDuration` recommended | 15–60s |
| `targetDuration` maximum | 180s |
| Hook window | First 3s |
| CTA convention | Follow, Duet, comment "1" |
| Caption burns | Strongly recommended (`autoCaption: true`) |
| Music | Expected — even at low volume. `musicBackground` should rarely be null. |

**Architecture notes:**
- Algorithm heavily rewards watch-through. Keep segments under 7s to maintain cut energy.
- Hook must have a text overlay *and* a voice hook in the first segment.
- Pattern: Hook (3–5s) → Body (10–40s) → CTA (5–8s).

---

## Instagram Reels

| Property | Value |
|----------|-------|
| `aspectRatio` | `9:16` |
| `targetDuration` recommended | 15–90s |
| `targetDuration` maximum | 90s |
| Hook window | First 3s |
| CTA convention | Save, share, comment, DM |
| Caption burns | Recommended |
| Music | Recommended; trending audio preferred |

**Architecture notes:**
- Slightly longer body segments acceptable vs TikTok.
- Image overlays (product, face) more common here — lean into `imageOverlay` for product content.

---

## YouTube Shorts

| Property | Value |
|----------|-------|
| `aspectRatio` | `9:16` |
| `targetDuration` recommended | 30–59s |
| `targetDuration` maximum | 60s (strict — over 60s becomes a regular video) |
| Hook window | First 5s |
| CTA convention | Subscribe, like, comment |
| Caption burns | Optional |
| Music | Optional |

**Architecture notes:**
- Hook can be slower than TikTok. 5s is acceptable.
- Subscription CTA is the dominant call to action.
- Keep `targetDuration` ≤ 59 to stay in Shorts format.

---

## YouTube (long-form)

| Property | Value |
|----------|-------|
| `aspectRatio` | `16:9` |
| `targetDuration` recommended | 180–900s (3–15 min) |
| `targetDuration` minimum | 60s |
| Hook window | First 30s |
| CTA convention | Subscribe, watch next, join channel |
| Caption burns | Optional (YouTube auto-captions exist) |
| Music | Optional; usually lower volume |

**Architecture notes:**
- Segments can be much longer (15–60s).
- Include a `transition` text overlay between major sections.
- Structure: Teaser (0–30s) → Intro (30–90s) → Body sections → Recap → Subscribe CTA.

---

## Universal

| Property | Value |
|----------|-------|
| `aspectRatio` | `9:16` |
| `targetDuration` recommended | 30–60s |
| Hook window | First 3s |

Use when platform is not specified. Apply TikTok constraints as the safe default.

---

## Quick-reference: duration decision table

| Concept type | Recommended duration | Pattern |
|--------------|---------------------|---------|
| Single hook/insight | 15–30s | hook → insight → CTA |
| Tutorial / how-to | 45–60s | hook → steps (3–4) → result → CTA |
| Story / narrative | 30–60s | hook → rising tension → resolution → CTA |
| Product demo | 30–45s | hook → problem → demo → offer → CTA |
| List (3–5 items) | 45–60s | hook → item × N → CTA |
