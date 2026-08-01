#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from style_contract_test_utils import compute_expected_style, load_style_contract, wrap_word_based_text

SKILL_ROOT = Path(__file__).resolve().parents[1]
HELPER = SKILL_ROOT / "scripts" / "render_subtitles_with_default_style.py"
STYLE_CONFIG = (SKILL_ROOT / "ressources" / "text-overlay-style.json").resolve()
STYLE_CONTRACT = load_style_contract(STYLE_CONFIG)
EXPECTED_STYLE = compute_expected_style(STYLE_CONTRACT, playres_x=1080, playres_y=1920)


def load_helper_module():
    spec = importlib.util.spec_from_file_location("render_subtitles_with_default_style", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load helper module.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    helper = load_helper_module()
    style = helper.build_ass_style_config(
        playres_x=1080,
        playres_y=1920,
        overlay_position_pct=float(EXPECTED_STYLE["overlay_position_pct"]),
    )
    style_payload = helper.shared_style_payload(style)
    assert style.fontsize == EXPECTED_STYLE["font_size"]
    assert style.outline == EXPECTED_STYLE["outline"]
    assert style.wrap_style == EXPECTED_STYLE["wrap_style"]
    assert abs(style.spacing - float(EXPECTED_STYLE["spacing"])) < 0.001
    assert style.line_height == EXPECTED_STYLE["line_height"]
    assert style.paragraph_gap == EXPECTED_STYLE["paragraph_gap"]
    assert Path(style_payload["style_config_path"]).resolve() == STYLE_CONFIG
    assert style_payload["reference_width"] == EXPECTED_STYLE["reference_width"]
    assert style_payload["font_name"] == EXPECTED_STYLE["font_name"]
    assert "style_line" not in style_payload
    assert "ass_bold" not in style_payload["font_weight"]
    assert "style_weight" not in style_payload["font_weight"]
    assert style_payload["font_weight"]["requested_label"] == EXPECTED_STYLE["font_weight_label"]
    assert style_payload["font_weight"]["requested_value"] == EXPECTED_STYLE["font_weight_value"]
    assert style_payload["font_weight"]["ass_override_value"] == EXPECTED_STYLE["font_ass_weight_override"]
    assert style_payload["font_weight"]["ass_override_tag"] == EXPECTED_STYLE["font_ass_weight_tag"]
    assert style_payload["font_weight"]["resolved_weight"] == EXPECTED_STYLE["font_weight_label"]
    assert abs(style_payload["outline_ratio"] - EXPECTED_STYLE["outline_ratio"]) < 0.0001
    assert style_payload["stroke"]["outline"] == EXPECTED_STYLE["outline"]

    wrapped, script_group, max_chars = helper.preprocess_overlay_text(
        "group chat is just us screaming about where we go next",
        reflow_text=True,
    )
    expected_wrapped_lines = wrap_word_based_text(
        "group chat is just us screaming about where we go next",
        max_chars,
    )
    assert script_group == "latin"
    assert max_chars == EXPECTED_STYLE["chars_per_line"]["latin"]
    assert wrapped == [[*expected_wrapped_lines]]

    manual_breaks, _, _ = helper.preprocess_overlay_text(
        "manual line one\nmanual line two",
        reflow_text=True,
    )
    assert manual_breaks == [["manual line one", "manual line two"]]

    paragraph_breaks, _, _ = helper.preprocess_overlay_text(
        "manual line one\n\nmanual line two",
        reflow_text=True,
    )
    assert paragraph_breaks == [["manual line one"], ["manual line two"]]

    screenshot_text = "comment ça je peux aller à Féria de Nîmes\net ne PAS perdre mes potes"
    screenshot_wrapped, _, screenshot_max_chars = helper.preprocess_overlay_text(
        screenshot_text,
        reflow_text=True,
    )
    expected_screenshot_lines = wrap_word_based_text(
        "comment ça je peux aller à Féria de Nîmes",
        screenshot_max_chars,
    )
    assert screenshot_wrapped == [[*expected_screenshot_lines, "et ne PAS perdre mes potes"]]

    screenshot_cue = helper.SubtitleCue(
        index=2,
        start_ms=0,
        end_ms=2500,
        text=screenshot_text,
    )
    _, screenshot_log = helper.build_ass_dialogue_lines_with_logs(
        screenshot_cue,
        style=style,
        reflow_text=True,
    )
    positioned_y = [line["positioned_y"] for line in screenshot_log["positioned_lines"]]
    assert len(positioned_y) == len(screenshot_wrapped[0])
    assert all(
        current - previous == EXPECTED_STYLE["line_height"]
        for previous, current in zip(positioned_y, positioned_y[1:])
    )

    cue = helper.SubtitleCue(
        index=1,
        start_ms=0,
        end_ms=2500,
        text="group chat is just us screaming about where we go next",
    )
    ass_document = helper.build_ass_document([cue], style=style, reflow_text=True)
    assert "PlayResX: 1080" in ass_document
    assert "PlayResY: 1920" in ass_document
    assert f"WrapStyle: {EXPECTED_STYLE['wrap_style']}" in ass_document
    assert f"Style: Overlay,{EXPECTED_STYLE['font_name']},{EXPECTED_STYLE['font_size']}" in ass_document
    assert r"{\an5\q2\pos(540," in ass_document
    if EXPECTED_STYLE["font_ass_weight_tag"] is not None:
        assert EXPECTED_STYLE["font_ass_weight_tag"] in ass_document
    for line in expected_wrapped_lines:
        assert line in ass_document

    print(
        json.dumps(
            {
                "status": "ok",
                "verified": [
                    "reference-derived ASS defaults are resolved at 1080x1920",
                    "short overlay text reflows to the shared latin width from the style contract",
                    "generated ASS contains PlayRes, WrapStyle, and explicit positioned dialogue lines",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
