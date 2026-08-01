---
name: pexel-video-downloader
description: Download portrait-orientation B-roll videos from Pexels for podcast-style short-form video production, saving them to ~/runs/pod-videos.
---

# Pod Video Downloader

Skill to download B-roll videos from Pexels for podcast-style short-form videos.

## Description
Automates the retrieval of portrait-orientation, medium-quality videos from Pexels based on a query. It ensures the query is appended to the filename for easier organization and saves them to a canonical location.

## Tooling
- **Script**: `scripts/download_pod_videos.py`
- **Default Output**: `~/runs/pod-videos`

## Usage
Run the script via `exec` to fetch videos for specific story titles.

```bash
python3 ~/.agents/skills/pod-video-downloader/scripts/download_pod_videos.py "Your Search Query" --limit 2
```

## Constraints
- Requires `PEXELS_API_KEY` in environment or a `.env` file (in usual .env file)
- downloads portrait videos and Medium quality (SD) by default
