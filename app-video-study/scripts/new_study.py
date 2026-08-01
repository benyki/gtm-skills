#!/usr/bin/env python3
"""new_study.py --slug <slug> --date <YYYY-MM-DD> [--outdir DIR]

Scaffold a run folder for a science-brand study video and drop in a starter config.

Creates:
  <outdir>/<slug>-<date>/
    video.config.json   <- copied from templates/study.config.template.json (edit this)
    source.md           <- stub for the finding + every number you'll put on screen

Default outdir: ~/code/<project>/world/video-study/runs
Prints the run folder and the config path.
"""
import argparse, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
TEMPLATE = os.path.join(SKILL, "templates", "study.config.template.json")
DEFAULT_OUT = os.path.expanduser("~/code/<project>/world/video-study/runs")

SOURCE_STUB = """# {slug} — source

**Finding (one paragraph):** <what the study found, in plain language>

**Source:** <institution> — <journal>, <year> — <URL>

**Every number that goes on screen (must match the video exactly):**
- sample size: <N>
- headline stat: <e.g. 75%>
- comparison: <e.g. 42% cued vs 17% not-cued>
- the striking human detail: <one concrete moment>

**The 'ask yourself' angle:** <how this finding turns back on the viewer>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="short kebab-case study tag, e.g. dream-incubation")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (use the date from context)")
    ap.add_argument("--outdir", default=DEFAULT_OUT)
    args = ap.parse_args()

    slug = args.slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        sys.exit(f"--slug must be kebab-case (got {slug!r})")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        sys.exit(f"--date must be YYYY-MM-DD (got {args.date!r})")

    run = os.path.join(os.path.expanduser(args.outdir), f"{slug}-{args.date}")
    os.makedirs(run, exist_ok=True)

    cfg = os.path.join(run, "video.config.json")
    if not os.path.exists(cfg):
        shutil.copyfile(TEMPLATE, cfg)
    src = os.path.join(run, "source.md")
    if not os.path.exists(src):
        with open(src, "w") as f:
            f.write(SOURCE_STUB.format(slug=slug))

    print(f"run folder -> {run}")
    print(f"config     -> {cfg}")
    print(f"source     -> {src}")
    print(f"\nnext: fill in source.md, edit {os.path.basename(cfg)} (read references/scene-arc.md), then render:")
    print(f"  bash ~/.agents/skills/app-dream-desk/scripts/video/build_video.sh {cfg} {run}/{slug}.mp4")


if __name__ == "__main__":
    main()
