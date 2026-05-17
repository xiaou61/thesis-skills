#!/usr/bin/env python3
"""Generate machine-readable template rule overrides from extracted .docx facts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


def section_preview(section: dict[str, Any]) -> str:
    header_text = " ".join(
        " ".join(item.get("text", []))
        for item in section.get("headers", [])
        if isinstance(item, dict)
    ).strip()
    footer_text = " ".join(
        " ".join(item.get("text", []))
        for item in section.get("footers", [])
        if isinstance(item, dict)
    ).strip()
    return " | ".join(part for part in [header_text, footer_text] if part)


def get_section_paragraph_samples(profile: dict[str, Any], section_index: int) -> list[str]:
    ordered = profile.get("paragraph_usage", {}).get("ordered_paragraph_samples", []) or []
    return [
        str(item.get("text", "")).strip()
        for item in ordered
        if isinstance(item, dict) and int(item.get("section_index", 0) or 0) == section_index and str(item.get("text", "")).strip()
    ]


def detect_first_page_number_section(profile: dict[str, Any]) -> int | None:
    sections = profile.get("sections", []) or []
    for section in sections:
        if not isinstance(section, dict):
            continue
        page_number = section.get("page_number", {}) or {}
        if page_number.get("start") is not None or page_number.get("format") is not None:
            index = section.get("index")
            return int(index) if index is not None else None
    return None


def detect_first_role_section(section_rules: list[dict[str, Any]], role_names: set[str]) -> int | None:
    for item in section_rules:
        if str(item.get("role_guess", "")) in role_names:
            return int(item.get("section_index", 0) or 0)
    return None


def guess_section_role(
    profile: dict[str, Any],
    section: dict[str, Any],
    index: int,
    total: int,
    toc_detected: bool,
) -> tuple[str, str]:
    preview = section_preview(section)
    section_paragraphs = get_section_paragraph_samples(profile, index)[:20]
    combined_text = " ".join([preview, *section_paragraphs]).strip()
    compact = combined_text.replace(" ", "").lower()
    leading_text = "".join(section_paragraphs[:8]).replace(" ", "").lower()

    if any(token in compact for token in ("目录", "contents")):
        return "table_of_contents", "section text contains TOC-like markers"
    if any(token in compact for token in ("摘要", "abstract", "诚信", "声明", "原创性")):
        return "front_matter", "section text contains front-matter markers"
    if any(token in compact for token in ("附录", "appendix", "参考文献", "致谢")):
        return "back_matter", "section text contains appendix/back-matter markers"
    if any(token in leading_text for token in ("第1章", "第一章", "引言", "绪论", "前言", "正文")):
        return "body_or_unknown", "leading section text contains body-opening markers"
    if re.search(r"(第[0-9一二三四五六七八九十]+章|^[1-9][0-9]*\s)", " ".join(section_paragraphs), re.MULTILINE):
        return "body_or_unknown", "section paragraphs contain chapter-like headings"
    if index == 1 and total > 1 and not toc_detected:
        return "front_or_cover", "first section in a multi-section template often hosts cover/front matter"
    if index == total and total > 1:
        return "body_or_back_matter", "last section may be body continuation or appendix"
    return "body_or_unknown", "no stable role marker detected"


def infer_heading_levels(profile: dict[str, Any]) -> list[dict[str, Any]]:
    style_index = {item.get("style_id"): item for item in profile.get("styles", []) if isinstance(item, dict)}
    style_counts = profile.get("paragraph_usage", {}).get("style_counts", [])
    heading_samples = profile.get("paragraph_usage", {}).get("heading_candidates", [])

    by_style: dict[str, dict[str, Any]] = {}
    for sample in heading_samples:
        style_id = sample.get("style_id")
        if not style_id:
            continue
        bucket = by_style.setdefault(
            style_id,
            {
                "style_id": style_id,
                "style_name": sample.get("style_name", style_id),
                "sample_texts": [],
            },
        )
        if sample.get("text"):
            bucket["sample_texts"].append(sample["text"])

    count_map = {item.get("style_id"): item.get("count", 0) for item in style_counts if isinstance(item, dict)}
    results = []
    for style_id, payload in by_style.items():
        style_meta = style_index.get(style_id, {})
        texts = payload["sample_texts"]
        likely_level = "unknown"
        reason = "insufficient heading markers"
        if any(re.match(r"^第[0-9一二三四五六七八九十]+章", text) for text in texts):
            likely_level = "chapter_title"
            reason = "sample text matches Chinese chapter-title pattern"
        elif any(re.match(r"^[0-9]+\.[0-9]+\.[0-9]+", text) for text in texts):
            likely_level = "heading_level_3"
            reason = "sample text matches 1.1.1-style numbering"
        elif any(re.match(r"^[0-9]+\.[0-9]+", text) for text in texts):
            likely_level = "heading_level_2"
            reason = "sample text matches 1.1-style numbering"
        elif any(re.match(r"^[0-9]+", text) for text in texts):
            likely_level = "heading_level_1"
            reason = "sample text matches top-level numeric heading"
        elif str(style_meta.get("name", "")).lower().startswith("heading 1"):
            likely_level = "heading_level_1_or_chapter"
            reason = "style name is Heading 1 but sample text is not conclusive"
        elif str(style_meta.get("name", "")).lower().startswith("heading 2"):
            likely_level = "heading_level_2"
            reason = "style name is Heading 2"
        elif str(style_meta.get("name", "")).lower().startswith("heading 3"):
            likely_level = "heading_level_3"
            reason = "style name is Heading 3"
        elif any(token in str(style_meta.get("name", "")) for token in ("一级标题", "二级标题", "三级标题")):
            name = str(style_meta.get("name", ""))
            if "一级标题" in name:
                likely_level = "heading_level_1"
            elif "二级标题" in name:
                likely_level = "heading_level_2"
            elif "三级标题" in name:
                likely_level = "heading_level_3"
            reason = "style name contains explicit Chinese heading level"

        results.append(
            {
                "style_id": style_id,
                "style_name": payload["style_name"],
                "usage_count": count_map.get(style_id, 0),
                "likely_level": likely_level,
                "reason": reason,
                "font_ascii": style_meta.get("font_ascii"),
                "font_east_asia": style_meta.get("font_east_asia"),
                "font_size_pt": style_meta.get("font_size_pt"),
                "alignment": style_meta.get("alignment"),
                "spacing_before_pt": style_meta.get("spacing_before_pt"),
                "spacing_after_pt": style_meta.get("spacing_after_pt"),
                "line_spacing_pt": style_meta.get("line_spacing_pt"),
                "line_spacing_rule": style_meta.get("line_spacing_rule"),
                "first_line_indent_cm": style_meta.get("first_line_indent_cm"),
                "sample_texts": texts[:5],
            }
        )
    return results


def infer_body_style_candidates(profile: dict[str, Any]) -> list[dict[str, Any]]:
    style_index = {item.get("style_id"): item for item in profile.get("styles", []) if isinstance(item, dict)}
    samples = profile.get("paragraph_usage", {}).get("style_format_samples", []) or []
    counts = {
        item.get("style_id"): item.get("count", 0)
        for item in profile.get("paragraph_usage", {}).get("style_counts", [])
        if isinstance(item, dict)
    }
    candidates: list[dict[str, Any]] = []
    for sample in samples:
        style_id = str(sample.get("style_id", "")).strip()
        if not style_id:
            continue
        style_name = str(sample.get("style_name", "")).strip()
        lowered = style_name.lower()
        if style_id.startswith("TOC") or "toc" in lowered or "目录" in style_name:
            continue
        if lowered.startswith("heading") or "标题" in style_name:
            continue
        if style_id != "Normal" and counts.get(style_id, 0) < 2:
            continue
        style_meta = style_index.get(style_id, {})
        candidates.append(
            {
                "style_id": style_id,
                "style_name": style_name,
                "usage_count": counts.get(style_id, 0),
                "font_ascii": style_meta.get("font_ascii"),
                "font_east_asia": style_meta.get("font_east_asia"),
                "font_size_pt": style_meta.get("font_size_pt"),
                "alignment": style_meta.get("alignment"),
                "spacing_before_pt": style_meta.get("spacing_before_pt"),
                "spacing_after_pt": style_meta.get("spacing_after_pt"),
                "line_spacing_pt": style_meta.get("line_spacing_pt"),
                "line_spacing_rule": style_meta.get("line_spacing_rule"),
                "first_line_indent_cm": style_meta.get("first_line_indent_cm"),
                "sample_text": sample.get("text"),
            }
        )
    candidates.sort(key=lambda item: (0 if item["style_id"] == "Normal" else 1, -int(item.get("usage_count", 0))))
    return candidates[:5]


def infer_reference_style_candidates(profile: dict[str, Any]) -> list[dict[str, Any]]:
    style_index = {item.get("style_id"): item for item in profile.get("styles", []) if isinstance(item, dict)}
    samples = profile.get("paragraph_usage", {}).get("style_format_samples", []) or []
    counts = {
        item.get("style_id"): item.get("count", 0)
        for item in profile.get("paragraph_usage", {}).get("style_counts", [])
        if isinstance(item, dict)
    }
    candidates: list[dict[str, Any]] = []
    for sample in samples:
        style_id = str(sample.get("style_id", "")).strip()
        style_name = str(sample.get("style_name", "")).strip()
        text = str(sample.get("text", "")).strip()
        lowered = style_name.lower()
        if not style_id:
            continue
        looks_like_reference = bool(re.match(r"^\[?\d+\]?", text)) and any(token in text for token in (".", "，", ",")) and len(text) > 12
        if not (
            "reference" in lowered
            or "bibliography" in lowered
            or "参考文献" in style_name
            or looks_like_reference
        ):
            continue
        style_meta = style_index.get(style_id, {})
        candidates.append(
            {
                "style_id": style_id,
                "style_name": style_name,
                "usage_count": counts.get(style_id, 0),
                "font_ascii": style_meta.get("font_ascii"),
                "font_east_asia": style_meta.get("font_east_asia"),
                "font_size_pt": style_meta.get("font_size_pt"),
                "alignment": style_meta.get("alignment"),
                "spacing_before_pt": style_meta.get("spacing_before_pt"),
                "spacing_after_pt": style_meta.get("spacing_after_pt"),
                "line_spacing_pt": style_meta.get("line_spacing_pt"),
                "line_spacing_rule": style_meta.get("line_spacing_rule"),
                "first_line_indent_cm": style_meta.get("first_line_indent_cm"),
                "sample_text": text,
            }
        )
    candidates.sort(key=lambda item: (-int(item.get("usage_count", 0)), item.get("style_name", "")))
    return candidates[:5]


def infer_caption_style_candidates(profile: dict[str, Any]) -> list[dict[str, Any]]:
    style_index = {item.get("style_id"): item for item in profile.get("styles", []) if isinstance(item, dict)}
    samples = profile.get("paragraph_usage", {}).get("style_format_samples", []) or []
    counts = {
        item.get("style_id"): item.get("count", 0)
        for item in profile.get("paragraph_usage", {}).get("style_counts", [])
        if isinstance(item, dict)
    }
    candidates: list[dict[str, Any]] = []
    for sample in samples:
        style_id = str(sample.get("style_id", "")).strip()
        style_name = str(sample.get("style_name", "")).strip()
        text = str(sample.get("text", "")).strip()
        lowered = style_name.lower()
        if not style_id:
            continue
        caption_kind = None
        if "caption" in lowered or "题注" in style_name:
            caption_kind = "generic_caption"
        if text.startswith("图") or text.lower().startswith("figure"):
            caption_kind = "figure_caption"
        elif text.startswith("表") or text.lower().startswith("table"):
            caption_kind = "table_caption"
        if caption_kind is None:
            continue
        style_meta = style_index.get(style_id, {})
        candidates.append(
            {
                "style_id": style_id,
                "style_name": style_name,
                "caption_kind": caption_kind,
                "usage_count": counts.get(style_id, 0),
                "font_ascii": style_meta.get("font_ascii"),
                "font_east_asia": style_meta.get("font_east_asia"),
                "font_size_pt": style_meta.get("font_size_pt"),
                "alignment": style_meta.get("alignment"),
                "spacing_before_pt": style_meta.get("spacing_before_pt"),
                "spacing_after_pt": style_meta.get("spacing_after_pt"),
                "line_spacing_pt": style_meta.get("line_spacing_pt"),
                "line_spacing_rule": style_meta.get("line_spacing_rule"),
                "first_line_indent_cm": style_meta.get("first_line_indent_cm"),
                "sample_text": text,
            }
        )
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(candidates, key=lambda x: (-int(x.get("usage_count", 0)), x.get("style_name", ""))):
        if item["style_id"] in seen:
            continue
        seen.add(item["style_id"])
        deduped.append(item)
    return deduped[:6]


def infer_caption_position_rules(profile: dict[str, Any]) -> dict[str, Any]:
    ordered = profile.get("paragraph_usage", {}).get("ordered_paragraph_samples", []) or []
    rules = {
        "figure_caption_position": "unknown",
        "table_caption_position": "unknown",
    }
    figure_scores = {"above": 0, "below": 0}
    table_scores = {"above": 0, "below": 0}
    for idx, item in enumerate(ordered):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        style_name = str(item.get("style_name", "")).lower()
        if not text:
            continue
        is_caption = "caption" in style_name or text.startswith("图") or text.startswith("表") or text.lower().startswith("figure") or text.lower().startswith("table")
        if not is_caption:
            continue
        prev_style = str(ordered[idx - 1].get("style_name", "")).lower() if idx > 0 and isinstance(ordered[idx - 1], dict) else ""
        next_style = str(ordered[idx + 1].get("style_name", "")).lower() if idx + 1 < len(ordered) and isinstance(ordered[idx + 1], dict) else ""
        prev_is_caption = "caption" in prev_style
        next_is_caption = "caption" in next_style
        if text.startswith("图") or text.lower().startswith("figure"):
            if idx > 0 and not prev_is_caption:
                figure_scores["below"] += 1
            if idx + 1 < len(ordered) and not next_is_caption:
                figure_scores["above"] += 1
        if text.startswith("表") or text.lower().startswith("table"):
            if idx > 0 and not prev_is_caption:
                table_scores["below"] += 1
            if idx + 1 < len(ordered) and not next_is_caption:
                table_scores["above"] += 1
    if max(figure_scores.values()) > 0:
        rules["figure_caption_position"] = "below" if figure_scores["below"] >= figure_scores["above"] else "above"
    if max(table_scores.values()) > 0:
        rules["table_caption_position"] = "above" if table_scores["above"] >= table_scores["below"] else "below"
    return rules


def build_rule_overrides(profile: dict[str, Any]) -> dict[str, Any]:
    toc_detected = bool(profile.get("paragraph_usage", {}).get("toc_detected"))
    sections = profile.get("sections", [])
    section_rules = []
    for idx, section in enumerate(sections, 1):
        role_guess, reason = guess_section_role(profile, section, idx, len(sections), toc_detected)
        section_rules.append(
            {
                "section_index": idx,
                "role_guess": role_guess,
                "reason": reason,
                "orientation": section.get("page", {}).get("orientation"),
                "page_size_cm": {
                    "width": section.get("page", {}).get("width_cm"),
                    "height": section.get("page", {}).get("height_cm"),
                },
                "header_preview": [
                    " ".join(item.get("text", []))
                    for item in section.get("headers", [])
                    if isinstance(item, dict) and item.get("text")
                ],
                "footer_preview": [
                    " ".join(item.get("text", []))
                    for item in section.get("footers", [])
                    if isinstance(item, dict) and item.get("text")
                ],
            }
        )

    body_start_section_index = None
    for item in section_rules:
        role_guess = str(item.get("role_guess", ""))
        if role_guess in {"body_or_unknown", "body_or_back_matter"}:
            body_start_section_index = int(item["section_index"])
            break
    if body_start_section_index is None:
        body_start_section_index = detect_first_page_number_section(profile)
    toc_section_indices = [
        int(item.get("section_index", 0) or 0)
        for item in section_rules
        if str(item.get("role_guess", "")) == "table_of_contents"
    ]
    back_matter_start_section_index = detect_first_role_section(section_rules, {"back_matter"})

    return {
        "schema_version": "1.0",
        "template_rule_overrides": {
            "source_docx": profile.get("source_docx"),
            "toc": {
                "detected": toc_detected,
                "policy": "update_in_word_before_final_pdf_if_present",
            },
            "section_roles": section_rules,
            "heading_style_map": infer_heading_levels(profile),
            "body_style_candidates": infer_body_style_candidates(profile),
            "reference_style_candidates": infer_reference_style_candidates(profile),
            "caption_style_candidates": infer_caption_style_candidates(profile),
            "body_layout_hints": {
                "paper_size_guess": (
                    f"{sections[0].get('page', {}).get('width_cm')}x{sections[0].get('page', {}).get('height_cm')}cm"
                    if sections
                    else "unknown"
                ),
                "multi_section_template": len(sections) > 1,
                "first_section_role_requires_review": len(sections) > 1,
            },
            "section_header_footer_rules": [
                {
                    "section_index": section.get("index"),
                    "different_first_page": bool(section.get("different_first_page")),
                    "header_types": [item.get("type") for item in section.get("headers", []) if isinstance(item, dict)],
                    "footer_types": [item.get("type") for item in section.get("footers", []) if isinstance(item, dict)],
                    "page_number_start": (section.get("page_number", {}) or {}).get("start"),
                    "page_number_format": (section.get("page_number", {}) or {}).get("format"),
                }
                for section in sections
            ],
            "body_start_section_index": body_start_section_index,
            "toc_section_indices": toc_section_indices,
            "back_matter_start_section_index": back_matter_start_section_index,
            "caption_position_rules": infer_caption_position_rules(profile),
            "manual_review_required": [
                "cover/front-matter role confirmation",
                "TOC field update in Word if TOC exists",
                "page number field continuity",
                "heading level mapping beyond samples",
                "reference-format details not inferable from style extraction alone",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate template rule overrides from template-profile.json.")
    parser.add_argument("template_profile", help="template-profile.json path.")
    parser.add_argument(
        "--out",
        default="paper-context/template-extract/template-rule-overrides.yaml",
        help="Output YAML path.",
    )
    args = parser.parse_args()

    profile_path = Path(args.template_profile).resolve()
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    payload = build_rule_overrides(profile)

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
