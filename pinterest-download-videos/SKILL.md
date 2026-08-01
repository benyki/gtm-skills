---
name: pinterest-download-videos
description: From a keyword, find and download the first N video pins on Pinterest (videos only, not images). Trigger when the user asks to search Pinterest for videos by keyword, scrape Pinterest video search results, grab b-roll from Pinterest, or download top-N Pinterest videos for a given query. Uses Pinterest's public BaseSearchResource JSON endpoint to enumerate video pin IDs, then yt-dlp to fetch each video as an MP4.
---

# pinterest-download-videos

Execution-ready flow for grabbing the first N video pins on Pinterest for a keyword.

## When to use

- User says "download 5 videos from Pinterest about X"
- User wants b-roll, UGC-style clips, or reference footage by keyword
- User explicitly asks for videos only (no image pins)

## Prerequisites

Both must be on PATH. They are pre-installed on this machine:

- `yt-dlp` → resolves to `/opt/homebrew/bin/yt-dlp`
- `python3` → resolves to `/opt/homebrew/bin/python3`
- `curl` → system

No API key required. Pinterest's search endpoint is public.

## Primary entrypoint

Always prefer the one-shot script:

```bash
bash ~/.agents/skills/pinterest-download-videos/scripts/search_and_download.sh \
  "<keyword>" <count> <out_dir>
```

| Arg | Required | Example | Notes |
|-----|----------|---------|-------|
| `keyword` | yes | `"running in the nature"` | Free-text, quote if multi-word |
| `count` | yes | `5` | Number of videos to download |
| `out_dir` | yes | `~/videos/ugc` | Created if missing |

Output: `<out_dir>/pinterest-<pin_id>.mp4` per video. Exit non-zero on fatal error.

## Scripts reference

All paths relative to this skill's root (`~/.agents/skills/pinterest-download-videos/`).

| Script | Purpose | Invocation |
|--------|---------|------------|
| `scripts/search_pins.sh` | Print first N video pin IDs for a keyword to stdout (one per line). | `bash scripts/search_pins.sh "<keyword>" <count>` |
| `scripts/download_pin.sh` | Download a single pin by ID into `<out_dir>`. | `bash scripts/download_pin.sh <pin_id> <out_dir>` |
| `scripts/search_and_download.sh` | End-to-end: search → download N videos. | `bash scripts/search_and_download.sh "<keyword>" <count> <out_dir>` |

## How it works (for debugging)

1. **Search.** GET `https://www.pinterest.com/resource/BaseSearchResource/get/` with query params:
   - `source_url=/search/videos/?q=<url-encoded-keyword>`
   - `data={"options":{"query":"<keyword>","scope":"videos","page_size":<count*2>},"context":{}}`

   Headers:
   - `user-agent: Mozilla/5.0`
   - `x-pinterest-pws-handler: www/search/[scope].js`
   - `accept: application/json`

   Response JSON path: `resource_response.data.results[].id` — each entry where `videos` field is present is a video pin. The search script filters out non-videos defensively.

2. **Download.** `yt-dlp -o "pinterest-%(id)s.%(ext)s" "https://www.pinterest.com/pin/<pin_id>/"` from inside `out_dir`. yt-dlp's Pinterest extractor handles both direct-MP4 (`V_720P`, `V_EXP7`) and HLS (`V_HLSV4-*`) formats and merges video+audio automatically.

## Expected outputs

For `search_and_download.sh "running in the nature" 5 ~/videos/ugc`:

```
~/videos/ugc/pinterest-1059894093738160705.mp4
~/videos/ugc/pinterest-1117455726272303644.mp4
~/videos/ugc/pinterest-832954893603518422.mp4
~/videos/ugc/pinterest-1065593961813621064.mp4
~/videos/ugc/pinterest-576883033529047994.mp4
```

Sizes typically 0.5–8 MB per clip. Aspect ratios vary (9:16, 1:1, 16:9) — post-process with the `ffmpeg` skill if a specific canvas is required.

## Known failure modes

- **404 from BaseSearchResource**: Pinterest occasionally changes handler names. Re-verify by loading `https://www.pinterest.com/search/videos/?q=<keyword>` in a browser and inspecting network calls.
- **yt-dlp "Unsupported URL"**: `yt-dlp -U` to update; Pinterest extractor changes.
- **Empty result set**: the keyword may return only image pins. Broaden the query.
- **Rate limit / CAPTCHA**: space requests or reduce `page_size`.

## References

- `~/.agents/skills/pinterest-download-videos/references/api-notes.md` — raw examples of the search response shape.
