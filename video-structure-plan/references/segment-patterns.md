# Segment Patterns

Pre-defined segment sequences. Pick the pattern that best matches the concept's tone and intent, then adapt segment durations to hit `targetDuration`.

Each pattern lists **segment roles** with a duration range. Scale proportionally when the total doesn't match `targetDuration`.

---

## Pattern 1 — Hook-Insight-CTA (HIC)
**Best for:** quick educational take, single insight, opinion drop  
**Duration:** 15–30s  
**Platforms:** TikTok, Reels, Shorts

| Position | Role | Duration | textOverlay role | Notes |
|----------|------|----------|-----------------|-------|
| 0 | `hook` | 3–5s | `hook` | Bold claim or question. Visual must be immediately arresting. |
| 1 | `insight` | 10–18s | `emphasis` (optional) | Deliver the core value. Keep voice tight. |
| 2 | `cta` | 4–7s | `cta` | Follow / save / comment. Upbeat energy. |

---

## Pattern 2 — Problem-Agitate-Solve-CTA (PASC)
**Best for:** product demos, productivity, self-improvement  
**Duration:** 30–60s  
**Platforms:** TikTok, Reels, Shorts, YouTube Shorts

| Position | Role | Duration | textOverlay role | Notes |
|----------|------|----------|-----------------|-------|
| 0 | `hook` | 3–5s | `hook` | Show the pain. Visual: tired person, messy desk, failing metric. |
| 1 | `problem` | 5–10s | `stat` (optional) | Name the problem explicitly. Can include a relatable stat. |
| 2 | `agitate` | 5–10s | `emphasis` | Twist the knife — why existing solutions fail. |
| 3 | `solve` | 10–20s | `emphasis` | Introduce the solution. Show, don't just tell. |
| 4 | `cta` | 5–8s | `cta` | Direct offer or follow prompt. |

---

## Pattern 3 — Reveal / Story Arc
**Best for:** transformation, before/after, personal story  
**Duration:** 30–60s  
**Platforms:** TikTok, Reels

| Position | Role | Duration | textOverlay role | Notes |
|----------|------|----------|-----------------|-------|
| 0 | `tease` | 3–5s | `hook` | Tease the payoff first ("I did X for 30 days..."). Curiosity gap. |
| 1 | `setup` | 5–10s | `caption` (optional) | Set the scene — the "before" state. |
| 2 | `journey` | 10–25s | `transition` (optional) | Compressed montage or explanation of the process. |
| 3 | `reveal` | 5–10s | `emphasis` | The "after" — the result or punchline. High-energy. |
| 4 | `cta` | 5–8s | `cta` | Follow for more / comment reaction. |

---

## Pattern 4 — List (N Tips / Facts)
**Best for:** educational content, listicles, "things you didn't know"  
**Duration:** 30–60s  
**Platforms:** TikTok, Reels, YouTube Shorts

| Position | Role | Duration | textOverlay role | Notes |
|----------|------|----------|-----------------|-------|
| 0 | `hook` | 3–5s | `hook` | Promise: "3 things that will X". Specific number creates commitment. |
| 1–N | `item` | 5–10s each | `stat` or `emphasis` | One item per segment. Text overlay = item title. Voice = explanation. |
| N+1 | `cta` | 4–6s | `cta` | Follow / save the list. |

**Note:** For 3-item list at 30s: hook 5s + 3 × 7s + CTA 4s = 30s.  
For 5-item list at 60s: hook 5s + 5 × 9s + CTA 5s = 55s (±5s).

---

## Pattern 5 — Commentary / Reaction
**Best for:** trending topics, duet-style commentary, "let me explain"  
**Duration:** 30–60s  
**Platforms:** TikTok, Reels

| Position | Role | Duration | textOverlay role | Notes |
|----------|------|----------|-----------------|-------|
| 0 | `hook` | 3–5s | `hook` | Present the thing being reacted to. Bold text. |
| 1 | `context` | 5–10s | `caption` | Brief context for viewers who missed the original. |
| 2 | `reaction` | 15–30s | `emphasis` | The main commentary. Multiple sub-clips possible. |
| 3 | `verdict` | 4–8s | `emphasis` | Hot take / conclusion. |
| 4 | `cta` | 4–6s | `cta` | "What do you think?" drives comments. |

---

## Pattern 6 — Product / Feature Demo
**Best for:** SaaS, apps, physical products  
**Duration:** 30–60s  
**Platforms:** TikTok, Reels, YouTube Shorts

| Position | Role | Duration | textOverlay role | Notes |
|----------|------|----------|-----------------|-------|
| 0 | `hook` | 3–5s | `hook` | Lead with the outcome, not the product. |
| 1 | `problem` | 4–8s | `stat` (optional) | Who this is for and what pain it solves. |
| 2 | `demo` | 10–25s | `caption` | Show the product in use. `type: "screen-recording"` for apps. |
| 3 | `social-proof` | 4–8s | `stat` | Numbers, reviews, results. `imageOverlay` for screenshot. |
| 4 | `offer` | 3–6s | `cta` | Link in bio / DM / promo code. |

---

## Choosing a pattern

| Tone / intent | Best pattern |
|---------------|-------------|
| Educational, quick insight | HIC |
| Selling a solution | PASC |
| Transformation story | Reveal |
| Tips / facts listicle | List |
| Commentary on a trend | Commentary |
| App or product showcase | Product Demo |

When the concept has mixed signals, default to **PASC** — it performs well across most content types.

---

## Segment duration fine-tuning

After picking a pattern, adjust durations so segments sum to `targetDuration`:

1. Fix the CTA at its minimum (4–6s) — this is non-negotiable.
2. Fix the hook at 3–5s — first impression must be tight.
3. Distribute remaining seconds across body segments proportionally.
4. No segment shorter than 2s. If a segment can't hit 2s, merge it with an adjacent one.
