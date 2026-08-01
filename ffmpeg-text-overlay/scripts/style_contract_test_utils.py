#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path

# Any short video works. Point TEST_BACKGROUND_CLIP at your own, or let the
# resolver generate a throwaway clip with ffmpeg.
import os
import subprocess
import tempfile

TEST_BACKGROUND_CLIP = Path(
    os.environ.get("TEST_BACKGROUND_CLIP", "")
).resolve() if os.environ.get("TEST_BACKGROUND_CLIP") else None


def load_style_contract(style_config_path: Path) -> dict[str, object]:
    return json.loads(style_config_path.read_text(encoding="utf-8"))


def resolve_test_background_clip() -> Path:
    """A clip to burn subtitles onto. Uses $TEST_BACKGROUND_CLIP when set,
    otherwise generates a 3s 1080x1920 colour clip so the tests run anywhere."""
    if TEST_BACKGROUND_CLIP is not None:
        if not TEST_BACKGROUND_CLIP.exists():
            raise FileNotFoundError(
                f"TEST_BACKGROUND_CLIP does not exist: {TEST_BACKGROUND_CLIP}")
        return TEST_BACKGROUND_CLIP

    generated = Path(tempfile.gettempdir()) / "text-overlay-test-bg.mp4"
    if not generated.exists():
        subprocess.run([
            os.environ.get("FFMPEG_BIN", "ffmpeg"), "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=0x1b2838:s=1080x1920:d=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(generated),
        ], check=True)
    return generated


def resolve_font_file(style_config: dict[str, object], style_config_path: Path) -> Path:
    font = style_config["font"]
    assert isinstance(font, dict)
    raw_path = Path(str(font["file"])).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve()
    return (style_config_path.parent / raw_path).resolve()


def compute_expected_style(style_config: dict[str, object], playres_x: int, playres_y: int) -> dict[str, object]:
    reference_width = int(style_config["reference_width"])
    font = dict(style_config["font"])
    layout = dict(style_config["layout"])
    sizing = dict(style_config["sizing"])
    stroke = dict(style_config["stroke"])
    font_bold = int(font["bold"])
    font_weight_value = int(font["weight_value"])
    base_ass_weight_value = 700 if font_bold not in (0, False) else 400
    normalized_weight = max(100, min(900, round(font_weight_value / 100) * 100))
    ass_weight_override = normalized_weight if normalized_weight != base_ass_weight_value else None

    scale_factor = playres_x / reference_width
    font_size = max(1, round(int(sizing["base_font_size"]) * scale_factor))
    line_height = max(font_size, round(font_size * float(layout["line_height_ratio"])))
    paragraph_gap = max(1, round(font_size * float(layout["paragraph_gap_ratio"])))
    outline = max(int(stroke["min_outline"]), round(font_size * float(stroke["outline_ratio"])))

    return {
        "reference_width": reference_width,
        "playres_x": playres_x,
        "playres_y": playres_y,
        "font_name": str(font["name"]),
        "font_size": font_size,
        "font_weight_label": str(font["weight_label"]),
        "font_weight_value": font_weight_value,
        "font_ass_weight_override": ass_weight_override,
        "font_ass_weight_tag": f"\\b{ass_weight_override}" if ass_weight_override is not None else None,
        "overlay_position_pct": float(layout["overlay_position_pct"]),
        "wrap_style": int(layout["wrap_style"]),
        "spacing": round(float(layout["spacing"]) * scale_factor, 2),
        "line_height": line_height,
        "paragraph_gap": paragraph_gap,
        "outline_ratio": float(stroke["outline_ratio"]),
        "min_outline": int(stroke["min_outline"]),
        "outline": outline,
        "chars_per_line": {key: int(value) for key, value in dict(style_config["chars_per_line"]).items()},
    }


def wrap_word_based_text(text: str, max_chars_per_line: int) -> list[str]:
    words = re.split(r"\s+", text.strip())
    lines: list[str] = []
    current_line = ""
    for word in words:
        if not word:
            continue
        candidate = word if not current_line else f"{current_line} {word}"
        if current_line and len(candidate) > max_chars_per_line:
            lines.append(current_line)
            current_line = word
            continue
        current_line = candidate
    if current_line:
        lines.append(current_line)
    return lines or [text.strip()]


def compute_positioned_lines(
    playres_x: int,
    playres_y: int,
    overlay_position_pct: float,
    line_height: int,
    paragraph_gap: int,
    paragraphs: list[list[str]],
) -> dict[str, object]:
    flattened_lines: list[str] = []
    offsets: list[float] = []
    cursor = 0.0
    first_line = True

    for paragraph_index, paragraph in enumerate(paragraphs):
        for line_index, line in enumerate(paragraph):
            if not first_line:
                cursor += line_height
                if line_index == 0 and paragraph_index > 0:
                    cursor += paragraph_gap
            flattened_lines.append(line)
            offsets.append(cursor)
            first_line = False

    anchor_x = round(playres_x / 2)
    anchor_y = round(playres_y * (overlay_position_pct / 100))
    center_shift = anchor_y - (offsets[-1] / 2.0) if offsets else float(anchor_y)
    positioned_y = [int(round(center_shift + offset)) for offset in offsets]

    return {
        "anchor_x": anchor_x,
        "anchor_y": anchor_y,
        "center_shift": round(center_shift, 2),
        "positioned_y": positioned_y,
        "flattened_lines": flattened_lines,
    }
