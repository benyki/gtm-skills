---
description: Turn a concept or social media URL into an execution-ready VideoArchitecture JSON — segments with background footage, duration, text/image overlays, voice script, and music spec. Trigger phrases: "architect a video", "plan this video", "turn this link into a video structure", "video plan from concept", "design a video script".
allowed-tools: Bash Read WebFetch
---

# video-structure-plan

Produce a `VideoArchitecture` JSON from a concept description **or** a social media URL. This skill outputs **only the JSON spec** — it does not render, upload, or POST anything. Downstream skills (e.g. `local-video-app-voice-template`) consume this output.

---

## Inputs

| Form | Example |
|------|---------|
| Social media URL | `https://www.tiktok.com/@user/video/123` |
| Concept sentence | `"A 30-second ad for a productivity app targeting burned-out founders"` |
| Both | URL for reference tone/angle + explicit concept override |

---

## Step 1 — Infer the concept

### If a social media URL is provided

Run `./scripts/fetch-social-meta.sh <url>` to extract title, description, and caption.  
If the script returns nothing useful, use the `agent-browser` skill to navigate to the URL and read the page text / caption.

Extract from that metadata:
- **Topic** — what is the video about?
- **Tone** — educational, entertaining, emotional, sales, shock, comedy?
- **Hook style** — question, bold claim, visual reveal, stat drop?
- **Target audience** — who is this for?
- **CTA intent** — follow, buy, click, save, share?

### If only a concept description is provided

Parse it directly. Infer platform from context clues (e.g. "TikTok", "Reels", "YouTube"). Default to `tiktok` if unspecified.

---

## Step 2 — Choose platform + duration

Consult `./references/platform-specs.md` for duration windows and constraints per platform.

**Defaults when not specified:**
- Platform: `tiktok`
- Aspect ratio: `9:16`
- Duration: `30` seconds

---

## Step 3 — Choose a segment pattern

Consult `./references/segment-patterns.md` and pick the pattern that best fits the concept's tone and intent.  
Each pattern defines a segment sequence with roles (hook, problem, proof, cta…).

---

## Step 4 — Build the VideoArchitecture JSON

Output a single JSON object matching the schema in `./references/output-schema.json`.

### Top-level structure

```json
{
  "meta": { ... },
  "voiceOverlay": { ... } | null,
  "musicBackground": { ... } | null,
  "segments": [ ... ]
}
```

### `meta`

| Field | Type | Notes |
|-------|------|-------|
| `title` | string | Short slug for the video (e.g. `"founder-burnout-30s"`) |
| `concept` | string | 1–2 sentence summary of inferred concept |
| `sourceUrl` | string? | Original URL if provided |
| `targetDuration` | number | Total seconds (sum of all segment durations) |
| `aspectRatio` | `"9:16"` \| `"16:9"` \| `"1:1"` | |
| `platform` | `"tiktok"` \| `"instagram-reels"` \| `"youtube-shorts"` \| `"youtube"` \| `"universal"` | |

### `voiceOverlay` (optional — omit if concept is purely visual)

| Field | Type | Notes |
|-------|------|-------|
| `fullScript` | string | Complete voice script for the whole video |
| `suggestedActor` | `"Adam"` \| `"Sara"` | Adam = default; Sara if first clip is clearly feminine |
| `autoCaption` | boolean | `true` for speech-heavy videos |

**Voice script rules:**
- Estimate speaking rate: ~14 characters/second
- Ensure `len(fullScript) / 14 ≤ targetDuration`
- Hook must land in the first segment
- Do **not** write a script if the concept is silent/music-only

### `musicBackground` (optional — omit or `null` for voice-only)

| Field | Type | Notes |
|-------|------|-------|
| `mood` | string | e.g. `"upbeat"`, `"emotional"`, `"tense"`, `"chill"` |
| `genre` | string | e.g. `"hip-hop"`, `"cinematic"`, `"lofi"`, `"pop"` |
| `volume` | number | 0.0–1.0; use `0.15` when voice is present, `0.6` for music-only |
| `suggestedTrack` | string? | Optional search query or known track name |

### `segments[]`

Each segment maps to one video block. Fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `position` | integer | yes | 0-indexed order |
| `duration` | number | yes | Seconds; min 2s, typical 3–8s |
| `backgroundFootage` | object | yes | See below |
| `textOverlay` | object \| null | no | Omit entirely if not needed |
| `imageOverlay` | object \| null | no | Omit entirely if not needed |
| `voiceScript` | string | no | Segment-level voice line (optional; `fullScript` takes precedence) |

**`backgroundFootage`:**
```json
{
  "type": "stock" | "ai-generated" | "social-clip" | "screen-recording",
  "query": "person typing laptop coffee shop morning",
  "description": "Close-up of hands on keyboard in warm café lighting",
  "preferredSource": "pexels" | "gcs" | "ai" | "social"
}
```
- `query` must be specific enough for a stock search agent to retrieve the right clip
- `description` is the human-readable intent
- Default `preferredSource` is `"pexels"` for stock footage

**`textOverlay`:**
```json
{
  "text": "You're not lazy.",
  "role": "hook" | "emphasis" | "caption" | "cta" | "stat" | "transition",
  "timing": "start" | "middle" | "end"
}
```
- Keep text short: hooks ≤ 6 words, CTAs ≤ 8 words, stats ≤ 12 words
- `timing` controls when in the segment the text appears

**`imageOverlay`:**
```json
{
  "description": "App screenshot showing the dashboard feature",
  "placement": "center" | "top" | "bottom" | "corner-br" | "corner-tl",
  "opacity": 0.9
}
```

---

## Step 5 — Validate before returning

Check all of these before outputting:

- [ ] `sum(segments[].duration) == meta.targetDuration` (±1s tolerance)
- [ ] `len(voiceOverlay.fullScript) / 14 ≤ meta.targetDuration` if voice is present
- [ ] First segment has a hook (textOverlay with `role: "hook"` or `voiceScript` that opens with a strong statement)
- [ ] Last segment has a CTA if platform is `tiktok`, `instagram-reels`, or `youtube-shorts`
- [ ] No segment shorter than 2 seconds
- [ ] `musicBackground.volume ≤ 0.2` when `voiceOverlay` is present

---

## Output format

Return **only** the JSON — no prose wrapper, no markdown fences unless the user explicitly asks for a formatted response.

Example minimum output:

```json
{
  "meta": {
    "title": "founder-burnout-hook",
    "concept": "A 30-second TikTok targeting burned-out founders — visual hook on exhaustion, then a productivity insight, ending with a follow CTA.",
    "targetDuration": 30,
    "aspectRatio": "9:16",
    "platform": "tiktok"
  },
  "voiceOverlay": {
    "fullScript": "You're not lazy. You're just running on empty. Here's what actually works when your brain is fried...",
    "suggestedActor": "Adam",
    "autoCaption": true
  },
  "musicBackground": {
    "mood": "tense-then-hopeful",
    "genre": "cinematic",
    "volume": 0.15
  },
  "segments": [
    {
      "position": 0,
      "duration": 4,
      "backgroundFootage": {
        "type": "stock",
        "query": "exhausted person slumped over desk late night office",
        "description": "Person face-down on desk, dim overhead light, messy papers",
        "preferredSource": "pexels"
      },
      "textOverlay": {
        "text": "You're not lazy.",
        "role": "hook",
        "timing": "start"
      },
      "voiceScript": "You're not lazy. You're just running on empty."
    },
    {
      "position": 1,
      "duration": 18,
      "backgroundFootage": {
        "type": "stock",
        "query": "person writing in notebook calm morning sunlight",
        "description": "Close-up journaling in natural light — calm and focused energy",
        "preferredSource": "pexels"
      },
      "textOverlay": null,
      "voiceScript": "Here's what actually works when your brain is fried: stop optimizing your schedule and start protecting your recovery time."
    },
    {
      "position": 2,
      "duration": 8,
      "backgroundFootage": {
        "type": "stock",
        "query": "person smiling looking at phone notification",
        "description": "Upbeat close-up reaction — positive outcome energy",
        "preferredSource": "pexels"
      },
      "textOverlay": {
        "text": "Follow for more founder sanity checks.",
        "role": "cta",
        "timing": "middle"
      },
      "voiceScript": "Follow if this hit different. More founder sanity checks every week."
    }
  ]
}
```

---

## Downstream compatibility

This JSON is designed to feed directly into:
- `local-video-app-voice-template` — maps `segments` → `blocks`, `voiceOverlay` → `actor` + `scriptText`, `musicBackground` → `music`
- Any video-maker skill that accepts a `VideoArchitecture` input
