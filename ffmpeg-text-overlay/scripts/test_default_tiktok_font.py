#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from style_contract_test_utils import (
    compute_expected_style,
    load_style_contract,
    resolve_font_file,
    resolve_test_background_clip,
)

SKILL_ROOT = Path(__file__).resolve().parents[1]
HELPER = SKILL_ROOT / "scripts" / "render_subtitles_with_default_style.py"
STYLE_CONFIG = (SKILL_ROOT / "ressources" / "text-overlay-style.json").resolve()
STYLE_CONTRACT = load_style_contract(STYLE_CONFIG)
EXPECTED_FONT_FILE = resolve_font_file(STYLE_CONTRACT, STYLE_CONFIG)
EXPECTED_FONTSDIR = EXPECTED_FONT_FILE.parent
EXPECTED_STYLE = compute_expected_style(
    STYLE_CONTRACT,
    playres_x=int(STYLE_CONTRACT["reference_width"]),
    playres_y=1920,
)
TEST_BACKGROUND_CLIP = resolve_test_background_clip()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=True)


def main() -> int:
    style_result = run(["python3", str(HELPER), "--print-style"])
    style_payload = json.loads(style_result.stdout)

    assert Path(style_payload["font_file"]).resolve() == EXPECTED_FONT_FILE
    assert Path(style_payload["style_config_path"]).resolve() == STYLE_CONFIG
    assert Path(style_payload["fontsdir"]).resolve() == EXPECTED_FONTSDIR
    assert style_payload["overlay_position_pct"] == EXPECTED_STYLE["overlay_position_pct"]
    assert style_payload["reflow_text"] is True
    assert style_payload["shared_style"]["font_name"] == EXPECTED_STYLE["font_name"]
    assert style_payload["shared_style"]["font_size"] == EXPECTED_STYLE["font_size"]
    assert abs(style_payload["shared_style"]["outline_ratio"] - EXPECTED_STYLE["outline_ratio"]) < 0.0001
    assert style_payload["shared_style"]["min_outline"] == EXPECTED_STYLE["min_outline"]
    assert style_payload["shared_style"]["outline"] == EXPECTED_STYLE["outline"]
    assert "style_line" not in style_payload["shared_style"]
    assert "ass_bold" not in style_payload["shared_style"]["font_weight"]
    assert "style_weight" not in style_payload["shared_style"]["font_weight"]
    assert style_payload["shared_style"]["font_weight"]["requested_label"] == EXPECTED_STYLE["font_weight_label"]
    assert style_payload["shared_style"]["font_weight"]["requested_value"] == EXPECTED_STYLE["font_weight_value"]
    assert (
        style_payload["shared_style"]["font_weight"]["ass_override_value"]
        == EXPECTED_STYLE["font_ass_weight_override"]
    )
    assert style_payload["shared_style"]["font_weight"]["ass_override_tag"] == EXPECTED_STYLE["font_ass_weight_tag"]
    assert style_payload["shared_style"]["font_weight"]["resolved_weight"] == EXPECTED_STYLE["font_weight_label"]
    assert style_payload["shared_style"]["wrap_style"] == EXPECTED_STYLE["wrap_style"]

    ffmpeg_bin = style_payload["ffmpeg_bin"]
    with tempfile.TemporaryDirectory(prefix="ffmpeg-text-overlay-style-smoke-") as tmpdir:
        tmp_path = Path(tmpdir)
        subtitles_path = tmp_path / "subtitles.srt"
        output_path = tmp_path / "output.mp4"
        resolved_ass_path = tmp_path / "resolved.ass"

        subtitles_path.write_text(
            "1\n00:00:00,000 --> 00:00:00,900\nTikTok Sans smoke test\n",
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
                "--loglevel",
                "debug",
            ]
        )
        render_payload = json.loads(render_result.stdout)
        ffmpeg_log_path = Path(render_payload["ffmpeg_log_path"]).resolve()
        overlay_log_path = Path(render_payload["log_path"]).resolve()
        combined_logs = ffmpeg_log_path.read_text(encoding="utf-8")

        assert output_path.exists()
        assert output_path.stat().st_size > 0
        assert resolved_ass_path.exists()
        assert ffmpeg_log_path.exists()
        assert overlay_log_path.exists()
        assert Path(render_payload["resolved_subtitles"]).resolve() == resolved_ass_path.resolve()
        if EXPECTED_STYLE["font_ass_weight_tag"] is not None:
            assert EXPECTED_STYLE["font_ass_weight_tag"] in resolved_ass_path.read_text(encoding="utf-8")
        assert "fontselect:" in combined_logs
        assert str(EXPECTED_STYLE["font_name"]) in combined_logs
        assert EXPECTED_FONT_FILE.stem in combined_logs

    print(
        json.dumps(
            {
                "status": "ok",
                "background_clip": str(TEST_BACKGROUND_CLIP),
                "font_file": str(EXPECTED_FONT_FILE),
                "fontsdir": str(EXPECTED_FONTSDIR),
                "font_name": str(EXPECTED_STYLE["font_name"]),
                "verified": [
                    "smoke render uses the shared France background clip",
                    "helper default style points at bundled TikTok Sans variable font asset",
                    "resolved ASS carries the shared semibold weight override",
                    "ffmpeg render completed successfully",
                    "libass fontselect log resolved the shared TikTok Sans font file",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
