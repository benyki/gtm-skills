# Text Overlay Logic

## Font Selection

**Font Map (`SCRIPT_FONT_MAP`):**

| Language | Font File |
|----------|-----------|
| Hebrew | `NotoSansHebrew-Bold.ttf` |
| Arabic | `NotoSansArabic-Bold.ttf` |
| Urdu | `NotoSansArabic-Bold.ttf` |
| Hindi | `NotoSansDevanagari-Bold.ttf` |
| Bengali | `NotoSansDevanagari-Bold.ttf` |
| Japanese | `NotoSansJP-Bold.ttf` |
| Korean | `NotoSansKR-Bold.ttf` |
| Chinese | `NotoSansJP-Bold.ttf` |
| Thai | `NotoSansThai-Bold.ttf` |
| Latin/Default | `TikTok Sans 12pt Regular` |

**Selection logic:** Auto-detects script from the text itself (Unicode ranges), overrides the `language` parameter. Non-Latin scripts use Noto Sans Bold (700) as primary with TikTok Sans 12pt as the default Latin fallback for mixed-script text.

---

## Font Size & Stroke

```
BASE_FONT_SIZE = hasScriptFont ? 78 : 76
scaleFactor    = videoWidth / 1080
fontSize       = round(BASE_FONT_SIZE * scaleFactor)
strokeWidth    = max(5, round(fontSize * 0.132))
```

At 1080p: Latin = 76px, Script = 78px, stroke ~10px.

Two-layer SVG render: black stroke underneath, white fill on top. Stroke uses `stroke-linejoin: round`, `stroke-linecap: round`.

---

## Line Height & Spacing

```
lineHeight    = fontSize * 1.27
paragraphGap  = fontSize * 0.5      (extra gap for explicit blank-line paragraph breaks)
letterSpacing = -2.2 * scaleFactor   (negative = tighter)
baseline      = lineHeight * 0.7     (text baseline offset within line)
```

---

## Characters Per Line

| Language Group | Chars/Line | Languages |
|---------------|-----------|-----------|
| CJK | 12 | Japanese, Chinese, Korean |
| RTL | 18 | Hebrew, Arabic, Urdu |
| Abugida | 20 | Hindi, Bengali, Thai |
| Latin (default) | 26 | English, Indonesian, Vietnamese, etc. |

---

## Line Breaking Logic

**CJK (Japanese, Chinese, Korean):**
- Break by character count (no word boundaries)
- Tries to break at punctuation first: `[\s,，。、！？：；]`
- Fallback: hard break at char limit

**Latin / spaced scripts:**
- Break on word boundaries (split by `/\s+/`)
- Respects explicit `\n` line breaks inside the same paragraph
- Uses blank lines (`\n\n`) for paragraph breaks with extra gap
- Words exceeding max chars go on their own line

---

## Text Positioning

```
overlayPosition = 33  (default, percentage from top)
anchorY = round(videoHeight * (overlayPosition / 100))
startY  = anchorY - totalTextHeight / 2   (centered around anchor)
x       = videoWidth / 2                   (always horizontally centered)
textAnchor = "middle"
```

---

## Script Auto-Detection (Unicode Ranges)

| Language | Unicode Range |
|----------|---------------|
| Hebrew | `U+0590-U+05FF`, `U+FB1D-U+FB4F` |
| Arabic | `U+0600-U+06FF`, `U+0750-U+077F` |
| Hindi | `U+0900-U+097F` |
| Bengali | `U+0980-U+09FF` |
| Thai | `U+0E00-U+0E7F` |
| Japanese | `U+3040-U+30FF`, `U+4E00-U+9FFF` |
| Korean | `U+AC00-U+D7AF` |

Detection runs on the actual text content and overrides the `language` parameter.

---

## RTL Handling

For Hebrew, Arabic, Urdu:
- SVG: `direction="rtl" unicode-bidi="embed"`
- Emojis placed LEFT of text (reversed from LTR)
- Emoji X increment direction reversed

---

## Emoji Handling

**Sizing & positioning:**
```
emojiSize    = round(fontSize * 1.0)     (1:1 with text)
emojiY       = baselineY - emojiSize * 0.85
charBudget   = emojiCount * 3            (each emoji ~ 3 char widths)
emojiSpacing = 4px                        (between consecutive emojis)
emojiGap     = fontSize * 0.2            (gap between text and first emoji)
```

**Sources (fallback order):**
1. Apple emoji PNG: `cdn.jsdelivr.net/npm/emoji-datasource-apple@16.0.0/img/apple/64/{codepoint}.png`
2. Twemoji SVG: `cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/svg/{codepoint}.svg`

**Wrapping:** If last line + emojis exceed `maxCharsPerLine`, re-wraps last line with tighter budget.

**Broken emojis removed:** `⏳⌛⏰⏱️⏲️⌚`

---

## FFmpeg Drawtext Fallback

When SVG rendering fails, falls back to FFmpeg drawtext:
```
maxCPL    = hasScriptFont ? 18 : 22     (different from SVG limits)
fontSize  = round(54 * (videoWidth / 1080))
borderW   = max(3, round(fontSize * 0.10))
```

---

## Function Signatures

```javascript
// Core renderer
renderTextToPng({ text, language = 'english', videoWidth = 1080, videoHeight = 1920, overlayPosition = 33 })

// Overlay onto video
overlayTextCore({ video_url, text, language = 'english', check_for_existing_text = false, overlay_duration = 0, overlay_position = 33, skip_ugc_degradation = false })
```

---

## Key Files

| File | What |
|------|------|
| `server.js` (~lines 72-370) | SVG rendering, font selection, wrapping, emoji compositing |
| `server.js` (~lines 3034-3112) | FFmpeg drawtext fallback |
| `fonts/` | All Noto Sans + any legacy custom Latin font files |
