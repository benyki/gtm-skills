#!/usr/bin/env python3
# Run:
#   python3 download_pod_videos.py "loving face"
#   python3 download_pod_videos.py "loving face" --limit 4 --orientation landscape --quality high
#   python3 download_pod_videos.py "loving face" --output "~/runs/pod-videos"
#
# Flow: Search the Pexels Videos API for a query, pick a best-matching file per result, and download the MP4s into an output folder with the query embedded in filenames.

import os
import sys
import time
import argparse
import requests
from pathlib import Path

# ======================
# Configuration
# ======================
DEFAULT_ORIENTATION = "portrait"  # pexels: portrait|landscape|square
DEFAULT_QUALITY = "medium"        # low|medium|high

# Using home-relative paths as per project preferences
DEFAULT_OUTPUT_DIR = Path("~/runs/pod-videos").expanduser()
API_BASE = "https://api.pexels.com"

def get_api_key():
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        # Look for .env files in common locations if not in env
        possible_env_files = [
            Path("~/.env.local").expanduser(),
            Path("~/.env").expanduser(),
            Path("./.env.local"),
            Path("./.env")
        ]
        for env_file in possible_env_files:
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("PEXELS_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if key:
                break
    if not key:
        print("ERROR: Set PEXELS_API_KEY in environment or .env file")
        sys.exit(1)
    return key

def pick_best_file(files, *, orientation_preference, quality_preference):
    """
    Pick a best-matching `video_files` entry based on:
    - requested orientation (portrait/landscape/square)
    - requested quality target (low/medium/high)
    """
    scored = []
    for f in files:
        w = f.get("width", 0)
        h = f.get("height", 0)
        quality = f.get("quality", "")
        score = 0

        # Orientation preference
        if orientation_preference == "portrait":
            if h > w:
                score += 100
        elif orientation_preference == "landscape":
            if w > h:
                score += 100
        elif orientation_preference == "square":
            # Prefer near-square aspect ratios
            score += max(0, 100 - abs(w - h))

        max_dim = max(w, h)

        # Quality preference. Pexels commonly returns "sd" and "hd".
        # We treat:
        # - low: prefer smaller SD
        # - medium: prefer SD around 640..1280
        # - high: prefer HD and larger dimensions
        if quality_preference == "low":
            if quality == "sd":
                score += 30
            if max_dim and max_dim <= 640:
                score += 20
        elif quality_preference == "medium":
            if quality == "sd":
                score += 35
            if 640 <= max_dim <= 1280:
                score += 25
            elif max_dim > 1280:
                score -= 5
        elif quality_preference == "high":
            if quality == "hd":
                score += 40
            if max_dim >= 1280:
                score += 25
            elif quality == "sd":
                score += 5

        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][1]
    dims = f"{best.get('width')}x{best.get('height')} {best.get('quality', '?')}"
    return best.get("link"), dims

def search_pexels_api(query, api_key, *, limit=5, orientation=DEFAULT_ORIENTATION, quality=DEFAULT_QUALITY, min_dur=None, max_dur=None):
    headers = {"Authorization": api_key}
    results = []
    page = 1
    per_page = min(limit * 3, 80)

    while len(results) < limit and page <= 5:
        params = {"query": query, "orientation": orientation, "per_page": per_page, "page": page}
        resp = requests.get(f"{API_BASE}/videos/search", headers=headers, params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(60)
            resp = requests.get(f"{API_BASE}/videos/search", headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            break

        videos = resp.json().get("videos", [])
        if not videos:
            break

        for v in videos:
            if len(results) >= limit:
                break
            dur = v.get("duration", 0)
            if min_dur and dur < min_dur: continue
            if max_dur and dur > max_dur: continue
            files = v.get("video_files", [])
            if not files: continue
            url, dims = pick_best_file(files, orientation_preference=orientation, quality_preference=quality)
            if url:
                results.append({
                    "video_id": v.get("id"),
                    "url": url,
                    "dims": dims,
                    "duration": dur,
                    "title": v.get("url", "").split("/")[-2].replace("-", " ") if v.get("url") else str(v.get("id")),
                })
        page += 1
        time.sleep(0.3)
    return results

def download_video(video_id, url, output_dir, query):
    # Append query to the filename as requested
    safe_query = "".join([c if c.isalnum() else "_" for c in query])
    out_path = output_dir / f"pexels-{video_id}_{safe_query}.mp4"
    
    if out_path.exists():
        return out_path, True

    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return out_path, True
    except Exception as e:
        if out_path.exists():
            out_path.unlink()
        return out_path, False

def main():
    parser = argparse.ArgumentParser(description="Download Pexels B-roll for Pod Videos")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", type=int, default=2, help="Max videos to download")
    parser.add_argument("--output", type=str, default=None, help="Override output directory")
    parser.add_argument(
        "--orientation",
        type=str,
        choices=["portrait", "landscape", "square"],
        default=DEFAULT_ORIENTATION,
        help=f"Pexels search orientation (default: {DEFAULT_ORIENTATION})",
    )
    parser.add_argument(
        "--quality",
        type=str,
        choices=["low", "medium", "high"],
        default=DEFAULT_QUALITY,
        help=f"Preferred download quality bucket (default: {DEFAULT_QUALITY})",
    )
    args = parser.parse_args()

    api_key = get_api_key()
    output_dir = Path(args.output).expanduser() if args.output else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Searching Pexels API for: \"{args.query}\" "
        f"({args.orientation}, quality={args.quality}, limit {args.limit})..."
    )
    results = search_pexels_api(
        args.query,
        api_key,
        limit=args.limit,
        orientation=args.orientation,
        quality=args.quality,
    )

    if not results:
        print("No videos found.")
        return

    print(f"Downloading {len(results)} videos to {output_dir}...")
    success = 0
    for i, r in enumerate(results):
        path, ok = download_video(r["video_id"], r["url"], output_dir, args.query)
        if ok:
            success += 1
            print(
                f"  [{i+1}/{len(results)}] OK {r['video_id']} "
                f"({r['duration']}s) {r['dims']} {r['title'][:40]}"
            )
        else:
            print(f"  [{i+1}/{len(results)}] FAIL {r['video_id']}")
    
    print(f"\nDone: {success} downloaded")

if __name__ == "__main__":
    main()
