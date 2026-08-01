#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from style_contract_test_utils import (
    compute_expected_style,
    compute_positioned_lines,
    load_style_contract,
    resolve_test_background_clip,
    wrap_word_based_text,
)

SKILL_ROOT = Path(__file__).resolve().parents[1]
HELPER = SKILL_ROOT / "scripts" / "render_subtitles_with_default_style.py"
STYLE_CONFIG = (SKILL_ROOT / "ressources" / "text-overlay-style.json").resolve()
STYLE_CONTRACT = load_style_contract(STYLE_CONFIG)
LONG_TEXT = "je voudrais un petit ricard dans un verre a ballon s'il vous plait"
TEST_BACKGROUND_CLIP = resolve_test_background_clip()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifact-dir",
        help="Optional directory where the rendered video, sidecars, and preview frame should be kept.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    style_result = run(["python3", str(HELPER), "--print-style"])
    style_payload = json.loads(style_result.stdout)
    ffmpeg_bin = style_payload["ffmpeg_bin"]

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir).expanduser().resolve()
        artifact_dir.mkdir(parents=True, exist_ok=True)
    else:
        artifact_dir = Path(tempfile.mkdtemp(prefix="ffmpeg-text-overlay-style-long-text-")).resolve()

    subtitles_path = artifact_dir / "subtitles.srt"
    output_path = (artifact_dir / "output.mp4").resolve()
    resolved_ass_path = (artifact_dir / "resolved.ass").resolve()
    preview_frame_path = (artifact_dir / "preview.png").resolve()

    subtitles_path.write_text(
        f"1\n00:00:00,000 --> 00:00:08,000\n{LONG_TEXT}\n",
        encoding="utf-8",
    )

    render_result = run(
            [
                "python3",
                str(HELPER),
                "--input",
                str(TEST_BACKGROUND_CLIP),
                "--subtitles",
                str(subtitles_path),
                "--out",
                str(output_path),
            "--write-resolved-ass",
            str(resolved_ass_path),
            "--drop-audio",
        ]
    )
    render_payload = json.loads(render_result.stdout)
    overlay_log_path = Path(render_payload["log_path"]).resolve()
    ffmpeg_log_path = Path(render_payload["ffmpeg_log_path"]).resolve()
    overlay_log_payload = json.loads(overlay_log_path.read_text(encoding="utf-8"))
    cue_log = render_payload["cue_logs"][0]
    positioned_lines = cue_log["positioned_lines"]

    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert resolved_ass_path.exists()
    assert resolved_ass_path.stat().st_size > 0
    assert overlay_log_path.exists()
    assert ffmpeg_log_path.exists()
    assert overlay_log_payload["status"] == "ok"
    assert Path(render_payload["output"]).resolve() == output_path
    assert render_payload["duration"] == 8.0
    assert render_payload["video_width"] == 720
    assert render_payload["video_height"] == 1280
    assert render_payload["cue_count"] == 1

    expected_style = compute_expected_style(STYLE_CONTRACT, playres_x=720, playres_y=1280)
    expected_paragraphs = [
        wrap_word_based_text(LONG_TEXT, int(expected_style["chars_per_line"]["latin"]))
    ]
    expected_positions = compute_positioned_lines(
        playres_x=720,
        playres_y=1280,
        overlay_position_pct=float(expected_style["overlay_position_pct"]),
        line_height=int(expected_style["line_height"]),
        paragraph_gap=int(expected_style["paragraph_gap"]),
        paragraphs=expected_paragraphs,
    )

    shared_style = render_payload["shared_style"]
    assert shared_style["font_name"] == expected_style["font_name"]
    assert shared_style["font_size"] == expected_style["font_size"]
    assert shared_style["outline"] == expected_style["outline"]
    assert shared_style["wrap_style"] == expected_style["wrap_style"]
    assert abs(shared_style["spacing"] - float(expected_style["spacing"])) < 0.001
    assert "style_line" not in shared_style
    assert "ass_bold" not in shared_style["font_weight"]
    assert "style_weight" not in shared_style["font_weight"]
    assert shared_style["font_weight"]["requested_label"] == expected_style["font_weight_label"]
    assert shared_style["font_weight"]["requested_value"] == expected_style["font_weight_value"]
    assert shared_style["font_weight"]["ass_override_value"] == expected_style["font_ass_weight_override"]
    assert shared_style["font_weight"]["ass_override_tag"] == expected_style["font_ass_weight_tag"]

    assert cue_log["script_group"] == "latin"
    assert cue_log["max_chars_per_line"] == expected_style["chars_per_line"]["latin"]
    assert cue_log["paragraphs"] == expected_paragraphs
    assert cue_log["anchor_x"] == expected_positions["anchor_x"]
    assert cue_log["anchor_y"] == expected_positions["anchor_y"]
    assert cue_log["center_shift"] == expected_positions["center_shift"]
    assert [line["positioned_y"] for line in positioned_lines] == expected_positions["positioned_y"]
    assert [line["text"] for line in positioned_lines] == expected_positions["flattened_lines"]
    assert overlay_log_payload["cue_logs"][0]["paragraphs"] == expected_paragraphs

    ass_document = resolved_ass_path.read_text(encoding="utf-8")
    assert "PlayResX: 720" in ass_document
    assert "PlayResY: 1280" in ass_document
    assert f"Style: Overlay,{expected_style['font_name']},{expected_style['font_size']}" in ass_document
    expected_weight_tag = expected_style["font_ass_weight_tag"] or ""
    for positioned_y, text in zip(expected_positions["positioned_y"], expected_positions["flattened_lines"], strict=True):
        assert (
            rf"{{\an5\q{expected_style['wrap_style']}\pos({expected_positions['anchor_x']},{positioned_y})"
            rf"{expected_weight_tag}}}{text}"
        ) in ass_document

    run(
        [
            ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "4",
            "-i",
            str(output_path),
            "-frames:v",
            "1",
            str(preview_frame_path),
        ]
    )
    assert preview_frame_path.exists()
    assert preview_frame_path.stat().st_size > 0

    print(
        json.dumps(
            {
                "status": "ok",
                "text": LONG_TEXT,
                "background_clip": str(TEST_BACKGROUND_CLIP),
                "artifact_dir": str(artifact_dir),
                "output_path": str(output_path),
                "resolved_ass_path": str(resolved_ass_path),
                "preview_frame_path": str(preview_frame_path),
                "verified": [
                    "portrait render uses the shared France background clip",
                    "long portrait overlay render completes and writes output plus sidecar files",
                    "latin text reflows to the expected three-line shared layout at 720x1280",
                    "preview frame extraction succeeds from the rendered output and is kept for sharing",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
