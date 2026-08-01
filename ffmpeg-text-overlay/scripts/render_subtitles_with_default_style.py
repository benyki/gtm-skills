#!/usr/bin/env python3
# Run:
#   python3 {baseDir}/scripts/render_subtitles_with_default_style.py --input /abs/path/in.mp4 --subtitles /abs/path/subtitles.srt --out /abs/path/out.mp4
#   python3 {baseDir}/scripts/render_subtitles_with_default_style.py --input /abs/path/in.mp4 --subtitles /abs/path/subtitles.srt --out /abs/path/out.mp4 --preset veryfast --crf 20
#   python3 {baseDir}/scripts/render_subtitles_with_default_style.py --input /abs/path/in.mp4 --subtitles /abs/path/subtitles.srt --out /abs/path/out.mp4 --append-video-filters "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p" --trim-seconds 4 --stream-loop -1 --fps 30 --drop-audio
#   python3 {baseDir}/scripts/render_subtitles_with_default_style.py --print-style
# Flow: resolves ffmpeg and ffprobe, converts SRT into a temporary ASS file with
# one shared overlay style, then burns that resolved ASS file into the video.
#
# Configuration:
#   ressources/text-overlay-style.json is the machine-readable source of truth
#   for shared text overlay style values across all skills that use this helper.

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
STYLE_CONFIG_PATH = SKILL_ROOT / "ressources" / "text-overlay-style.json"
DEFAULT_VIDEO_CODEC = "libx264"
DEFAULT_PRESET = "slow"
DEFAULT_CRF = "18"
DEFAULT_MOVFLAGS = "+faststart"


def load_style_config(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_style_config_font_path(style_config: dict[str, object], config_path: Path) -> Path:
    font = style_config["font"]
    assert isinstance(font, dict)
    raw_path = Path(str(font["file"])).expanduser()
    if raw_path.is_absolute():
        return raw_path
    return (config_path.parent / raw_path).resolve()


STYLE_CONFIG = load_style_config(STYLE_CONFIG_PATH)
STYLE_FONT = STYLE_CONFIG["font"]
STYLE_LAYOUT = STYLE_CONFIG["layout"]
STYLE_SIZING = STYLE_CONFIG["sizing"]
STYLE_STROKE = STYLE_CONFIG["stroke"]
STYLE_COLORS = STYLE_CONFIG["colors"]
DEFAULT_FONTFILE_PATH = resolve_style_config_font_path(STYLE_CONFIG, STYLE_CONFIG_PATH)
DEFAULT_FONTNAME = str(STYLE_FONT["name"])
DEFAULT_OVERLAY_POSITION_PCT = float(STYLE_LAYOUT["overlay_position_pct"])
DEFAULT_WRAPSTYLE = int(STYLE_LAYOUT["wrap_style"])
DEFAULT_BASE_FONT_SIZE = int(STYLE_SIZING["base_font_size"])
DEFAULT_BASE_SPACING = float(STYLE_LAYOUT["spacing"])
DEFAULT_LINE_HEIGHT_RATIO = float(STYLE_LAYOUT["line_height_ratio"])
DEFAULT_PARAGRAPH_GAP_RATIO = float(STYLE_LAYOUT["paragraph_gap_ratio"])
DEFAULT_OUTLINE_RATIO = float(STYLE_STROKE["outline_ratio"])
DEFAULT_MIN_OUTLINE = int(STYLE_STROKE["min_outline"])
DEFAULT_PRIMARY_COLOUR = str(STYLE_COLORS["primary"])
DEFAULT_SECONDARY_COLOUR = str(STYLE_COLORS["secondary"])
DEFAULT_OUTLINE_COLOUR = str(STYLE_COLORS["outline"])
DEFAULT_BACK_COLOUR = str(STYLE_COLORS["back"])
DEFAULT_BOLD = int(STYLE_FONT["bold"])
DEFAULT_ITALIC = int(STYLE_FONT["italic"])
DEFAULT_UNDERLINE = int(STYLE_FONT["underline"])
DEFAULT_STRIKEOUT = int(STYLE_FONT["strikeout"])
DEFAULT_SCALE_X = int(STYLE_FONT["scale_x"])
DEFAULT_SCALE_Y = int(STYLE_FONT["scale_y"])
DEFAULT_ANGLE = int(STYLE_FONT["angle"])
DEFAULT_BORDERSTYLE = int(STYLE_STROKE["border_style"])
DEFAULT_SHADOW = int(STYLE_STROKE["shadow"])
DEFAULT_ALIGNMENT = int(STYLE_LAYOUT["alignment"])
DEFAULT_MARGIN_L = int(STYLE_LAYOUT["margin_l"])
DEFAULT_MARGIN_R = int(STYLE_LAYOUT["margin_r"])
DEFAULT_MARGIN_V = int(STYLE_LAYOUT["margin_v"])
DEFAULT_ENCODING = int(STYLE_FONT["encoding"])
DEFAULT_FONT_WEIGHT_LABEL = str(
    STYLE_FONT.get("weight_label", "bold" if DEFAULT_BOLD not in (0, False) else "regular")
)
DEFAULT_FONT_WEIGHT_VALUE = int(
    STYLE_FONT.get("weight_value", 700 if DEFAULT_BOLD not in (0, False) else 400)
)
BASE_ASS_WEIGHT_VALUE = 700 if DEFAULT_BOLD not in (0, False) else 400
REQUESTED_ASS_WEIGHT_VALUE = max(100, min(900, round(DEFAULT_FONT_WEIGHT_VALUE / 100) * 100))
DEFAULT_ASS_WEIGHT_OVERRIDE = (
    REQUESTED_ASS_WEIGHT_VALUE if REQUESTED_ASS_WEIGHT_VALUE != BASE_ASS_WEIGHT_VALUE else None
)
DEFAULT_ASS_WEIGHT_TAG = (
    f"\\b{DEFAULT_ASS_WEIGHT_OVERRIDE}" if DEFAULT_ASS_WEIGHT_OVERRIDE is not None else ""
)
REFERENCE_WIDTH = int(STYLE_CONFIG["reference_width"])

SCRIPT_CHAR_LIMITS = {
    key: int(value) for key, value in dict(STYLE_CONFIG["chars_per_line"]).items()
}

SRT_TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
)
WHITESPACE_RE = re.compile(r"\s+")
CJK_PUNCTUATION = set(",，。、！？：；")
RTL_RANGES = (
    (0x0590, 0x05FF),
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB1D, 0xFDFF),
    (0xFE70, 0xFEFF),
)
ABUGIDA_RANGES = (
    (0x0900, 0x097F),
    (0x0980, 0x09FF),
    (0x0E00, 0x0E7F),
)
CJK_RANGES = (
    (0x3040, 0x30FF),
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xAC00, 0xD7AF),
)


@dataclass(frozen=True)
class SubtitleCue:
    index: int
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class VideoMetadata:
    width: int
    height: int
    duration: float


@dataclass(frozen=True)
class AssStyleConfig:
    playres_x: int
    playres_y: int
    overlay_position_pct: float
    fontname: str
    fontsize: int
    spacing: float
    line_height: int
    paragraph_gap: int
    outline: int
    wrap_style: int


def resolve_default_fontfile() -> str:
    path = DEFAULT_FONTFILE_PATH
    if path.exists():
        return str(path.resolve())
    return str(path)


def resolve_default_fontsdir() -> str | None:
    font_file = Path(DEFAULT_FONTFILE).expanduser()
    if font_file.exists():
        return str(font_file.resolve().parent)
    return None


DEFAULT_FONTFILE = resolve_default_fontfile()
DEFAULT_FONTSDIR = resolve_default_fontsdir()


def resolve_binary(env_name: str, preferred_path: str, fallback_name: str) -> str:
    explicit = os.environ.get(env_name)
    if explicit:
        return explicit
    preferred = Path(preferred_path)
    if preferred.exists():
        return str(preferred)
    found = shutil.which(fallback_name)
    if found:
        return found
    return fallback_name


FFMPEG_BIN = resolve_binary("FFMPEG_BIN", "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg", "ffmpeg")
FFPROBE_BIN = resolve_binary("FFPROBE_BIN", "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe", "ffprobe")


def in_ranges(codepoint: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(start <= codepoint <= end for start, end in ranges)


def detect_script_group(text: str) -> str:
    counts = {"latin": 0, "rtl": 0, "abugida": 0, "cjk": 0}
    for char in text:
        codepoint = ord(char)
        if in_ranges(codepoint, CJK_RANGES):
            counts["cjk"] += 1
        elif in_ranges(codepoint, RTL_RANGES):
            counts["rtl"] += 1
        elif in_ranges(codepoint, ABUGIDA_RANGES):
            counts["abugida"] += 1
    if counts["cjk"]:
        return "cjk"
    if counts["rtl"]:
        return "rtl"
    if counts["abugida"]:
        return "abugida"
    return "latin"


def collapse_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def normalize_overlay_text(text: str) -> str:
    value = text.replace("\r\n", "\n").replace("\r", "\n").replace(r"\N", "\n")
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"</?(?:i|b|u|font)(?: [^>]*)?>", "", value, flags=re.IGNORECASE)
    value = html.unescape(value)
    normalized_parts: list[str] = []
    pending_paragraph_break = False

    for raw_part in value.split("\n"):
        part = collapse_whitespace(raw_part)
        if part:
            if pending_paragraph_break and normalized_parts:
                normalized_parts.append("")
            normalized_parts.append(part)
            pending_paragraph_break = False
            continue
        pending_paragraph_break = bool(normalized_parts)

    return "\n".join(normalized_parts)


def measure_text_units(text: str) -> int:
    return len(text)


def wrap_word_based_text(text: str, max_chars_per_line: int) -> list[str]:
    words = re.split(r"\s+", text.strip())
    lines: list[str] = []
    current_line = ""
    for word in words:
        if not word:
            continue
        candidate = word if not current_line else f"{current_line} {word}"
        if current_line and measure_text_units(candidate) > max_chars_per_line:
            lines.append(current_line)
            current_line = word
            continue
        current_line = candidate
    if current_line:
        lines.append(current_line)
    return lines or [text.strip()]


def wrap_unspaced_text(text: str, max_chars_per_line: int) -> list[str]:
    compact_text = re.sub(r"\s+", "", text)
    if not compact_text:
        return [""]
    lines: list[str] = []
    remaining = compact_text
    while remaining:
        if len(remaining) <= max_chars_per_line:
            lines.append(remaining)
            break
        split_at = max_chars_per_line
        candidate = remaining[:max_chars_per_line]
        for index in range(len(candidate) - 1, -1, -1):
            if candidate[index] in CJK_PUNCTUATION:
                split_at = index + 1
                break
        lines.append(remaining[:split_at])
        remaining = remaining[split_at:]
    return lines


def preprocess_overlay_text(text: str, reflow_text: bool) -> tuple[list[list[str]], str, int]:
    details = preprocess_overlay_text_details(text=text, reflow_text=reflow_text)
    return details["paragraphs"], details["script_group"], details["max_chars_per_line"]


def preprocess_overlay_text_details(text: str, reflow_text: bool) -> dict[str, object]:
    normalized = normalize_overlay_text(text)
    script_group = detect_script_group(normalized)
    max_chars_per_line = SCRIPT_CHAR_LIMITS[script_group]
    paragraphs: list[list[str]] = []
    current_paragraph: list[str] = []

    for raw_line in normalized.split("\n"):
        line = collapse_whitespace(raw_line)
        if not line:
            if current_paragraph:
                paragraphs.append(current_paragraph)
                current_paragraph = []
            continue
        if not reflow_text or measure_text_units(line) <= max_chars_per_line:
            current_paragraph.append(line)
            continue
        if script_group == "cjk" or (" " not in line and script_group != "latin"):
            current_paragraph.extend(wrap_unspaced_text(line, max_chars_per_line))
            continue
        current_paragraph.extend(wrap_word_based_text(line, max_chars_per_line))

    if current_paragraph:
        paragraphs.append(current_paragraph)

    if not paragraphs:
        paragraphs = [[""]]
    return {
        "normalized_text": normalized,
        "script_group": script_group,
        "max_chars_per_line": max_chars_per_line,
        "paragraphs": paragraphs,
    }


def parse_srt_timestamp(value: str) -> int:
    hours, minutes, seconds_and_ms = value.split(":", 2)
    seconds, milliseconds = re.split(r"[,.]", seconds_and_ms)
    return (
        int(hours) * 3_600_000
        + int(minutes) * 60_000
        + int(seconds) * 1_000
        + int(milliseconds)
    )


def parse_srt(text: str) -> list[SubtitleCue]:
    normalized = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    cues: list[SubtitleCue] = []
    blocks = re.split(r"\n{2,}", normalized)
    for fallback_index, block in enumerate(blocks, start=1):
        lines = [line.rstrip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        cue_index = fallback_index
        if lines[0].strip().isdigit():
            cue_index = int(lines[0].strip())
            lines = lines[1:]
        if len(lines) < 2:
            raise ValueError(f"Malformed SRT cue around block {fallback_index}.")
        timestamp_match = SRT_TIMESTAMP_RE.fullmatch(lines[0].strip())
        if not timestamp_match:
            raise ValueError(f"Malformed SRT timestamp around block {fallback_index}.")
        cue_text = "\n".join(lines[1:])
        cues.append(
            SubtitleCue(
                index=cue_index,
                start_ms=parse_srt_timestamp(timestamp_match.group("start")),
                end_ms=parse_srt_timestamp(timestamp_match.group("end")),
                text=cue_text,
            )
        )
    return cues


def ms_to_ass_time(milliseconds: int) -> str:
    hours = milliseconds // 3_600_000
    remainder = milliseconds % 3_600_000
    minutes = remainder // 60_000
    remainder %= 60_000
    seconds = remainder // 1_000
    centiseconds = round((remainder % 1_000) / 10)
    if centiseconds == 100:
        centiseconds = 0
        seconds += 1
    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        hours += 1
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def ass_escape_text(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def build_ass_dialogue_override_block(style: AssStyleConfig, anchor_x: int, positioned_y: int) -> str:
    tags = [
        f"\\an{DEFAULT_ALIGNMENT}",
        f"\\q{style.wrap_style}",
        f"\\pos({anchor_x},{positioned_y})",
    ]
    if DEFAULT_ASS_WEIGHT_OVERRIDE is not None:
        tags.append(DEFAULT_ASS_WEIGHT_TAG)
    return "{" + "".join(tags) + "}"


def build_ass_style_config(
    playres_x: int,
    playres_y: int,
    overlay_position_pct: float,
) -> AssStyleConfig:
    scale_factor = playres_x / REFERENCE_WIDTH
    font_size = max(1, round(DEFAULT_BASE_FONT_SIZE * scale_factor))
    return AssStyleConfig(
        playres_x=playres_x,
        playres_y=playres_y,
        overlay_position_pct=overlay_position_pct,
        fontname=DEFAULT_FONTNAME,
        fontsize=font_size,
        spacing=round(DEFAULT_BASE_SPACING * scale_factor, 2),
        line_height=max(font_size, round(font_size * DEFAULT_LINE_HEIGHT_RATIO)),
        paragraph_gap=max(1, round(font_size * DEFAULT_PARAGRAPH_GAP_RATIO)),
        outline=max(DEFAULT_MIN_OUTLINE, round(font_size * DEFAULT_OUTLINE_RATIO)),
        wrap_style=DEFAULT_WRAPSTYLE,
    )


def build_ass_style_line(style: AssStyleConfig) -> str:
    return ",".join(
        [
            "Overlay",
            style.fontname,
            str(style.fontsize),
            DEFAULT_PRIMARY_COLOUR,
            DEFAULT_SECONDARY_COLOUR,
            DEFAULT_OUTLINE_COLOUR,
            DEFAULT_BACK_COLOUR,
            str(DEFAULT_BOLD),
            str(DEFAULT_ITALIC),
            str(DEFAULT_UNDERLINE),
            str(DEFAULT_STRIKEOUT),
            str(DEFAULT_SCALE_X),
            str(DEFAULT_SCALE_Y),
            f"{style.spacing:.2f}",
            str(DEFAULT_ANGLE),
            str(DEFAULT_BORDERSTYLE),
            str(style.outline),
            str(DEFAULT_SHADOW),
            str(DEFAULT_ALIGNMENT),
            str(DEFAULT_MARGIN_L),
            str(DEFAULT_MARGIN_R),
            str(DEFAULT_MARGIN_V),
            str(DEFAULT_ENCODING),
        ]
    )


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sidecar_path_for_output(output_path: Path, suffix: str) -> Path:
    return output_path.with_name(f"{output_path.stem}{suffix}")


def write_text_file(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def write_json_file(path: Path, payload: dict[str, object]) -> None:
    write_text_file(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def build_ass_dialogue_lines_with_logs(
    cue: SubtitleCue,
    style: AssStyleConfig,
    reflow_text: bool,
) -> tuple[list[str], dict[str, object]]:
    preprocessing = preprocess_overlay_text_details(text=cue.text, reflow_text=reflow_text)
    paragraphs = preprocessing["paragraphs"]

    assert isinstance(paragraphs, list)
    normalized_text = preprocessing["normalized_text"]
    script_group = preprocessing["script_group"]
    max_chars_per_line = preprocessing["max_chars_per_line"]

    flattened_lines: list[str] = []
    offsets: list[float] = []
    cursor = 0.0
    first_line = True

    for paragraph_index, paragraph in enumerate(paragraphs):
        for line_index, line in enumerate(paragraph):
            if not first_line:
                cursor += style.line_height
                if line_index == 0 and paragraph_index > 0:
                    cursor += style.paragraph_gap
            flattened_lines.append(line)
            offsets.append(cursor)
            first_line = False

    if not flattened_lines:
        return [], {
            "cue_index": cue.index,
            "start_ms": cue.start_ms,
            "end_ms": cue.end_ms,
            "original_text": cue.text,
            "normalized_text": normalized_text,
            "script_group": script_group,
            "max_chars_per_line": max_chars_per_line,
            "paragraphs": paragraphs,
            "positioned_lines": [],
        }

    anchor_x = round(style.playres_x / 2)
    anchor_y = round(style.playres_y * (style.overlay_position_pct / 100))
    center_shift = anchor_y - (offsets[-1] / 2.0)

    start_time = ms_to_ass_time(cue.start_ms)
    end_time = ms_to_ass_time(cue.end_ms)
    dialogues: list[str] = []
    positioned_lines: list[dict[str, object]] = []
    if len(flattened_lines) != len(offsets):
        raise ValueError("Subtitle layout line/offset count mismatch")
    for line, offset in zip(flattened_lines, offsets):
        positioned_y = int(round(center_shift + offset))
        dialogues.append(
            "Dialogue: 0,"
            f"{start_time},{end_time},Overlay,,0,0,0,,"
            f"{build_ass_dialogue_override_block(style, anchor_x, positioned_y)}"
            f"{ass_escape_text(line)}"
        )
        positioned_lines.append(
            {
                "text": line,
                "offset_y": round(offset, 2),
                "positioned_y": positioned_y,
            }
        )

    return dialogues, {
        "cue_index": cue.index,
        "start_ms": cue.start_ms,
        "end_ms": cue.end_ms,
        "start_ass": start_time,
        "end_ass": end_time,
        "original_text": cue.text,
        "normalized_text": normalized_text,
        "script_group": script_group,
        "max_chars_per_line": max_chars_per_line,
        "paragraphs": paragraphs,
        "anchor_x": anchor_x,
        "anchor_y": anchor_y,
        "center_shift": round(center_shift, 2),
        "positioned_lines": positioned_lines,
    }


def build_ass_dialogue_lines(
    cue: SubtitleCue,
    style: AssStyleConfig,
    reflow_text: bool,
) -> list[str]:
    dialogues, _log_details = build_ass_dialogue_lines_with_logs(
        cue=cue,
        style=style,
        reflow_text=reflow_text,
    )
    return dialogues


def build_ass_document_with_logs(
    cues: list[SubtitleCue],
    style: AssStyleConfig,
    reflow_text: bool,
) -> tuple[str, list[dict[str, object]]]:
    script_lines = [
        "[Script Info]",
        "; Generated by render_subtitles_with_default_style.py",
        "ScriptType: v4.00+",
        f"PlayResX: {style.playres_x}",
        f"PlayResY: {style.playres_y}",
        f"WrapStyle: {style.wrap_style}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: {build_ass_style_line(style)}",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    cue_logs: list[dict[str, object]] = []

    for cue in cues:
        dialogue_lines, cue_log = build_ass_dialogue_lines_with_logs(
            cue=cue,
            style=style,
            reflow_text=reflow_text,
        )
        script_lines.extend(dialogue_lines)
        cue_logs.append(cue_log)

    return "\n".join(script_lines) + "\n", cue_logs


def build_ass_document(
    cues: list[SubtitleCue],
    style: AssStyleConfig,
    reflow_text: bool,
) -> str:
    ass_document, _cue_logs = build_ass_document_with_logs(
        cues=cues,
        style=style,
        reflow_text=reflow_text,
    )
    return ass_document


def probe_video_metadata(path: Path) -> VideoMetadata:
    output = subprocess.check_output(
        [
            FFPROBE_BIN,
            "-v",
            "error",
            "-show_entries",
            "stream=width,height:format=duration",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    payload = json.loads(output)
    streams = payload.get("streams", [])
    if not streams:
        raise ValueError(f"No video stream metadata found for {path}.")
    stream = next(
        (
            candidate
            for candidate in streams
            if str(candidate.get("codec_type", "")).lower() == "video"
            or ("width" in candidate and "height" in candidate)
        ),
        None,
    )
    if stream is None:
        raise ValueError(f"No video stream metadata found for {path}.")
    return VideoMetadata(
        width=int(stream["width"]),
        height=int(stream["height"]),
        duration=float(payload["format"]["duration"]),
    )


def build_subtitles_filter(
    subtitles_path: Path,
    fontsdir_path: Path | None,
    force_style: str | None,
    append_video_filters: str | None = None,
) -> str:
    filter_value = f"subtitles=filename='{subtitles_path.as_posix()}'"
    if fontsdir_path is not None:
        filter_value += f":fontsdir='{fontsdir_path.as_posix()}'"
    if force_style:
        filter_value += f":force_style='{force_style}'"
    if append_video_filters:
        extra_filters = append_video_filters.strip().lstrip(",")
        if extra_filters:
            filter_value = f"{filter_value},{extra_filters}"
    return filter_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--subtitles")
    parser.add_argument("--out")
    parser.add_argument("--fontsdir", default=DEFAULT_FONTSDIR)
    parser.add_argument("--overlay-position-pct", type=float, default=DEFAULT_OVERLAY_POSITION_PCT)
    parser.add_argument(
        "--reflow-text",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Reflow manual SRT cue text to the shared per-script char limits.",
    )
    parser.add_argument("--write-resolved-ass")
    parser.add_argument("--log-json-path")
    parser.add_argument("--ffmpeg-log-path")
    parser.add_argument("--preset", default=DEFAULT_PRESET)
    parser.add_argument("--crf", default=DEFAULT_CRF)
    parser.add_argument("--video-codec", default=DEFAULT_VIDEO_CODEC)
    parser.add_argument("--audio-codec", default="copy")
    parser.add_argument("--movflags", default=DEFAULT_MOVFLAGS)
    parser.add_argument("--force-style")
    parser.add_argument("--append-video-filters")
    parser.add_argument("--trim-seconds", type=float)
    parser.add_argument("--stream-loop", type=int)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--drop-audio", action="store_true")
    parser.add_argument("--loglevel", default="error")
    parser.add_argument("--print-style", action="store_true")
    return parser.parse_args()


def fail(message: str, **extra: object) -> int:
    payload: dict[str, object] = {"status": "error", "error": message}
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False))
    return 1


def shared_style_payload(style: AssStyleConfig) -> dict[str, object]:
    return {
        "style_config_path": str(STYLE_CONFIG_PATH),
        "reference_width": REFERENCE_WIDTH,
        "playres_x": style.playres_x,
        "playres_y": style.playres_y,
        "overlay_position_pct": style.overlay_position_pct,
        "font_name": style.fontname,
        "base_font_size": DEFAULT_BASE_FONT_SIZE,
        "font_size": style.fontsize,
        "base_spacing": DEFAULT_BASE_SPACING,
        "spacing": style.spacing,
        "line_height_ratio": DEFAULT_LINE_HEIGHT_RATIO,
        "line_height": style.line_height,
        "paragraph_gap_ratio": DEFAULT_PARAGRAPH_GAP_RATIO,
        "paragraph_gap": style.paragraph_gap,
        "outline_ratio": DEFAULT_OUTLINE_RATIO,
        "min_outline": DEFAULT_MIN_OUTLINE,
        "outline": style.outline,
        "wrap_style": style.wrap_style,
        "font_weight": {
            "requested_label": DEFAULT_FONT_WEIGHT_LABEL,
            "requested_value": DEFAULT_FONT_WEIGHT_VALUE,
            "ass_override_value": DEFAULT_ASS_WEIGHT_OVERRIDE,
            "ass_override_tag": DEFAULT_ASS_WEIGHT_TAG or None,
            "resolved_weight": DEFAULT_FONT_WEIGHT_LABEL,
        },
        "stroke": {
            "border_style": DEFAULT_BORDERSTYLE,
            "outline": style.outline,
            "outline_colour": DEFAULT_OUTLINE_COLOUR,
            "shadow": DEFAULT_SHADOW,
        },
        "max_chars_per_line": SCRIPT_CHAR_LIMITS,
    }


def main() -> int:
    args = parse_args()

    preview_style = build_ass_style_config(
        playres_x=REFERENCE_WIDTH,
        playres_y=1920,
        overlay_position_pct=args.overlay_position_pct,
    )

    if args.print_style:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "ffmpeg_bin": FFMPEG_BIN,
                    "ffprobe_bin": FFPROBE_BIN,
                    "style_config_path": str(STYLE_CONFIG_PATH),
                    "font_file": DEFAULT_FONTFILE,
                    "fontsdir": str(Path(args.fontsdir).expanduser().resolve()) if args.fontsdir else None,
                    "overlay_position_pct": args.overlay_position_pct,
                    "reflow_text": args.reflow_text,
                    "shared_style": shared_style_payload(preview_style),
                    "force_style": args.force_style,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if not args.input or not args.subtitles or not args.out:
        return fail("Missing required flags: --input, --subtitles, and --out are required unless --print-style is used.")

    input_path = Path(args.input).expanduser().resolve()
    subtitles_path = Path(args.subtitles).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    fontsdir_path = Path(args.fontsdir).expanduser().resolve() if args.fontsdir else None
    default_fontfile_path = Path(DEFAULT_FONTFILE).expanduser().resolve()
    resolved_ass_out_path = (
        Path(args.write_resolved_ass).expanduser().resolve()
        if args.write_resolved_ass
        else sidecar_path_for_output(out_path, ".resolved.ass")
    )
    log_json_path = (
        Path(args.log_json_path).expanduser().resolve()
        if args.log_json_path
        else sidecar_path_for_output(out_path, ".overlay-log.json")
    )
    ffmpeg_log_path = (
        Path(args.ffmpeg_log_path).expanduser().resolve()
        if args.ffmpeg_log_path
        else sidecar_path_for_output(out_path, ".ffmpeg.log")
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_ass_out_path.parent.mkdir(parents=True, exist_ok=True)
    log_json_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_log_path.parent.mkdir(parents=True, exist_ok=True)

    render_payload: dict[str, object] = {
        "status": "running",
        "started_at_utc": utc_timestamp(),
        "cwd": str(Path.cwd()),
        "argv": sys.argv,
        "style_config_path": str(STYLE_CONFIG_PATH),
        "input": str(input_path),
        "subtitles": str(subtitles_path),
        "resolved_subtitles": str(resolved_ass_out_path),
        "font_file": str(default_fontfile_path),
        "fontsdir": str(fontsdir_path) if fontsdir_path is not None else None,
        "output": str(out_path),
        "ffmpeg_bin": FFMPEG_BIN,
        "ffprobe_bin": FFPROBE_BIN,
        "overlay_position_pct": args.overlay_position_pct,
        "reflow_text": args.reflow_text,
        "force_style": args.force_style,
        "append_video_filters": args.append_video_filters,
        "trim_seconds": args.trim_seconds,
        "stream_loop": args.stream_loop,
        "fps": args.fps,
        "drop_audio": args.drop_audio,
        "log_path": str(log_json_path),
        "ffmpeg_log_path": str(ffmpeg_log_path),
    }
    write_json_file(log_json_path, render_payload)

    def finish(status: str, **extra: object) -> int:
        payload = dict(render_payload)
        payload.update(extra)
        payload["status"] = status
        payload["completed_at_utc"] = utc_timestamp()
        write_json_file(log_json_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if status == "ok" else 1

    if not input_path.exists():
        return finish("error", error="Input video not found.", path=str(input_path))
    if not subtitles_path.exists():
        return finish("error", error="Subtitle file not found.", path=str(subtitles_path))
    if not default_fontfile_path.exists():
        return finish("error", error="Default font file not found.", path=str(default_fontfile_path))
    if fontsdir_path is not None and not fontsdir_path.exists():
        return finish("error", error="Font directory not found.", path=str(fontsdir_path))

    try:
        metadata = probe_video_metadata(input_path)
    except (ValueError, subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as error:
        return finish("error", error="Unable to probe video metadata.", details=str(error), path=str(input_path))

    shared_style = build_ass_style_config(
        playres_x=metadata.width,
        playres_y=metadata.height,
        overlay_position_pct=args.overlay_position_pct,
    )
    render_payload.update(
        {
            "duration": metadata.duration,
            "video_width": metadata.width,
            "video_height": metadata.height,
            "shared_style": shared_style_payload(shared_style),
        }
    )
    write_json_file(log_json_path, render_payload)

    cmd: list[str] = []
    cue_logs: list[dict[str, object]] = []
    filter_value = ""
    ffmpeg_combined_output = ""
    render_mode = "ass_passthrough" if subtitles_path.suffix.lower() == ".ass" else "srt_to_ass"

    try:
        with tempfile.TemporaryDirectory(prefix="ffmpeg-text-overlay-style-"):
            resolved_subtitles_path = resolved_ass_out_path
            if subtitles_path.suffix.lower() == ".ass":
                if subtitles_path != resolved_ass_out_path:
                    shutil.copyfile(subtitles_path, resolved_ass_out_path)
                else:
                    resolved_ass_out_path.write_text(
                        subtitles_path.read_text(encoding="utf-8"),
                        encoding="utf-8",
                    )
            else:
                cues = parse_srt(subtitles_path.read_text(encoding="utf-8-sig"))
                ass_document, cue_logs = build_ass_document_with_logs(
                    cues=cues,
                    style=shared_style,
                    reflow_text=args.reflow_text,
                )
                write_text_file(resolved_ass_out_path, ass_document)
                render_payload["cue_count"] = len(cues)

            filter_value = build_subtitles_filter(
                subtitles_path=resolved_subtitles_path,
                fontsdir_path=fontsdir_path,
                force_style=args.force_style,
                append_video_filters=args.append_video_filters,
            )

            cmd = [FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", args.loglevel]
            if args.stream_loop is not None:
                cmd.extend(["-stream_loop", str(args.stream_loop)])
            cmd.extend(["-i", str(input_path)])
            if args.trim_seconds is not None:
                cmd.extend(["-t", str(args.trim_seconds)])
            cmd.extend(["-vf", filter_value])
            if args.fps is not None:
                cmd.extend(["-r", str(args.fps)])
            cmd.extend(
                [
                    "-c:v",
                    args.video_codec,
                    "-preset",
                    args.preset,
                    "-crf",
                    str(args.crf),
                ]
            )
            if args.drop_audio:
                cmd.append("-an")
            else:
                cmd.extend(["-c:a", args.audio_codec])
            cmd.extend(["-movflags", args.movflags, str(out_path)])

            ffmpeg_result = subprocess.run(cmd, text=True, capture_output=True)
            ffmpeg_combined_output = "\n".join(
                chunk for chunk in (ffmpeg_result.stdout, ffmpeg_result.stderr) if chunk
            )
            write_text_file(ffmpeg_log_path, ffmpeg_combined_output)
            if ffmpeg_result.returncode != 0:
                return finish(
                    "error",
                    error="ffmpeg render failed.",
                    details=f"ffmpeg exited with code {ffmpeg_result.returncode}",
                    render_mode=render_mode,
                    subtitle_input_format=subtitles_path.suffix.lower(),
                    filter_value=filter_value,
                    command=cmd,
                    cue_logs=cue_logs,
                )
    except (ValueError, OSError) as error:
        if ffmpeg_combined_output:
            write_text_file(ffmpeg_log_path, ffmpeg_combined_output)
        return finish(
            "error",
            error="ffmpeg render failed.",
            details=str(error),
            render_mode=render_mode,
            subtitle_input_format=subtitles_path.suffix.lower(),
            filter_value=filter_value or None,
            command=cmd or None,
            cue_logs=cue_logs,
        )

    return finish(
        "ok",
        render_mode=render_mode,
        subtitle_input_format=subtitles_path.suffix.lower(),
        filter_value=filter_value,
        command=cmd,
        cue_logs=cue_logs,
    )


if __name__ == "__main__":
    raise SystemExit(main())
