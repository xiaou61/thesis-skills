#!/usr/bin/env python3
"""Apply extracted .docx template facts to standard-profile.yaml conservatively."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def detect_paper_size(sections: list[dict[str, Any]]) -> str:
    if not sections:
        return "A4"
    page = sections[0].get("page", {})
    width = page.get("width_cm")
    height = page.get("height_cm")
    if width is None or height is None:
        return "A4"
    dims = sorted([round(width, 2), round(height, 2)])
    if abs(dims[0] - 21.0) < 0.8 and abs(dims[1] - 29.7) < 1.0:
        return "A4"
    if abs(dims[0] - 21.59) < 0.8 and abs(dims[1] - 27.94) < 1.0:
        return "Letter"
    return f"custom_{width}x{height}_cm"


def summarize_margins(section: dict[str, Any]) -> str:
    margins = section.get("margins_cm", {})
    return (
        f"模板主分节检测值：上{margins.get('top')}cm，下{margins.get('bottom')}cm，"
        f"左{margins.get('left')}cm，右{margins.get('right')}cm；需在 Word/PDF 中复核。"
    )


def find_style(profile: dict[str, Any], *style_ids: str) -> dict[str, Any] | None:
    by_id = {item.get("style_id"): item for item in profile.get("styles", []) if isinstance(item, dict)}
    for style_id in style_ids:
        item = by_id.get(style_id)
        if item:
            return item
    return None


def summarize_body_font(profile: dict[str, Any]) -> str:
    normal = find_style(profile, "Normal")
    defaults = profile.get("style_defaults", {})
    font = None
    size = None
    if normal:
        font = normal.get("font_east_asia") or normal.get("font_ascii")
        size = normal.get("font_size_pt")
    if not font:
        font = defaults.get("font_east_asia") or defaults.get("font_ascii")
    if not size:
        size = defaults.get("font_size_pt")
    pieces = []
    if font:
        pieces.append(str(font))
    if size:
        pieces.append(f"{size}pt")
    if not pieces:
        return "模板未明确检测到正文默认字体；需人工确认。"
    return f"模板正文默认样式推测为：{' / '.join(pieces)}；需与学校模板视觉复核。"


def infer_heading_numbering(profile: dict[str, Any]) -> str:
    samples = profile.get("paragraph_usage", {}).get("heading_candidates", [])
    texts = [item.get("text", "") for item in samples if isinstance(item, dict)]
    if any(re.match(r"^第[0-9一二三四五六七八九十]+章", text) for text in texts):
        return "按模板样例推测一级标题使用“第1章”形式；更细层级编号规则需人工确认。"
    if any(re.match(r"^[0-9]+(\.[0-9]+)*", text) for text in texts):
        return "按模板样例推测使用阿拉伯数字分级编号，例如 1、1.1、1.1.1；需人工确认。"
    return "按学校模板；当前无法从样例稳定推断章节编号规则。"


def ensure_unresolved_items(standard_profile: dict[str, Any], items: list[dict[str, str]]) -> None:
    conflict_resolution = standard_profile.setdefault("conflict_resolution", {})
    unresolved = conflict_resolution.setdefault("unresolved", [])
    if not isinstance(unresolved, list):
        unresolved = []
        conflict_resolution["unresolved"] = unresolved

    existing_keys = {str(item.get("item")) for item in unresolved if isinstance(item, dict)}
    for item in items:
        if item["item"] not in existing_keys:
            unresolved.append(item)


def apply_profile(template_profile: dict[str, Any], standard_profile: dict[str, Any], template_path: Path) -> dict[str, Any]:
    standard_profile.setdefault("profile", {})
    standard_profile["profile"]["updated_at"] = date.today().isoformat()
    standard_profile["profile"]["status"] = "needs_confirmation"

    source_priority = standard_profile.setdefault("source_priority", [])
    if source_priority and isinstance(source_priority[0], dict):
        source_priority[0]["file_or_url"] = str(template_path)
        source_priority[0]["confirmation_status"] = "confirmed"
        source_priority[0]["notes"] = "页面、字体、标题、目录、页眉页脚等优先以学校模板为准；已完成首轮自动提取。"

    sections = template_profile.get("sections", [])
    format_defaults = standard_profile.setdefault("format_defaults", {})
    format_defaults["paper_size"] = detect_paper_size(sections)
    if sections:
        format_defaults["page_margin"] = summarize_margins(sections[0])
    format_defaults["body_font"] = summarize_body_font(template_profile)
    format_defaults["heading_numbering"] = infer_heading_numbering(template_profile)

    unresolved_items = [
        {
            "item": "模板自动提取后的格式项人工复核",
            "candidate_sources": [str(template_path), "paper-context/template-extract/template-profile.md"],
            "chosen_source": "needs_confirmation",
            "notes": "需在 Word/PDF 中人工确认封面、目录、页码域、页眉页脚、标题层级和参考文献格式。",
        }
    ]
    if len(sections) > 1:
        unresolved_items.append(
            {
                "item": "多分节模板的分节用途确认",
                "candidate_sources": [str(template_path), "paper-context/template-extract/template-profile.json"],
                "chosen_source": "needs_confirmation",
                "notes": "模板存在多分节，需确认是否用于封面、目录、正文、横向页面或附录。",
            }
        )
    if template_profile.get("paragraph_usage", {}).get("toc_detected"):
        unresolved_items.append(
            {
                "item": "目录域更新策略确认",
                "candidate_sources": [str(template_path)],
                "chosen_source": "needs_confirmation",
                "notes": "模板中检测到 TOC 域，终稿需在 Word 中更新目录并复核页码。",
            }
        )
    ensure_unresolved_items(standard_profile, unresolved_items)
    return standard_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a .docx template extraction profile to standard-profile.yaml.")
    parser.add_argument("template_profile", help="template-profile.json path.")
    parser.add_argument(
        "--standard-profile",
        default="thesis-ai-standard/templates/standard-profile.yaml",
        help="standard-profile.yaml path.",
    )
    parser.add_argument("--template-docx", help="Original .docx template path for source tracking.")
    parser.add_argument("--out", help="Optional output YAML path. Defaults to in-place update.")
    args = parser.parse_args()

    profile_path = Path(args.template_profile).resolve()
    standard_path = Path(args.standard_profile).resolve()
    template_profile = json.loads(profile_path.read_text(encoding="utf-8"))
    standard_profile = load_yaml(standard_path)

    template_docx = Path(args.template_docx).resolve() if args.template_docx else Path(
        template_profile.get("source_docx", profile_path)
    ).resolve()
    updated = apply_profile(template_profile, standard_profile, template_docx)

    out_path = Path(args.out).resolve() if args.out else standard_path
    dump_yaml(out_path, updated)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
