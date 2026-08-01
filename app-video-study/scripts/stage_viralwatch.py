#!/usr/bin/env python3
"""stage_viralwatch.py CONFIG.json MP4 --slug <slug> [--date YYYY-MM-DD] [--stem STEM]

Stage a rendered science-brand study video so the `viralwatch` desktop app can see it, in the
study's OWN lane so it never collides with the weekly dream-desk stems.

viralwatch scans ~/code/<project>/world/videos/**/published/*.mp4 and reads a stem-keyed
sidecar next to the mp4 (`published/<stem>.json`). This stages the mp4 and writes that
sidecar RIGHT NEXT TO IT (same stem), in viralwatch's shape (hook / outro / bg_query /
duration / items / config) — the canonical one-lookup-rule convention.

Lane: ~/code/<project>/world/videos/video-study/final/  (stem: video-study-<slug>-<date>)

After this, POST the STAGED mp4 with upload-post (`--file <staged>`), whose archiver
moves the mp4 AND its sibling <stem>.json into .../published/ and appends the ledger.

Prints the staged mp4 path on the last line (feed it to upload-post --file).

Adapted from ~/.agents/skills/app-dream-desk/scripts/video/publish_viralwatch.py.
"""
import argparse, json, os, shutil, subprocess, sys

VIDEOS_ROOT = os.path.expanduser("~/code/<project>/world/videos")
FORMAT_DIR = "video-study/final"  # study lane; posting moves both files into .../final/published/


def probe_dur(mp4):
    try:
        return round(float(subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", mp4]).decode().strip()), 2)
    except Exception:
        return None


def oneline(s):
    return " ".join((s or "").replace("\n", " ").split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("mp4")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--date", default=None)
    ap.add_argument("--stem", default=None)
    ap.add_argument("--videos-root", default=VIDEOS_ROOT)
    args = ap.parse_args()

    cfg = json.load(open(args.config))
    stem = args.stem or (f"video-study-{args.slug}-{args.date}" if args.date
                         else f"video-study-{args.slug}")
    dur = probe_dur(args.mp4)

    scenes = cfg.get("scenes", [])
    hook_scene = next((s for s in scenes if s.get("kind") == "hook"), scenes[0] if scenes else {})
    outro_scene = next((s for s in scenes if s.get("kind") == "outro"), {})
    queries = [s["query"] for s in scenes if s.get("query")]

    sidecar = {
        "language": "English",
        "hook": [oneline(hook_scene.get("title") or hook_scene.get("vo") or "")],
        "outro": oneline(outro_scene.get("sub") or outro_scene.get("vo") or ""),
        "bg_query": "; ".join(queries),
        "duration": dur,
        "brand": cfg.get("brand", "YOUR BRAND"),
        "items": [
            {"prompt": oneline(s.get("title", s.get("id", ""))), "answer": oneline(s.get("vo", ""))}
            for s in scenes if s.get("vo")
        ],
        "config": cfg,
    }

    base = os.path.join(args.videos_root, FORMAT_DIR)
    os.makedirs(base, exist_ok=True)
    staged_mp4 = os.path.join(base, f"{stem}.mp4")
    sidecar_path = os.path.join(base, f"{stem}.json")
    shutil.copyfile(args.mp4, staged_mp4)
    json.dump(sidecar, open(sidecar_path, "w"), ensure_ascii=False, indent=1)

    print(f"staged sidecar -> {sidecar_path}", file=sys.stderr)
    print(f"viralwatch will scan -> {base}/published/{stem}.mp4 (+ {stem}.json)  (after upload-post archives it)", file=sys.stderr)
    print(staged_mp4)  # stdout: the file to pass to upload-post --file


if __name__ == "__main__":
    main()
