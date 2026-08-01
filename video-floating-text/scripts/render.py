#!/usr/bin/env python3
"""video-floating-text — generic 9:16 floating-text video renderer.

Reads a template JSON that describes:
  - 1–4 text elements (each with its own font/size/style + literal or data-pull value)
  - a background clip source (one or more dirs, recursive or not, random or sequential)
  - a layout (anchored absolute positioning, in the style of `references/styles.md`)
  - a data source (JSON file with a list of items, one per video)
  - an output dir + filename pattern
  - a registry path where used data items + used clips + produced outputs are recorded

Usage:
    python3 scripts/render.py --template <name> [-n COUNT] [--force] [--dry-run]

Notes:
  - The skill stays domain-agnostic. Add a new look = drop a new JSON in templates/.
  - The registry is the single source of truth for "what's already done". The data JSON
    is never mutated; the engine only reads from it.
  - When `--force`, the registry is reset (existing outputs are NOT deleted; the engine
    will simply re-emit them, overwriting if the filename matches).
"""
import argparse
import datetime as dt
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"
STATE_DIR = SKILL_DIR / "state"

OUT_W, OUT_H = 1080, 1920
DEFAULT_DURATION_S = 15


# ---------- utilities ----------

def expand_path(p: str | Path) -> Path:
    return Path(os.path.expanduser(str(p))).resolve()


def ass_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def wrap_text(s: str, width: int) -> list[str]:
    return textwrap.wrap(s, width=width, break_long_words=False, break_on_hyphens=False)


def apply_case(s: str, case: str) -> str:
    if case == "upper":
        return s.upper()
    if case == "lower":
        return s.lower()
    if case == "title":
        return s.title()
    return s


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "untitled"


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def end_ts(duration: float) -> str:
    h = int(duration // 3600)
    m = int((duration % 3600) // 60)
    s = duration - h * 3600 - m * 60
    return f"{h}:{m:02d}:{s:05.2f}"


# ---------- template + registry ----------

def load_template(name: str) -> dict:
    path = TEMPLATES_DIR / f"{name}.json"
    if not path.exists():
        available = sorted(p.stem for p in TEMPLATES_DIR.glob("*.json"))
        raise SystemExit(f"Template '{name}' not found. Available: {available}")
    return json.loads(path.read_text())


def registry_path(template: dict, template_name: str) -> Path:
    if "registry" in template:
        return expand_path(template["registry"])
    return STATE_DIR / f"{template_name}.json"


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {"renders": [], "used_clips": [], "used_data_keys": []}
    return json.loads(path.read_text())


def save_registry(path: Path, reg: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")


# ---------- data loading ----------

def load_data_items(template: dict) -> list[dict]:
    data_cfg = template.get("data")
    if not data_cfg:
        return []
    data_path = expand_path(data_cfg["path"])
    if not data_path.exists():
        raise SystemExit(
            f"Data file not found: {data_path}\n"
            f"Template references this path under `data.path`. "
            f"Create it with shape: {{ \"{data_cfg.get('items_path','items')}\": [ {{...}}, {{...}} ] }}"
        )
    raw = json.loads(data_path.read_text())
    items_path = data_cfg.get("items_path")
    if items_path:
        for key in items_path.split("."):
            raw = raw[key]
    if not isinstance(raw, list):
        raise SystemExit(f"Data at `{items_path}` is not a list (got {type(raw).__name__}).")
    return raw


def data_key_of(item: dict, template: dict) -> str:
    """A stable, human-readable key for the data item (used for slug + dedup)."""
    name_key = template.get("data", {}).get("name_key")
    if name_key and name_key in item:
        return str(item[name_key])
    # Fallback: first string value in the item
    for v in item.values():
        if isinstance(v, str):
            return v
    return json.dumps(item, sort_keys=True)


# ---------- clip discovery ----------

def discover_clips(bg_cfg: dict) -> list[Path]:
    paths = bg_cfg.get("paths") or ([bg_cfg["path"]] if "path" in bg_cfg else [])
    if not paths:
        raise SystemExit("Background config must include `path` or `paths`.")
    recursive = bg_cfg.get("recursive", False)
    extensions = bg_cfg.get("extensions", [".mp4", ".mov", ".m4v"])
    excludes = bg_cfg.get("exclude_substrings", [])
    found: list[Path] = []
    for raw in paths:
        d = expand_path(raw)
        if not d.exists():
            print(f"  warn: clip dir does not exist: {d}", file=sys.stderr)
            continue
        glob = "**/*" if recursive else "*"
        for p in d.glob(glob):
            if not p.is_file():
                continue
            if p.suffix.lower() not in extensions:
                continue
            if any(sub in p.name for sub in excludes):
                continue
            found.append(p)
    return sorted(set(found))


def pick_clips(all_clips: list[Path], used: set[str], bg_cfg: dict, n_needed: int) -> list[Path]:
    """Return n_needed clips, preferring unused. Falls back to reuse if exhausted."""
    unused = [c for c in all_clips if str(c) not in used]
    pool = unused if bg_cfg.get("random", True) else unused
    if bg_cfg.get("random", True):
        rng = random.Random(bg_cfg.get("seed", 42) + len(used))
        rng.shuffle(pool)
    chosen: list[Path] = []
    i = 0
    while len(chosen) < n_needed:
        if i < len(pool):
            chosen.append(pool[i])
            i += 1
        else:
            # Exhausted unique pool — start reusing in original order, cycling
            # as many full passes as needed to hit n_needed.
            print(f"  warn: only {len(unused)} unused clips for {n_needed} renders; reusing.", file=sys.stderr)
            while len(chosen) < n_needed:
                reuse_pool = all_clips[:]
                if bg_cfg.get("random", True):
                    rng2 = random.Random(bg_cfg.get("seed", 42) + 9999 + len(chosen))
                    rng2.shuffle(reuse_pool)
                need = n_needed - len(chosen)
                chosen.extend(reuse_pool[: need])
            break
    return chosen


# ---------- element value resolution ----------

def resolve_element_value(el: dict, item: dict | None, idx: int) -> str:
    src = el.get("source", "literal")
    if src == "literal":
        val = el["value"]
        return val.format(idx=idx, n=idx)
    if src == "data":
        if item is None:
            raise SystemExit(f"Element '{el.get('name')}' uses data source but no data item provided.")
        key = el["data_key"]
        val = item.get(key)
        if val is None:
            raise SystemExit(f"Element '{el.get('name')}': data field '{key}' missing from item.")
        return str(val)
    raise SystemExit(f"Unknown element source: {src}")


def apply_transform(value: str, transform: str | None) -> str:
    if not transform or transform == "none":
        return value
    if transform == "before_emdash":
        parts = re.split(r"\s+[—–-]\s+", value, maxsplit=1)
        v = parts[0].strip()
        if not v.endswith("."):
            v += "."
        return v
    raise SystemExit(f"Unknown transform: {transform}")


def split_element_text(value: str, split_before: str | None) -> list[str]:
    if not split_before:
        return [value]
    i = value.find(split_before)
    if i < 0:
        return [value]
    head, tail = value[:i].rstrip(), value[i:].lstrip()
    return [head, tail] if head else [tail]


# ---------- ASS construction ----------

def ass_header(first_el: dict, outline: float) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{first_el["font"]},{first_el["size"]},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{outline},0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def element_segment(el: dict, lines: list[str]) -> tuple[str, int]:
    """Return (ass-text, block-height-in-px) for one element block."""
    size = el["size"]
    bold = "\\b1" if el.get("bold") else "\\b0"
    italic = "\\i1" if el.get("italic") else "\\i0"
    tag = f"{{\\fn{el['font']}\\fs{size}{bold}{italic}}}"
    text = "\\N".join(tag + ass_escape(l) for l in lines)
    height = size * len(lines)
    return text, height


def build_ass(template: dict, resolved: list[dict], duration: float) -> str:
    """resolved: list of {'el': el_cfg, 'lines': [str, str, ...]} per element, top-to-bottom."""
    layout = template.get("layout", "anchored")
    outline = template.get("outline_px", 1)
    spacer_size = template.get("spacer_size", 70)
    geom = template.get("geometry", {})
    first_el = resolved[0]["el"]

    header = ass_header(first_el, outline)
    end = end_ts(duration)

    if layout == "centered":
        # Single block: stack all elements vertically with spacer, center on `center_y`.
        center_y = geom.get("center_y", OUT_H // 2)
        segs, heights = [], []
        for r in resolved:
            seg, h = element_segment(r["el"], r["lines"])
            segs.append(seg); heights.append(h)
        block_h = sum(heights) + spacer_size * (len(segs) - 1)
        spacer = f"{{\\fs{spacer_size}\\b0\\i0}} "
        body_text = ("\\N" + spacer + "\\N").join(segs)
        cx = OUT_W // 2
        return header + f"Dialogue: 0,0:00:00.00,{end},Main,,0,0,0,,{{\\an5\\pos({cx},{center_y})}}{body_text}\n"

    if layout != "anchored":
        raise SystemExit(f"Layout '{layout}' not implemented yet. Use 'anchored' or 'centered'.")

    # Anchored: element[0] = hook (top), element[1] = phrase (anchor), element[2..] = body
    # Geometry: `phrase_center_y` locks element[1] center; `gap_px` = px between hook bottom and phrase top.
    # Elements after [1] stack below phrase with a spacer between them and each other.

    if len(resolved) < 2:
        raise SystemExit("anchored layout requires at least 2 elements (hook + anchor).")

    phrase_center_y = geom.get("phrase_center_y", 830)
    gap_px = geom.get("gap_px", 180)

    # Phrase + below elements form the body block. Compute block height + phrase offset.
    anchor = resolved[1]
    anchor_seg, anchor_h = element_segment(anchor["el"], anchor["lines"])

    body_h = anchor_h
    body_parts = [anchor_seg]
    for r in resolved[2:]:
        seg, h = element_segment(r["el"], r["lines"])
        body_h += spacer_size + h
        body_parts.append(seg)
    spacer = f"{{\\fs{spacer_size}\\b0\\i0}} "
    body_text = ("\\N" + spacer + "\\N").join(body_parts)

    # Phrase center is at anchor_h/2 from block top; body_block_center is at body_h/2 from block top.
    body_block_center_y = phrase_center_y + (body_h // 2 - anchor_h // 2)

    # Hook block(s): every element with index 0 sits above. Currently only one hook element supported.
    hook = resolved[0]
    hook_seg, hook_h = element_segment(hook["el"], hook["lines"])
    phrase_top = phrase_center_y - anchor_h // 2
    hook_bottom = phrase_top - gap_px
    hook_center_y = hook_bottom - hook_h // 2

    cx = OUT_W // 2
    e1 = f"Dialogue: 0,0:00:00.00,{end},Main,,0,0,0,,{{\\an5\\pos({cx},{hook_center_y})}}{hook_seg}\n"
    e2 = f"Dialogue: 0,0:00:00.00,{end},Main,,0,0,0,,{{\\an5\\pos({cx},{body_block_center_y})}}{body_text}\n"
    return header + e1 + e2


# ---------- per-render orchestration ----------

def resolve_element(el: dict, item: dict | None, idx: int) -> dict:
    raw = resolve_element_value(el, item, idx)
    transformed = apply_transform(raw, el.get("transform"))
    cased = apply_case(transformed, el.get("case", "preserve"))

    # Enforce max_chars (hard truncate) BEFORE wrap.
    mc = el.get("max_chars")
    if mc and len(cased) > mc:
        cased = cased[: mc].rstrip()

    # Preserve user-authored line breaks (\n in source / data values) by splitting
    # first, then wrapping each segment independently when wrap_chars is set.
    wrap_chars = el.get("wrap_chars")
    pre_lines = cased.split("\n")
    if wrap_chars:
        lines = []
        for seg in pre_lines:
            wrapped = wrap_text(seg, wrap_chars) if seg.strip() else [seg]
            lines.extend(wrapped or [""])
    else:
        lines = pre_lines

    # split_before applies to a single-line element (typically the hook).
    sb = el.get("split_before")
    if sb and len(lines) == 1:
        lines = split_element_text(lines[0], sb)

    # Enforce max_lines (truncate, mark with ellipsis on last line).
    ml = el.get("max_lines")
    if ml and len(lines) > ml:
        lines = lines[: ml]
        lines[-1] = lines[-1].rstrip().rstrip(".") + "…"

    return {"el": el, "lines": lines, "raw_value": raw, "rendered_text": "\n".join(lines)}


def render_one(template: dict, item: dict | None, idx: int, clip: Path, out_path: Path,
               dry_run: bool) -> dict:
    elements = template["elements"]
    resolved = [resolve_element(el, item, idx) for el in elements]
    print(f"  → {out_path.name}  bg: {clip.name}")
    for r in resolved:
        text = " / ".join(r["lines"])
        print(f"     [{r['el'].get('name','?'):<12}] {text[:60]}{'…' if len(text)>60 else ''}")

    if dry_run:
        return {"resolved": resolved, "rendered": False}

    clip_duration = probe_duration(clip)
    target_duration = float(template.get("duration_s", DEFAULT_DURATION_S))
    duration = min(clip_duration, target_duration)
    ass = build_ass(template, resolved, duration)
    with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False) as f:
        f.write(ass); ass_path = f.name

    vf = (
        f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={OUT_W}:{OUT_H},"
        "setsar=1,"
        f"subtitles='{ass_path}'"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(clip), "-t", f"{duration:.3f}", "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True)
    finally:
        try: os.unlink(ass_path)
        except OSError: pass

    return {"resolved": resolved, "rendered": True}


# ---------- main ----------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--template", required=True, help="Template name in templates/ (no .json).")
    p.add_argument("-n", "--count", type=int, default=10, help="Max renders this run.")
    p.add_argument("--force", action="store_true", help="Reset registry and re-render all.")
    p.add_argument("--dry-run", action="store_true", help="Print plan, do not encode.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    template = load_template(args.template)
    reg_path = registry_path(template, args.template)
    reg = {"renders": [], "used_clips": [], "used_data_keys": []} if args.force else load_registry(reg_path)

    out_cfg = template["output"]
    out_dir = expand_path(out_cfg["dir"])
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    filename_pattern = out_cfg.get("filename_pattern", "{idx:02d}-{slug}.mp4")

    items = load_data_items(template)
    if not items:
        raise SystemExit(f"Template '{args.template}' has no data items.")

    used_keys = set(reg["used_data_keys"])
    used_clips = set(reg["used_clips"])

    # Pending = items whose key isn't in the registry.
    pending: list[tuple[int, dict, str]] = []
    for idx, item in enumerate(items, start=1):
        key = data_key_of(item, template)
        if key in used_keys:
            continue
        pending.append((idx, item, key))
        if len(pending) >= args.count:
            break

    if not pending:
        print(f"Nothing to render — {len(used_keys)} items already done. Use --force to reset.")
        return 0

    all_clips = discover_clips(template["background"])
    if not all_clips:
        raise SystemExit("No background clips discovered. Check `background.paths`.")
    clips_for_this_run = pick_clips(all_clips, used_clips, template["background"], len(pending))

    print(f"Template={args.template}  pending={len(pending)}  clips_available={len(all_clips)}  "
          f"already_used_clips={len(used_clips)}  out={out_dir}")

    for (idx, item, key), clip in zip(pending, clips_for_this_run):
        slug = slugify(key)
        out_name = filename_pattern.format(idx=idx, slug=slug, key=key)
        out_path = out_dir / out_name
        print(f"[{idx}] {key}")
        result = render_one(template, item, idx, clip, out_path, args.dry_run)
        if args.dry_run:
            continue
        reg["renders"].append({
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "idx": idx,
            "data_key": key,
            "clip": str(clip),
            "output": str(out_path),
            "elements": [{"name": r["el"].get("name"), "lines": r["lines"]} for r in result["resolved"]],
        })
        reg["used_data_keys"].append(key)
        reg["used_clips"].append(str(clip))
        save_registry(reg_path, reg)

    if args.dry_run:
        print(f"\nDry-run: would render {len(pending)} videos.")
    else:
        print(f"\nDone. Rendered {len(pending)}. Registry: {reg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
