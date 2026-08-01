---
name: yt-dlp
description: Download videos and audio from YouTube and other platforms using yt-dlp; supports URL downloads, keyword search, audio extraction, and format selection.
---

# yt-dlp

Skill for downloading videos and audio from YouTube and other platforms using the `yt-dlp` command-line tool.

## Description
`yt-dlp` is a powerful command-line downloader. This skill provides the essential patterns for downloading specific videos, navigating search results without needing a URL, and extracting high-quality audio.

## Basic Usage

### 1. Download a Specific Video
To download a video in the best available quality:
```bash
yt-dlp "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 2. Navigating Search (Download without URL)
If you don't have a URL, you can search directly from the CLI. Use `ytsearchN:` where `N` is the number of results to consider.

**Download the first result for a query:**
```bash
yt-dlp "ytsearch1:Sibelius Finlandia instrumental"
```

**Download the top 5 results for a query:**
```bash
yt-dlp "ytsearch5:traditional Finnish kantele music"
```

### 3. Customizing Output Filenames
Use the `-o` flag to specify the output path and filename template.
```bash
yt-dlp -o "~/Downloads/%(title)s.%(ext)s" "URL"
```

## Optional: Extracting Audio
To download a video and convert it into a standalone audio file (e.g., MP3):

**The "Audio-Only" Pattern:**
- `-x`: Extract audio.
- `--audio-format mp3`: Convert the extracted audio to MP3.
- `--audio-quality 0`: Best quality (0 is best, 9 is worst).

**Default destination for music:** `~/videos/music/`. Unless the user specifies another folder, download audio there (create it with `mkdir -p ~/videos/music` first). If the user names a sub-grouping (e.g. "geo/french"), nest it under the default: `~/videos/music/geo/french/`.

**Full Command Example:**
```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 -o "~/videos/music/%(title)s.%(ext)s" "URL"
```

**Combined with Search:**
```bash
yt-dlp -x --audio-format mp3 -o "~/videos/music/Song_Name.%(ext)s" "ytsearch1:Song Name instrumental"
```

## Kebab-case Filenames
`yt-dlp` has no built-in slugify, and `%(title)s` keeps spaces, capitals, and punctuation (`Love Story - Indila.mp3`). When a kebab-case name is wanted, fetch the title first, normalize it, then pass it to `-o`.

**Slugify helper** (lowercase, strip punctuation, spaces/underscores → single hyphen, trim):
```bash
kebab() { echo "$1" | iconv -t ascii//TRANSLIT 2>/dev/null \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'; }
```

**Download a single track with a kebab-case name:**
```bash
mkdir -p ~/videos/music
url="https://www.youtube.com/watch?v=VIDEO_ID"
slug=$(kebab "$(yt-dlp --no-warnings --get-title "$url")")
yt-dlp -x --audio-format mp3 --audio-quality 0 --no-warnings \
  -o "$HOME/clips/music/$slug.%(ext)s" "$url"
```

Note: add `--no-warnings` to keep output clean (YouTube JS-challenge warnings are noisy but usually harmless).

## Common Troubleshooting
- **Update yt-dlp**: YouTube frequently updates its site, which can break the tool. Keep it updated:
  `brew upgrade yt-dlp`
- **Cookies**: For age-restricted or private videos, you may need to pass cookies from your browser:
  `yt-dlp --cookies-from-browser chrome "URL"`
