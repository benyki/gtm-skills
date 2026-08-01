---
name: music-downloader
description: Download audio from any source — short video platforms (Instagram, TikTok, YouTube Shorts, X, Pinterest) or full songs from Spotify URLs. Uses yt-dlp for non-Instagram sources; Apify fallback for Instagram reels, then ffmpeg to extract audio. Spotify: resolves title via page metadata, then YouTube search with duration filter (1–9 min).
---

# Music Downloader

Download audio and save as MP3 to `~/videos/music/` (or a user-specified subfolder).

## When to Use This Skill

- User shares a short video URL and wants the audio/music extracted
- User shares an Instagram audio page URL (`instagram.com/reels/audio/...`)
- User shares a Spotify track/album/playlist URL
- User says "download this music", "save this song", "add this to music folder"

## Platform Decision Tree

| Source | Tool |
|--------|------|
| YouTube / YouTube Shorts | `yt-dlp -x --audio-format mp3` directly |
| TikTok | `yt-dlp -x --audio-format mp3` directly |
| X (Twitter) | `yt-dlp -x --audio-format mp3` directly |
| Pinterest | `yt-dlp -x --audio-format mp3` directly |
| Instagram reel URL | Apify `elis/instagram-downloader-api` → ffmpeg |
| Instagram audio page (`/reels/audio/...`) | Find a reel using that audio → Apify → ffmpeg |
| Spotify URL | Extract title from page metadata → YouTube search with duration filter → yt-dlp |

**Never use yt-dlp with `--cookies-from-browser chrome` for Instagram** — it hangs waiting on macOS Keychain and will time out.

## Instructions

### 1. Non-Instagram sources (yt-dlp)

```bash
mkdir -p ~/videos/music
yt-dlp -x --audio-format mp3 --audio-quality 0 --no-warnings \
  -o "~/videos/music/%(title)s.%(ext)s" "URL"
```

### 2. Instagram reel URL

Load env, call Apify, download reel, extract audio:

```bash
set -a; . ~/.agents/.env; set +a
```

```javascript
const APIFY_TOKEN = process.env.APIFY_FALLBACK_API_KEY;  // always use fallback
const body = JSON.stringify({ url: [reelUrl] });
// POST to /v2/acts/elis~instagram-downloader-api/run-sync-get-dataset-items?token=...&timeout=60
// Pick result[result.length - 1].url  ← last item is the actual mp4; first items are thumbnails
// curl -L -s -o /tmp/reel.mp4 <video_url>
```

Then extract audio:
```bash
ffmpeg -y -i /tmp/reel.mp4 -vn -acodec libmp3lame -q:a 2 ~/videos/music/song-name.mp3
rm /tmp/reel.mp4
```

### 3. Instagram audio page (`/reels/audio/<id>`)

Instagram audio pages are JS-only — no direct download possible. Protocol:

1. **Identify the song** via curl og:title:
   ```bash
   curl -s -A "Mozilla/5.0" "https://www.instagram.com/reels/audio/<id>/" | grep -oE 'og:title[^>]{1,200}'
   ```

2. **Find a reel using that audio** via web search:
   ```
   site:instagram.com/reel "<song name>"
   ```

3. **Download the reel and extract audio** using the Instagram reel protocol above (step 2).

### 4. Spotify URL

Spotify blocks yt-dlp and direct audio access. Protocol:

1. **Extract song title + artist** from the Spotify page og:title:
   ```bash
   curl -s -A "Mozilla/5.0" "https://open.spotify.com/track/<id>" \
     | grep -oE 'og:title[^>]{1,200}'
   # Returns e.g. "Thinking of You by Sister Sledge"
   ```

2. **Search YouTube with a duration filter** (1–9 min = full song, not a snippet or DJ set):
   ```bash
   yt-dlp -x --audio-format mp3 --audio-quality 0 --no-warnings \
     --match-filter "duration >= 60 & duration <= 540" \
     -o "~/videos/music/artist-title.%(ext)s" \
     "ytsearch5:Sister Sledge Thinking of You official audio"
   ```
   - `ytsearch5` gives 5 candidates; `--match-filter` picks the first that fits the duration window
   - Append `official audio` to the query to prefer audio-only uploads over live sets or covers
   - If no match in 5 results, widen to `ytsearch10`

3. **Filename**: kebab-case from `"artist - title"` → `artist-title.mp3`

### 5. Filename

Use kebab-case: `artist-title.mp3`. Default destination: `~/videos/music/`. If user specifies a subfolder (e.g. "music/geo/french"), nest under it.

## Scripts

- `scripts/download-instagram-audio.js` — full Node.js script implementing the Apify → ffmpeg pipeline

## Key Notes

- **Always use `APIFY_FALLBACK_API_KEY`**, not `APIFY_API_KEY` — the main account is often low on credits
- The Apify actor returns an array in `result[]`; **last item** is always the video mp4, earlier items are thumbnails
- The downloaded animals/music reel must be validated with `file` command — if it says "HTML document", the wrong URL was used
