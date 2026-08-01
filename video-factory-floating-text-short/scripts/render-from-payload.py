#!/usr/bin/env python3
"""
Drain payload.json into final/ MP4s, append to runs.json.

Builds a complete .ass overlay file with the factory's **visual hierarchy**
(line 1 small / line 2 normal-hero / line 3 small) and passes it to the shared
helper in `$ffmpeg-text-overlay-style` via its .ass passthrough mode. Colors,
default font, outline ratios, line-height ratio, and overlay position are still
sourced from that skill's text-overlay-style.json — so the factory stays
visually linked to every other skill that uses the shared style.

Per-entry overrides (optional, in payload.json entry under "style"):
  - title_caps: bool         — uppercase line 2 (default false)
  - title_font: str | null   — fontname swap for line 2 (default: shared font).
                               The font must be installed on the system or
                               available via the shared helper's fontsdir.
  - hierarchy: {line_1: float, line_2: float, line_3: float}
                             — multipliers on base_font_size (defaults below).

Usage:
  render-from-payload.py --working-folder <dir> [-n N] [--force]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
OVERLAY_STYLE_SKILL = SKILL_DIR.parent / "ffmpeg-text-overlay-style"
OVERLAY_HELPER = OVERLAY_STYLE_SKILL / "scripts" / "render_subtitles_with_default_style.py"
SHARED_STYLE_JSON = OVERLAY_STYLE_SKILL / "ressources" / "text-overlay-style.json"
FLAGS_DIR = SKILL_DIR / "references" / "flags"
# libass 0.17.4 does not reliably render color-bitmap (sbix/COLR) emoji glyphs
# — anything emoji-shaped will turn into .notdef boxes on the burned video.
# For series identity marks (e.g. the French flag in douce-france-def), the
# render path uses a PNG overlay pass *after* libass burn-in instead.

# Visual hierarchy — multipliers on shared base_font_size.
# line 1 = small (hook), line 2 = normal/hero (title), line 3 = small (detail).
DEFAULT_HIERARCHY = {
    "line_1": 0.75,
    "line_2": 1.10,
    "line_3": 0.75,
}

# Asymmetric paragraph-gap multipliers (applied on top of the shared
# paragraph_gap_ratio from text-overlay-style.json). The hook should breathe
# above the title (1.8×), and the detail should hug the title (0.6×).
DEFAULT_PARAGRAPH_GAP_SCALE = {
    ("line_1", "line_2"): 1.8,  # wider gap between hook and title
    ("line_2", "line_3"): 0.6,  # tighter gap between title and detail
}


def fail(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path: Path):
    return json.loads(path.read_text())


def save_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def probe_duration(video: Path) -> float:
    res = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(res.stdout.strip())


def probe_dimensions(video: Path) -> tuple[int, int]:
    res = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=,",
            str(video),
        ],
        capture_output=True, text=True, check=True,
    )
    w, h = res.stdout.strip().split(",")
    return int(w), int(h)


def ass_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def ms_to_ass_time(ms: int) -> str:
    cs = ms // 10
    h = cs // 360000
    m = (cs % 360000) // 6000
    s = (cs % 6000) // 100
    c = cs % 100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def wrap_to_chars(text: str, max_chars: int) -> list[str]:
    """Greedy word-wrap. Returns at least one line."""
    text = text.strip()
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        candidate = (cur + " " + w).strip() if cur else w
        if len(candidate) <= max_chars:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def build_hierarchy_ass(
    overlay: dict,
    duration_s: float,
    video_w: int,
    video_h: int,
    opts: dict | None = None,
) -> tuple[str, dict]:
    """Produce a full ASS document with per-line size hierarchy.

    Returns (ass_text, layout) where `layout` records key positioning data
    per role (font size, anchor x, anchor y, est. text width, alignment).
    Downstream callers use it to place sibling visual elements like a flag
    PNG overlay anchored relative to the hook text.
    """
    opts = opts or {}
    if not SHARED_STYLE_JSON.exists():
        fail(f"shared style config missing at {SHARED_STYLE_JSON}")
    style = json.loads(SHARED_STYLE_JSON.read_text(encoding="utf-8"))

    base = int(style["sizing"]["base_font_size"])
    ref_w = int(style["reference_width"])
    scale = video_w / ref_w

    pos_pct = float(style["layout"]["overlay_position_pct"])
    line_height_ratio = float(style["layout"]["line_height_ratio"])
    paragraph_gap_ratio = float(style["layout"]["paragraph_gap_ratio"])
    spacing = float(style["layout"]["spacing"]) * scale
    wrap_style = int(style["layout"]["wrap_style"])
    outline_ratio = float(style["stroke"]["outline_ratio"])
    min_outline = int(style["stroke"]["min_outline"])
    chars_per_line = int(style["chars_per_line"]["latin"])

    default_font = str(style["font"]["name"])
    primary = str(style["colors"]["primary"])
    outline_color = str(style["colors"]["outline"])
    back = str(style["colors"]["back"])

    title_caps = bool(opts.get("title_caps", False))
    title_font = opts.get("title_font") or None
    hierarchy = {**DEFAULT_HIERARCHY, **(opts.get("hierarchy") or {})}

    # hook_suffix: appended to line_1 text only. **Do not put a color emoji
    # here** — libass can't render sbix/COLR bitmap glyphs reliably (they
    # come out as .notdef boxes). For series-identity flag icons, use
    # hook_emoji_image instead (PNG overlay pass).
    hook_suffix = str(opts.get("hook_suffix", "") or "")
    # hook_duration_s: cap line_1's on-screen time (in seconds). None = full clip.
    hook_duration_s = opts.get("hook_duration_s")
    # alignment: per-role alignment. "center" (default, \an5) or "left" (\an4).
    raw_alignment = opts.get("alignment", "center")
    if isinstance(raw_alignment, str):
        alignment_map = {"line_1": raw_alignment, "line_2": raw_alignment, "line_3": raw_alignment}
    else:
        alignment_map = {"line_1": "center", "line_2": "center", "line_3": "center"}
        alignment_map.update({k: str(v) for k, v in (raw_alignment or {}).items()})
    # font_weight: int in [100, 900]. Applied via libass \b<weight> override.
    # None → keep whatever the shared Style line implies.
    font_weight = opts.get("font_weight")
    if font_weight is not None:
        font_weight = max(100, min(900, int(font_weight)))
    # outline_scale: either a scalar (applies to all lines) or a dict keyed by
    # role ({"line_1": 0, "line_2": 0.7, ...}) for per-line control. A scale
    # of exactly 0 disables the stroke for that line (\bord0).
    raw_outline_scale = opts.get("outline_scale", 1.0)
    if isinstance(raw_outline_scale, dict):
        outline_scale_map = {k: float(v) for k, v in raw_outline_scale.items()}
        outline_scale_default = float(raw_outline_scale.get("default", 1.0))
    else:
        outline_scale_map = {}
        outline_scale_default = float(raw_outline_scale)

    # Paragraph-gap scale overrides — accept either dict form
    # {"line_1_to_line_2": 1.8, ...} (payload-friendly) or the tuple-keyed
    # internal form. Defaults to DEFAULT_PARAGRAPH_GAP_SCALE.
    gap_scale: dict[tuple[str, str], float] = dict(DEFAULT_PARAGRAPH_GAP_SCALE)
    raw_gap_override = opts.get("paragraph_gap_scale") or {}
    for key, value in raw_gap_override.items():
        if isinstance(key, tuple) and len(key) == 2:
            gap_scale[key] = float(value)
        elif isinstance(key, str) and "_to_" in key:
            a, b = key.split("_to_", 1)
            gap_scale[(a, b)] = float(value)

    # Build per-line spec — each logical line may wrap to multiple visual lines.
    specs: list[dict] = []
    for role in ("line_1", "line_2", "line_3"):
        raw = str(overlay.get(role, "")).strip()
        if not raw:
            continue
        if role == "line_1" and hook_suffix:
            raw = f"{raw}{hook_suffix}"
        is_title = role == "line_2"
        text = raw.upper() if (is_title and title_caps) else raw
        font = title_font if (is_title and title_font) else default_font
        size = max(8, round(base * hierarchy[role] * scale))
        # Caps are visually wider — tighten the wrap threshold a bit.
        effective_limit = chars_per_line - 5 if (is_title and title_caps) else chars_per_line
        # Smaller lines fit more characters per visual line. Scale the limit
        # inversely to the size ratio (very rough but keeps both small and
        # large lines from overflowing on screen).
        effective_limit = max(8, round(effective_limit * (base / size) * 0.95))
        wrapped = wrap_to_chars(text, effective_limit)
        for i, visual_line in enumerate(wrapped):
            specs.append({
                "role": role,
                "text": visual_line,
                "size": size,
                "font": font,
                "is_paragraph_start": i == 0,
            })

    if not specs:
        fail("payload entry has no non-empty overlay lines")

    # Vertical layout — advance the cursor by each line's own height; insert
    # an asymmetric paragraph gap between logical lines (hook → title gets a
    # wider gap than title → detail). Gaps come from paragraph_gap_ratio in
    # the shared style, then multiplied by gap_scale per role-transition.
    positions: list[float] = []
    cursor = 0.0
    prev_size: int | None = None
    prev_role: str | None = None
    for s in specs:
        if prev_size is not None:
            cursor += prev_size * line_height_ratio
            if s["is_paragraph_start"] and prev_role is not None:
                base_gap = max(s["size"], prev_size) * paragraph_gap_ratio
                scale = gap_scale.get((prev_role, s["role"]), 1.0)
                cursor += base_gap * scale
        positions.append(cursor)
        prev_size = s["size"]
        prev_role = s["role"]

    total = positions[-1] if positions else 0.0
    anchor_y = video_h * (pos_pct / 100.0)
    center_shift = anchor_y - total / 2.0
    anchor_x = round(video_w / 2)

    end_time = ms_to_ass_time(int(duration_s * 1000))

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {video_w}\n"
        f"PlayResY: {video_h}\n"
        f"WrapStyle: {wrap_style}\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{default_font},{base},{primary},{primary},"
        f"{outline_color},{back},0,0,0,0,100,100,{spacing:.2f},0,1,"
        f"{min_outline},0,5,0,0,0,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )

    events: list[str] = []
    weight_tag = f"\\b{font_weight}" if font_weight is not None else ""
    left_margin_x = round(video_w * 0.075)  # ~80px on a 1080-wide canvas
    hook_end_time = (
        ms_to_ass_time(int(float(hook_duration_s) * 1000))
        if hook_duration_s is not None
        else end_time
    )
    layout: dict = {"video_w": video_w, "video_h": video_h, "roles": {}}
    for spec, off in zip(specs, positions):
        y = int(round(center_shift + off))
        this_scale = outline_scale_map.get(spec["role"], outline_scale_default)
        if this_scale <= 0:
            outline = 0
        else:
            raw_outline = round(spec["size"] * outline_ratio * this_scale)
            outline = max(min_outline, raw_outline) if this_scale >= 1.0 else max(1, raw_outline)
        align = alignment_map.get(spec["role"], "center")
        if align == "left":
            an_tag = "\\an4"
            x = left_margin_x
        else:
            an_tag = "\\an5"
            x = anchor_x
        this_end = hook_end_time if spec["role"] == "line_1" else end_time
        override = (
            f"{{{an_tag}\\q{wrap_style}\\pos({x},{y})"
            f"\\fs{spec['size']}\\fn{spec['font']}{weight_tag}\\bord{outline}}}"
        )
        events.append(
            f"Dialogue: 0,0:00:00.00,{this_end},Default,,0,0,0,,"
            f"{override}{ass_escape(spec['text'])}"
        )
        # Track per-role first-visual-line layout for sibling overlays
        # (flag PNG, badges, etc). TikTok Sans Bold averages ~0.45× em-square
        # per glyph in practice; refine if a different font is used.
        if spec["role"] not in layout["roles"]:
            est_text_width = round(len(spec["text"]) * spec["size"] * 0.45)
            layout["roles"][spec["role"]] = {
                "text": spec["text"],
                "size": spec["size"],
                "x_center": x if align != "left" else x + est_text_width // 2,
                "y_center": y,
                "x_left": (x - est_text_width // 2) if align != "left" else x,
                "x_right": (x + est_text_width // 2) if align != "left" else x + est_text_width,
                "est_width": est_text_width,
                "alignment": align,
                "end_time": this_end,
            }

    return header + "\n".join(events) + "\n", layout


def merge_style(defaults: dict | None, entry_style: dict | None) -> dict:
    """Per-entry style wins over workspace defaults. None-safe."""
    merged: dict = dict(defaults or {})
    for k, v in (entry_style or {}).items():
        if v is None:
            continue  # don't let an explicit None erase a default
        merged[k] = v
    return merged


def render_one(entry: dict, working: Path, defaults_style: dict | None = None) -> dict:
    eid = entry["id"]
    overlay = entry["overlay"]
    bg = (working / entry["background_video"]).resolve()
    if not bg.exists():
        fail(f"{eid}: background_video not found: {bg}")

    duration = probe_duration(bg)
    width, height = probe_dimensions(bg)
    final_dir = working / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    out_path = final_dir / f"{eid}.mp4"

    if not OVERLAY_HELPER.exists():
        fail(
            "$ffmpeg-text-overlay-style helper not found at "
            f"{OVERLAY_HELPER} — install/symlink that skill first."
        )

    merged_style = merge_style(defaults_style, entry.get("style"))

    with tempfile.TemporaryDirectory() as tmpd:
        ass_path = Path(tmpd) / "overlay.ass"
        ass_body, layout = build_hierarchy_ass(
            overlay=overlay,
            duration_s=duration,
            video_w=width,
            video_h=height,
            opts=merged_style,
        )
        ass_path.write_text(ass_body, encoding="utf-8")

        # First pass — libass burn-in via the shared helper.
        burn_path = out_path
        emoji_image = resolve_hook_emoji_image(merged_style.get("hook_emoji_image"))
        if emoji_image is not None:
            burn_path = Path(tmpd) / "burned.mp4"

        cmd = [
            "python3", str(OVERLAY_HELPER),
            "--input", str(bg),
            "--subtitles", str(ass_path),
            "--out", str(burn_path),
        ]
        subprocess.run(cmd, check=True)

        # Optional second pass — PNG overlay anchored to the hook text.
        # Bypasses libass's broken color-emoji rendering by drawing the icon
        # as a separate ffmpeg overlay stream.
        if emoji_image is not None:
            overlay_hook_emoji(
                src=burn_path,
                emoji_image=emoji_image,
                layout=layout,
                opts=merged_style,
                out=out_path,
            )

    return {
        "id": eid,
        "video": f"final/{out_path.name}",
        "rendered_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_clip": entry["background_video"],
        "duration_s": round(duration, 2),
    }


def resolve_hook_emoji_image(value) -> Path | None:
    """Resolve a hook_emoji_image option to an actual PNG path.

    Accepts:
      - None → no overlay
      - Absolute path string → used as-is
      - 2-letter country/lang code (e.g. "fr") → looks up references/flags/<code>.png
      - Relative path string → relative to the skill's references dir
    """
    if value in (None, "", False):
        return None
    s = str(value).strip()
    p = Path(os.path.expanduser(s))
    if p.is_absolute() and p.exists():
        return p
    # 2-letter code shortcut
    if len(s) <= 4 and "/" not in s and "." not in s:
        candidate = FLAGS_DIR / f"{s.lower()}.png"
        if candidate.exists():
            return candidate
    # relative to skill references
    candidate = SKILL_DIR / "references" / s
    if candidate.exists():
        return candidate
    fail(f"hook_emoji_image not found: {value!r}")
    return None  # unreachable


def overlay_hook_emoji(
    src: Path,
    emoji_image: Path,
    layout: dict,
    opts: dict,
    out: Path,
) -> None:
    """Compose a second ffmpeg pass that overlays a PNG icon next to the hook.

    Position math:
      - The icon's height ≈ hook font size × hook_emoji_size_ratio (default 0.9).
      - Aspect ratio of the source PNG is preserved.
      - Icon sits to the right of the hook text by hook_emoji_gap_px (default 14).
      - Icon vanishes at the hook's end_time so it disappears with the hook.
    """
    hook = (layout.get("roles") or {}).get("line_1")
    if not hook:
        # No hook line → nothing to anchor to; just copy the burn.
        if src != out:
            os.replace(src, out)
        return

    size_ratio = float(opts.get("hook_emoji_size_ratio", 0.9))
    gap_px = int(opts.get("hook_emoji_gap_px", 14))
    icon_h = max(8, round(hook["size"] * size_ratio))

    # Probe PNG aspect to compute width.
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=,",
            str(emoji_image),
        ],
        capture_output=True, text=True, check=True,
    )
    src_w, src_h = (int(v) for v in probe.stdout.strip().split(","))
    icon_w = max(1, round(icon_h * (src_w / src_h)))

    x = int(hook["x_right"]) + gap_px
    y = int(hook["y_center"]) - icon_h // 2

    # Convert hook end_time (ASS H:MM:SS.cc) back to seconds for the enable expr.
    h, m, rest = hook["end_time"].split(":")
    enable_end = float(h) * 3600 + float(m) * 60 + float(rest)
    enable_expr = f"lt(t,{enable_end:.2f})"

    filter_complex = (
        f"[1:v]scale={icon_w}:{icon_h},format=rgba[fg];"
        f"[0:v][fg]overlay={x}:{y}:enable='{enable_expr}'[v]"
    )

    # Detect whether the source has an audio stream so we can copy it through.
    audio_probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(src)],
        capture_output=True, text=True,
    )
    has_audio = audio_probe.stdout.strip() == "audio"

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(src),
        "-i", str(emoji_image),
        "-filter_complex", filter_complex,
        "-map", "[v]",
    ]
    if has_audio:
        cmd.extend(["-map", "0:a:0", "-c:a", "copy"])
    cmd.extend([
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out),
    ])
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--working-folder", required=True)
    ap.add_argument("-n", type=int, default=10, help="max entries to render this run")
    ap.add_argument("--force", action="store_true", help="also re-render already-done entries")
    args = ap.parse_args()

    working = Path(os.path.expanduser(args.working_folder)).resolve()
    payload_path = working / "payload.json"
    runs_path = working / "runs.json"
    if not payload_path.exists():
        fail(f"{payload_path} not found — run init-workflow.sh first")
    if not runs_path.exists():
        fail(f"{runs_path} not found — run init-workflow.sh first")

    payload = load_json(payload_path)
    runs = load_json(runs_path)

    defaults_style = (payload.get("defaults") or {}).get("style") or {}

    rendered = 0
    for entry in payload["entries"]:
        if rendered >= args.n:
            break
        if entry.get("status") == "done" and not args.force:
            continue
        try:
            run = render_one(entry, working, defaults_style=defaults_style)
        except subprocess.CalledProcessError as e:
            print(f"render failed for {entry['id']}: {e}", file=sys.stderr)
            continue
        entry["status"] = "done"
        runs["runs"].append(run)
        # incremental save — crash-safe
        save_json(payload_path, payload)
        save_json(runs_path, runs)
        rendered += 1
        print(f"done {entry['id']} → {run['video']}")

    print(f"\nrendered {rendered} entries this run")


if __name__ == "__main__":
    main()
